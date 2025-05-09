# chat/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

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
            '/planfix/',
            '/profile/',
        ]
        
        # Список URL-адресов, доступных всем пользователям
        public_urls = [
            '/login/',
            '/register/',
            '/logout/',
            '/access-denied/',
            '/static/',
            '/api/agent/',  # Разрешаем доступ к API для всех
            '/agent/',      # Разрешаем доступ к агенту для всех
        ]
        
        # Проверка URL для административных страниц
        if any(request.path.startswith(url) for url in admin_only_urls):
            if not request.user.is_authenticated:
                messages.error(request, "Для доступа к этой странице необходимо войти в систему.")
                return redirect(reverse('chat:login') + f'?next={request.path}')
            if not request.user.is_admin():
                messages.error(request, "У вас нет прав доступа к этой странице.")
                return redirect('chat:access_denied')
        
        # Проверка URL для аутентифицированных пользователей
        if any(request.path.startswith(url) for url in auth_only_urls) and not any(request.path.startswith(url) for url in public_urls):
            if not request.user.is_authenticated:
                messages.error(request, "Для доступа к этой странице необходимо войти в систему.")
                return redirect(reverse('chat:login') + f'?next={request.path}')
        
        # Продолжаем обработку запроса
        response = self.get_response(request)
        return response