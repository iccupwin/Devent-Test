from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Conversation, Message, User
from .planfix_cache_service import planfix_cache
from .agent_query_processor import agent
import logging

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
    
    return render(request, 'chat/agent_dashboard.html', {
        'conversations': conversations,
        'stats': stats,
        'cache_valid': planfix_cache.is_cache_valid(max_age_minutes=60)
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
    
    return render(request, 'chat/agent_conversation.html', {
        'conversation': conversation,
        'messages': messages,
        'conversations': conversations,
        'stats': stats,
        'cache_valid': planfix_cache.is_cache_valid(max_age_minutes=60)
    })

def new_agent_conversation(request):
    """
    Page to start a new conversation with the Planfix-Claude agent
    """
    # Get or create anonymous user
    user, created = User.objects.get_or_create(username='anonymous')
    
    # Get list of conversations
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    # Get agent statistics
    stats = planfix_cache.get_stats()
    
    return render(request, 'chat/agent_conversation_new.html', {
        'conversations': conversations,
        'stats': stats,
        'cache_valid': planfix_cache.is_cache_valid(max_age_minutes=60)
    })