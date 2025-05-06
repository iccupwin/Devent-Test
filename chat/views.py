from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from .models import Conversation, Message, User

def index(request):
    """
    Стартовая страница (главная)
    """
    # Проверка, использовать ли Apple-стиль
    if should_use_apple_style(request):
        return index_apple(request)
        
    # Получаем или создаем анонимного пользователя
    user, created = User.objects.get_or_create(username='anonymous')
    
    # Получаем список бесед
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    return render(request, 'chat/index.html', {
        'conversations': conversations
    })

def index_apple(request):
    """
    Стартовая страница (главная) в стиле Apple
    """
    # Получаем или создаем анонимного пользователя
    user, created = User.objects.get_or_create(username='anonymous')
    
    # Получаем список бесед
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    return render(request, 'chat/index_apple.html', {
        'conversations': conversations
    })

def conversation(request, conversation_id):
    """
    Страница беседы
    """
    # Проверка, использовать ли Apple-стиль
    if should_use_apple_style(request):
        return conversation_apple(request, conversation_id)
        
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

def conversation_apple(request, conversation_id):
    """
    Страница беседы в стиле Apple
    """
    # Получаем или создаем анонимного пользователя
    user, created = User.objects.get_or_create(username='anonymous')
    
    # Получаем список бесед
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    # Получаем текущую беседу
    conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
    
    # Получаем сообщения беседы
    messages = Message.objects.filter(conversation=conversation).order_by('created_at')
    
    return render(request, 'chat/conversation_apple.html', {
        'conversation': conversation,
        'messages': messages,
        'conversations': conversations
    })

def new_conversation(request):
    """
    Создание новой беседы
    """
    if should_use_apple_style(request):
        return new_conversation_apple(request)
        
    if request.method == 'POST':
        # Для демонстрации просто перенаправляем на страницу беседы
        return redirect('chat:conversation', conversation_id=1)
    
    return render(request, 'chat/index.html', {'title': 'Новая беседа'})

def new_conversation_apple(request):
    """
    Создание новой беседы в стиле Apple
    """
    if request.method == 'POST':
        # Для демонстрации просто перенаправляем на страницу беседы
        return redirect('chat:conversation_apple', conversation_id=1)
    
    return render(request, 'chat/index_apple.html', {'title': 'Новая беседа'})

def toggle_style(request):
    """
    Переключатель между обычным и Apple стилем
    """
    # Получаем текущий URL
    next_url = request.GET.get('next', '/')
    
    # Получаем текущую настройку стиля
    current_style = request.COOKIES.get('use_apple_style', '')
    
    # Создаем ответ
    response = HttpResponseRedirect(next_url)
    
    # Переключаем стиль
    if current_style == 'true':
        response.set_cookie('use_apple_style', 'false', max_age=30*24*60*60)  # 30 дней
    else:
        response.set_cookie('use_apple_style', 'true', max_age=30*24*60*60)  # 30 дней
    
    return response

def should_use_apple_style(request):
    """
    Вспомогательная функция для определения стиля
    """
    # Проверяем запрос на явный параметр style
    style_param = request.GET.get('style', '')
    if style_param == 'apple':
        return True
    elif style_param == 'default':
        return False
    
    # Проверяем cookie
    return request.COOKIES.get('use_apple_style', '') == 'true'