from django.db import migrations

def add_initial_ai_models(apps, schema_editor):
    AIModel = apps.get_model('chat', 'AIModel')
    
    # Создаем начальные модели ИИ
    models_data = [
        {
            'name': 'Claude 3 Opus',
            'model_type': 'claude',
            'version': '3.0',
            'api_base_url': 'https://api.anthropic.com/v1/messages',
            'is_active': True
        },
        {
            'name': 'GPT-4 Turbo',
            'model_type': 'gpt',
            'version': '4.0',
            'api_base_url': 'https://api.openai.com/v1/chat/completions',
            'is_active': True
        },
        {
            'name': 'Gemini Pro',
            'model_type': 'gemini',
            'version': '1.0',
            'api_base_url': 'https://generativelanguage.googleapis.com/v1/models/gemini-pro',
            'is_active': True
        }
    ]
    
    for model_data in models_data:
        AIModel.objects.get_or_create(
            name=model_data['name'],
            defaults=model_data
        )

def remove_ai_models(apps, schema_editor):
    AIModel = apps.get_model('chat', 'AIModel')
    AIModel.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_initial_ai_models, remove_ai_models),
    ] 