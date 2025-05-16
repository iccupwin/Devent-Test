# chat/analytics_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db import models

from .models import Conversation, Message, User, UserMetrics, AnalyticsEvent, AIModelMetrics
from .conversation_analytics_service import ConversationAnalyticsService

@login_required
def user_analytics_view(request):
    """Представление для просмотра аналитики пользователя"""
    user = request.user
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Получаем метрики пользователя
    metrics = UserMetrics.objects.filter(
        user=user,
        day__range=[start_date, end_date]
    ).order_by('day')
    
    # Получаем метрики использования ИИ-моделей
    ai_metrics = AIModelMetrics.objects.filter(
        day__range=[start_date, end_date]
    ).order_by('day')
    
    # Считаем общую статистику
    total_conversations = sum(m.conversations_count for m in metrics)
    total_messages = sum(m.messages_sent for m in metrics)
    total_tokens = sum(m.tokens_used for m in metrics)
    total_tasks = sum(m.tasks_integrated for m in metrics)
    
    # Получаем топ моделей ИИ по использованию
    top_models = AIModelMetrics.objects.filter(
        day__range=[start_date, end_date]
    ).values('ai_model__name').annotate(
        total_requests=models.Sum('requests_count'),
        total_tokens=models.Sum('tokens_used')
    ).order_by('-total_requests')[:5]
    
    # Получаем топ пользователей по активности
    top_users = UserMetrics.objects.filter(
        day__range=[start_date, end_date]
    ).values(
        'user__username',
        'user__first_name',
        'user__last_name'
    ).annotate(
        total_messages=models.Sum('messages_sent'),
        total_conversations=models.Sum('conversations_count'),
        total_tokens=models.Sum('tokens_used')
    ).order_by('-total_messages')[:5]
    
    # Подготавливаем данные для графиков
    daily_activity = metrics.values('day').annotate(
        messages_count=models.Sum('messages_sent'),
        conversations_count=models.Sum('conversations_count')
    ).order_by('day')
    
    daily_tokens = metrics.values('day').annotate(
        tokens_used=models.Sum('tokens_used')
    ).order_by('day')
    
    context = {
        'user': user,
        'metrics': metrics,
        'ai_metrics': ai_metrics,
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'total_tokens': total_tokens,
        'total_tasks': total_tasks,
        'top_models': top_models,
        'top_users': top_users,
        'daily_activity': list(daily_activity),
        'daily_tokens': list(daily_tokens),
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'chat/analytics/user_analytics.html', context)

@login_required
def conversation_analytics_view(request, conversation_id):
    """Представление для просмотра аналитики беседы"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    messages = Message.objects.filter(conversation=conversation)
    
    context = {
        'conversation': conversation,
        'total_messages': messages.count(),
        'total_tokens': sum(m.tokens for m in messages),
        'user_messages': messages.filter(role='user').count(),
        'assistant_messages': messages.filter(role='assistant').count(),
        'system_messages': messages.filter(role='system').count(),
        'first_message': messages.order_by('created_at').first(),
        'last_message': messages.order_by('-created_at').first(),
    }
    
    return render(request, 'chat/analytics/conversation_analytics.html', context)