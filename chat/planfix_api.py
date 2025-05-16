import requests
import json
import logging
from .planfix_config import (
    API_BASE_URL,
    API_TOKEN,
    PLANFIX_ACCOUNT,
    PROJECT_REQUEST,
    TASKS_REQUEST
)

# Настройка логирования
logger = logging.getLogger(__name__)

def fetch_from_planfix(endpoint, method='POST', body=None):
    """
    Базовая функция для запросов к API Planfix
    """
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {API_TOKEN}'
    }

    logger.debug(f"Planfix API запрос: {url}")
    if body:
        logger.debug(f"Тело запроса: {json.dumps(body, ensure_ascii=False)}")

    try:
        response = requests.request(method, url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"Ответ Planfix API: {data}")
        return data
    except Exception as e:
        logger.error(f"Ошибка Planfix API: {e}")
        return {}

def get_projects():
    """
    Получение списка всех проектов
    """
    logger.info("Запрашиваем проекты из Planfix...")
    try:
        response = fetch_from_planfix(
            PROJECT_REQUEST['endpoint'],
            PROJECT_REQUEST['method'],
            PROJECT_REQUEST['body']
        )
        
        # Получаем проекты из ответа
        projects = response.get('projects', []) or response.get('data', []) or []
        
        # Логируем для отладки
        logger.info(f"Получено проектов: {len(projects)}")
        for project in projects[:3]:  # Логируем первые 3 проекта для отладки
            logger.info(f"Проект: {project}")
        
        return projects
    except Exception as e:
        logger.error(f"Ошибка при получении проектов: {e}")
        return []

def get_tasks_page(page=0):
    """
    Получение страницы задач
    
    :param page: Номер страницы (начиная с 0)
    :return: Список задач и общее количество
    """
    logger.info(f"Запрашиваем задачи из Planfix: страница {page}")
    try:
        page_size = TASKS_REQUEST['pageSize']
        offset = page * page_size
        
        # Создаем копию базового запроса
        body = TASKS_REQUEST['baseBody'].copy()
        body['offset'] = offset
        body['pageSize'] = page_size
        
        response = fetch_from_planfix(
            TASKS_REQUEST['endpoint'],
            TASKS_REQUEST['method'],
            body
        )
        
        # Извлекаем список задач и метаданные
        tasks = response.get('tasks', []) or response.get('data', []) or []
        
        # Получаем общее количество задач, если оно доступно
        total_count = response.get('count', 0)
        
        return {
            'tasks': tasks,
            'total_count': total_count
        }
    except Exception as e:
        logger.error(f"Ошибка при получении задач: {e}")
        return {
            'tasks': [],
            'total_count': 0
        }

def get_task_detail(task_id):
    """
    Получение детальной информации о задаче
    
    :param task_id: ID задачи
    :return: Подробная информация о задаче
    """
    logger.info(f"Запрашиваем детали задачи из Planfix: ID {task_id}")
    try:
        endpoint = f"task/{task_id}"
        response = fetch_from_planfix(endpoint, "GET")
        return response
    except Exception as e:
        logger.error(f"Ошибка при получении деталей задачи: {e}")
        return {}