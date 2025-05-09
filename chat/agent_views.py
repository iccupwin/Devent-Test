from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Conversation, Message, User, UserMetrics, AIModel
from .planfix_cache_service import planfix_cache
from .agent_query_processor import agent
import json
import os
import logging
from django.utils import timezone

# Configure logging
logger = logging.getLogger(__name__)

def agent_dashboard(request):
    """
    Dashboard for the Planfix-Claude intelligent agent
    """
    # Get or create anonymous user
    user, created = User.objects.get_or_create(username='anonymous')
    
    # Get list of conversations
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    # Get agent statistics
    stats = planfix_cache.get_stats()
    
    # Get employees data from cache file
    employees_data = []
    cache_file_path = os.path.join(os.path.dirname(__file__), 'cache', 'users.json')
    try:
        with open(cache_file_path, 'r', encoding='utf-8') as f:
            employees = json.load(f)
            # Filter out non-user entries and format data
            for employee in employees:
                if employee['id'].startswith('user:'):
                    employees_data.append({
                        'id': employee['id'],
                        'name': employee['name'],
                        'email': employee['email'],
                        'role': 'Сотрудник',
                        'active_tasks': employee['assigned_active'],
                        'completed_tasks': employee['assigned_completed'],
                        'overdue_tasks': employee['assigned_overdue'],
                        'total_tasks': employee['assigned_tasks'],
                        'created_tasks': employee['created_tasks'],
                        'projects': len(employee['projects'])
                    })
    except Exception as e:
        logger.error(f"Error reading employees cache file: {str(e)}")
        employees_data = []
    
    # Get registered users from database
    users = User.objects.filter(is_active=True).order_by('-date_joined')
    users_data = []
    for user in users:
        users_data.append({
            'name': user.username,
            'email': user.email,
            'role': user.get_role_display(),
            'date_joined': user.date_joined,
            'last_active': user.last_active,
            'is_admin': user.is_admin,
            'is_staff': user.is_staff
        })
    
    return render(request, 'chat/agent_dashboard.html', {
        'conversations': conversations,
        'stats': stats,
        'cache_valid': planfix_cache.is_cache_valid(max_age_minutes=60),
        'employees': employees_data,
        'users': users_data
    })

def agent_conversation(request, conversation_id):
    """
    Page to view and continue a conversation with the Planfix-Claude agent
    """
    # Get or create anonymous user
    user, created = User.objects.get_or_create(username='anonymous')
    
    # Get list of conversations
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    # Get current conversation
    conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
    
    # Get conversation messages
    messages = Message.objects.filter(conversation=conversation).order_by('created_at')
    
    # Get agent statistics
    stats = planfix_cache.get_stats()
    
    # Update user metrics
    today = timezone.now().date()
    user_metrics, _ = UserMetrics.objects.get_or_create(
        user=user,
        day=today,
        defaults={
            'messages_sent': 0,
            'conversations_count': 0,
            'tokens_used': 0,
            'tasks_integrated': 0,
            'average_response_time': 0
        }
    )
    
    # Update metrics
    user_metrics.messages_sent += messages.count()
    
    # Check if this is a new conversation
    if conversation.created_at.date() == today:
        user_metrics.conversations_count += 1
    
    user_metrics.save()
    
    ai_models = AIModel.objects.filter(is_active=True).order_by('name')
    return render(request, 'chat/agent_conversation.html', {
        'conversation': conversation,
        'messages': messages,
        'conversations': conversations,
        'stats': stats,
        'cache_valid': planfix_cache.is_cache_valid(max_age_minutes=60),
        'ai_models': ai_models,
    })

def new_agent_conversation(request):
    """
    Page to start a new conversation with the Planfix-Claude agent
    """
    # Get or create anonymous user
    user, created = User.objects.get_or_create(username='anonymous')

    ai_models = AIModel.objects.filter(is_active=True).order_by('name')
    default_model = ai_models.first() if ai_models.exists() else None

    if request.method == 'POST':
        # Создаем новую беседу с моделью по умолчанию
        conversation = Conversation.objects.create(user=user, title='Новая беседа', ai_model=default_model)
        return redirect('chat:agent_conversation', conversation_id=conversation.id)

    # Get list of conversations
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    # Get agent statistics
    stats = planfix_cache.get_stats()
    return render(request, 'chat/agent_conversation_new.html', {
        'conversations': conversations,
        'stats': stats,
        'cache_valid': planfix_cache.is_cache_valid(max_age_minutes=60),
        'ai_models': ai_models,
    })