import os
import requests
from dotenv import load_dotenv
from .planfix_service import get_all_tasks, get_projects

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiAgent:
    def __init__(self):
        self.system_prompt = """Ты - ассистент, который помогает работать с задачами и проектами в Planfix.
У тебя есть доступ к следующим данным:
1. Список всех задач с их статусами, описаниями и проектами
2. Список всех проектов с их описаниями

Ты можешь:
- Отвечать на вопросы о задачах и проектах
- Помогать анализировать статусы задач
- Давать рекомендации по управлению проектами
- Отвечать на вопросы о сроках и приоритетах

При ответе используй только те данные, которые есть в контексте. Если информации недостаточно, так и скажи."""

    def _format_task(self, task):
        """Форматирование информации о задаче"""
        project_name = task.get('project', {}).get('name', 'Без проекта')
        status = task.get('status', {}).get('name', 'Статус не указан')
        priority = task.get('priority', {}).get('name', 'Приоритет не указан')
        deadline = task.get('deadline', 'Срок не указан')
        description = task.get('description', 'Описание отсутствует')
        
        return f"""
Задача: {task.get('name', 'Без названия')}
ID: {task.get('id', 'Не указан')}
Проект: {project_name}
Статус: {status}
Приоритет: {priority}
Срок: {deadline}
Описание: {description}
"""

    def _format_project(self, project):
        """Форматирование информации о проекте"""
        return f"""
Проект: {project.get('name', 'Без названия')}
ID: {project.get('id', 'Не указан')}
Описание: {project.get('description', 'Описание отсутствует')}
Статус: {project.get('status', {}).get('name', 'Статус не указан')}
"""

    def _get_context(self):
        """Получение и форматирование контекста задач и проектов"""
        tasks = get_all_tasks()
        projects = get_projects()
        
        # Форматируем задачи
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append(self._format_task(task))
        
        # Форматируем проекты
        formatted_projects = []
        for project in projects:
            formatted_projects.append(self._format_project(project))
        
        # Создаем структурированный контекст
        context = f"""
АКТИВНЫЕ ЗАДАЧИ:
{''.join(formatted_tasks)}

ПРОЕКТЫ:
{''.join(formatted_projects)}
"""
        
        return context

    def process_query(self, message_text, conversation_history):
        url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent"
        headers = {"Content-Type": "application/json"}
        
        # Получаем контекст задач и проектов
        context = self._get_context()
        
        # Формируем системный промпт с контекстом
        system_message = f"{self.system_prompt}\n\nКонтекст:\n{context}"
        
        # Форматируем историю диалога
        contents = [
            {
                "role": "model",
                "parts": [{"text": system_message}]
            }
        ]
        
        # Добавляем историю диалога
        for message in conversation_history:
            role = "user" if message.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": message["content"]}]
            })
        
        # Добавляем текущее сообщение
        contents.append({
            "role": "user",
            "parts": [{"text": message_text}]
        })
        
        data = {"contents": contents}
        params = {"key": GEMINI_API_KEY}
        
        resp = requests.post(url, headers=headers, params=params, json=data)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            return {"message": f"Ошибка Gemini API: {resp.status_code} {resp.text}"}
            
        result = resp.json()
        return {"message": result["candidates"][0]["content"]["parts"][0]["text"]}

gemini_ai = GeminiAgent() 