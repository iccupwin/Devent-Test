from django.db import models
from django.utils.translation import gettext_lazy as _

class AIModel(models.Model):
    """
    Модель для хранения информации о доступных ИИ-моделях
    """
    MODEL_TYPES = (
        ('claude', 'Claude AI'),
        ('gpt', 'ChatGPT'),
        ('deepseek', 'DeepSeek'),
    )
    
    name = models.CharField(max_length=50)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    version = models.CharField(max_length=50)
    api_base_url = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('ИИ-модель')
        verbose_name_plural = _('ИИ-модели')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.version})" 