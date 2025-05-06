import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Conversation, Message, User
from .services import ClaudeService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def message_api(request):
    """API endpoint для отправки сообщений в Claude и получения ответов"""
    try:
        # Parse request data
        data = json.loads(request.body)
        message_text = data.get('message', '')
        conversation_id = data.get('conversation_id')
        
        # Validate message
        if not message_text:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get or create anonymous user
        user, created = User.objects.get_or_create(username='anonymous')
        
        # Get or create conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id, user=user)
            except Conversation.DoesNotExist:
                return JsonResponse({'error': 'Conversation not found'}, status=404)
        else:
            # Create a new conversation - use first few words as title
            title = ' '.join(message_text.split()[:5]) + '...'
            conversation = Conversation.objects.create(
                user=user,
                title=title
            )
        
        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_text
        )
        
        # Get previous messages for context (limit to last 10 for simplicity)
        previous_messages = Message.objects.filter(conversation=conversation).order_by('created_at')
        
        # Format messages for Claude API
        messages_for_claude = []
        for msg in previous_messages:
            if not messages_for_claude and msg.role == 'assistant':
                # Если первое сообщение от ассистента, добавим перед ним виртуальное сообщение от пользователя
                messages_for_claude.append({
                    "role": "user",
                    "content": "Привет, давай начнем разговор."
                })
            
            messages_for_claude.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Send to Claude API
        claude_service = ClaudeService()
        claude_response = claude_service.send_message(messages_for_claude)
        
        # Save Claude's response
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=claude_response
        )
        
        # Update conversation's updated_at timestamp
        conversation.save()
        
        # Return response
        return JsonResponse({
            'message': claude_response,
            'conversation_id': conversation.id
        })
        
    except Exception as e:
        logger.error(f"Error in message API: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def conversations_api(request):
    """API эндпоинт для получения списка бесед"""
    try:
        # Получаем анонимного пользователя
        user, created = User.objects.get_or_create(username='anonymous')
        
        # Получаем беседы
        conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
        
        # Форматируем ответ
        conversations_data = []
        for conversation in conversations:
            # Получаем первое сообщение как превью
            first_message = Message.objects.filter(conversation=conversation).order_by('created_at').first()
            preview = first_message.content[:50] + '...' if first_message else 'Пустая беседа'
            
            conversations_data.append({
                'id': conversation.id,
                'title': conversation.title,
                'preview': preview,
                'updated_at': conversation.updated_at.isoformat()
            })
        
        return JsonResponse({'conversations': conversations_data})
        
    except Exception as e:
        logger.error(f"Ошибка в API бесед: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
    
def task_api(request, task_id):
    """API endpoint для получения данных задачи"""
    try:
        # Получаем задачу из Planfix
        from .planfix_service import get_task_by_id
        task = get_task_by_id(task_id)
        
        if not task:
            return JsonResponse({'error': 'Задача не найдена'}, status=404)
        
        return JsonResponse(task)
    except Exception as e:
        logger.error(f"Ошибка при получении задачи {task_id}: {e}", exc_info=True)
        return JsonResponse({'error': 'Не удалось загрузить задачу', 'message': str(e)}, status=500)