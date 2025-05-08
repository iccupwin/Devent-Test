# chat/views_admin.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Avg, F, Q
from django.utils import timezone
from datetime import timedelta
import json
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import (
    User, Conversation, Message, AIModel,
    AnalyticsEvent, UserMetrics, AIModelMetrics
)

@staff_member_required
def analytics_dashboard(request):
    """
    Представление для административной панели аналитики
    """
    # Базовые метрики
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    # Количество пользователей
    users_count = User.objects.filter(is_active=True).count()
    users_last_week = User.objects.filter(date_joined__gte=last_week).count()
    users_previous_week = User.objects.filter(
        date_joined__lt=last_week, 
        date_joined__gte=last_week - timedelta(days=7)
    ).count()
    users_trend = calculate_trend(users_last_week, users_previous_week)
    
    # Количество бесед
    conversations_count = Conversation.objects.count()
    conversations_last_week = Conversation.objects.filter(created_at__gte=last_week).count()
    conversations_previous_week = Conversation.objects.filter(
        created_at__lt=last_week, 
        created_at__gte=last_week - timedelta(days=7)
    ).count()
    conversations_trend = calculate_trend(conversations_last_week, conversations_previous_week)
    
    # Количество сообщений
    messages_count = Message.objects.count()
    messages_last_week = Message.objects.filter(created_at__gte=last_week).count()
    messages_previous_week = Message.objects.filter(
        created_at__lt=last_week, 
        created_at__gte=last_week - timedelta(days=7)
    ).count()
    messages_trend = calculate_trend(messages_last_week, messages_previous_week)
    
    # Количество интеграций с задачами
    task_integrations_count = Conversation.objects.filter(planfix_task_id__isnull=False).count()
    task_integrations_last_week = Conversation.objects.filter(
        planfix_task_id__isnull=False,
        created_at__gte=last_week
    ).count()
    task_integrations_previous_week = Conversation.objects.filter(
        planfix_task_id__isnull=False,
        created_at__lt=last_week,
        created_at__gte=last_week - timedelta(days=7)
    ).count()
    task_integrations_trend = calculate_trend(task_integrations_last_week, task_integrations_previous_week)
    
    # Данные для графиков
    
    # 1. Использование ИИ-моделей
    ai_models = AIModel.objects.filter(is_active=True)
    ai_models_data = []
    ai_models_labels = []
    
    for model in ai_models:
        count = Conversation.objects.filter(ai_model=model).count()
        ai_models_data.append(count)
        ai_models_labels.append(model.name)
    
    # 2. Ежедневная активность за последний месяц
    daily_data = {}
    daily_labels = []
    daily_conversations = []
    daily_messages = []
    
    for i in range(30, -1, -1):
        day = today - timedelta(days=i)
        daily_labels.append(day.strftime('%d %b'))
        
        conv_count = Conversation.objects.filter(created_at__date=day).count()
        msg_count = Message.objects.filter(created_at__date=day).count()
        
        daily_conversations.append(conv_count)
        daily_messages.append(msg_count)
    
    # 3. Использование токенов по моделям
    tokens_by_model = []
    for model in ai_models:
        tokens = Message.objects.filter(ai_model_used=model).aggregate(Sum('tokens'))['tokens__sum'] or 0
        tokens_by_model.append(tokens)
    
    # 4. Топ пользователей
    top_users = UserMetrics.objects.filter(day__gte=last_month).values('user').annotate(
        total_messages=Sum('messages_sent')
    ).order_by('-total_messages')[:10]
    
    top_users_data = []
    top_users_labels = []
    
    for user_metric in top_users:
        user = User.objects.get(id=user_metric['user'])
        top_users_labels.append(user.username)
        top_users_data.append(user_metric['total_messages'])
    
    # 5. Недавние события аналитики
    recent_events = AnalyticsEvent.objects.select_related('user', 'conversation').order_by('-timestamp')[:20]
    
    # Формирование контекста для шаблона
    context = {
        'users_count': users_count,
        'users_trend': users_trend,
        'conversations_count': conversations_count,
        'conversations_trend': conversations_trend,
        'messages_count': messages_count,
        'messages_trend': messages_trend,
        'task_integrations_count': task_integrations_count,
        'task_integrations_trend': task_integrations_trend,
        
        'ai_models_data': ai_models_data,
        'ai_models_labels': json.dumps(ai_models_labels),
        
        'daily_labels': json.dumps(daily_labels),
        'daily_conversations': daily_conversations,
        'daily_messages': daily_messages,
        
        'tokens_by_model': tokens_by_model,
        
        'top_users_data': top_users_data,
        'top_users_labels': json.dumps(top_users_labels),
        
        'recent_events': recent_events,
    }
    
    return render(request, 'admin/analytics/dashboard.html', context)

def calculate_trend(current, previous):
    """
    Расчет процентного изменения между текущим и предыдущим периодами
    """
    if previous == 0:
        return 100 if current > 0 else 0
    
    return round(((current - previous) / previous) * 100, 1)

@staff_member_required
def user_analytics(request):
    """
    Представление для анализа пользовательской активности
    """
    # Получаем статистику за последний месяц
    last_month = timezone.now() - timedelta(days=30)
    
    user_stats = UserMetrics.objects.filter(
        day__gte=last_month
    ).values('user').annotate(
        total_messages=Sum('messages_sent'),
        total_conversations=Sum('conversations_started'),
        avg_response_time=Avg('avg_response_time'),
        total_tokens=Sum('tokens_used')
    ).order_by('-total_messages')

    users_data = []
    for stat in user_stats:
        user = User.objects.get(id=stat['user'])
        users_data.append({
            'username': user.username,
            'messages': stat['total_messages'],
            'conversations': stat['total_conversations'],
            'avg_response_time': round(stat['avg_response_time'] if stat['avg_response_time'] else 0, 2),
            'tokens': stat['total_tokens']
        })

    context = {
        'users_data': users_data,
        'period': '30 дней'
    }
    
    return render(request, 'admin/analytics/user_analytics.html', context)

@staff_member_required
def conversation_analytics(request):
    """
    Представление для анализа бесед
    """
    last_month = timezone.now() - timedelta(days=30)
    
    conversations = Conversation.objects.filter(
        created_at__gte=last_month
    ).annotate(
        message_count=Count('message'),
        total_tokens=Sum('message__tokens')
    ).order_by('-created_at')

    context = {
        'conversations': conversations,
        'period': '30 дней'
    }
    
    return render(request, 'admin/analytics/conversation_analytics.html', context)

@staff_member_required
def model_analytics(request):
    """
    Представление для анализа производительности ИИ-моделей
    """
    last_month = timezone.now() - timedelta(days=30)
    
    model_stats = AIModelMetrics.objects.filter(
        day__gte=last_month
    ).values('model').annotate(
        total_usage=Count('id'),
        total_tokens=Sum('tokens_used'),
        avg_response_time=Avg('avg_response_time')
    ).order_by('-total_usage')

    models_data = []
    for stat in model_stats:
        model = AIModel.objects.get(id=stat['model'])
        models_data.append({
            'name': model.name,
            'usage': stat['total_usage'],
            'tokens': stat['total_tokens'],
            'avg_response_time': round(stat['avg_response_time'] if stat['avg_response_time'] else 0, 2)
        })

    context = {
        'models_data': models_data,
        'period': '30 дней'
    }
    
    return render(request, 'admin/analytics/model_analytics.html', context)

@staff_member_required
def task_analytics(request):
    """
    Представление для анализа интеграций с задачами
    """
    last_month = timezone.now() - timedelta(days=30)
    
    task_conversations = Conversation.objects.filter(
        created_at__gte=last_month,
        planfix_task_id__isnull=False
    ).annotate(
        message_count=Count('message')
    ).order_by('-created_at')

    context = {
        'task_conversations': task_conversations,
        'period': '30 дней'
    }
    
    return render(request, 'admin/analytics/task_analytics.html', context)

@staff_member_required
def ai_settings(request):
    """
    Представление для управления настройками ИИ-моделей
    """
    models = AIModel.objects.all().order_by('-is_active', 'name')
    
    context = {
        'models': models
    }
    
    return render(request, 'admin/settings/ai_settings.html', context)

@staff_member_required
def ai_model_settings(request, model_id):
    """
    Представление для редактирования настроек конкретной ИИ-модели
    """
    model = get_object_or_404(AIModel, id=model_id)
    
    if request.method == 'POST':
        # Обработка формы обновления настроек
        model.name = request.POST.get('name', model.name)
        model.is_active = request.POST.get('is_active', '') == 'on'
        model.save()
        return redirect('chat:ai_settings')

    context = {
        'model': model
    }
    
    return render(request, 'admin/settings/ai_model_settings.html', context)

@staff_member_required
def user_management(request):
    """
    Представление для управления пользователями
    """
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin/users/user_management.html', {'users': users})

@staff_member_required
def update_user_role(request, user_id):
    """
    Представление для обновления роли пользователя
    """
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')
        
        if new_role in ['user', 'admin']:
            user.role = new_role
            user.save()
            messages.success(request, f'Роль пользователя {user.username} успешно обновлена')
        else:
            messages.error(request, 'Некорректная роль')
            
    return redirect('chat:user_management')

@staff_member_required
def delete_user(request, user_id):
    """
    Представление для удаления пользователя
    """
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        username = user.username
        user.delete()
        messages.success(request, f'Пользователь {username} успешно удален')
    return redirect('chat:user_management')

@staff_member_required
def user_edit(request, user_id):
    """
    Представление для редактирования пользователя
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Обработка формы обновления пользователя
        user.is_active = request.POST.get('is_active', '') == 'on'
        user.save()
        return redirect('chat:user_management')

    context = {
        'edit_user': user
    }
    
    return render(request, 'admin/users/user_edit.html', context)
