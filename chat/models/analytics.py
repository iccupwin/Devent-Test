from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class AnalyticsEvent(models.Model):
    """
    Модель для отслеживания событий в системе для аналитики
    """
    EVENT_TYPES = (
        ('conversation_start', _('Начало беседы')),
        ('conversation_end', _('Завершение беседы')),
        ('message_sent', _('Отправлено сообщение')),
        ('ai_response', _('Ответ ИИ')),
        ('task_integration', _('Интеграция с задачей')),
        ('cache_refresh', _('Обновление кэша')),
        ('login', _('Вход в систему')),
        ('logout', _('Выход из системы')),
        ('error', _('Ошибка')),
    )
    
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    conversation = models.ForeignKey('Conversation', on_delete=models.SET_NULL, null=True, blank=True)
    planfix_task_id = models.CharField(max_length=100, null=True, blank=True)
    planfix_project_id = models.CharField(max_length=100, null=True, blank=True)
    ai_model = models.ForeignKey('AIModel', on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = _('Событие аналитики')
        verbose_name_plural = _('События аналитики')
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.timestamp}"

class UserMetrics(models.Model):
    """
    Модель для хранения агрегированных метрик пользователей
    """
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='metrics')
    day = models.DateField()
    conversations_count = models.IntegerField(default=0)
    messages_sent = models.IntegerField(default=0)
    tokens_used = models.IntegerField(default=0)
    tasks_integrated = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    
    class Meta:
        verbose_name = _('Метрика пользователя')
        verbose_name_plural = _('Метрики пользователей')
        unique_together = ['user', 'day']
        indexes = [
            models.Index(fields=['user', 'day']),
            models.Index(fields=['day']),
        ]
    
    def __str__(self):
        return f"Метрики {self.user.username} за {self.day}"

class AIModelMetrics(models.Model):
    """
    Модель для хранения метрик использования ИИ-моделей
    """
    ai_model = models.ForeignKey('AIModel', on_delete=models.CASCADE, related_name='metrics')
    day = models.DateField()
    requests_count = models.IntegerField(default=0)
    tokens_used = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    error_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = _('Метрика ИИ-модели')
        verbose_name_plural = _('Метрики ИИ-моделей')
        unique_together = ['ai_model', 'day']
        indexes = [
            models.Index(fields=['ai_model', 'day']),
            models.Index(fields=['day']),
        ]
    
    def __str__(self):
        return f"Метрики {self.ai_model.name} за {self.day}"


# chat/models.py или chat/models/analytics.py
class AIUsageDaily(models.Model):
    """Ежедневная статистика использования ИИ-моделей"""
    date = models.DateField()
    ai_model = models.ForeignKey('AIModel', on_delete=models.CASCADE)
    requests_count = models.IntegerField(default=0)
    tokens_used = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ['date', 'ai_model']
        indexes = [models.Index(fields=['date']), models.Index(fields=['ai_model'])]

class UserActivityDaily(models.Model):
    """Ежедневная активность пользователей"""
    date = models.DateField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    messages_count = models.IntegerField(default=0)
    conversations_count = models.IntegerField(default=0)
    tokens_used = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['date', 'user']
        indexes = [models.Index(fields=['date']), models.Index(fields=['user'])] 