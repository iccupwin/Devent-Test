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
from .planfix_cache_service import PlanfixCacheService
from .analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

@shared_task
def refresh_planfix_cache():
    """
    Задача для обновления кэша Planfix
    """
    cache_service = PlanfixCacheService()
    
    try:
        # Проверяем, не выполняется ли уже обновление
        if cache_service.is_updating:
            logger.info("Обновление кэша уже выполняется")
            return
            
        # Устанавливаем флаг обновления
        cache_service.is_updating = True
        
        # Обновляем кэш
        success = cache_service.refresh_all_caches()
        
        if success:
            logger.info("Кэш Planfix успешно обновлен")
            AnalyticsService.log_cache_refresh(success=True)
        else:
            error_msg = cache_service.last_error or "Неизвестная ошибка при обновлении кэша"
            logger.error(f"Ошибка при обновлении кэша: {error_msg}")
            AnalyticsService.log_cache_refresh(success=False, error_message=error_msg)
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Неожиданная ошибка при обновлении кэша: {error_msg}")
        AnalyticsService.log_cache_refresh(success=False, error_message=error_msg)
        
    finally:
        # Сбрасываем флаг обновления
        cache_service.is_updating = False

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