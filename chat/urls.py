from django.urls import path, include
from . import views, api_views, views_planfix, api

app_name = 'chat'

urlpatterns = [
    # Основные представления для чата
    path('', views.index, name='index'),
    path('conversation/<int:conversation_id>/', views.conversation, name='conversation'),
    path('conversation/new/', views.new_conversation, name='new_conversation'),
    
    # API для работы с задачами Planfix
    path('api/tasks/', api_views.tasks_api, name='tasks_api'),
    path('api/tasks/update/', api_views.update_tasks_cache_api, name='update_tasks_cache_api'),
    path('api/projects/', api_views.projects_api, name='projects_api'),
    path('api/message/', api.message_api, name='message_api'),
    path('api/conversations/', api.conversations_api, name='conversations_api'),
    path('api/task/<int:task_id>/', api_views.task_api, name='task_api'),
    
    # Представления для работы с задачами Planfix
    path('planfix/tasks/', views_planfix.planfix_tasks, name='planfix_tasks'),
    path('planfix/task/<int:task_id>/', views_planfix.planfix_task_detail, name='planfix_task_detail'),
    path('planfix/task/<int:task_id>/integrate/', views_planfix.planfix_task_integrate, name='planfix_task_integrate'),
    
    # Apple-style версии представлений
    path('apple/', views.index_apple, name='index_apple'),
    path('apple/conversation/<int:conversation_id>/', views.conversation_apple, name='conversation_apple'),
    path('apple/conversation/new/', views.new_conversation_apple, name='new_conversation_apple'),
    path('apple/planfix/tasks/', views_planfix.planfix_tasks_apple, name='planfix_tasks_apple'),
    path('apple/planfix/task/<int:task_id>/', views_planfix.planfix_task_detail_apple, name='planfix_task_detail_apple'),
    
    # Переключатель стиля
    path('toggle-style/', views.toggle_style, name='toggle_style'),
]