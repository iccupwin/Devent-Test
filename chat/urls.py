from django.urls import path, include
from . import views, api_views, views_planfix, api, agent_api

app_name = 'chat'

urlpatterns = [
    # Основные представления для чата (Apple стиль)
    path('', views.agent_dashboard, name='index'),
    path('chat/', views.index_apple, name='index_apple'),
    path('conversation/<int:conversation_id>/', views.conversation_apple, name='conversation'),
    path('conversation/new/', views.new_conversation_apple, name='new_conversation'),
    
    # API для работы с задачами Planfix
    path('api/tasks/', api_views.tasks_api, name='tasks_api'),
    path('api/tasks/update/', api_views.update_tasks_cache_api, name='update_tasks_cache_api'),
    path('api/projects/', api_views.projects_api, name='projects_api'),
    path('api/message/', api.message_api, name='message_api'),
    path('api/conversations/', api.conversations_api, name='conversations_api'),
    path('api/task/<int:task_id>/', api_views.task_api, name='task_api'),
    
    # NEW: Agent API endpoints for Planfix-Claude integration
    path('api/agent/message/', agent_api.agent_message_api, name='agent_message_api'),
    path('api/agent/status/', agent_api.agent_status_api, name='agent_status_api'),
    path('api/agent/refresh-cache/', agent_api.refresh_cache_api, name='refresh_cache_api'),
    
    # Представления для работы с задачами Planfix (Apple стиль)
    path('planfix/tasks/', views_planfix.planfix_tasks_apple, name='planfix_tasks'),
    path('planfix/task/<int:task_id>/', views_planfix.planfix_task_detail_apple, name='planfix_task_detail'),
    path('planfix/task/<int:task_id>/integrate/', views_planfix.planfix_task_integrate, name='planfix_task_integrate'),
    
    # NEW: Agent views
    path('agent/', views.agent_dashboard, name='agent_dashboard'),
    path('agent/conversation/<int:conversation_id>/', views.agent_conversation, name='agent_conversation'),
    path('agent/conversation/new/', views.new_agent_conversation, name='new_agent_conversation'),
    
    # Старый стиль (для обратной совместимости)
    path('default/', views.index, name='index_default'),
    path('default/conversation/<int:conversation_id>/', views.conversation, name='conversation_default'),
    path('default/conversation/new/', views.new_conversation, name='new_conversation_default'),
    path('default/planfix/tasks/', views_planfix.planfix_tasks, name='planfix_tasks_default'),
    path('default/planfix/task/<int:task_id>/', views_planfix.planfix_task_detail, name='planfix_task_detail_default'),
    
    # Переключатель стиля (оставлен для обратной совместимости)
    path('toggle-style/', views.toggle_style, name='toggle_style'),
]