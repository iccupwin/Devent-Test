#!/usr/bin/env python
import os
import sys
import django
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claude_chat.settings')
django.setup()

# Импорт моделей
User = get_user_model()
from chat.models import AIModel

def create_superuser():
    """Создание суперпользователя, если он не существует"""
    if not User.objects.filter(username='admin').exists():
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        )
        print(f"Создан суперпользователь: {user.username}")
    else:
        print("Суперпользователь уже существует")

def create_test_user():
    """Создание тестового пользователя, если он не существует"""
    if not User.objects.filter(username='user').exists():
        user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='user123',
            role='user'
        )
        print(f"Создан тестовый пользователь: {user.username}")
    else:
        print("Тестовый пользователь уже существует")

def create_ai_models():
    """Создание моделей ИИ, если они не существуют"""
    ai_models = [
        {
            'name': 'Claude 3 Opus',
            'model_type': 'claude',
            'version': 'claude-3-opus-20240229',
            'api_base_url': 'https://api.anthropic.com/v1/messages',
            'is_active': True,
        },
        {
            'name': 'Claude 3 Sonnet',
            'model_type': 'claude',
            'version': 'claude-3-sonnet-20240229',
            'api_base_url': 'https://api.anthropic.com/v1/messages',
            'is_active': True,
        },
        {
            'name': 'Claude 3 Haiku',
            'model_type': 'claude',
            'version': 'claude-3-haiku-20240307',
            'api_base_url': 'https://api.anthropic.com/v1/messages',
            'is_active': True,
        },
        {
            'name': 'GPT-4',
            'model_type': 'gpt',
            'version': 'gpt-4',
            'api_base_url': 'https://api.openai.com/v1/chat/completions',
            'is_active': False,
        },
        {
            'name': 'DeepSeek',
            'model_type': 'deepseek',
            'version': 'deepseek-llm',
            'api_base_url': 'https://api.deepseek.com/v1/chat/completions',
            'is_active': False,
        },
    ]
    
    for model_data in ai_models:
        if not AIModel.objects.filter(name=model_data['name']).exists():
            AIModel.objects.create(
                name=model_data['name'],
                model_type=model_data['model_type'],
                version=model_data['version'],
                api_base_url=model_data['api_base_url'],
                is_active=model_data['is_active'],
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            print(f"Создана модель ИИ: {model_data['name']}")
        else:
            print(f"Модель ИИ {model_data['name']} уже существует")

def main():
    """Основная функция инициализации базы данных"""
    print("Инициализация базы данных...")
    
    # Применение миграций
    print("Применение миграций...")
    call_command('migrate')
    
    # Создание учетных записей
    print("Создание учетных записей...")
    create_superuser()
    create_test_user()
    
    # Создание моделей ИИ
    print("Создание моделей ИИ...")
    create_ai_models()
    
    print("Инициализация базы данных завершена!")

if __name__ == '__main__':
    main()