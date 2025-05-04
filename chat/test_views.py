from django.http import JsonResponse
from django.shortcuts import render
import logging
from .planfix_service import get_all_tasks, get_active_tasks, get_completed_tasks

# Настройка логирования
logger = logging.getLogger(__name__)

def test_planfix_api(request):
    """Тестовое представление для проверки работы с Planfix API"""
    try:
        # Получаем задачи
        all_tasks = get_all_tasks()
        active_tasks = get_active_tasks()
        completed_tasks = get_completed_tasks()
        
        # Возвращаем JSON с данными
        return JsonResponse({
            'success': True,
            'all_tasks_count': len(all_tasks),
            'active_tasks_count': len(active_tasks),
            'completed_tasks_count': len(completed_tasks),
            'sample_tasks': all_tasks[:5] if all_tasks else []
        })
    except Exception as e:
        logger.error(f"Ошибка при тестировании Planfix API: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)