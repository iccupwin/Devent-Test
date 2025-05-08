# chat/analytics_service.py
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from .models import (
    AnalyticsEvent, Message, User, AIModel, Conversation,
    AIModelMetrics, UserMetrics
)

class AnalyticsService:
    @staticmethod
    def get_ai_models_usage(days=30):
        """Получение статистики использования моделей ИИ"""
        start_date = timezone.now().date() - timedelta(days=days)
        
        models_usage = AIModelMetrics.objects.filter(
            day__gte=start_date
        ).values('ai_model__name').annotate(
            total_requests=Sum('requests_count'),
            total_tokens=Sum('tokens_used')
        ).order_by('-total_requests')
        
        return models_usage
    
    @staticmethod
    def get_daily_activity(days=30):
        """Получение ежедневной активности"""
        start_date = timezone.now().date() - timedelta(days=days)
        end_date = timezone.now().date()
        
        # Создаем полный список дат
        date_list = []
        current = start_date
        while current <= end_date:
            date_list.append(current)
            current += timedelta(days=1)
        
        # Получаем данные активности
        daily_data = UserMetrics.objects.filter(
            day__gte=start_date
        ).values('day').annotate(
            messages_count=Sum('messages_sent'),
            conversations_count=Sum('conversations_count')
        ).order_by('day')
        
        # Преобразуем в словарь для быстрого доступа
        data_dict = {item['day']: item for item in daily_data}
        
        # Форматируем результат
        result = []
        for date in date_list:
            if date in data_dict:
                result.append({
                    'day': date.strftime('%Y-%m-%d'),
                    'messages_count': data_dict[date]['messages_count'],
                    'conversations_count': data_dict[date]['conversations_count']
                })
            else:
                result.append({
                    'day': date.strftime('%Y-%m-%d'),
                    'messages_count': 0,
                    'conversations_count': 0
                })
        
        return result
    
    @staticmethod
    def get_tokens_usage(days=30):
        """Получение статистики использования токенов"""
        start_date = timezone.now().date() - timedelta(days=days)
        
        tokens_data = UserMetrics.objects.filter(
            day__gte=start_date
        ).values('day').annotate(
            tokens_used=Sum('tokens_used')
        ).order_by('day')
        
        return tokens_data
    
    @staticmethod
    def get_top_users(limit=10, days=30):
        """Получение топ пользователей по активности"""
        start_date = timezone.now().date() - timedelta(days=days)
        
        top_users = UserMetrics.objects.filter(
            day__gte=start_date
        ).values(
            'user__username',
            'user__first_name',
            'user__last_name'
        ).annotate(
            total_messages=Sum('messages_sent'),
            total_conversations=Sum('conversations_count'),
            total_tokens=Sum('tokens_used')
        ).order_by('-total_messages')[:limit]
        
        return top_users

# Пример использования в agent_api.py
# from .analytics_service import AnalyticsService
# 
# # В методе обработки сообщения:
# AnalyticsService.track_message_sent(user, user_message)
# 
# # После получения ответа от ИИ:
# AnalyticsService.track_ai_response(user, assistant_message, ai_model, response_time)