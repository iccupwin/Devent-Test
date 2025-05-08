# chat/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Avg
import logging

from .models import (
    User, Conversation, Message, AIModel,
    UserMetrics, AIModelMetrics, AnalyticsEvent
)

logger = logging.getLogger(__name__)

@shared_task
def update_daily_metrics():
    """
    Ежедневное обновление метрик пользователей и ИИ-моделей
    """
    logger.info("Starting daily metrics update")
    yesterday = timezone.now().date() - timedelta(days=1)
    
    # Обновление метрик пользователей
    active_users = User.objects.filter(
        messages__created_at__date=yesterday
    ).distinct()
    
    for user in active_users:
        # Получение данных о беседах пользователя
        conversations = Conversation.objects.filter(
            user=user,
            messages__created_at__date=yesterday
        ).distinct()
        
        # Получение данных о сообщениях пользователя
        user_messages = Message.objects.filter(
            conversation__user=user,
            created_at__date=yesterday,
            role='user'
        )
        
        # Получение данных об интеграциях с задачами
        task_integrations = Conversation.objects.filter(
            user=user,
            planfix_task_id__isnull=False,
            created_at__date=yesterday
        ).count()
        
        # Получение данных о времени ответа
        assistant_messages = Message.objects.filter(
            conversation__user=user,
            created_at__date=yesterday,
            role='assistant'
        )
        
        total_response_time = 0
        avg_response_time = 0
        
        if assistant_messages.exists():
            # Расчет среднего времени ответа
            for msg in assistant_messages:
                # Находим предшествующее сообщение пользователя
                try:
                    user_msg = Message.objects.filter(
                        conversation=msg.conversation,
                        role='user',
                        created_at__lt=msg.created_at
                    ).latest('created_at')
                    
                    # Расчет времени ответа
                    response_time = (msg.created_at - user_msg.created_at).total_seconds()
                    total_response_time += response_time
                    
                except Message.DoesNotExist:
                    continue
            
            avg_response_time = total_response_time / assistant_messages.count() if assistant_messages.count() > 0 else 0
        
        # Создание или обновление метрик пользователя
        UserMetrics.objects.update_or_create(
            user=user,
            day=yesterday,
            defaults={
                'conversations_count': conversations.count(),
                'messages_sent': user_messages.count(),
                'tokens_used': user_messages.aggregate(Sum('tokens'))['tokens__sum'] or 0,
                'tasks_integrated': task_integrations,
                'average_response_time': avg_response_time
            }
        )
    
    # Обновление метрик ИИ-моделей
    ai_models = AIModel.objects.filter(is_active=True)
    
    for model in ai_models:
        # Количество запросов к модели
        requests = Message.objects.filter(
            ai_model_used=model,
            created_at__date=yesterday,
            role='assistant'
        )
        
        # Количество использованных токенов
        tokens = requests.aggregate(Sum('tokens'))['tokens__sum'] or 0
        
        # Среднее время ответа
        avg_response_time = 0
        total_response_time = 0
        
        if requests.exists():
            for msg in requests:
                try:
                    user_msg = Message.objects.filter(
                        conversation=msg.conversation,
                        role='user',
                        created_at__lt=msg.created_at
                    ).latest('created_at')
                    
                    response_time = (msg.created_at - user_msg.created_at).total_seconds()
                    total_response_time += response_time
                    
                except Message.DoesNotExist:
                    continue
            
            avg_response_time = total_response_time / requests.count() if requests.count() > 0 else 0
        
        # Количество ошибок
        errors = AnalyticsEvent.objects.filter(
            event_type='error',
            ai_model=model,
            timestamp__date=yesterday
        ).count()
        
        # Создание или обновление метрик модели
        AIModelMetrics.objects.update_or_create(
            ai_model=model,
            day=yesterday,
            defaults={
                'requests_count': requests.count(),
                'tokens_used': tokens,
                'average_response_time': avg_response_time,
                'error_count': errors
            }
        )
    
    logger.info("Daily metrics update completed")
    
    return "Metrics updated successfully"

@shared_task
def cleanup_old_data():
    """
    Очистка старых данных аналитики для экономии места в базе данных
    """
    # Удаление событий аналитики старше 3 месяцев
    three_months_ago = timezone.now() - timedelta(days=90)
    AnalyticsEvent.objects.filter(timestamp__lt=three_months_ago).delete()
    
    logger.info("Old analytics data cleanup completed")
    
    return "Old data cleaned up successfully"