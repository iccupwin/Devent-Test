# chat/analytics_service.py
from django.utils import timezone
from .models import AnalyticsEvent, Message, User, AIModel, Conversation

class AnalyticsService:
    """
    Сервис для отправки событий в аналитику
    """
    @staticmethod
    def track_event(user, event_type, conversation=None, planfix_task_id=None, 
                   planfix_project_id=None, ai_model=None, metadata=None):
        """
        Отслеживание события для аналитики
        
        Args:
            user: Объект пользователя или None для анонимных событий
            event_type: Тип события (из AnalyticsEvent.EVENT_TYPES)
            conversation: Объект беседы (опционально)
            planfix_task_id: ID задачи Planfix (опционально)
            planfix_project_id: ID проекта Planfix (опционально)
            ai_model: Объект ИИ-модели (опционально)
            metadata: Дополнительные данные в формате JSON (опционально)
        
        Returns:
            Объект события аналитики
        """
        # Создание словаря метаданных, если он не был передан
        if metadata is None:
            metadata = {}
        
        # Создание и сохранение события
        event = AnalyticsEvent.objects.create(
            user=user,
            event_type=event_type,
            conversation=conversation,
            planfix_task_id=planfix_task_id,
            planfix_project_id=planfix_project_id,
            ai_model=ai_model,
            metadata=metadata
        )
        
        return event
    
    @staticmethod
    def track_conversation_start(user, conversation, ai_model=None):
        """
        Отслеживание начала новой беседы
        """
        metadata = {
            'conversation_id': conversation.id,
            'conversation_title': conversation.title,
        }
        
        if conversation.planfix_task_id:
            metadata['planfix_task_id'] = conversation.planfix_task_id
        
        return AnalyticsService.track_event(
            user=user,
            event_type='conversation_start',
            conversation=conversation,
            planfix_task_id=conversation.planfix_task_id,
            planfix_project_id=conversation.planfix_project_id,
            ai_model=ai_model,
            metadata=metadata
        )
    
    @staticmethod
    def track_message_sent(user, message):
        """
        Отслеживание отправки сообщения пользователем
        """
        metadata = {
            'message_id': message.id,
            'conversation_id': message.conversation.id,
            'tokens': message.tokens,
        }
        
        return AnalyticsService.track_event(
            user=user,
            event_type='message_sent',
            conversation=message.conversation,
            planfix_task_id=message.conversation.planfix_task_id,
            planfix_project_id=message.conversation.planfix_project_id,
            metadata=metadata
        )
    
    @staticmethod
    def track_ai_response(user, message, ai_model, response_time):
        """
        Отслеживание ответа от ИИ
        """
        metadata = {
            'message_id': message.id,
            'conversation_id': message.conversation.id,
            'tokens': message.tokens,
            'response_time': response_time,
        }
        
        return AnalyticsService.track_event(
            user=user,
            event_type='ai_response',
            conversation=message.conversation,
            planfix_task_id=message.conversation.planfix_task_id,
            planfix_project_id=message.conversation.planfix_project_id,
            ai_model=ai_model,
            metadata=metadata
        )
    
    @staticmethod
    def track_task_integration(user, conversation, planfix_task_id):
        """
        Отслеживание интеграции с задачей Planfix
        """
        metadata = {
            'conversation_id': conversation.id,
            'conversation_title': conversation.title,
            'planfix_task_id': planfix_task_id,
        }
        
        return AnalyticsService.track_event(
            user=user,
            event_type='task_integration',
            conversation=conversation,
            planfix_task_id=planfix_task_id,
            metadata=metadata
        )
    
    @staticmethod
    def track_error(user, error_message, conversation=None, ai_model=None):
        """
        Отслеживание ошибки в системе
        """
        metadata = {
            'error_message': error_message,
        }
        
        if conversation:
            metadata['conversation_id'] = conversation.id
        
        return AnalyticsService.track_event(
            user=user,
            event_type='error',
            conversation=conversation,
            ai_model=ai_model,
            metadata=metadata
        )

# Пример использования в agent_api.py
# from .analytics_service import AnalyticsService
# 
# # В методе обработки сообщения:
# AnalyticsService.track_message_sent(user, user_message)
# 
# # После получения ответа от ИИ:
# AnalyticsService.track_ai_response(user, assistant_message, ai_model, response_time)