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
def refresh_planfix_cache():
    """
    Периодическое обновление кэша данных Planfix
    """
    logger.info("Starting Planfix cache refresh (scheduled)")
    try:
        from .planfix_service import update_tasks_cache
        from .planfix_cache_service import planfix_cache
        
        # Обновление основного кэша задач
        tasks = update_tasks_cache(force=True)
        logger.info(f"Main tasks cache updated, {len(tasks)} tasks loaded")
        
        # Обновление производных кэшей
        planfix_cache.refresh_all_caches()
        logger.info("All derived caches refreshed")
        
        # Получение обновленной статистики
        stats = planfix_cache.get_stats()
        
        # Логирование статистики
        logger.info(f"Total tasks: {stats.get('total_tasks', 0)}")
        logger.info(f"Active tasks: {stats.get('active_tasks', 0)}")
        logger.info(f"Completed tasks: {stats.get('completed_tasks', 0)}")
        logger.info(f"Overdue tasks: {stats.get('overdue_tasks', 0)}")
        
        return "Cache refresh completed successfully"
    except Exception as e:
        logger.error(f"Error refreshing Planfix cache: {e}", exc_info=True)
        return f"Error refreshing cache: {str(e)}"
    
    
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