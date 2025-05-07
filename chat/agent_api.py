import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404

from .models import Conversation, Message, User
from .agent_query_processor import agent
from .planfix_cache_service import planfix_cache
from .planfix_service import update_tasks_cache

# Configure logging
logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def agent_message_api(request):
    """
    API endpoint for sending messages to the Planfix-Claude intelligent agent
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        message_text = data.get('message', '')
        conversation_id = data.get('conversation_id')
        
        # Validate message
        if not message_text:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get or create anonymous user
        user, created = User.objects.get_or_create(username='anonymous')
        
        # Get or create conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id, user=user)
            except Conversation.DoesNotExist:
                return JsonResponse({'error': 'Conversation not found'}, status=404)
        else:
            # Create a new conversation - use first few words as title
            title = ' '.join(message_text.split()[:5]) + '...'
            conversation = Conversation.objects.create(
                user=user,
                title=title
            )
        
        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_text
        )
        
        # Get previous messages for context (limit to last 10 for simplicity)
        previous_messages = Message.objects.filter(conversation=conversation).order_by('created_at')
        
        # Format messages for agent
        conversation_history = []
        for msg in previous_messages:
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Handle messages about cache refresh
        if 'refresh' in message_text.lower() and any(keyword in message_text.lower() for keyword in ['cache', 'data', 'update']):
            # Update cache
            try:
                update_tasks_cache(force=True)
                planfix_cache.refresh_all_caches()
                response = "I've refreshed the Planfix data. Now I'm working with the latest information."
            except Exception as e:
                logger.error(f"Error refreshing cache: {e}", exc_info=True)
                response = f"I encountered an error while refreshing the Planfix data: {str(e)}"
        else:
            # Process query with agent
            agent_response = agent.process_query(message_text, conversation_history)
            
            # Handle different response types
            response_type = agent_response.get('response_type', '')
            response = agent_response.get('message', '')
            
            if response_type == 'cache_refresh_needed':
                # Ask user if they want to refresh cache
                pass
            elif response_type == 'cache_refresh_requested':
                # Refresh cache
                try:
                    update_tasks_cache(force=True)
                    planfix_cache.refresh_all_caches()
                    response += "\n\nCache refreshed successfully! Now I'm working with the latest Planfix data."
                except Exception as e:
                    logger.error(f"Error refreshing cache: {e}", exc_info=True)
                    response += f"\n\nI encountered an error while refreshing the data: {str(e)}"
            # For other response types, just use the message directly
        
        # Save agent's response
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response
        )
        
        # Update conversation's updated_at timestamp
        conversation.save()
        
        # Return response
        return JsonResponse({
            'message': response,
            'conversation_id': conversation.id
        })
        
    except Exception as e:
        logger.error(f"Error in agent message API: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def agent_status_api(request):
    """
    API endpoint to get agent status and cache information
    """
    try:
        # Get cache stats
        stats = planfix_cache.get_stats()
        
        # Format response
        response = {
            'status': 'active',
            'cache': {
                'age_minutes': stats.get('cache_age_minutes', 0),
                'last_updated': stats.get('cache_updated_at', ''),
                'is_valid': planfix_cache.is_cache_valid(max_age_minutes=60)
            },
            'tasks': {
                'total': stats.get('total_tasks', 0),
                'active': stats.get('active_tasks', 0),
                'completed': stats.get('completed_tasks', 0),
                'overdue': stats.get('overdue_tasks', 0),
                'due_this_week': stats.get('tasks_due_this_week', 0)
            },
            'projects': {
                'total': stats.get('total_projects', 0)
            }
        }
        
        return JsonResponse(response)
    except Exception as e:
        logger.error(f"Error in agent status API: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e), 'status': 'error'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def refresh_cache_api(request):
    """
    API endpoint to manually refresh the Planfix data cache
    """
    try:
        # Update main cache
        update_tasks_cache(force=True)
        
        # Refresh derived caches
        planfix_cache.refresh_all_caches()
        
        # Get updated stats
        stats = planfix_cache.get_stats()
        
        return JsonResponse({
            'success': True,
            'message': 'Cache refreshed successfully',
            'stats': {
                'total_tasks': stats.get('total_tasks', 0),
                'active_tasks': stats.get('active_tasks', 0),
                'completed_tasks': stats.get('completed_tasks', 0),
                'overdue_tasks': stats.get('overdue_tasks', 0),
                'total_projects': stats.get('total_projects', 0),
                'cache_age_minutes': stats.get('cache_age_minutes', 0)
            }
        })
    except Exception as e:
        logger.error(f"Error refreshing cache: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error refreshing cache: {str(e)}'
        }, status=500)