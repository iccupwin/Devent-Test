from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages  # Добавлен импорт для сообщений
import json
import logging

from .models import Conversation, Message, User
from .planfix_service import (
    get_active_tasks, 
    get_completed_tasks, 
    get_task_by_id, 
    format_task_for_claude,
    get_all_tasks
)
from .services import ClaudeService

# Настройка логирования
logger = logging.getLogger(__name__)

def planfix_tasks(request):
    """Отображение списка задач из Planfix с постраничной навигацией"""
    try:
        # Базовые параметры запроса
        page = int(request.GET.get('page', 1)) - 1  # Страницы в UI с 1, в API с 0
        status_filter = request.GET.get('status', 'all')
        
        # Получаем задачи в зависимости от фильтра статуса
        if status_filter == 'active':
            tasks = get_active_tasks()
            total_count = len(tasks)
        elif status_filter == 'completed':
            tasks = get_completed_tasks()
            total_count = len(tasks)
        else:  # 'all' по умолчанию
            tasks = get_all_tasks()
            total_count = len(tasks)
        
        # Вычисляем общее количество страниц
        page_size = 25
        total_pages = (total_count + page_size - 1) // page_size
        
        # Логируем информацию о запросе
        logger.info(f"Запрос задач Planfix: страница={page+1}, статус={status_filter}, всего={total_count}")
        
        return render(request, 'chat/planfix_task.html', {
            'tasks': tasks,
            'total_count': total_count,
            'current_page': page + 1,
            'status_filter': status_filter,
            'total_pages': total_pages
        })
    
    except Exception as e:
        logger.error(f"Ошибка при получении задач Planfix: {str(e)}", exc_info=True)
        return render(request, 'chat/planfix_task.html', {
            'tasks': [],
            'total_count': 0,
            'current_page': 1,
            'status_filter': 'all',
            'error': str(e),
            'total_pages': 1
        })

def planfix_task_detail(request, task_id):
    """Отображение детальной информации о задаче"""
    try:
        # Получаем задачу из Planfix по ID
        task = get_task_by_id(task_id)
        
        # Добавляем логирование для отладки
        logger.info(f"Получена задача с ID {task_id}: {task}")
        
        if not task:
            # Добавляем обработку случая, когда задача не найдена
            logger.error(f"Задача с ID {task_id} не найдена")
            # Вместо сообщения в messages, просто переходим на страницу со списком задач
            # или можно использовать встроенный механизм сообщений Django
            return redirect('chat:planfix_tasks')
        
        # Передаем задачу в шаблон
        return render(request, 'chat/planfix_task_detail.html', {
            'task': task,
            'debug': False  # Можно установить в True для отладки
        })
    
    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при получении деталей задачи {task_id}: {str(e)}", exc_info=True)
        
        # Переходим на страницу со списком задач без сообщения об ошибке
        return redirect('chat:planfix_tasks')

@csrf_exempt
def planfix_task_integrate(request, task_id):
    """API endpoint для интеграции задачи с Claude"""
    if request.method == 'POST':
        try:
            logger.info(f"Запрос на интеграцию задачи {task_id} с Claude")
            
            # Получаем задачу из Planfix
            task = get_task_by_id(task_id)
            
            if not task:
                return JsonResponse({
                    'success': False,
                    'error': 'Задача не найдена'
                }, status=404)
            
            # Получаем или создаем анонимного пользователя
            user, created = User.objects.get_or_create(username='anonymous')
            
            # Создаем новый разговор
            conversation = Conversation.objects.create(
                user=user,
                title=f"Задача #{task_id}: {task.get('name', 'Без названия')}",
            )
            
            # Форматируем задачу для обсуждения с Claude
            task_text = format_task_for_claude(task)
            
            # Создаем первое сообщение пользователя
            user_message = (
                f"Я хочу обсудить с тобой следующую задачу из Planfix:\n\n"
                f"{task_text}\n\n"
                f"Пожалуйста, проанализируй эту задачу и помоги мне с ее выполнением. "
                f"Что бы ты посоветовал в первую очередь обратить внимание?"
            )
            
            # Сохраняем сообщение пользователя
            user_msg = Message.objects.create(
                conversation=conversation,
                role='user',
                content=user_message
            )
            
            logger.info(f"Создано сообщение пользователя для задачи {task_id}")
            
            # Отправляем сообщение Claude
            claude_service = ClaudeService()
            response = claude_service.send_message([
                {"role": "user", "content": user_message}
            ])
            
            logger.info(f"Получен ответ от Claude для задачи {task_id}")
            
            # Сохраняем ответ от Claude
            assistant_msg = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=response
            )
            
            logger.info(f"Создано сообщение ассистента для задачи {task_id}")
            
            return JsonResponse({
                'success': True,
                'conversation_id': conversation.id
            })
            
        except Exception as e:
            logger.error(f"Ошибка интеграции задачи {task_id} с Claude: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Метод не поддерживается'
    }, status=405)