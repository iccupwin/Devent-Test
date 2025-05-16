import json
import logging
import time
import os
from pathlib import Path
from django.conf import settings
from typing import List, Dict, Any
from .planfix_api import get_projects, get_tasks_page, get_task_detail

# Настройка логирования
logger = logging.getLogger(__name__)

# Путь к директории для кэш-файлов
BASE_DIR = Path(settings.BASE_DIR)
CACHE_DIR = BASE_DIR / 'chat' / 'cache'
TASKS_CACHE_FILE = CACHE_DIR / 'tasks_cache.json'
LAST_UPDATE_FILE = CACHE_DIR / 'last_update.txt'

def get_all_tasks(force_update=False):
    """
    Получение всех задач из кэша или API
    
    :param force_update: Принудительное обновление кэша
    :return: Список всех задач
    """
    return update_tasks_cache(force=force_update)

# Инициализация кэша
def init_cache():
    """Инициализирует директорию кэша и файлы"""
    # Проверяем и создаем директорию кэша, если она не существует
    if not CACHE_DIR.exists():
        logger.info(f"Создание директории кэша: {CACHE_DIR}")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Создаем пустой файл кэша задач
        with open(TASKS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        
        # Создаем файл с временем последнего обновления
        with open(LAST_UPDATE_FILE, 'w') as f:
            # Устанавливаем время так, чтобы первый запрос обновил кэш
            f.write(str(time.time() - 7200))  # 2 часа назад
        
        logger.info("Кэш Planfix инициализирован")
    else:
        # Проверяем существование файлов кэша
        if not TASKS_CACHE_FILE.exists():
            with open(TASKS_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
        
        if not LAST_UPDATE_FILE.exists():
            with open(LAST_UPDATE_FILE, 'w') as f:
                f.write(str(time.time() - 7200))  # 2 часа назад

# Инициализируем кэш при загрузке модуля
init_cache()

def update_tasks_cache(force=False):
    """
    Проверяет и обновляет кэш задач если прошло более часа
    с последнего обновления или если force=True
    
    :param force: Принудительное обновление кэша
    :return: Список всех задач
    """
    # Проверяем, существуют ли файлы кэша
    cache_exists = TASKS_CACHE_FILE.exists() and LAST_UPDATE_FILE.exists()
    
    # Определяем, нужно ли обновлять кэш
    need_update = True
    if cache_exists and not force:
        # Получаем время последнего обновления
        with open(LAST_UPDATE_FILE, 'r') as f:
            last_update_str = f.read().strip()
            try:
                last_update = float(last_update_str)
                # Проверяем, прошел ли час с последнего обновления
                need_update = (time.time() - last_update) > 3600  # 3600 секунд = 1 час
            except ValueError:
                need_update = True
    
    # Если нужно обновить кэш или файлы кэша не существуют
    if need_update or not cache_exists or force:
        logger.info(f"Обновление кэша задач Planfix")
        all_tasks = []
        page = 0
        more_pages = True
        
        # Загружаем все страницы задач
        while more_pages:
            result = get_tasks_page(page)
            tasks = result.get('tasks', [])
            
            if not tasks:
                more_pages = False
            else:
                all_tasks.extend(tasks)
                page += 1
                
                # Проверяем, есть ли еще задачи по размеру страницы
                if len(tasks) < 100:  # 100 - максимальное количество задач на странице
                    more_pages = False
        
        # Отладочный вывод
        logger.info(f"Загружено всего задач: {len(all_tasks)}")
        if all_tasks:
            task_sample = all_tasks[0]
            logger.info(f"Пример задачи: {json.dumps(task_sample, ensure_ascii=False)}")
            if 'project' in task_sample:
                logger.info(f"Информация о проекте: {json.dumps(task_sample['project'], ensure_ascii=False)}")

        # Получаем актуальный список проектов
        all_projects = get_projects()
        logger.info(f"Получено проектов: {len(all_projects)}")
        
        # Создаем карту проектов для быстрого доступа по ID
        project_map = {}
        for project in all_projects:
            if 'id' in project and 'name' in project and project['name']:
                project_map[str(project['id'])] = project['name']
        
        logger.info(f"Создана карта проектов с {len(project_map)} элементами")
        
        # Проверяем, что данные проектов корректны
        projects_fixed = 0
        for task in all_tasks:
            if 'project' in task and task['project'] is not None:
                project = task['project']
                
                # Если у проекта нет имени или имя в формате "Проект ID", исправляем его
                if 'name' not in project or project['name'] is None or project['name'].startswith('Проект '):
                    # Если ID проекта есть в карте, устанавливаем правильное имя
                    if 'id' in project and str(project['id']) in project_map:
                        project['name'] = project_map[str(project['id'])]
                        projects_fixed += 1
                        logger.debug(f"Исправлен проект {project['id']}: {project['name']}")
                    # Иначе используем ID как часть имени
                    elif 'id' in project:
                        project['name'] = f"Проект {project['id']}"
                        logger.debug(f"Создано имя для проекта {project['id']}")
        
        logger.info(f"Исправлено проектов: {projects_fixed}")
        
        # Сохраняем задачи в кэш
        with open(TASKS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_tasks, f, ensure_ascii=False, indent=2)
        
        # Обновляем время последнего обновления
        with open(LAST_UPDATE_FILE, 'w') as f:
            f.write(str(time.time()))
            
        return all_tasks
    else:
        # Загружаем задачи из кэша
        with open(TASKS_CACHE_FILE, 'r', encoding='utf-8') as f:
            all_tasks = json.load(f)
        return all_tasks

def get_active_tasks():
    """
    Получение активных задач (не завершенных)
    
    :return: Список активных задач
    """
    all_tasks = get_all_tasks()
    return [
        task for task in all_tasks 
        if not is_task_completed(task)
    ]

def get_completed_tasks():
    """
    Получение завершенных задач
    
    :return: Список завершенных задач
    """
    all_tasks = get_all_tasks()
    return [
        task for task in all_tasks 
        if is_task_completed(task)
    ]

def is_task_completed(task):
    """
    Проверяет, является ли задача завершенной
    
    :param task: Задача Planfix
    :return: True, если задача завершена
    """
    status = task.get('status', {})
    status_name = status.get('name', '').lower()
    status_id = status.get('id')
    
    return (
        'завершен' in status_name or 
        'completed' in status_name or 
        status_id == 3
    )

def get_task_by_id(task_id):
    """
    Получение задачи по ID из кэша или API
    
    :param task_id: ID задачи
    :return: Задача или None, если не найдена
    """
    # Преобразуем task_id в строку для сравнения
    task_id_str = str(task_id)
    
    # Логирование запроса
    logger.info(f"Запрос задачи с ID {task_id_str}")
    
    # Сначала пытаемся найти в кэше
    all_tasks = get_all_tasks()
    logger.debug(f"Поиск задачи {task_id_str} в кэше, всего задач: {len(all_tasks)}")
    
    for task in all_tasks:
        if str(task.get('id')) == task_id_str:
            logger.info(f"Задача {task_id_str} найдена в кэше")
            return task
    
    # Если в кэше нет, запрашиваем напрямую через API
    try:
        logger.info(f"Задача {task_id_str} не найдена в кэше, запрашиваем из API")
        task = get_task_detail(task_id)
        
        if task:
            logger.info(f"Задача {task_id_str} успешно получена из API")
            return task
        else:
            logger.warning(f"API вернул пустой результат для задачи {task_id_str}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при получении задачи {task_id_str} через API: {str(e)}", exc_info=True)
        return None

def format_task_for_claude(task):
    """
    Форматирует задачу из Planfix для представления в чате.
    
    Args:
        task: задача из Planfix
    
    Returns:
        отформатированное представление задачи
    """
    if not task:
        return "Задача не найдена"
    
    # Создаем читаемое представление задачи
    task_data = {
        'ID': task.get('id'),
        'Название': task.get('name', 'Без названия'),
        'Статус': task.get('status', {}).get('name', 'Неизвестно'),
        'Описание': task.get('description', 'Нет описания'),
        'Исполнитель': ', '.join([assignee.get('name', 'Неизвестно') for assignee in task.get('assignees', [])]),
        'Срок': task.get('dueDate', 'Не установлен'),
        'Приоритет': task.get('priority', {}).get('name', 'Обычный'),
        'Проект': task.get('project', {}).get('name', 'Не указан')
    }
    
    # Форматируем в текст
    formatted_text = (
        f"**Задача: {task_data['Название']}**\n"
        f"ID: {task_data['ID']}\n"
        f"Статус: {task_data['Статус']}\n"
        f"Приоритет: {task_data['Приоритет']}\n"
        f"Проект: {task_data['Проект']}\n"
        f"Исполнитель: {task_data['Исполнитель']}\n"
        f"Срок: {task_data['Срок']}\n\n"
        f"Описание:\n{task_data['Описание']}"
    )
    
    return formatted_text


# chat/planfix_cache_service.py - modify the _generate_projects_cache method
def _generate_projects_cache(self) -> List[Dict[str, Any]]:
    """Generate projects cache from all tasks"""
    all_tasks = self.get_all_tasks()
    
    # Extract unique projects
    projects_map = {}
    for task in all_tasks:
        if task.get('project') and task['project'].get('id'):
            project_id = str(task['project']['id'])
            
            if project_id not in projects_map:
                # Extract relevant project info
                project_info = {
                    'id': task['project']['id'],
                    'name': task['project'].get('name', f"Project {project_id}"),
                    'task_count': 1,
                    'active_tasks': 0,
                    'completed_tasks': 0,
                    'overdue_tasks': 0
                }
                
                # Count task status
                if self._is_task_completed(task):
                    project_info['completed_tasks'] = 1
                else:
                    project_info['active_tasks'] = 1
                    
                    # Check if overdue
                    today = datetime.now().date().isoformat()
                    end_date = None
                    if task.get('endDateTime') and isinstance(task['endDateTime'], dict):
                        if 'date' in task['endDateTime']:
                            end_date = task['endDateTime']['date']
                        elif 'dateTo' in task['endDateTime']:
                            end_date = task['endDateTime']['dateTo']
                    elif task.get('endDateTime') and isinstance(task['endDateTime'], str):
                        end_date = task['endDateTime']
                    elif task.get('dateEnd') and isinstance(task['dateEnd'], str):
                        end_date = task['dateEnd']
                    
                    if end_date and end_date < today:
                        project_info['overdue_tasks'] = 1
                
                projects_map[project_id] = project_info
            else:
                # Update existing project info
                projects_map[project_id]['task_count'] += 1
                
                # Ensure project has a name
                if not projects_map[project_id]['name'] or projects_map[project_id]['name'] == f"Project {project_id}":
                    projects_map[project_id]['name'] = task['project'].get('name', f"Project {project_id}")
                
                if self._is_task_completed(task):
                    projects_map[project_id]['completed_tasks'] += 1
                else:
                    projects_map[project_id]['active_tasks'] += 1
                    
                    # Check if overdue
                    today = datetime.now().date().isoformat()
                    end_date = None
                    if task.get('endDateTime') and isinstance(task['endDateTime'], dict):
                        if 'date' in task['endDateTime']:
                            end_date = task['endDateTime']['date']
                        elif 'dateTo' in task['endDateTime']:
                            end_date = task['endDateTime']['dateTo']
                    elif task.get('endDateTime') and isinstance(task['endDateTime'], str):
                        end_date = task['endDateTime']
                    elif task.get('dateEnd') and isinstance(task['dateEnd'], str):
                        end_date = task['dateEnd']
                    
                    if end_date and end_date < today:
                        projects_map[project_id]['overdue_tasks'] += 1
    
    # Convert map to list
    projects = list(projects_map.values())
    
    try:
        with open(PROJECTS_CACHE, 'w', encoding='utf-8') as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
        logger.info(f"Generated projects cache with {len(projects)} projects")
    except IOError as e:
        logger.error(f"Error writing projects cache: {e}")
    
    return projects