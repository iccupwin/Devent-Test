import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Conversation, Message, User, UserMetrics, AIModel
from .agent_query_processor import agent
from .planfix_cache_service import planfix_cache
from .planfix_service import update_tasks_cache
from .claude_ai_service import claude_ai
from .openai_service import openai_ai
from .gemini_service import gemini_ai

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
        model_id = data.get('model_id')
        
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
            selected_model = None
            if model_id:
                try:
                    selected_model = AIModel.objects.get(id=model_id)
                except AIModel.DoesNotExist:
                    pass
            conversation = Conversation.objects.create(
                user=user,
                title=title,
                ai_model=selected_model
            )
        
        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_text
        )
        
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
        user_metrics.messages_sent += 1
        
        # Check if this is a new conversation
        if conversation.created_at.date() == today:
            user_metrics.conversations_count += 1
        
        user_metrics.save()
        
        # Get previous messages for context (limit to last 10 for simplicity)
        previous_messages = Message.objects.filter(conversation=conversation).order_by('created_at')
        
        # Format messages for agent
        conversation_history = []
        for msg in previous_messages:
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Получаем выбранную модель ИИ для беседы
        ai_model = conversation.ai_model
        response = ""
        if not ai_model:
            response = "Модель ИИ не выбрана для этой беседы."
        else:
            try:
                if ai_model.model_type == 'claude':
                    ai_response = claude_ai.process_query(message_text, conversation_history)
                    response = ai_response.get('message', str(ai_response)) if isinstance(ai_response, dict) else str(ai_response)
                elif ai_model.model_type == 'gpt':
                    ai_response = openai_ai.process_query(message_text, conversation_history, model_name=ai_model.version)
                    response = ai_response.get('message', str(ai_response)) if isinstance(ai_response, dict) else str(ai_response)
                elif ai_model.model_type == 'gemini':
                    ai_response = gemini_ai.process_query(message_text, conversation_history)
                    response = ai_response.get('message', str(ai_response)) if isinstance(ai_response, dict) else str(ai_response)
                else:
                    response = f"Неизвестный тип модели: {ai_model.model_type}"
            except Exception as e:
                logger.error(f"Error processing query with {ai_model.model_type}: {e}", exc_info=True)
                response = f"Ошибка при обработке запроса через {ai_model.name}: {str(e)}"
        
        # Save agent's response
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response,
            ai_model_used=ai_model
        )
        
        # Update conversation's updated_at timestamp
        conversation.save()
        
        # Return response
        return JsonResponse({
            'message': response,
            'conversation_id': conversation.id
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request: {e}", exc_info=True)
        return JsonResponse({'error': 'Invalid request format'}, status=400)
    except Exception as e:
        logger.error(f"Error in agent message API: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }, status=500)

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

@csrf_exempt
@require_POST
def change_conversation_model(request, conversation_id):
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        data = json.loads(request.body)
        model_id = data.get('model_id')
        if not model_id:
            logger.warning(f"Model ID not provided for conversation {conversation_id}")
            return JsonResponse({'success': False, 'error': 'Model ID is required'})
        model = get_object_or_404(AIModel, id=model_id)
        conversation.ai_model = model
        conversation.save()
        logger.info(f"Устанавливаю модель {model} для беседы {conversation.id}")
        return JsonResponse({'success': True, 'model_name': model.name})
    except Exception as e:
        logger.error(f"Ошибка при смене модели: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)