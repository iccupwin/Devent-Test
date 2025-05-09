from django.urls import path, include
from . import views, api_views, views_planfix, api, agent_api, analytics_api, analytics_views
from django.urls import path
from . import views_admin
from . import auth_views

app_name = 'chat'

urlpatterns = [
    # Основные представления для чата (Apple стиль)
    path('', views.agent_dashboard, name='index'),
    path('chat/', views.index_apple, name='index_apple'),
    path('conversation/<int:conversation_id>/', views.conversation, name='conversation'),
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
    path('agent/conversation/<int:conversation_id>/change-model/', agent_api.change_conversation_model, name='change_conversation_model'),
    
    # Старый стиль (для обратной совместимости)
    path('default/', views.index, name='index_default'),
    path('default/conversation/<int:conversation_id>/', views.conversation, name='conversation_default'),
    path('default/conversation/new/', views.new_conversation, name='new_conversation_default'),
    path('default/planfix/tasks/', views_planfix.planfix_tasks, name='planfix_tasks_default'),
    path('default/planfix/task/<int:task_id>/', views_planfix.planfix_task_detail, name='planfix_task_detail_default'),
    
    # Переключатель стиля (оставлен для обратной совместимости)
    path('toggle-style/', views.toggle_style, name='toggle_style'),
    
    # Cache refresh endpoint
    path('refresh-cache/', views.refresh_cache, name='refresh_cache'),

    path('analytics/dashboard/', views_admin.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/users/', views_admin.user_analytics, name='user_analytics'),
    path('analytics/conversations/', views_admin.conversation_analytics, name='conversation_analytics'),
    path('analytics/models/', views_admin.model_analytics, name='model_analytics'),
    path('analytics/tasks/', views_admin.task_analytics, name='task_analytics'),
    
    # Настройки ИИ-моделей
    path('ai-settings/', views_admin.ai_settings, name='ai_settings'),
    path('ai-settings/<int:model_id>/', views_admin.ai_model_settings, name='ai_model_settings'),
    
    # Управление пользователями
    path('user-management/', views_admin.user_management, name='user_management'),
    path('user-management/<int:user_id>/', views_admin.user_edit, name='user_edit'),
    path('employees/', views_admin.employees_view, name='employees'),
    path('employee-tasks/<str:employee_id>/', views_admin.employee_active_tasks, name='employee_active_tasks'),
    path('employee-completed-tasks/<str:employee_id>/', views_admin.employee_completed_tasks, name='employee_completed_tasks'),

    # Аутентификация и профиль
    path('login/', auth_views.login_view, name='login'),
    path('register/', auth_views.register_view, name='register'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('profile/', auth_views.profile_view, name='profile'),
    path('access-denied/', auth_views.access_denied, name='access_denied'),

    # API endpoints for analytics
    path('api/analytics/user/', analytics_api.user_stats_api, name='user_stats_api'),
    path('api/analytics/conversation/<int:conversation_id>/', analytics_api.conversation_stats_api, name='conversation_stats_api'),
    path('api/analytics/message/<int:message_id>/feedback/', analytics_api.add_message_feedback_api, name='add_message_feedback_api'),
    path('api/analytics/conversation/<int:conversation_id>/tag/', analytics_api.add_conversation_tag_api, name='add_conversation_tag_api'),

    # Views for analytics
    path('analytics/user/', analytics_views.user_analytics_view, name='user_analytics'),
    path('analytics/conversation/<int:conversation_id>/', analytics_views.conversation_analytics_view, name='conversation_analytics'),

    # Административные URL
    path('admin/users/', views_admin.user_management, name='user_management'),
    path('admin/users/<int:user_id>/update-role/', views_admin.update_user_role, name='update_user_role'),
    path('admin/users/<int:user_id>/delete/', views_admin.delete_user, name='delete_user'),

    # Изменение модели ИИ в беседе
    path('conversation/<int:conversation_id>/change-model/', views.change_conversation_model, name='change_conversation_model'),
]