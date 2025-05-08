from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class UserSettings(models.Model):
    """
    Модель для хранения настроек пользователя
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    theme = models.CharField(
        verbose_name=_('Тема оформления'),
        max_length=20,
        choices=(
            ('light', _('Светлая')),
            ('dark', _('Темная')),
            ('system', _('Системная')),
        ),
        default='system'
    )
    language = models.CharField(
        verbose_name=_('Язык интерфейса'),
        max_length=10,
        choices=(
            ('ru', _('Русский')),
            ('en', _('Английский')),
        ),
        default='ru'
    )
    enable_notifications = models.BooleanField(
        verbose_name=_('Включить уведомления'),
        default=True
    )
    show_completed_tasks = models.BooleanField(
        verbose_name=_('Показывать завершенные задачи'),
        default=True
    )
    default_page_size = models.IntegerField(
        verbose_name=_('Размер страницы по умолчанию'),
        default=25,
        choices=(
            (10, '10'),
            (25, '25'),
            (50, '50'),
            (100, '100'),
        )
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Настройки пользователя')
        verbose_name_plural = _('Настройки пользователей')
    
    def __str__(self):
        return f"Настройки пользователя {self.user.username}"