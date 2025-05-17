from django.core.management.base import BaseCommand
from chat.vector_service import search_planfix_tasks, update_vector_store
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Тестирование векторного поиска задач Planfix'

    def add_arguments(self, parser):
        parser.add_argument('query', type=str, help='Поисковый запрос')
        parser.add_argument(
            '--update',
            action='store_true',
            help='Обновить векторное хранилище перед поиском'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Количество результатов (по умолчанию 5)'
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.7,
            help='Порог релевантности (по умолчанию 0.7)'
        )

    def handle(self, *args, **options):
        try:
            # Обновляем хранилище, если нужно
            if options['update']:
                self.stdout.write('Обновление векторного хранилища...')
                updated_count = update_vector_store()
                self.stdout.write(self.style.SUCCESS(f'Обновлено {updated_count} задач'))

            # Выполняем поиск
            self.stdout.write(f'\nПоиск по запросу: {options["query"]}')
            results = search_planfix_tasks(
                query=options['query'],
                limit=options['limit'],
                score_threshold=options['threshold']
            )

            # Выводим результаты
            if not results:
                self.stdout.write(self.style.WARNING('Ничего не найдено'))
                return

            self.stdout.write(f'\nНайдено результатов: {len(results)}')
            for hit in results:
                task_data = hit.payload.get('data', {})
                self.stdout.write(f"""
Задача: {task_data.get('title', '')}
Ответственный: {task_data.get('assignee', {}).get('name', '')}
Проект: {task_data.get('project', {}).get('name', '')}
Статус: {task_data.get('status', {}).get('name', '')}
Приоритет: {task_data.get('priority', '')}
Дедлайн: {task_data.get('deadline', '')}
Релевантность: {hit.score:.3f}
""")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {str(e)}'))
            raise 