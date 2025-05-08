# chat/analytics_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .models import Conversation, Message, User, ConversationAnalytics, MessageFeedback
from .conversation_analytics_service import ConversationAnalyticsService

@login_required
def user_analytics_view(request):
    """Страница с аналитикой пользователя"""
    days = int(request.GET.get('days', 30))
    
    # Получение статистики
    stats = ConversationAnalyticsService.get_user_activity_stats(request.user, days=days)
    
    # Получение последних бесед
    recent_conversations = Conversation.objects.filter(
        user=request.user
    ).order_by('-updated_at')[:10]
    
    return render(request, 'chat/analytics/user_analytics.html', {
        'stats': stats,
        'recent_conversations': recent_conversations,
        'days': days
    })

@login_required
def conversation_analytics_view(request, conversation_id):
    """Страница с аналитикой беседы"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Проверка доступа
    if conversation.user != request.user and not request.user.is_admin():
        return redirect('chat:access_denied')
    
    # Обновление аналитики
    analytics = ConversationAnalyticsService.update_conversation_analytics(conversation_id)
    
    # Получение сообщений
    messages = Message.objects.filter(conversation=conversation).order_by('created_at')
    
    # Получение обратной связи
    feedback = MessageFeedback.objects.filter(
        message__conversation=conversation,
        user=request.user
    ).values('message_id', 'feedback_type')
    
    # Создаем словарь обратной связи для удобства
    feedback_dict = {item['message_id']: item['feedback_type'] for item in feedback}
    
    return render(request, 'chat/analytics/conversation_analytics.html', {
        'conversation': conversation,
        'analytics': analytics,
        'messages': messages,
        'feedback_dict': feedback_dict
    })