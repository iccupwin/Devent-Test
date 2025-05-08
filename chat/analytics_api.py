# chat/analytics_api.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from .models import Conversation, Message, User, ConversationAnalytics, MessageFeedback
from .conversation_analytics_service import ConversationAnalyticsService

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET"])
def user_stats_api(request):
    """API endpoint для получения статистики активности пользователя"""
    try:
        # Получаем параметры запроса
        days = int(request.GET.get('days', 30))
        
        # Получаем статистику
        stats = ConversationAnalyticsService.get_user_activity_stats(request.user, days=days)
        
        return JsonResponse(stats)
    except Exception as e:
        logger.error(f"Ошибка при получении статистики пользователя: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def conversation_stats_api(request, conversation_id):
    """API endpoint для получения статистики беседы"""
    try:
        # Проверяем доступ к беседе
        conversation = Conversation.objects.get(id=conversation_id)
        if conversation.user != request.user and not request.user.is_admin():
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)
        
        # Обновляем аналитику
        analytics = ConversationAnalyticsService.update_conversation_analytics(conversation_id)
        
        if not analytics:
            return JsonResponse({'error': 'Не удалось получить аналитику'}, status=404)
        
        # Формируем ответ
        response = {
            'conversation_id': conversation_id,
            'title': conversation.title,
            'total_messages': analytics.total_messages,
            'total_tokens': analytics.total_tokens,
            'average_response_time': analytics.average_response_time,
            'first_message_time': analytics.first_message_time.isoformat() if analytics.first_message_time else None,
            'last_message_time': analytics.last_message_time.isoformat() if analytics.last_message_time else None,
            'total_duration': str(analytics.total_duration) if analytics.total_duration else None,
            'related_planfix_tasks': analytics.related_planfix_tasks,
            'tags': list(analytics.tags.values('id', 'name', 'color'))
        }
        
        return JsonResponse(response)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Беседа не найдена'}, status=404)
    except Exception as e:
        logger.error(f"Ошибка при получении статистики беседы {conversation_id}: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def add_message_feedback_api(request, message_id):
    """API endpoint для добавления обратной связи к сообщению"""
    try:
        # Получаем параметры запроса
        data = json.loads(request.body)
        feedback_type = data.get('feedback_type')
        comment = data.get('comment')
        
        # Проверяем параметры
        if not feedback_type:
            return JsonResponse({'error': 'Тип обратной связи обязателен'}, status=400)
        
        # Проверяем доступ к сообщению
        message = Message.objects.get(id=message_id)
        if message.conversation.user != request.user and not request.user.is_admin():
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)
        
        # Добавляем обратную связь
        feedback = ConversationAnalyticsService.add_message_feedback(
            message_id=message_id,
            user=request.user,
            feedback_type=feedback_type,
            comment=comment
        )
        
        if not feedback:
            return JsonResponse({'error': 'Не удалось добавить обратную связь'}, status=500)
        
        return JsonResponse({
            'success': True,
            'message_id': message_id,
            'feedback_type': feedback.feedback_type
        })
    except Message.DoesNotExist:
        return JsonResponse({'error': 'Сообщение не найдено'}, status=404)
    except Exception as e:
        logger.error(f"Ошибка при добавлении обратной связи к сообщению {message_id}: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def add_conversation_tag_api(request, conversation_id):
    """API endpoint для добавления тега к беседе"""
    try:
        # Получаем параметры запроса
        data = json.loads(request.body)
        tag_name = data.get('tag_name')
        tag_description = data.get('tag_description')
        tag_color = data.get('tag_color')
        
        # Проверяем параметры
        if not tag_name:
            return JsonResponse({'error': 'Название тега обязательно'}, status=400)
        
        # Проверяем доступ к беседе
        conversation = Conversation.objects.get(id=conversation_id)
        if conversation.user != request.user and not request.user.is_admin():
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)
        
        # Добавляем тег
        success = ConversationAnalyticsService.add_conversation_tag(
            conversation_id=conversation_id,
            tag_name=tag_name,
            tag_description=tag_description,
            tag_color=tag_color
        )
        
        if not success:
            return JsonResponse({'error': 'Не удалось добавить тег'}, status=500)
        
        return JsonResponse({
            'success': True,
            'conversation_id': conversation_id,
            'tag_name': tag_name
        })
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Беседа не найдена'}, status=404)
    except Exception as e:
        logger.error(f"Ошибка при добавлении тега к беседе {conversation_id}: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)