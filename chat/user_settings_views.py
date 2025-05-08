from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import UserSettings
from .forms import UserSettingsForm

@login_required
def user_settings_view(request):
    """Представление для настроек пользователя"""
    # Получение или создание настроек пользователя
    settings, created = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, _('Настройки успешно сохранены'))
            return redirect('chat:user_settings')
    else:
        form = UserSettingsForm(instance=settings)
    
    return render(request, 'auth/user_settings.html', {
        'form': form,
        'settings': settings,
    })