#!/bin/sh
set -e

# Создаем директорию для логов и устанавливаем права
mkdir -p /app/logs
chown -R appuser:appuser /app/logs
chmod -R 777 /app/logs

# Ждем доступности базы данных
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is up!"

# Применяем миграции
echo "Applying migrations..."
python manage.py migrate

# Собираем статические файлы
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Запускаем Gunicorn от appuser
echo "Starting Gunicorn..."
exec su appuser -c ./start_gunicorn.sh 