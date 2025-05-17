from django.core.management.base import BaseCommand
from chat.test_vector_store import test_vector_store

class Command(BaseCommand):
    help = 'Тестирование векторного хранилища данных'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Запуск тестирования векторного хранилища...'))
        test_vector_store()
        self.stdout.write(self.style.SUCCESS('Тестирование завершено.')) 