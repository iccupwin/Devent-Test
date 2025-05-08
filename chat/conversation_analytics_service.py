# chat/conversation_analytics_service.py
import logging
from django.db.models import Count, Sum, Avg, F, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    Conversation, Message, User, ConversationAnalytics,
    AnalyticsEvent, MessageFeedback, ConversationTag
)

logger = logging.getLogger(__name__)

class ConversationAnalyticsService:
    """
    Сервис для работы с аналитикой бесед
    """
    
    @staticmethod
    def update_conversation_analytics(conversation_id):
        """
        Обновление аналитики для указанной беседы
        
        Args:
            conversation_id: ID беседы
        
        Returns:
            Объект аналитики беседы
        """
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            analytics, created = ConversationAnalytics.objects.get_or_create(conversation=conversation)
            
            # Обновление аналитики
            analytics.update_analytics()
            
            logger.info(f"Обновлена аналитика для беседы {conversation_id}")
            return analytics
        except Conversation.DoesNotExist:
            logger.error(f"Беседа с ID {conversation_id} не найдена")
            return None
        except Exception as e:
            logger.error(f"Ошибка при обновлении аналитики беседы {conversation_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_conversation_statistics(user=None, days=30):
        """
        Получение статистики по беседам за указанный период
        
        Args:
            user: Пользователь (None для всех пользователей)
            days: Количество дней для анализа
        
        Returns:
            Словарь со статистикой
        """
        start_date = timezone.now() - timedelta(days=days)
        
        # Базовый фильтр по дате
        conversations = Conversation.objects.filter(created_at__gte=start_date)
        
        # Фильтр по пользователю, если указан
        if user:
            conversations = conversations.filter(user=user)
        
        # Получение статистики
        total_conversations = conversations.count()
        total_messages = Message.objects.filter(conversation__in=conversations).count()
        
        # Среднее количество сообщений в беседе
        avg_messages_per_conversation = total_messages / total_conversations if total_conversations > 0 else 0
        
        # Статистика по AI моделям
        model_stats = Message.objects.filter(
            conversation__in=conversations,
            role='assistant'
        ).values('ai_model_used__name').annotate(
            count=Count('id'),
            tokens=Sum('tokens')
        ).order_by('-count')
        
        # Статистика по тегам
        tag_stats = ConversationTag.objects.filter(
            conversations__conversation__in=conversations
        ).annotate(
            count=Count('conversations')
        ).values('name', 'count').order_by('-count')
        
        # Интеграция с Planfix
        planfix_integrations = conversations.filter(planfix_task_id__isnull=False).count()
        
        # Результат
        stats = {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'avg_messages_per_conversation': round(avg_messages_per_conversation, 2),
            'model_stats': list(model_stats),
            'tag_stats': list(tag_stats),
            'planfix_integrations': planfix_integrations,
            'period_days': days
        }
        
        return stats
    
    @staticmethod
    def add_conversation_tag(conversation_id, tag_name, tag_description=None, tag_color=None):
        """
        Добавление тега к беседе
        
        Args:
            conversation_id: ID беседы
            tag_name: Название тега
            tag_description: Описание тега (опционально)
            tag_color: Цвет тега (опционально)
        
        Returns:
            True в случае успеха, False в случае ошибки
        """
        try:
            # Получение или создание беседы
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Получение или создание аналитики беседы
            analytics, created = ConversationAnalytics.objects.get_or_create(conversation=conversation)
            
            # Получение или создание тега
            tag, created = ConversationTag.objects.get_or_create(
                name=tag_name,
                defaults={
                    'description': tag_description or '',
                    'color': tag_color or '#0071e3'
                }
            )
            
            # Добавление тега к аналитике беседы
            analytics.tags.add(tag)
            
            logger.info(f"Добавлен тег '{tag_name}' к беседе {conversation_id}")
            return True
        except Conversation.DoesNotExist:
            logger.error(f"Беседа с ID {conversation_id} не найдена")
            return False
        except Exception as e:
            logger.error(f"Ошибка при добавлении тега к беседе {conversation_id}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def add_message_feedback(message_id, user, feedback_type, comment=None):
        """
        Добавление обратной связи к сообщению
        
        Args:
            message_id: ID сообщения
            user: Объект пользователя
            feedback_type: Тип обратной связи
            comment: Комментарий (опционально)
        
        Returns:
            Объект обратной связи или None в случае ошибки
        """
        try:
            message = Message.objects.get(id=message_id)
            
            # Создание или обновление обратной связи
            feedback, created = MessageFeedback.objects.update_or_create(
                message=message,
                user=user,
                defaults={
                    'feedback_type': feedback_type,
                    'comment': comment
                }
            )
            
            logger.info(f"Добавлена обратная связь к сообщению {message_id} от пользователя {user.username}")
            return feedback
        except Message.DoesNotExist:
            logger.error(f"Сообщение с ID {message_id} не найдено")
            return None
        except Exception as e:
            logger.error(f"Ошибка при добавлении обратной связи к сообщению {message_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_user_activity_stats(user, days=30):
        """
        Получение статистики активности пользователя
        
        Args:
            user: Объект пользователя
            days: Количество дней для анализа
        
        Returns:
            Словарь со статистикой активности
        """
        start_date = timezone.now() - timedelta(days=days)
        
        # Беседы пользователя
        conversations = Conversation.objects.filter(user=user, created_at__gte=start_date)
        
        # Сообщения пользователя
        user_messages = Message.objects.filter(
            conversation__in=conversations,
            role='user',
            created_at__gte=start_date
        )
        
        # Сообщения ассистента
        assistant_messages = Message.objects.filter(
            conversation__in=conversations,
            role='assistant',
            created_at__gte=start_date
        )
        
        # Активность по дням
        daily_activity = user_messages.values('created_at__date').annotate(
            count=Count('id')
        ).order_by('created_at__date')
        
        # Токены
        total_tokens = assistant_messages.aggregate(Sum('tokens'))['tokens__sum'] or 0
        
        # Среднее время ответа ассистента
        avg_response_time = None  # Требует сложного расчета, можно реализовать отдельно
        
        # Результат
        stats = {
            'total_conversations': conversations.count(),
            'total_user_messages': user_messages.count(),
            'total_assistant_messages': assistant_messages.count(),
            'total_tokens': total_tokens,
            'daily_activity': list(daily_activity),
            'avg_response_time': avg_response_time,
            'period_days': days
        }
        
        return stats