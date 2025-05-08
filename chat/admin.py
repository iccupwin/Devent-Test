# chat/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, AIModel, Conversation, Message,
    PlanfixCache, PlanfixTask, AnalyticsEvent,
    UserMetrics, AIModelMetrics
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'last_active')
    list_filter = ('role', 'is_active', 'date_joined', 'last_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('role', 'is_active')}),
        (_('Planfix integration'), {'fields': ('planfix_user_id', 'planfix_api_token')}),
        (_('Settings'), {'fields': ('preferred_ai_model',)}),
    )

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_type', 'version', 'is_active', 'updated_at')
    list_filter = ('model_type', 'is_active')
    search_fields = ('name', 'version')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'ai_model', 'planfix_task_id', 'created_at', 'updated_at')
    list_filter = ('ai_model', 'created_at', 'is_archived')
    search_fields = ('title', 'user__username', 'planfix_task_id')
    date_hierarchy = 'created_at'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'created_at', 'tokens', 'ai_model_used')
    list_filter = ('role', 'created_at', 'ai_model_used')
    search_fields = ('content', 'conversation__title')
    date_hierarchy = 'created_at'

@admin.register(PlanfixCache)
class PlanfixCacheAdmin(admin.ModelAdmin):
    list_display = ('cache_name', 'last_update', 'is_valid', 'entries_count', 'update_duration')
    list_filter = ('is_valid', 'last_update')
    search_fields = ('cache_name',)

@admin.register(PlanfixTask)
class PlanfixTaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'name', 'status', 'project_name', 'start_date', 'end_date', 'is_completed', 'is_overdue')
    list_filter = ('status', 'is_completed', 'is_overdue', 'last_sync')
    search_fields = ('task_id', 'name', 'project_name', 'assignee')
    date_hierarchy = 'end_date'

@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user', 'timestamp', 'conversation')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('user__username', 'planfix_task_id', 'metadata')
    date_hierarchy = 'timestamp'

@admin.register(UserMetrics)
class UserMetricsAdmin(admin.ModelAdmin):
    list_display = ('user', 'day', 'conversations_count', 'messages_sent', 'tokens_used')
    list_filter = ('day',)
    search_fields = ('user__username',)
    date_hierarchy = 'day'

@admin.register(AIModelMetrics)
class AIModelMetricsAdmin(admin.ModelAdmin):
    list_display = ('ai_model', 'day', 'requests_count', 'tokens_used', 'error_count')
    list_filter = ('day', 'ai_model')
    date_hierarchy = 'day'