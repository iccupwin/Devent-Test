# chat/analytics_api.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from .models import Conversation, Message, User, UserMetrics, AnalyticsEvent
from .conversation_analytics_service import ConversationAnalyticsService

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET"])
def user_stats_api(request):
    """API endpoint для получения статистики пользователя"""
    user = request.user
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    metrics = UserMetrics.objects.filter(
        user=user,
        day__range=[start_date, end_date]
    ).order_by('day')
    
    data = {
        'conversations_count': sum(m.conversations_count for m in metrics),
        'messages_sent': sum(m.messages_sent for m in metrics),
        'tokens_used': sum(m.tokens_used for m in metrics),
        'tasks_integrated': sum(m.tasks_integrated for m in metrics),
        'average_response_time': sum(m.average_response_time for m in metrics) / len(metrics) if metrics else 0,
        'daily_stats': [
            {
                'day': m.day.isoformat(),
                'conversations_count': m.conversations_count,
                'messages_sent': m.messages_sent,
                'tokens_used': m.tokens_used,
                'tasks_integrated': m.tasks_integrated,
                'average_response_time': m.average_response_time
            }
            for m in metrics
        ]
    }
    
    return JsonResponse(data)

@login_required
@require_http_methods(["GET"])
def conversation_stats_api(request, conversation_id):
    """API endpoint для получения статистики беседы"""
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    
    messages = Message.objects.filter(conversation=conversation)
    
    data = {
        'total_messages': messages.count(),
        'total_tokens': sum(m.tokens for m in messages),
        'user_messages': messages.filter(role='user').count(),
        'assistant_messages': messages.filter(role='assistant').count(),
        'system_messages': messages.filter(role='system').count(),
        'first_message_time': messages.order_by('created_at').first().created_at if messages.exists() else None,
        'last_message_time': messages.order_by('-created_at').first().created_at if messages.exists() else None,
    }
    
    return JsonResponse(data)

@login_required
@require_http_methods(["POST"])
def add_message_feedback_api(request, message_id):
    """API endpoint для добавления обратной связи по сообщению"""
    try:
        message = Message.objects.get(id=message_id, conversation__user=request.user)
    except Message.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)
    
    feedback_type = request.POST.get('feedback_type')
    comment = request.POST.get('comment', '')
    
    if not feedback_type:
        return JsonResponse({'error': 'Feedback type is required'}, status=400)
    
    # Создаем событие аналитики
    AnalyticsEvent.objects.create(
        user=request.user,
        event_type='message_feedback',
        conversation=message.conversation,
        metadata={
            'message_id': message.id,
            'feedback_type': feedback_type,
            'comment': comment
        }
    )
    
    return JsonResponse({'status': 'success'})

@login_required
@require_http_methods(["POST"])
def add_conversation_tag_api(request, conversation_id):
    """API endpoint для добавления тега к беседе"""
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    
    tag_name = request.POST.get('tag_name')
    if not tag_name:
        return JsonResponse({'error': 'Tag name is required'}, status=400)
    
    # Создаем событие аналитики
    AnalyticsEvent.objects.create(
        user=request.user,
        event_type='conversation_tag',
        conversation=conversation,
        metadata={'tag_name': tag_name}
    )
    
    return JsonResponse({'status': 'success'})