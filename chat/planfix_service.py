import json
import logging
import time
import os
from pathlib import Path
from django.conf import settings
from .planfix_api import get_projects, get_tasks_page, get_task_detail

# Настройка логирования
logger = logging.getLogger(__name__)

# Путь к директории для кэш-файлов
BASE_DIR = Path(settings.BASE_DIR)
CACHE_DIR = BASE_DIR / 'chat' / 'cache'
TASKS_CACHE_FILE = CACHE_DIR / 'tasks_cache.json'
LAST_UPDATE_FILE = CACHE_DIR / 'last_update.txt'

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

def get_all_tasks(force_update=False):
    """
    Получение всех задач из кэша или API
    
    :param force_update: Принудительное обновление кэша
    :return: Список всех задач
    """
    return update_tasks_cache(force=force_update)

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
    # Сначала пытаемся найти в кэше
    all_tasks = get_all_tasks()
    for task in all_tasks:
        if str(task.get('id')) == str(task_id):
            return task
    
    # Если в кэше нет, запрашиваем напрямую
    return get_task_detail(task_id)

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