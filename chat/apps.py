from django.apps import AppConfig
from django.apps import AppConfig
import posthog


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'
    
    def ready(self):
        import chat.signals

class YourAppConfig(AppConfig):
    name = "Devent-Test"
    def ready(self):
        posthog.api_key = 'phc_GqSt8VQZ0mIMqSZVXY1ZhnTxTqpQfQdHpwoWb9FSBzK'
        posthog.host = 'https://eu.i.posthog.com'