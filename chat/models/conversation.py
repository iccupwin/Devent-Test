from django.db import models
from django.utils.translation import gettext_lazy as _

class Conversation(models.Model):
    """
    Расширенная модель беседы с привязкой к проектам и задачам Planfix
    """
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255)
    ai_model = models.ForeignKey('AIModel', on_delete=models.SET_NULL, null=True, related_name='conversations')
    planfix_task_id = models.CharField(max_length=100, blank=True, null=True)
    planfix_project_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    summary = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Беседа')
        verbose_name_plural = _('Беседы')
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['planfix_task_id']),
            models.Index(fields=['planfix_project_id']),
        ]
    
    def get_related_task_info(self):
        """Получить информацию о связанной задаче из Planfix"""
        if self.planfix_task_id:
            from chat.planfix_service import get_task_by_id
            return get_task_by_id(self.planfix_task_id)
        return None
    
    def __str__(self):
        return self.title 