from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import time

from .planfix_service import (
    get_all_tasks,
    get_active_tasks,
    get_completed_tasks,
    get_projects,
    update_tasks_cache
)

# Настройка логирования
logger = logging.getLogger(__name__)

# Размер страницы для отображения в UI
UI_PAGE_SIZE = 25

def projects_api(request):
    """API endpoint для получения списка проектов"""
    projects = get_projects()
    return JsonResponse(projects, safe=False)

def tasks_api(request):
    """
    API endpoint для получения задач с пагинацией из кэша
    
    GET-параметры:
    - page: номер страницы (начиная с 0)
    - status: статус задач (active, completed, all)
    - page_size: размер страницы (опционально, по умолчанию UI_PAGE_SIZE)
    """
    # Получаем параметры запроса
    page = int(request.GET.get('page', 0))
    status_param = request.GET.get('status', 'all').lower()
    page_size = int(request.GET.get('page_size', UI_PAGE_SIZE))
    
    logger.info(f"Запрос задач: page={page}, status={status_param}, page_size={page_size}")
    
    # Получаем задачи в зависимости от статуса
    if status_param == 'active':
        tasks = get_active_tasks()
    elif status_param == 'completed':
        tasks = get_completed_tasks()
    else:  # 'all' по умолчанию
        tasks = get_all_tasks()
    
    # Считаем общее количество страниц
    total_count = len(tasks)
    total_pages = (total_count + page_size - 1) // page_size  # Округление вверх
    
    # Получаем задачи для текущей страницы
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, total_count)
    page_tasks = tasks[start_idx:end_idx]
    
    # Формируем ответ
    response = {
        'tasks': page_tasks,
        'pagination': {
            'current_page': page,
            'total_count': total_count,
            'page_size': page_size,
            'total_pages': total_pages
        }
    }
    
    return JsonResponse(response)

@csrf_exempt
def force_update_cache(request):
    """
    API endpoint для принудительного обновления кэша задач
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Требуется метод POST'}, status=405)
    
    try:
        logger.info("Запрос на принудительное обновление кэша задач")
        
        # Вызываем обновление кэша с принудительным флагом
        all_tasks = update_tasks_cache(force=True)
        
        # Возвращаем информацию о том, сколько задач было загружено
        return JsonResponse({
            'success': True,
            'total_tasks': len(all_tasks),
            'updated_at': time.time()
        })
    except Exception as e:
        logger.error(f"Ошибка при обновлении кэша: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)