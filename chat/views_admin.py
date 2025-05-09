# chat/views_admin.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Avg, F, Q, FloatField
from django.db.models.functions import Cast
from django.utils import timezone
from datetime import timedelta
import json
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
import os

from .models import (
    User, Conversation, Message, AIModel,
    AnalyticsEvent, UserMetrics, AIModelMetrics
)
from .analytics_service import AnalyticsService

@staff_member_required
def analytics_dashboard(request):
    """
    Представление для административной панели аналитики
    """
    # Период анализа
    days = int(request.GET.get('days', 30))
    
    # Получаем данные из сервиса аналитики
    analytics_summary = AnalyticsService.get_analytics_summary(days)
    models_usage = AnalyticsService.get_ai_models_usage(days)
    daily_activity = AnalyticsService.get_daily_activity(days)
    tokens_usage = AnalyticsService.get_tokens_usage(days)
    top_users = AnalyticsService.get_top_users(limit=10, days=days)
    
    # Подготовка данных для графиков
    activity_dates = [item['day'] for item in daily_activity]
    activity_messages = [item['messages_count'] for item in daily_activity]
    activity_conversations = [item['conversations_count'] for item in daily_activity]
    
    tokens_dates = [item['day'].strftime('%Y-%m-%d') for item in tokens_usage]
    tokens_values = [item['tokens_used'] for item in tokens_usage]
    
    models_names = [item['ai_model__name'] for item in models_usage]
    models_requests = [item['total_requests'] for item in models_usage]
    models_tokens = [item['total_tokens'] for item in models_usage]
    
    user_names = [user['user__username'] for user in top_users]
    user_messages = [user['total_messages'] for user in top_users]
    
    # Базовые метрики
    total_users = User.objects.filter(is_active=True).count()
    total_conversations = Conversation.objects.count()
    total_messages = Message.objects.count()
    
    # Получаем данные для модальных окон
    users = User.objects.all().order_by('-date_joined')
    conversations = Conversation.objects.all().order_by('-created_at')
    messages = Message.objects.all().order_by('-created_at')
    
    # Получаем данные о задачах
    task_integrations = Conversation.objects.filter(planfix_task_id__isnull=False).count()
    last_week_task_integrations = Conversation.objects.filter(
        planfix_task_id__isnull=False,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    task_integrations_trend = calculate_trend(task_integrations, last_week_task_integrations)
    
    # Данные для новых модальных окон
    top_queries = analytics_summary.get('top_queries', [])
    quality_score = analytics_summary.get('quality_score', 0)
    helpful_responses = analytics_summary.get('helpful_responses', 0)
    accuracy_score = analytics_summary.get('accuracy_score', 0)
    quality_feedback = analytics_summary.get('quality_feedback', [])
    
    # Данные для мониторинга использования
    active_users = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    requests_per_hour = Message.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    # Расчет среднего времени ответа
    avg_response_time = Message.objects.filter(
        role='assistant',
        processing_time__gt=0
    ).aggregate(
        avg_time=Avg('processing_time')
    )['avg_time'] or 0.0
    
    # Получаем пики использования
    usage_peaks = Message.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).values('created_at__hour').annotate(
        requests=Count('id'),
        avg_time=Avg('processing_time'),
        errors=Count(
            'id',
            filter=Q(metadata__has_key='error')
        )
    ).order_by('-requests')[:10]
    
    context = {
        'days': days,
        'total_users': total_users,
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'task_integrations_count': task_integrations,
        'task_integrations_trend': task_integrations_trend,
        
        # Данные для графиков
        'models_usage': models_usage,
        'models_names': json.dumps(models_names),
        'models_requests': models_requests,
        'models_tokens': models_tokens,
        
        'activity_dates': json.dumps(activity_dates),
        'activity_messages': activity_messages,
        'activity_conversations': activity_conversations,
        
        'tokens_dates': json.dumps(tokens_dates),
        'tokens_values': tokens_values,
        
        'top_users': top_users,
        'user_names': json.dumps(user_names),
        'user_messages': user_messages,
        
        # Данные для модальных окон
        'users': users,
        'conversations': conversations,
        'messages': messages,
        
        # Данные для новых модальных окон
        'top_queries': top_queries,
        'quality_score': quality_score,
        'helpful_responses': helpful_responses,
        'accuracy_score': accuracy_score,
        'quality_feedback': quality_feedback,
        'active_users': active_users,
        'requests_per_hour': requests_per_hour,
        'avg_response_time': avg_response_time,
        'usage_peaks': usage_peaks,
        
        # Данные для графиков качества и использования
        'quality_data': json.dumps({
            'labels': [item['day'] for item in analytics_summary.get('quality_history', [])],
            'scores': [item['score'] for item in analytics_summary.get('quality_history', [])],
            'helpful': [item['helpful'] for item in analytics_summary.get('quality_history', [])],
            'accuracy': [item['accuracy'] for item in analytics_summary.get('quality_history', [])]
        }),
        'usage_data': json.dumps({
            'labels': [item['day'] for item in analytics_summary.get('usage_history', [])],
            'requests': [item['requests'] for item in analytics_summary.get('usage_history', [])],
            'responseTime': [item['response_time'] for item in analytics_summary.get('usage_history', [])]
        })
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
        total_conversations=Sum('conversations_count'),
        avg_response_time=Avg('average_response_time'),
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
    
    # Получаем базовую статистику по моделям
    model_stats = AIModelMetrics.objects.filter(
        day__gte=last_month
    ).values('ai_model').annotate(
        total_usage=Count('id'),
        total_tokens=Sum('tokens_used'),
        avg_response_time=Avg('average_response_time'),
        error_rate=Cast(Sum('error_count'), FloatField()) / Cast(Sum('requests_count'), FloatField()) * 100.0
    ).order_by('-total_usage')

    # Получаем ежедневную статистику для графиков
    daily_stats = AIModelMetrics.objects.filter(
        day__gte=last_month
    ).values('day', 'ai_model__name').annotate(
        requests=Sum('requests_count'),
        tokens=Sum('tokens_used'),
        response_time=Avg('average_response_time')
    ).order_by('day', 'ai_model__name')

    # Форматируем данные для шаблона
    models_data = []
    for stat in model_stats:
        model = AIModel.objects.get(id=stat['ai_model'])
        models_data.append({
            'name': model.name,
            'type': model.get_model_type_display(),
            'version': model.version,
            'usage': stat['total_usage'],
            'tokens': stat['total_tokens'],
            'avg_response_time': round(stat['avg_response_time'] if stat['avg_response_time'] else 0, 2),
            'error_rate': round(stat['error_rate'] if stat['error_rate'] else 0, 2),
            'is_active': model.is_active
        })

    # Подготавливаем данные для графиков
    chart_data = {
        'labels': [],
        'datasets': {}
    }

    # Инициализируем наборы данных для каждой модели
    for model in AIModel.objects.all():
        chart_data['datasets'][model.name] = {
            'requests': [],
            'tokens': [],
            'response_times': []
        }

    # Заполняем данные для графиков
    current_date = None
    for stat in daily_stats:
        if current_date != stat['day']:
            current_date = stat['day']
            chart_data['labels'].append(current_date.strftime('%Y-%m-%d'))
        
        model_name = stat['ai_model__name']
        chart_data['datasets'][model_name]['requests'].append(stat['requests'])
        chart_data['datasets'][model_name]['tokens'].append(stat['tokens'])
        chart_data['datasets'][model_name]['response_times'].append(
            round(stat['response_time'], 2) if stat['response_time'] else 0
        )

    context = {
        'models_data': models_data,
        'chart_data': chart_data,
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

@staff_member_required
def employees_view(request):
    """
    Представление для отображения списка сотрудников
    """
    employees = User.objects.filter(is_active=True).order_by('username')
    
    context = {
        'employees': employees
    }
    
    return render(request, 'admin/employees.html', context)

def employee_active_tasks(request, employee_id):
    """
    Возвращает список активных задач для сотрудника по его Planfix id (user:4 и т.д.)
    """
    cache_path = os.path.join(os.path.dirname(__file__), 'cache', 'active_tasks.json')
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        filtered = [task for task in tasks if task.get('assignees') and task['assignees'].get('users') and any(u['id'] == employee_id for u in task['assignees']['users'])]
        return JsonResponse({'tasks': filtered})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def employee_completed_tasks(request, employee_id):
    """
    Возвращает список завершённых задач для сотрудника по его Planfix id (user:4 и т.д.)
    """
    cache_path = os.path.join(os.path.dirname(__file__), 'cache', 'completed_tasks.json')
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        filtered = [task for task in tasks if task.get('assignees') and task['assignees'].get('users') and any(u['id'] == employee_id for u in task['assignees']['users'])]
        return JsonResponse({'tasks': filtered})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
