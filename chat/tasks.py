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
from .vector_service import upsert_message, upsert_planfix_task

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

# === ВНИЗУ ФАЙЛА ===

@shared_task
def vectorize_message(message_id: int):
    """
    Векторизует новое сообщение и складывает в Qdrant
    """
    from .models import Message  # локальный импорт, чтобы избежать круговой зависимости
    msg = Message.objects.select_related('conversation').get(pk=message_id)
    meta = {
        "conversation_id": msg.conversation_id,
        "role": msg.role,
        "created_at": msg.created_at.isoformat()
    }
    upsert_message(msg.id, msg.content, meta)

@shared_task
def update_planfix_vector_store():
    """
    Периодическая задача для обновления данных Planfix в векторном хранилище.
    Запускается каждые 5 минут.
    """
    try:
        # Получаем все активные задачи из Planfix
        planfix_tasks = planfix_cache.get_all_tasks()
        
        # Обновляем каждую задачу в векторном хранилище
        for task in planfix_tasks:
            upsert_planfix_task(task['id'], task)
            
        logger.info(f"Successfully updated {len(planfix_tasks)} tasks in vector store")
        
    except Exception as e:
        logger.error(f"Error updating Planfix vector store: {str(e)}")
        raise
