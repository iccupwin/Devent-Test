import os
from settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Разрешенные хосты
ALLOWED_HOSTS = ['83.217.223.111', 'localhost', '127.0.0.1']

# База данных
DATABASES = {
    'default': {
        'ENGINE': os.getenv("DB_ENGINE"),
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASSWORD"),
        'HOST': os.getenv("DB_HOST"),
        'PORT': os.getenv("DB_PORT"),
    }
}

# Настройки безопасности
SECURE_HSTS_SECONDS = 31536000  # 1 год
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = False  # Отключаем SSL редирект, так как используем IP
SESSION_COOKIE_SECURE = False  # Отключаем для IP
CSRF_COOKIE_SECURE = False  # Отключаем для IP
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Статические файлы


JAZZMIN_SETTINGS = {
    "site_title": "Devent Admin",
    "site_header": "Администрирование Devent",
    "welcome_sign": "Добро пожаловать в систему управления Devent",
    "copyright": "© 2025 Devent",
    "show_sidebar": True,
    "navigation_expanded": True,
    "theme": "darkly",
    "order_with_respect_to": ["auth", "chat", "users"],
    "custom_links": {
        "chat": [{
            "name": "Обновить кэш",
            "url": "/update-cache",
            "icon": "fas fa-sync",
        }]
    },
}


STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")  # = /opt/Devent-Test/static

# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "chat/static"),  # <- сюда ты кладёшь кастомный CSS
# ]


# Создаем директории для статических файлов
os.makedirs(STATIC_ROOT, exist_ok=True)
# os.makedirs(STATICFILES_DIRS[0], exist_ok=True)

# Логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# Создаем директорию для логов
os.makedirs('/app/logs', exist_ok=True)
