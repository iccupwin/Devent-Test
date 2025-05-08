from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from django.urls import reverse
from functools import wraps

def admin_required(view_func):
    """Декоратор для проверки, является ли пользователь администратором"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_admin():
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('chat:access_denied'))
    return wrapper

def login_required_with_redirect(view_func):
    """Декоратор для проверки, авторизован ли пользователь"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('chat:login') + f'?next={request.path}')
    return wrapper