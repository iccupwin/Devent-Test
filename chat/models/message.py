from django.db import models
from django.utils.translation import gettext_lazy as _

class Message(models.Model):
    """
    Расширенная модель сообщений с метаданными и поддержкой различных ИИ
    """
    ROLE_CHOICES = (
        ('user', _('Пользователь')),
        ('assistant', _('Ассистент')),
        ('system', _('Система')),
    )
    
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    tokens = models.IntegerField(default=0)  # Количество токенов для расчета стоимости
    ai_model_used = models.ForeignKey('AIModel', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    metadata = models.JSONField(default=dict, blank=True)  # Для дополнительных данных от ИИ
    processing_time = models.FloatField(default=0.0, verbose_name='Время обработки (сек)')  # Время обработки запроса в секундах
    
    class Meta:
        ordering = ['created_at']
        verbose_name = _('Сообщение')
        verbose_name_plural = _('Сообщения')
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.role} - {self.content[:50]}..." 