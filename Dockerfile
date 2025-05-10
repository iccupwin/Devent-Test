FROM python:3.10-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Создание директорий и установка прав
RUN mkdir -p /app/logs /app/staticfiles && \
    chmod +x start_gunicorn.sh entrypoint.sh && \
    chmod -R 777 /app/logs /app/staticfiles && \
    chown -R root:root /app

# Создание непривилегированного пользователя
RUN useradd -m appuser && \
    chown -R appuser:appuser /app/logs /app/staticfiles && \
    chmod -R 777 /app/logs /app/staticfiles

# USER appuser

# Запуск приложения
ENTRYPOINT ["sh", "./entrypoint.sh"] 