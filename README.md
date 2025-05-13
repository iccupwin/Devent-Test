# Planfix Dashboard с интеграцией Claude AI

Дашборд на базе Django для системы управления проектами Planfix с интеграцией Claude AI для анализа данных и получения аналитических данных. Проект включает аналитику в реальном времени, управление задачами и аналитику на базе искусственного интеллекта.

## Возможности

- Интеграция с системой управления задачами Planfix
- Аналитическая панель в реальном времени
- Интеграция с Claude AI для анализа данных
- Синхронизация задач с Planfix
- Кэширование на базе Redis
- Фоновые задачи с использованием Celery
- Поддержка Docker для производственного развертывания

## Требования

- Python 3.8+
- PostgreSQL
- Redis
- Docker (опционально, для производственного развертывания)

## Установка и настройка

1. Клонируйте репозиторий:
   ```bash
   git clone <repository-url>
   cd Devent-Test
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\activate

   # Linux/Mac
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` в корневой директории проекта со следующими переменными:
   ```env
   # Настройки Django
   SECRET_KEY=ваш_секретный_ключ_django
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   
   # Настройки базы данных
   DATABASE_URL=postgres://пользователь:пароль@localhost:5432/имя_базы
   
   # Настройки API Planfix
   PLANFIX_ACCOUNT_ID=ваш_идентификатор_аккаунта
   PLANFIX_API_TOKEN=ваш_токен_api
   
   # Настройки API Claude
   CLAUDE_API_KEY=ваш_ключ_api_claude
   CLAUDE_API_URL=https://api.anthropic.com/v1/messages
   
   # Настройки Redis
   REDIS_URL=redis://localhost:6379/0
   ```

5. Выполните миграции и запустите сервер разработки:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Развертывание в продакшене

Проект включает поддержку Docker для производственного развертывания. Для развертывания:

1. Соберите и запустите контейнеры:
   ```bash
   docker-compose up -d
   ```

2. Выполните миграции в контейнере:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. Соберите статические файлы:
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```

## Структура проекта

- `chat/` - Основная директория приложения
  - `api/` - API endpoints
  - `templates/` - HTML шаблоны
  - `static/` - Статические файлы
- `claude_chat/` - Конфигурация проекта
- `templates/` - Глобальные шаблоны
- `static/` - Глобальные статические файлы

## Зависимости

- Django 5.0
- django-environ 0.11.2
- requests 2.31.0
- python-dotenv 1.0.0
- gunicorn 21.2.0
- psycopg2-binary 2.9.7
- whitenoise 6.6.0
- redis 5.0.1
- celery 5.3.6
- django-redis 5.4.0
- anthropic 0.16.0
- openai
