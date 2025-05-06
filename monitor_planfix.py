# monitor_planfix.py
import os
import sys
import logging
from pathlib import Path

# Настройка путей и добавление проекта в PYTHONPATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Установка переменных окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claude_chat.settings')

# Импорт Django и настройка
import django
django.setup()

from chat.planfix_service import get_all_tasks
from django.conf import settings

# Путь к директории для кэш-файлов
CACHE_DIR = Path(settings.BASE_DIR) / 'chat' / 'cache'
TASKS_CACHE_FILE = CACHE_DIR / 'tasks_cache.json'

# Проверка состояния кэша
if TASKS_CACHE_FILE.exists():
    tasks = get_all_tasks()
    print(f"Статус кэша задач Planfix:")
    print(f"- Всего задач: {len(tasks)}")
    print(f"- Размер файла кэша: {TASKS_CACHE_FILE.stat().st_size / (1024*1024):.2f} МБ")
    print(f"- Время последнего обновления: {TASKS_CACHE_FILE.stat().st_mtime}")
else:
    print("Ошибка: файл кэша задач не найден")
    sys.exit(1)