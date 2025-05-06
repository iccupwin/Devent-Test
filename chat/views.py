from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Conversation, Message, User

def index(request):
    """
    Стартовая страница (главная)
    """
    # Получаем или создаем анонимного пользователя
    user, created = User.objects.get_or_create(username='anonymous')
    
    # Получаем список бесед
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    return render(request, 'chat/index.html', {
        'conversations': conversations
    })

def conversation(request, conversation_id):
    """
    Страница беседы
    """
    # Получаем или создаем анонимного пользователя
    user, created = User.objects.get_or_create(username='anonymous')
    
    # Получаем список бесед
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    # Получаем текущую беседу
    conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
    
    # Получаем сообщения беседы
    messages = Message.objects.filter(conversation=conversation).order_by('created_at')
    
    return render(request, 'chat/conversation.html', {
        'conversation': conversation,
        'messages': messages,
        'conversations': conversations
    })

def new_conversation(request):
    """
    Создание новой беседы
    """
    if request.method == 'POST':
        # Для демонстрации просто перенаправляем на страницу беседы
        return redirect('chat:conversation', conversation_id=1)
    
    return render(request, 'chat/index.html', {'title': 'Новая беседа'})