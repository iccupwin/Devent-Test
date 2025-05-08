from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
import time

class Command(BaseCommand):
    help = 'Обновляет кэш данных Planfix'

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write(self.style.SUCCESS(f'Начало обновления кэша Planfix: {timezone.now()}'))
        
        try:
            from chat.planfix_service import update_tasks_cache
            from chat.planfix_cache_service import planfix_cache
            
            # Обновление основного кэша задач
            tasks = update_tasks_cache(force=True)
            self.stdout.write(self.style.SUCCESS(f'Основной кэш задач обновлен, загружено {len(tasks)} задач'))
            
            # Обновление производных кэшей
            planfix_cache.refresh_all_caches()
            self.stdout.write(self.style.SUCCESS('Все производные кэши обновлены'))
            
            # Получение обновленной статистики
            stats = planfix_cache.get_stats()
            
            # Вывод статистики
            self.stdout.write(f'Всего задач: {stats.get("total_tasks", 0)}')
            self.stdout.write(f'Активных задач: {stats.get("active_tasks", 0)}')
            self.stdout.write(f'Завершенных задач: {stats.get("completed_tasks", 0)}')
            self.stdout.write(f'Просроченных задач: {stats.get("overdue_tasks", 0)}')
            
            # Расчет времени выполнения
            elapsed_time = time.time() - start_time
            self.stdout.write(self.style.SUCCESS(f'Обновление кэша завершено за {elapsed_time:.2f} секунд'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при обновлении кэша: {str(e)}'))