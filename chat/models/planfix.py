from django.db import models
from django.utils.translation import gettext_lazy as _

class PlanfixCache(models.Model):
    """
    Модель для отслеживания и управления кэшированием данных Planfix
    """
    cache_name = models.CharField(max_length=100, unique=True)
    last_update = models.DateTimeField(auto_now=True)
    is_valid = models.BooleanField(default=True)
    entries_count = models.IntegerField(default=0)
    update_duration = models.FloatField(default=0.0)  # Время обновления в секундах
    
    class Meta:
        verbose_name = _('Кэш Planfix')
        verbose_name_plural = _('Кэши Planfix')
    
    def __str__(self):
        return f"{self.cache_name} ({self.entries_count} entries)"

class PlanfixTask(models.Model):
    """
    Модель для хранения ключевой информации о задачах Planfix для аналитики
    """
    task_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=100)
    project_id = models.CharField(max_length=100, null=True, blank=True)
    project_name = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    assignee = models.CharField(max_length=255, null=True, blank=True)
    assigner = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    is_overdue = models.BooleanField(default=False)
    last_sync = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Задача Planfix')
        verbose_name_plural = _('Задачи Planfix')
        indexes = [
            models.Index(fields=['task_id']),
            models.Index(fields=['project_id']),
            models.Index(fields=['status']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['is_overdue']),
        ]
    
    def __str__(self):
        return f"{self.name} (ID: {self.task_id})" 