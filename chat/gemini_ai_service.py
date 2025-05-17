import json
import logging
import time
import os
import random
from typing import Dict, List, Any, Optional
from django.conf import settings
import google.generativeai as genai
from .analytics_service import AnalyticsService
from .vector_service import search, search_planfix_tasks
from .planfix_cache_service import planfix_cache
from functools import lru_cache

# Configure logging
logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    """Custom exception for rate limit errors"""
    def __init__(self, message: str, retry_after: int = 60):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)

class GeminiAIService:
    """
    Service for communicating with Google's Gemini AI
    """
    
    # Кэш для результатов vector search
    _vector_cache = {}
    _vector_cache_ttl = 300  # 5 минут

    def _check_available_models(self) -> List[str]:
        """
        Проверяет доступные модели Gemini API
        Returns:
            List[str]: Список доступных моделей
        """
        try:
            logger.info("\n=== Checking Available Gemini Models ===")
            available_models = []
            for model in genai.list_models():
                model_info = {
                    'name': model.name,
                    'display_name': model.display_name,
                    'description': model.description,
                    'generation_methods': model.supported_generation_methods
                }
                available_models.append(model.name)
                logger.info(f"Model: {model.name}")
                logger.info(f"Display Name: {model.display_name}")
                logger.info(f"Description: {model.description}")
                logger.info(f"Supported Methods: {model.supported_generation_methods}")
                logger.info("---")
            
            logger.info(f"Total available models: {len(available_models)}")
            logger.info("=== End of Available Models ===\n")
            return available_models
        except Exception as e:
            logger.error(f"Error checking available models: {str(e)}")
            return []

    def __init__(self):
        """Initialize Gemini AI service with API configuration"""
        self.api_key = os.environ.get('GEMINI_API_KEY', '')
        # Используем самую быструю модель по умолчанию
        self.model = os.environ.get('GEMINI_API_MODEL', 'gemini-1.5-flash')
        self.max_retries = 3
        self.base_retry_delay = 5
        self.max_retry_delay = 60
        self.analytics = AnalyticsService()
        
        # Rate limiting configuration
        self.requests_per_minute = 60
        self.tokens_per_minute = 60000
        self.requests_per_day = 1000
        self.last_request_time = 0
        self.minute_requests = 0
        self.minute_tokens = 0
        self.day_requests = 0
        self.last_reset_time = time.time()
        
        # Проверяем наличие API ключа
        if not self.api_key:
            logger.error("GEMINI_API_KEY не найден в переменных окружения!")
        else:
            logger.info("GEMINI_API_KEY успешно загружен")
            logger.info(f"API Key (первые 10 символов): {self.api_key[:10]}...")
            logger.info(f"Используется модель: {self.model}")
        
        # Configure the Gemini API
        try:
            logger.info("Попытка конфигурации Gemini API...")
            genai.configure(api_key=self.api_key)
            logger.info("Gemini API успешно сконфигурирован")
            
            # Проверяем доступные модели
            available_models = self._check_available_models()
            
            if self.model not in available_models:
                logger.warning(f"Выбранная модель {self.model} не найдена в списке доступных моделей")
                # Try to find a suitable model, prioritizing faster versions
                suitable_models = [m for m in available_models if 'gemini-1.5-flash' in m.lower()]
                if not suitable_models:
                    suitable_models = [m for m in available_models if 'gemini-1.5' in m.lower()]
                if not suitable_models:
                    suitable_models = [m for m in available_models if 'gemini' in m.lower()]
                if suitable_models:
                    self.model = suitable_models[0]
                    logger.info(f"Переключение на модель: {self.model}")
                else:
                    raise ValueError("No suitable Gemini models found")
                
        except Exception as e:
            logger.error(f"Ошибка при конфигурации Gemini API: {str(e)}")
            raise
        
        logger.info(f"Initialized GeminiAIService with model: {self.model}")

    @lru_cache(maxsize=100)
    def _get_vector_search_results(self, query: str, limit: int = 5) -> List[Any]:
        """
        Получает результаты векторного поиска с кэшированием
        """
        cache_key = f"{query}:{limit}"
        current_time = time.time()
        
        # Проверяем кэш
        if cache_key in self._vector_cache:
            cache_time, cache_data = self._vector_cache[cache_key]
            if current_time - cache_time < self._vector_cache_ttl:
                return cache_data
        
        # Получаем новые результаты
        try:
            # Поиск в истории сообщений
            message_results = search(query, limit=limit)
            
            # Поиск в задачах Planfix
            task_results = search_planfix_tasks(query, limit=limit)
            
            # Объединяем и сортируем результаты
            all_results = []
            
            # Добавляем сообщения
            for hit in message_results:
                all_results.append({
                    'type': 'message',
                    'id': hit.id,
                    'score': hit.score,
                    'content': hit.payload.get('text', ''),
                    'role': hit.payload.get('role', '')
                })
            
            # Добавляем задачи
            for hit in task_results:
                task_data = hit.payload.get('data', {})
                all_results.append({
                    'type': 'task',
                    'id': hit.payload.get('task_id'),
                    'score': hit.score,
                    'title': task_data.get('title', ''),
                    'status': task_data.get('status', ''),
                    'priority': task_data.get('priority', ''),
                    'assignee': task_data.get('assignee', ''),
                    'deadline': task_data.get('deadline', '')
                })
            
            # Сортируем по релевантности
            all_results.sort(key=lambda x: x['score'], reverse=True)
            
            # Обновляем кэш
            self._vector_cache[cache_key] = (current_time, all_results)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            return []

    def _enrich_query_with_context(self, query: str) -> str:
        """
        Обогащает запрос контекстом из векторного хранилища
        """
        try:
            # Получаем релевантные результаты
            results = self._get_vector_search_results(query)
            
            if not results:
                return query
            
            # Формируем контекст
            context_parts = []
            
            # Добавляем сообщения
            messages = [r for r in results if r['type'] == 'message']
            if messages:
                context_parts.append("Релевантные сообщения из истории:")
                for msg in messages[:3]:  # Берем топ-3 сообщения
                    context_parts.append(f"[{msg['role']}]: {msg['content']}")
            
            # Добавляем задачи
            tasks = [r for r in results if r['type'] == 'task']
            if tasks:
                context_parts.append("\nРелевантные задачи:")
                for task in tasks[:3]:  # Берем топ-3 задачи
                    context_parts.append(
                        f"Задача {task['id']}:\n"
                        f"Название: {task['title']}\n"
                        f"Статус: {task['status']}\n"
                        f"Приоритет: {task['priority']}\n"
                        f"Ответственный: {task['assignee']}\n"
                        f"Срок: {task['deadline']}"
                    )
            
            # Формируем финальный контекст
            context = "\n\n".join(context_parts)
            
            return f"""
Контекст:
{context}

Запрос пользователя:
{query}
"""
            
        except Exception as e:
            logger.error(f"Error enriching query with context: {str(e)}")
            return query

    def _check_rate_limits(self, estimated_tokens: int = 100) -> None:
        """
        Check if we're within rate limits and wait if necessary
        """
        current_time = time.time()
        
        # Reset counters if a minute has passed
        if current_time - self.last_reset_time >= 60:
            self.minute_requests = 0
            self.minute_tokens = 0
            self.last_reset_time = current_time
        
        # Check if we need to wait
        if self.minute_requests >= self.requests_per_minute:
            wait_time = 60 - (current_time - self.last_reset_time)
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                self._check_rate_limits(estimated_tokens)
        
        if self.minute_tokens + estimated_tokens >= self.tokens_per_minute:
            wait_time = 60 - (current_time - self.last_reset_time)
            if wait_time > 0:
                logger.warning(f"Token limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                self._check_rate_limits(estimated_tokens)

    def _handle_rate_limit_error(self, error: Exception, attempt: int) -> None:
        """
        Handle rate limit errors with exponential backoff
        """
        if "429" in str(error):
            # Extract retry delay from error if available
            retry_after = 60  # Default to 60 seconds
            if hasattr(error, 'retry_after'):
                retry_after = error.retry_after
            
            # Calculate backoff time with jitter
            backoff_time = min(self.max_retry_delay, 
                             self.base_retry_delay * (2 ** attempt) + random.uniform(0, 1))
            
            logger.warning(f"Rate limit hit. Waiting {backoff_time:.2f} seconds before retry...")
            time.sleep(backoff_time)
        else:
            raise error

    def process_query(self, user_query: str, conversation_history: Optional[List[Dict[str, str]]] = None,
                     user=None, conversation=None) -> Dict[str, Any]:
        """Оптимизированная обработка запроса"""
        attempt = 0
        start_time = time.time()
        
        while attempt < self.max_retries:
            try:
                self._check_rate_limits(len(user_query.split()))
                
                # Инициализация модели
                try:
                    model_name = self.model.replace('models/', '')
                    model = genai.GenerativeModel(model_name)
                except Exception as e:
                    logger.error(f"Ошибка инициализации модели: {str(e)}")
                    # Пробуем альтернативные модели
                    for fallback_model in ['gemini-1.5-flash', 'gemini-1.5-pro']:
                        try:
                            model = genai.GenerativeModel(fallback_model)
                            logger.info(f"Успешно переключились на модель: {fallback_model}")
                            break
                        except Exception:
                            continue
                    else:
                        raise ValueError("No available models")
                
                # Обновляем счетчики
                self.minute_requests += 1
                self.minute_tokens += len(user_query.split())
                self.day_requests += 1
                self.last_request_time = time.time()
                
                # Подготовка чата
                chat = model.start_chat(history=[])
                
                # Отправляем системный промпт
                system_prompt = self._get_system_prompt()
                chat.send_message(system_prompt)
                
                # Добавляем контекст и отправляем запрос
                enriched_query = self._enrich_query_with_context(user_query)
                
                # Добавляем историю диалога
                if conversation_history:
                    for msg in conversation_history:
                        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                            chat.send_message(msg['content'])
                
                # Отправляем обогащенный запрос
                response = chat.send_message(enriched_query)
                
                # Проверяем качество ответа
                if not response.text or len(response.text.strip()) < 10:
                    raise ValueError("Empty or too short response from AI")
                
                # Записываем аналитику
                response_time = time.time() - start_time
                if user and conversation:
                    self.analytics.track_ai_response(
                        user=user,
                        message=None,
                        ai_model=self.model,
                        response_time=response_time
                    )
                
                return {
                    'response_type': 'ai_response',
                    'message': response.text
                }
                
            except RateLimitError as e:
                logger.warning(f"Rate limit hit: {str(e)}")
                if attempt < self.max_retries - 1:
                    sleep_time = min(e.retry_after, self.max_retry_delay)
                    time.sleep(sleep_time)
                attempt += 1
            except Exception as e:
                logger.error(f"Error processing query: {str(e)}")
                if attempt < self.max_retries - 1:
                    attempt += 1
                    time.sleep(self.base_retry_delay * (2 ** attempt))
                    continue
                return {
                    'response_type': 'error',
                    'message': f"Sorry, there was an error processing your query: {str(e)}"
                }
        
        return {
            'response_type': 'error',
            'message': "Sorry, the service is currently experiencing high load. Please try again later."
        }

    def _get_system_prompt(self) -> str:
        """Возвращает системный промпт для модели"""
        # Получаем статистику из Planfix
        stats = planfix_cache.get_stats()
        
        return f"""
Ты ассистент для работы с данными Planfix. Используй информацию из контекста, если она релевантна.

Текущая статистика системы:
- Всего задач: {stats.get('total_tasks', 0)}
- Активных задач: {stats.get('active_tasks', 0)}
- Завершенных задач: {stats.get('completed_tasks', 0)}
- Просроченных задач: {stats.get('overdue_tasks', 0)}
- Задач на этой неделе: {stats.get('tasks_due_this_week', 0)}
- Процент выполнения: {stats.get('completion_rate', 0)}%
- Всего проектов: {stats.get('total_projects', 0)}

Правила работы:
1. Анализируй задачи и давай рекомендации на основе их статусов, приоритетов и сроков
2. Помогай с поиском задач по различным параметрам
3. Давай советы по оптимизации рабочего процесса на основе данных из Planfix
4. Всегда указывай, если информация может быть неактуальной
5. Используй контекст из истории сообщений и релевантных задач для более точных ответов
6. При анализе задач учитывай:
   - Приоритеты (высокий, средний, низкий)
   - Сроки выполнения
   - Загруженность ответственных
   - Зависимости между задачами
7. При работе с проектами анализируй:
   - Общий прогресс
   - Распределение задач
   - Риски и блокеры
8. При работе с командой учитывай:
   - Текущую загруженность
   - Специализацию
   - Историю выполнения задач
9. Форматируй ответы структурированно:
   - Используй маркированные списки
   - Выделяй важную информацию
   - Добавляй рекомендации по улучшению
10. Всегда предлагай конкретные действия и следующие шаги
"""

# Singleton instance
gemini_ai = GeminiAIService() 