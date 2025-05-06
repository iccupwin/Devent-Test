import time
import requests
import json
import logging
from django.conf import settings

# Настройка логирования
logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        self.api_key = settings.CLAUDE_API_KEY
        self.api_url = settings.CLAUDE_API_URL
        self.headers = {
            'anthropic-version': '2023-06-01',
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        self.max_retries = 3
        self.retry_delay = 5
        
        logger.info(f"Инициализация ClaudeService с API URL: {self.api_url}")
        logger.info(f"API ключ задан: {bool(self.api_key)}")
    
    def send_message(self, messages, model="claude-3-opus-20240229"):
        """
        Отправляет сообщение в Claude API и получает ответ с повторными попытками при ошибке 429
        
        Args:
            messages: список сообщений в формате [{"role": "user", "content": "Привет"}, ...]
            model: модель Claude для использования
        
        Returns:
            текст ответа от Claude
        """
        retries = 0
        
        while retries <= self.max_retries:
            try:
                # Логируем отправку запроса
                logger.info(f"Отправляем сообщение в Claude API, модель: {model}")
                logger.info(f"Количество сообщений: {len(messages)}")
                logger.info(f"Попытка #{retries + 1}")
                
                # Преобразуем сообщения в строковый контент, если необходимо
                processed_messages = []
                for msg in messages:
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    
                    # Если контент - строка, просто используем как есть
                    # Иначе - преобразуем в строку
                    if not isinstance(content, str):
                        content = str(content)
                    
                    processed_messages.append({"role": role, "content": content})
                
                # Формируем запрос к API
                payload = {
                    "model": model,
                    "messages": processed_messages,
                    "max_tokens": 4000
                }
                
                # Для отладки - логируем тело запроса в урезанном виде
                debug_payload = payload.copy()
                if len(processed_messages) > 0:
                    first_message = processed_messages[0].copy()
                    content = first_message.get('content', '')
                    if len(content) > 100:
                        first_message['content'] = content[:100] + '...'
                    debug_payload['messages'] = [first_message, f"... еще {len(processed_messages)-1} сообщений"]
                
                logger.debug(f"Отправляем запрос: {debug_payload}")
                
                # Отправляем запрос
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload
                )
                
                # Логируем статус ответа
                logger.info(f"Статус ответа от API: {response.status_code}")
                
                # Проверяем ответ
                if response.status_code == 401:
                    error_text = response.text
                    logger.error(f"Ошибка аутентификации (401): {error_text}")
                    return f"Произошла ошибка аутентификации. Пожалуйста, проверьте API-ключ Claude. Ошибка: {error_text[:100]}..."
                
                elif response.status_code == 429:
                    retries += 1
                    if retries <= self.max_retries:
                        wait_time = self.retry_delay * (2 ** (retries - 1))  # Экспоненциальная задержка
                        logger.warning(f"Ошибка лимита запросов (429). Ожидание {wait_time} секунд перед повторной попыткой...")
                        time.sleep(wait_time)
                        continue
                    else:
                        error_text = response.text
                        logger.error(f"Превышено количество повторных попыток. Последняя ошибка: {error_text[:200]}")
                        return f"Превышен лимит запросов к Claude API. Пожалуйста, попробуйте позже. Ошибка: {error_text[:100]}..."
                
                elif response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Ошибка API: {response.status_code}, текст: {error_text[:200]}")
                    return f"Произошла ошибка при обращении к Claude API. Код ошибки: {response.status_code}, Ответ: {error_text[:100]}..."
                
                # Парсим ответ
                try:
                    response_data = response.json()
                    logger.info("Успешно получен и распарсен ответ от API")
                    
                    # Извлекаем текст
                    if 'content' in response_data and len(response_data['content']) > 0:
                        result = response_data['content'][0].get('text', '')
                        logger.info(f"Извлечен текст ответа (первые 50 символов): {result[:50]}...")
                        return result
                    else:
                        # Если массив content пустой, формируем специальное сообщение
                        logger.warning(f"Ответ API содержит пустой массив content: {response_data}")
                        if 'stop_reason' in response_data:
                            stop_reason = response_data.get('stop_reason', 'unknown')
                            logger.info(f"Причина остановки: {stop_reason}")
                            
                            if stop_reason == 'end_turn':
                                # Формируем заменяющий ответ
                                return "Я обдумал задачу, но не смог сформулировать подходящий ответ. Пожалуйста, опишите вашу задачу более подробно, чтобы я мог помочь."
                            else:
                                return f"Ответ от API получен, но не содержит текста. Причина: {stop_reason}"
                        return "Ответ от API получен, но в нем отсутствует ожидаемое содержимое."
                    
                except ValueError:
                    logger.error("Не удалось распарсить JSON из ответа API")
                    return f"Ошибка при обработке ответа от Claude API: не удалось распарсить JSON."
            
            except requests.exceptions.RequestException as e:
                # Обработка ошибок API
                logger.error(f"Ошибка запроса: {str(e)}", exc_info=True)
                return f"Ошибка соединения с Claude API: {str(e)}"
            
            except Exception as e:
                # Обработка других ошибок
                logger.error(f"Непредвиденная ошибка: {str(e)}", exc_info=True)
                return f"Произошла непредвиденная ошибка: {str(e)}"
            
            # Если дошли до этой точки, значит запрос успешно выполнен
            break