# chat/conversation_analytics_service.py
import logging
from django.db.models import Count, Sum, Avg, F, Q
from django.utils import timezone
from datetime import timedelta

from .models import Conversation, Message, User, AnalyticsEvent

logger = logging.getLogger(__name__)

class ConversationAnalyticsService:
    """
    Сервис для работы с аналитикой бесед
    """
    
    @staticmethod
    def get_conversation_statistics(user=None, days=30):
        """
        Получение статистики по беседам за указанный период
        
        Args:
            user: Пользователь (None для всех пользователей)
            days: Количество дней для анализа
        
        Returns:
            Словарь со статистикой
        """
        start_date = timezone.now() - timedelta(days=days)
        
        # Базовый фильтр по дате
        conversations = Conversation.objects.filter(created_at__gte=start_date)
        
        # Фильтр по пользователю, если указан
        if user:
            conversations = conversations.filter(user=user)
        
        # Получение статистики
        total_conversations = conversations.count()
        total_messages = Message.objects.filter(conversation__in=conversations).count()
        
        # Среднее количество сообщений в беседе
        avg_messages_per_conversation = total_messages / total_conversations if total_conversations > 0 else 0
        
        # Статистика по AI моделям
        model_stats = Message.objects.filter(
            conversation__in=conversations,
            role='assistant'
        ).values('ai_model_used__name').annotate(
            count=Count('id'),
            tokens=Sum('tokens')
        ).order_by('-count')
        
        # Интеграция с Planfix
        planfix_integrations = conversations.filter(planfix_task_id__isnull=False).count()
        
        # Результат
        stats = {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'avg_messages_per_conversation': round(avg_messages_per_conversation, 2),
            'model_stats': list(model_stats),
            'planfix_integrations': planfix_integrations,
            'period_days': days
        }
        
        return stats
    
    @staticmethod
    def get_user_activity_stats(user, days=30):
        """
        Получение статистики активности пользователя
        
        Args:
            user: Объект пользователя
            days: Количество дней для анализа
        
        Returns:
            Словарь со статистикой активности
        """
        start_date = timezone.now() - timedelta(days=days)
        
        # Беседы пользователя
        conversations = Conversation.objects.filter(user=user, created_at__gte=start_date)
        
        # Сообщения пользователя
        user_messages = Message.objects.filter(
            conversation__in=conversations,
            role='user',
            created_at__gte=start_date
        )
        
        # Сообщения ассистента
        assistant_messages = Message.objects.filter(
            conversation__in=conversations,
            role='assistant',
            created_at__gte=start_date
        )
        
        # Активность по дням
        daily_activity = user_messages.values('created_at__date').annotate(
            count=Count('id')
        ).order_by('created_at__date')
        
        # Токены
        total_tokens = assistant_messages.aggregate(Sum('tokens'))['tokens__sum'] or 0
        
        # Результат
        stats = {
            'total_conversations': conversations.count(),
            'total_user_messages': user_messages.count(),
            'total_assistant_messages': assistant_messages.count(),
            'total_tokens': total_tokens,
            'daily_activity': list(daily_activity),
            'period_days': days
        }
        
        return stats