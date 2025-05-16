#!/usr/bin/env python
import os
import sys
import logging
import json
import time

# Настройка путей и добавление проекта в PYTHONPATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Установка переменных окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claude_chat.settings')

# Импорт Django и настройка
import django
django.setup()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('planfix_sync.log')
    ]
)
logger = logging.getLogger("planfix_sync")

from chat.planfix_service import update_tasks_cache, get_all_tasks
from chat.planfix_api import get_projects
from pathlib import Path
from django.conf import settings

# Путь к директории для кэш-файлов
CACHE_DIR = Path(settings.BASE_DIR) / 'chat' / 'cache'
TASKS_CACHE_FILE = CACHE_DIR / 'tasks_cache.json'
LAST_UPDATE_FILE = CACHE_DIR / 'last_update.txt'

def clear_cache():
    """Очистка файлов кэша"""
    logger.info("Очистка кэша задач Planfix")
    
    # Удаляем файл кэша задач
    if TASKS_CACHE_FILE.exists():
        os.remove(TASKS_CACHE_FILE)
        logger.info(f"Файл {TASKS_CACHE_FILE} удален")
    
    # Удаляем файл с временем последнего обновления
    if LAST_UPDATE_FILE.exists():
        os.remove(LAST_UPDATE_FILE)
        logger.info(f"Файл {LAST_UPDATE_FILE} удален")
    
    # Создаем пустой файл кэша задач
    with open(TASKS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)
    
    # Создаем файл с временем последнего обновления (2 часа назад)
    with open(LAST_UPDATE_FILE, 'w') as f:
        f.write(str(time.time() - 7200))
    
    logger.info("Кэш успешно очищен")

def force_update():
    """Принудительное обновление кэша задач"""
    logger.info("Начало принудительного обновления кэша задач")
    
    # Получаем начальное время
    start_time = time.time()
    
    # Принудительно обновляем кэш
    tasks = update_tasks_cache(force=True)
    
    # Вычисляем затраченное время
    elapsed_time = time.time() - start_time
    
    logger.info(f"Загружено всего задач: {len(tasks)}")
    logger.info(f"Время загрузки: {elapsed_time:.2f} секунд")
    
    # Вывод статистики по статусам
    status_counts = {}
    for task in tasks:
        status = task.get('status', {}).get('name', 'Неизвестно')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    logger.info("Статистика по статусам:")
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {status}: {count}")
    
    # Статистика по проектам
    project_counts = {}
    for task in tasks:
        project = task.get('project', {}).get('name', 'Без проекта')
        project_counts[project] = project_counts.get(project, 0) + 1
    
    logger.info("Статистика по проектам (топ-10):")
    for project, count in sorted(project_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"  {project}: {count}")
    
    return tasks

def verify_projects():
    """Проверка соответствия проектов в задачах и списке проектов"""
    logger.info("Проверка информации о проектах")
    
    # Получаем список проектов
    projects = get_projects()
    logger.info(f"Получено проектов из API: {len(projects)}")
    
    # Создаем словарь проектов для быстрого доступа
    project_map = {}
    for project in projects:
        if 'id' in project and project['id']:
            project_map[str(project['id'])] = project.get('name', f"Проект {project['id']}")
    
    # Получаем задачи из кэша
    tasks = get_all_tasks()
    logger.info(f"Загружено задач из кэша: {len(tasks)}")
    
    # Проверяем соответствие проектов
    missing_projects = 0
    projects_in_tasks = set()
    
    for task in tasks:
        if 'project' in task and task['project'] and 'id' in task['project']:
            project_id = str(task['project']['id'])
            projects_in_tasks.add(project_id)
            
            if project_id not in project_map:
                missing_projects += 1
                logger.warning(f"Проект с ID {project_id} не найден в списке проектов")
    
    logger.info(f"Уникальных проектов в задачах: {len(projects_in_tasks)}")
    logger.info(f"Проектов, отсутствующих в API: {missing_projects}")
    
    return {
        'total_projects': len(projects),
        'unique_projects_in_tasks': len(projects_in_tasks),
        'missing_projects': missing_projects
    }

if __name__ == "__main__":
    logger.info("=== Запуск скрипта синхронизации задач Planfix ===")
    
    # Очищаем кэш
    clear_cache()
    
    # Принудительно обновляем кэш
    tasks = force_update()
    
    # Проверяем информацию о проектах
    projects_info = verify_projects()
    
    logger.info("=== Синхронизация задач завершена ===")
    logger.info(f"Всего загружено задач: {len(tasks)}")
    logger.info(f"Проверка проектов: {projects_info}")