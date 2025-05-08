# chat/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class RoleMiddleware:
    """
    Middleware для проверки ролей пользователей и управления доступом
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Список URL-адресов, доступных только администраторам
        admin_only_urls = [
            '/admin/',
            '/analytics/',
            '/reports/',
            '/user-management/',
            '/ai-settings/',
        ]
        
        # Список URL-адресов, доступных только аутентифицированным пользователям
        auth_only_urls = [
            '/conversation/',
            '/api/agent/',
            '/planfix/',
        ]
        
        # Проверка URL для административных страниц
        if any(request.path.startswith(url) for url in admin_only_urls):
            if not request.user.is_authenticated:
                return redirect(reverse('login') + f'?next={request.path}')
            if not request.user.is_admin():
                return redirect('access_denied')
        
        # Проверка URL для аутентифицированных пользователей
        if any(request.path.startswith(url) for url in auth_only_urls):
            if not request.user.is_authenticated:
                return redirect(reverse('login') + f'?next={request.path}')
        
        # Продолжаем обработку запроса
        response = self.get_response(request)
        return response