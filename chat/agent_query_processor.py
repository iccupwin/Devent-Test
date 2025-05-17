import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from .planfix_cache_service import planfix_cache
from .claude_ai_service import claude_ai
from .gemini_ai_service import GeminiAIService
from .openai_service import openai_ai
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

class AgentQueryProcessor:
    """
    Middleware to process user queries about Planfix data and route them appropriately
    """
    
    def __init__(self):
        """Initialize the processor"""
        logger.info("Initializing Agent Query Processor")
        self.gemini_ai = GeminiAIService()
    
    def process_query(self, user_query: str, conversation_history: Optional[List[Dict[str, str]]] = None,
                     ai_model: str = None) -> Dict[str, Any]:
        """
        Process a user query about Planfix data and return the appropriate response
        
        Args:
            user_query: The user's query text
            conversation_history: Optional list of previous messages
            ai_model: Optional AI model to use ('claude', 'gpt', or 'gemini')
        
        Returns:
            Dictionary with response data
        """
        logger.info(f"Processing user query: {user_query[:50]}...")
        logger.info(f"Selected AI model: {ai_model}")
        
        # Проверяем, является ли это первым сообщением после переключения модели
        if conversation_history and len(conversation_history) > 0:
            last_message = conversation_history[-1]
            if last_message.get('role') == 'assistant' and 'model_switched' in last_message.get('content', ''):
                # Если это первое сообщение после переключения, добавляем подтверждение
                welcome_message = {
                    'response_type': 'ai_response',
                    'message': f"Я {ai_model.upper()} AI. Чем могу помочь?"
                }
                return welcome_message
        
        # Check if cache needs refreshing
        if not planfix_cache.is_cache_valid(max_age_minutes=60):
            logger.info("Cache is stale, suggesting refresh")
            return {
                'response_type': 'cache_refresh_needed',
                'message': "The Planfix data cache is more than 60 minutes old. Would you like me to refresh it before answering your question?",
                'cache_age_minutes': planfix_cache.get_cache_age_minutes() or 0
            }
        
        # Check if query is about cache stats or system status
        if self._is_system_query(user_query):
            return self._handle_system_query(user_query)
        
        # Determine which AI model to use
        if ai_model is None:
            # Use default model from settings or fallback to Claude
            ai_model = getattr(settings, 'DEFAULT_AI_MODEL', 'claude')
        
        # Process query using selected AI model
        try:
            ai_model = ai_model.lower()
            logger.info(f"Processing with AI model: {ai_model}")
            
            if ai_model == 'gemini':
                logger.info("Using Gemini AI for processing")
                ai_response = self.gemini_ai.process_query(user_query, conversation_history)
                logger.info("Received response from Gemini AI")
            elif ai_model == 'gpt':
                logger.info("Using ChatGPT for processing")
                ai_response = openai_ai.process_query(user_query, conversation_history)
                logger.info("Received response from ChatGPT")
            else:  # Default to Claude
                logger.info("Using Claude AI for processing")
                ai_response = claude_ai.process_query(user_query, conversation_history)
                logger.info("Received response from Claude AI")
            
            # If ai_response is already a dictionary with response_type and message, return it
            if isinstance(ai_response, dict) and 'response_type' in ai_response and 'message' in ai_response:
                logger.info(f"Returning response from {ai_model} AI")
                return ai_response
            
            # Otherwise, wrap the response in our standard format
            logger.info(f"Wrapping response from {ai_model} AI in standard format")
            return {
                'response_type': 'ai_response',
                'message': str(ai_response)
            }
        except Exception as e:
            logger.error(f"Error processing query with {ai_model} AI: {e}", exc_info=True)
            return {
                'response_type': 'error',
                'message': f"Sorry, there was an error processing your query: {str(e)}"
            }
    
    def _is_system_query(self, query: str) -> bool:
        """Check if the query is about system status or cache"""
        query_lower = query.lower()
        system_keywords = [
            'system status', 'cache stats', 'refresh cache', 'update cache',
            'статус системы', 'статистика кэша', 'обновить кэш'
        ]
        
        return any(keyword in query_lower for keyword in system_keywords)
    
    def _handle_system_query(self, query: str) -> Dict[str, Any]:
        """Handle system-related queries"""
        query_lower = query.lower()
        
        # Check for refresh/update request
        if any(keyword in query_lower for keyword in ['refresh cache', 'update cache', 'обновить кэш']):
            return {
                'response_type': 'cache_refresh_requested',
                'message': "I'll refresh the Planfix data cache now. This may take a moment..."
            }
        
        # Otherwise return cache stats
        stats = planfix_cache.get_stats()
        
        response = f"""
        ## System Status
        
        **Cache Information:**
        - Last updated: {stats.get('cache_age_minutes', 0):.1f} minutes ago
        - Total tasks: {stats.get('total_tasks', 0)}
        - Active tasks: {stats.get('active_tasks', 0)}
        - Completed tasks: {stats.get('completed_tasks', 0)}
        - Overdue tasks: {stats.get('overdue_tasks', 0)}
        - Total projects: {stats.get('total_projects', 0)}
        - Completion rate: {stats.get('completion_rate', 0):.1f}%
        
        **Task Status Breakdown:**
        """
        
        # Add status counts
        status_counts = stats.get('status_counts', {})
        for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            response += f"- {status}: {count}\n"
        
        return {
            'response_type': 'system_status',
            'message': response
        }
    
    def refresh_cache(self) -> Dict[str, Any]:
        """
        Request cache refresh and return status
        
        Returns:
            Dictionary with refresh status
        """
        try:
            logger.info("Requesting cache refresh")
            # Request cache refresh
            planfix_cache.refresh_all_caches()
            
            # Get updated stats
            stats = planfix_cache.get_stats()
            
            return {
                'response_type': 'cache_refreshed',
                'success': True,
                'message': f"Cache refreshed successfully. {stats['total_tasks']} tasks loaded, including {stats['active_tasks']} active tasks and {stats['overdue_tasks']} overdue tasks."
            }
        except Exception as e:
            logger.error(f"Error refreshing cache: {e}", exc_info=True)
            return {
                'response_type': 'cache_refreshed',
                'success': False,
                'message': f"Error refreshing cache: {str(e)}"
            }
    
    def format_conversation_history(self, messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format Django model messages into Claude API format
        
        Args:
            messages: List of Message model instances
        
        Returns:
            List of message dictionaries in Claude API format
        """
        formatted_messages = []
        
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            # Skip system messages or invalid roles
            if role not in ['user', 'assistant']:
                continue
            
            formatted_messages.append({
                "role": role,
                "content": content
            })
        
        return formatted_messages

# Singleton instance
agent = AgentQueryProcessor()