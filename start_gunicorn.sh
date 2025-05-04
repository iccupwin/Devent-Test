#!/bin/bash

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем переменные окружения
export DJANGO_ENV=production

# Собираем статические файлы
python manage.py collectstatic --noinput

# Запускаем Gunicorn
gunicorn claude_chat.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --log-level=info \
    --log-file=logs/gunicorn.log \
    --access-logfile=logs/access.log \
    --error-logfile=logs/error.log \
    --capture-output \
    --daemon