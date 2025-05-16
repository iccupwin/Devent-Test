from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserSettings, Message
from .tasks import vectorize_message

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_settings(sender, instance, created, **kwargs):
    """Создает настройки пользователя при его регистрации"""
    if created:
        UserSettings.objects.create(user=instance)

@receiver(post_save, sender=Message)
def enqueue_vectorization(sender, instance: Message, created, **kwargs):
    if created:
        vectorize_message.delay(instance.id)