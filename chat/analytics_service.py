# chat/analytics_service.py
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from .models import (
    AnalyticsEvent, Message, User, AIModel, Conversation,
    AIModelMetrics, UserMetrics
)
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Сервис для работы с аналитикой"""
    
    @staticmethod
    def log_event(event_type, status, user=None, details=None):
        """
        Логирование события
        
        Args:
            event_type (str): Тип события
            status (str): Статус события
            user (User, optional): Пользователь
            details (dict, optional): Детали события
        """
        try:
            event = AnalyticsEvent(
                event_type=event_type,
                status=status,
                user=user,
                details=details or {}
            )
            event.save()
            logger.info(f"Logged event: {event_type} - {status}")
        except Exception as e:
            logger.error(f"Ошибка при логировании события: {str(e)}")
            # Try to log with minimal fields if the full creation fails
            try:
                event = AnalyticsEvent(
                    event_type=event_type,
                    status='error',
                    details={'error': str(e)}
                )
                event.save()
            except Exception as e2:
                logger.error(f"Failed to log error event: {str(e2)}")
    
    @staticmethod
    def log_cache_refresh(success, error_message=None):
        """
        Логирование обновления кэша
        
        Args:
            success (bool): Успешность обновления
            error_message (str, optional): Сообщение об ошибке
        """
        status = 'success' if success else 'error'
        details = {'error': error_message} if error_message else {}
        
        AnalyticsService.log_event(
            event_type='cache_refresh',
            status=status,
            details=details
        )
    
    @staticmethod
    def log_ai_query(query, success, user=None, error_message=None):
        """
        Логирование запроса к ИИ
        
        Args:
            query (str): Текст запроса
            success (bool): Успешность запроса
            user (User, optional): Пользователь
            error_message (str, optional): Сообщение об ошибке
        """
        try:
            status = 'success' if success else 'error'
            details = {
                'query': query,
                'error': error_message
            } if error_message else {'query': query}
            
            event = AnalyticsEvent(
                event_type='ai_query',
                status=status,
                user=user,
                details=details
            )
            event.save()
            logger.info(f"Logged AI query: {query[:50]}...")
        except Exception as e:
            logger.error(f"Ошибка при логировании запроса к ИИ: {str(e)}")
    
    @staticmethod
    def get_analytics_summary(days=7):
        """Получение сводки аналитики за указанный период"""
        try:
            start_date = timezone.now() - timezone.timedelta(days=days)
            
            # Общая статистика
            total_events = AnalyticsEvent.objects.filter(
                timestamp__gte=start_date
            ).count()
            
            # Статистика по типам событий
            events_by_type = AnalyticsEvent.objects.filter(
                timestamp__gte=start_date
            ).values('event_type').annotate(
                count=models.Count('id')
            )
            
            # Статистика по статусам
            events_by_status = AnalyticsEvent.objects.filter(
                timestamp__gte=start_date
            ).values('status').annotate(
                count=models.Count('id')
            )
            
            # Топ запросов
            top_queries = AnalyticsEvent.get_top_queries(limit=5)
            
            # Статистика ошибок
            error_stats = AnalyticsEvent.get_error_stats(days=days)
            
            # Статистика кэша
            cache_stats = AnalyticsEvent.get_cache_stats(days=days)
            
            # Качество ответов
            quality_stats = AnalyticsService.get_quality_stats(days)
            
            # История качества
            quality_history = AnalyticsService.get_quality_history(days)
            
            # История использования
            usage_history = AnalyticsService.get_usage_history(days)
            
            return {
                'total_events': total_events,
                'events_by_type': list(events_by_type),
                'events_by_status': list(events_by_status),
                'top_queries': list(top_queries),
                'error_stats': list(error_stats),
                'cache_stats': list(cache_stats),
                'quality_score': quality_stats['overall_score'],
                'helpful_responses': quality_stats['helpful_percentage'],
                'accuracy_score': quality_stats['accuracy_score'],
                'quality_feedback': quality_stats['recent_feedback'],
                'quality_history': quality_history,
                'usage_history': usage_history
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении сводки аналитики: {str(e)}")
            return {}
    
    @staticmethod
    def get_quality_stats(days=7):
        """Получение статистики качества ответов"""
        try:
            start_date = timezone.now() - timezone.timedelta(days=days)
            
            # Получаем все оценки за период
            feedback = AnalyticsEvent.objects.filter(
                event_type='feedback',
                timestamp__gte=start_date
            ).order_by('-timestamp')
            
            # Считаем общую оценку
            total_ratings = feedback.count()
            if total_ratings > 0:
                overall_score = feedback.aggregate(
                    avg_score=models.Avg('details__rating')
                )['avg_score'] * 20  # Преобразуем в проценты
            else:
                overall_score = 0
            
            # Считаем процент полезных ответов
            helpful_count = feedback.filter(
                details__rating__gte=4
            ).count()
            helpful_percentage = (helpful_count / total_ratings * 100) if total_ratings > 0 else 0
            
            # Считаем точность ответов
            accuracy_count = feedback.filter(
                details__accuracy=True
            ).count()
            accuracy_score = (accuracy_count / total_ratings * 100) if total_ratings > 0 else 0
            
            # Получаем последние оценки
            recent_feedback = feedback[:10].values(
                'details__query',
                'details__rating',
                'details__comment',
                'timestamp'
            )
            
            return {
                'overall_score': round(overall_score, 1),
                'helpful_percentage': round(helpful_percentage, 1),
                'accuracy_score': round(accuracy_score, 1),
                'recent_feedback': list(recent_feedback)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики качества: {str(e)}")
            return {
                'overall_score': 0,
                'helpful_percentage': 0,
                'accuracy_score': 0,
                'recent_feedback': []
            }
    
    @staticmethod
    def get_quality_history(days=7):
        """Получение истории качества ответов"""
        try:
            start_date = timezone.now().date() - timezone.timedelta(days=days)
            
            # Получаем ежедневную статистику качества
            daily_stats = AnalyticsEvent.objects.filter(
                event_type='feedback',
                timestamp__date__gte=start_date
            ).values('timestamp__date').annotate(
                score=models.Avg('details__rating') * 20,
                helpful=models.Count('id', filter=models.Q(details__rating__gte=4)) * 100.0 / models.Count('id'),
                accuracy=models.Count('id', filter=models.Q(details__accuracy=True)) * 100.0 / models.Count('id')
            ).order_by('timestamp__date')
            
            # Форматируем результат
            result = []
            for stat in daily_stats:
                result.append({
                    'day': stat['timestamp__date'].strftime('%Y-%m-%d'),
                    'score': round(stat['score'], 1),
                    'helpful': round(stat['helpful'], 1),
                    'accuracy': round(stat['accuracy'], 1)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории качества: {str(e)}")
            return []
    
    @staticmethod
    def get_usage_history(days=7):
        """Получение истории использования системы"""
        try:
            start_date = timezone.now().date() - timezone.timedelta(days=days)
            
            # Получаем ежедневную статистику использования
            daily_stats = Message.objects.filter(
                timestamp__date__gte=start_date
            ).values('timestamp__date').annotate(
                requests=models.Count('id'),
                response_time=models.Avg('processing_time')
            ).order_by('timestamp__date')
            
            # Форматируем результат
            result = []
            for stat in daily_stats:
                result.append({
                    'day': stat['timestamp__date'].strftime('%Y-%m-%d'),
                    'requests': stat['requests'],
                    'response_time': round(stat['response_time'], 2) if stat['response_time'] else 0
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории использования: {str(e)}")
            return []
    
    @staticmethod
    def get_ai_models_usage(days=30):
        """Получение статистики использования моделей ИИ"""
        start_date = timezone.now().date() - timedelta(days=days)
        
        models_usage = AIModelMetrics.objects.filter(
            day__gte=start_date
        ).values('ai_model__name').annotate(
            total_requests=Sum('requests_count'),
            total_tokens=Sum('tokens_used')
        ).order_by('-total_requests')
        
        return models_usage
    
    @staticmethod
    def get_daily_activity(days=30):
        """Получение ежедневной активности"""
        start_date = timezone.now().date() - timedelta(days=days)
        end_date = timezone.now().date()
        
        # Создаем полный список дат
        date_list = []
        current = start_date
        while current <= end_date:
            date_list.append(current)
            current += timedelta(days=1)
        
        # Получаем данные активности
        daily_data = UserMetrics.objects.filter(
            day__gte=start_date
        ).values('day').annotate(
            messages_count=Sum('messages_sent'),
            conversations_count=Sum('conversations_count')
        ).order_by('day')
        
        # Преобразуем в словарь для быстрого доступа
        data_dict = {item['day']: item for item in daily_data}
        
        # Форматируем результат
        result = []
        for date in date_list:
            if date in data_dict:
                result.append({
                    'day': date.strftime('%Y-%m-%d'),
                    'messages_count': data_dict[date]['messages_count'] or 0,
                    'conversations_count': data_dict[date]['conversations_count'] or 0
                })
            else:
                result.append({
                    'day': date.strftime('%Y-%m-%d'),
                    'messages_count': 0,
                    'conversations_count': 0
                })
        
        return result
    
    @staticmethod
    def get_tokens_usage(days=30):
        """Получение статистики использования токенов"""
        start_date = timezone.now().date() - timedelta(days=days)
        
        tokens_data = UserMetrics.objects.filter(
            day__gte=start_date
        ).values('day').annotate(
            tokens_used=Sum('tokens_used')
        ).order_by('day')
        
        return tokens_data
    
    @staticmethod
    def get_top_users(limit=10, days=30):
        """Получение топ пользователей по активности"""
        start_date = timezone.now().date() - timedelta(days=days)
        
        top_users = UserMetrics.objects.filter(
            day__gte=start_date
        ).values(
            'user__username',
            'user__first_name',
            'user__last_name'
        ).annotate(
            total_messages=Sum('messages_sent'),
            total_conversations=Sum('conversations_count'),
            total_tokens=Sum('tokens_used')
        ).order_by('-total_messages')[:limit]
        
        return top_users

# Пример использования в agent_api.py
# from .analytics_service import AnalyticsService
# 
# # В методе обработки сообщения:
# AnalyticsService.track_message_sent(user, user_message)
# 
# # После получения ответа от ИИ:
# AnalyticsService.track_ai_response(user, assistant_message, ai_model, response_time)