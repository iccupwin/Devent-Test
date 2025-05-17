import logging
import sys
import os
from pathlib import Path

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
        logging.FileHandler('vector_search_test.log')
    ]
)
logger = logging.getLogger("vector_search_test")

from .vector_service import search_planfix_tasks, update_vector_store
from .planfix_cache_service import planfix_cache

def print_search_results(results):
    """Вывод результатов поиска в читаемом формате"""
    print(f"\nНайдено результатов: {len(results)}")
    
    for hit in results:
        task_data = hit.payload.get('data', {})
        print(f"""
Задача: {task_data.get('title', '')}
Ответственный: {task_data.get('assignee', {}).get('name', '')}
Проект: {task_data.get('project', {}).get('name', '')}
Статус: {task_data.get('status', {}).get('name', '')}
Приоритет: {task_data.get('priority', '')}
Дедлайн: {task_data.get('deadline', '')}
Релевантность: {hit.score:.3f}
""")

def test_vector_search():
    """Тестирование векторного поиска"""
    try:
        # Обновляем векторное хранилище
        updated_count = update_vector_store()
        print(f"Обновлено {updated_count} задач")
        
        # Тестовые запросы
        test_queries = [
            "Какие задачи у Константина?",
            "Показать задачи по проекту Автовокзал",
            "Какие задачи с высоким приоритетом?",
            "Задачи с дедлайном на этой неделе",
            "Задачи в статусе В работе"
        ]
        
        for query in test_queries:
            print(f"\nТестируем запрос: {query}")
            results = search_planfix_tasks(query)
            print_search_results(results)
            
        print("\n=== Тестирование завершено ===")
        
    except Exception as e:
        print(f"Ошибка при тестировании: {str(e)}")
        raise

if __name__ == "__main__":
    test_vector_search() 