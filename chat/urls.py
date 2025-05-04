from django.urls import path
from . import views
from . import views_planfix
from . import api_views
from . import test_views

app_name = 'chat'

urlpatterns = [
    # Основные маршруты чата
    path('', views.index, name='index'),
    path('conversation/<int:conversation_id>/', views.get_conversation, name='conversation'),
    path('api/message/', views.send_message, name='send_message'),
    
    # Маршруты для Planfix
    path('planfix/tasks/', views_planfix.planfix_tasks, name='planfix_tasks'),
    path('planfix/task/<int:task_id>/', views_planfix.planfix_task_detail, name='planfix_task_detail'),
    path('planfix/task/<int:task_id>/integrate/', views_planfix.planfix_task_integrate, name='planfix_task_integrate'),
    
    # API endpoints для Planfix
    path('api/projects/', api_views.projects_api, name='api_projects'),
    path('api/tasks/', api_views.tasks_api, name='api_tasks'),
    path('api/tasks/update/', api_views.force_update_cache, name='api_update_tasks'),
    
    # Тестовый маршрут для проверки API
    path('test-planfix-api/', test_views.test_planfix_api, name='test_planfix_api'),
    
    # Совместимость со старыми URL для отладки (по необходимости)
    path('debug/projects/', api_views.projects_api, name='debug_projects'),
]