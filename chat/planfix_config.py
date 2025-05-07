import os
from django.conf import settings

# Получаем настройки из settings или переменных окружения
PLANFIX_ACCOUNT = getattr(settings, 'PLANFIX_ACCOUNT_ID', 'deventky')
API_TOKEN = getattr(settings, 'PLANFIX_API_KEY', os.environ.get('PLANFIX_API_TOKEN', ''))
API_BASE_URL = f"https://{PLANFIX_ACCOUNT}.planfix.com/rest"

PROJECT_REQUEST = {
    'endpoint': 'project/list',
    'method': 'POST',
    'body': {
        'offset': 0,
        'pageSize': 100,
        'filters': [
            {
                'type': 5001,
                'operator': 'equal',
                'value': ''
            }
        ],
        'fields': 'id,name,status,startDateTime,endDateTime,description'  # Обновлены поля дат
    }
}

# Увеличиваем размер страницы до 100 для получения большего количества задач за раз
TASKS_REQUEST = {
    'endpoint': 'task/list',
    'method': 'POST',
    'pageSize': 100,
    'baseBody': {
        'offset': 0,
        'pageSize': 100,
        'fields': 'id,name,status,project,startDateTime,endDateTime,description,assignees,assigner'  # Заменено owner на assigner
    }
}