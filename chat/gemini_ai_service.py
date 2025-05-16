import json
import logging
import time
import os
from typing import Dict, List, Any, Optional
from django.conf import settings
import google.generativeai as genai
from .analytics_service import AnalyticsService

# Configure logging
logger = logging.getLogger(__name__)

class GeminiAIService:
    """
    Service for communicating with Google's Gemini AI
    """

    def __init__(self):
        """Initialize Gemini AI service with API configuration"""
        self.api_key = os.environ.get('GEMINI_API_KEY', '')
        self.model = os.environ.get('GEMINI_API_MODEL', 'gemini-pro')
        self.max_retries = 3
        self.retry_delay = 5
        self.analytics = AnalyticsService()
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        logger.info(f"Initialized GeminiAIService with model: {self.model}")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for Gemini AI"""
        return """
        You are a helpful AI assistant. Use the provided context if it's relevant to answer the question.
        Always respond in the same language as the user's question.
        """

    def process_query(self, user_query: str, conversation_history: Optional[List[Dict[str, str]]] = None,
                     user=None, conversation=None) -> Dict[str, Any]:
        """
        Process a user query using Gemini AI
        
        Args:
            user_query: The user's question or request
            conversation_history: Optional list of previous messages in the conversation
            user: Optional user object for analytics
            conversation: Optional conversation object for analytics
            
        Returns:
            Dictionary with response data including response_type and message
        """
        try:
            print("\n=== Starting Gemini query processing ===")
            print(f"User query: {user_query}")
            print(f"API Key present: {'Yes' if self.api_key else 'No'}")
            print(f"Model: {self.model}")
            
            # Start timing the response
            start_time = time.time()
            
            # Initialize the model
            model = genai.GenerativeModel(self.model)
            
            # Prepare the chat
            chat = model.start_chat(history=[])
            
            # Add system prompt
            system_prompt = self._get_system_prompt()
            chat.send_message(system_prompt)
            
            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        if msg['role'] == 'user':
                            chat.send_message(msg['content'])
                        elif msg['role'] == 'assistant':
                            # Store the response in chat history
                            chat.history.append({
                                'role': 'model',
                                'parts': [msg['content']]
                            })
            
            # Send the user query
            response = chat.send_message(user_query)
            
            # Calculate response time
            response_time = time.time() - start_time
            print(f"\nResponse time: {response_time:.2f} seconds")
            
            # Log the response time
            logger.info(f"Gemini AI response time: {response_time:.2f} seconds")
            
            # Record analytics if user and conversation are provided
            if user:
                self.analytics.record_ai_interaction(
                    user=user,
                    conversation=conversation,
                    model=self.model,
                    response_time=response_time
                )
            
            return {
                'response_type': 'ai_response',
                'message': response.text
            }
            
        except Exception as e:
            logger.error(f"Error in Gemini AI processing: {str(e)}", exc_info=True)
            return {
                'response_type': 'error',
                'message': f"Sorry, there was an error processing your query: {str(e)}"
            } 