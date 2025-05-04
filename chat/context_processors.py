from django.contrib.auth.models import User
from .models import Conversation

def conversations_list(request):
    """
    Добавляет список разговоров в контекст всех шаблонов
    """
    # Получаем или создаем анонимного пользователя
    user, created = User.objects.get_or_create(username='anonymous')
    
    # Получаем список разговоров
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    return {
        'conversations': conversations
    }