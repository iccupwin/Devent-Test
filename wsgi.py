import os
from django.core.wsgi import get_wsgi_application

# Используем разные настройки в зависимости от переменной окружения
if os.environ.get('DJANGO_ENV') == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claude_chat.settings_prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claude_chat.settings')

application = get_wsgi_application()