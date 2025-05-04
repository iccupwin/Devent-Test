from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
import logging

from .models import Conversation, Message
from .services import ClaudeService

# Настройка логирования
logger = logging.getLogger(__name__)

def index(request):
    """Отображение главной страницы с чатом"""
    # Получаем или создаем анонимного пользователя
    user, created = User.objects.get_or_create(username='anonymous')
    
    # Получаем список чатов
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    return render(request, 'chat/index.html', {'conversations': conversations})

@csrf_exempt
def send_message(request):
    """API endpoint для отправки сообщений Claude"""
    if request.method == 'POST':
        try:
            logger.info("Получен POST запрос на /api/message/")
            
            # Логируем тело запроса
            body = request.body.decode('utf-8')
            logger.info(f"Тело запроса: {body}")
            
            data = json.loads(body)
            user_message = data.get('message', '')
            conversation_id = data.get('conversation_id')
            
            logger.info(f"Сообщение: {user_message}")
            logger.info(f"ID разговора: {conversation_id}")
            
            # Получаем или создаем анонимного пользователя
            user, created = User.objects.get_or_create(username='anonymous')
            
            # Получение или создание разговора
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id, user=user)
                    logger.info(f"Найден существующий разговор с ID {conversation_id}")
                except Conversation.DoesNotExist:
                    logger.info(f"Разговор с ID {conversation_id} не найден, создаем новый")
                    conversation = Conversation.objects.create(
                        user=user,
                        title=user_message[:30] + "..." if len(user_message) > 30 else user_message
                    )
            else:
                logger.info("Создаем новый разговор")
                conversation = Conversation.objects.create(
                    user=user,
                    title=user_message[:30] + "..." if len(user_message) > 30 else user_message
                )
            
            # Сохранение сообщения пользователя
            user_msg = Message.objects.create(
                conversation=conversation,
                role='user',
                content=user_message
            )
            logger.info(f"Сохранено сообщение пользователя с ID {user_msg.id}")
            
            # Получение всех предыдущих сообщений для контекста
            messages_history = conversation.messages.all()
            formatted_messages = [
                {"role": msg.role, "content": msg.content} 
                for msg in messages_history
            ]
            
            # Отправка сообщения Claude
            logger.info("Отправляем запрос к Claude API")
            claude_service = ClaudeService()
            response = claude_service.send_message(formatted_messages)
            logger.info(f"Получен ответ от Claude API: {response[:100]}...")
            
            # Сохранение ответа от Claude
            assistant_msg = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=response
            )
            logger.info(f"Сохранен ответ от Claude с ID {assistant_msg.id}")
            
            # Обновляем заголовок разговора, если это первое сообщение
            if conversation.messages.count() <= 2:
                conversation.title = user_message[:30] + ("..." if len(user_message) > 30 else "")
                conversation.save()
                logger.info(f"Обновлен заголовок разговора: {conversation.title}")
            
            logger.info("Отправляем успешный ответ клиенту")
            return JsonResponse({
                'message': response,
                'conversation_id': conversation.id
            })
            
        except Exception as e:
            logger.error(f"Ошибка в send_message: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    
    logger.warning("Получен не-POST запрос на /api/message/")
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

def get_conversation(request, conversation_id):
    """Получение конкретного разговора"""
    try:
        # Получаем или создаем анонимного пользователя
        user, created = User.objects.get_or_create(username='anonymous')
        
        conversation = Conversation.objects.get(id=conversation_id, user=user)
        messages = conversation.messages.all()
        
        # Получаем список всех чатов для боковой панели
        conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
        
        return render(request, 'chat/conversation.html', {
            'conversation': conversation,
            'messages': messages,
            'conversations': conversations
        })
    except Conversation.DoesNotExist:
        return redirect('chat:index')
    
