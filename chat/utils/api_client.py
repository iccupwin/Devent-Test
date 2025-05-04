import requests
import json
from django.conf import settings

class APIClient:
    """
    Базовый класс для работы с API.
    Реализует общую логику для разных API сервисов.
    """
    def __init__(self, base_url=None, api_key=None, headers=None):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = headers or {}
        
    def make_request(self, method, endpoint, params=None, data=None, json_data=None):
        """
        Выполняет HTTP запрос к API.
        
        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: конечная точка API
            params: параметры запроса (для GET)
            data: данные запроса (для POST, PUT)
            json_data: JSON данные запроса (для POST, PUT)
        
        Returns:
            ответ от API
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=self.headers
            )
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
        
        except requests.exceptions.RequestException as e:
            # Логирование ошибки
            print(f"API request error: {str(e)}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    print(f"API error response: {error_data}")
                except:
                    print(f"API error status: {e.response.status_code}")
            
            # Пробрасываем ошибку дальше
            raise