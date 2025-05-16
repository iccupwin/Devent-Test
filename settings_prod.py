import os
from settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Разрешенные хосты
ALLOWED_HOSTS = ['83.217.223.111', 'localhost', '127.0.0.1']

# База данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'devent_db'),
        'USER': os.environ.get('DB_USER', 'devent_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'devent_password'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
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
STATIC_ROOT = '/app/staticfiles'
STATICFILES_DIRS = [
    '/app/static',
]

# Создаем директории для статических файлов
os.makedirs(STATIC_ROOT, exist_ok=True)
os.makedirs(STATICFILES_DIRS[0], exist_ok=True)

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