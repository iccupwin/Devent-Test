from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import CustomAuthenticationForm, CustomUserCreationForm
from .models import User

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Добро пожаловать, {username}!")
                # Перенаправление в зависимости от роли пользователя
                if user.is_admin():
                    return redirect('chat:analytics_dashboard')
                else:
                    return redirect('chat:index')
            else:
                messages.error(request, "Неверное имя пользователя или пароль.")
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Аккаунт создан для {user.username}!")
            # Перенаправление в зависимости от роли пользователя
            if user.is_admin():
                return redirect('chat:analytics_dashboard')
            else:
                return redirect('chat:index')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect('chat:login')

@login_required
def profile_view(request):
    user = request.user
    return render(request, 'auth/profile.html', {'user': user})

def access_denied(request):
    return render(request, 'auth/access_denied.html')