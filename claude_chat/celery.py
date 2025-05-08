# claude_chat/celery.py
import os
from celery import Celery
from django.conf import settings

# Установка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claude_chat.settings')

# Создание экземпляра Celery
app = Celery('claude_chat')

# Загрузка настроек из settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическая загрузка задач из приложений
app.autodiscover_tasks()

# Настройка периодических задач
app.conf.beat_schedule = {
    'update-daily-metrics': {
        'task': 'chat.tasks.update_daily_metrics',
        'schedule': 3600.0 * 24,  # Запуск каждые 24 часа
        'args': (),
        'options': {'expires': 3600 * 25},  # Истекает через 25 часов
    },
    'cleanup-old-data': {
        'task': 'chat.tasks.cleanup_old_data',
        'schedule': 3600.0 * 24 * 7,  # Запуск каждую неделю
        'args': (),
        'options': {'expires': 3600 * 25},
    },
    'refresh-planfix-cache': {
        'task': 'chat.tasks.refresh_planfix_cache',
        'schedule': 3600.0,  # Запуск каждый час
        'args': (),
        'options': {'expires': 3600 * 2},  # Истекает через 2 часа
    },
}