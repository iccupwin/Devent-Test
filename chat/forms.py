from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import User
from .models import UserSettings

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label=_("Имя пользователя"),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя пользователя'}),
    )
    password = forms.CharField(
        label=_("Пароль"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
    )

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите email'}),
    )
    
    username = forms.CharField(
        label=_("Имя пользователя"),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя пользователя'}),
    )
    
    password1 = forms.CharField(
        label=_("Пароль"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
    )
    
    password2 = forms.CharField(
        label=_("Подтверждение пароля"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'}),
    )
    
    role = forms.ChoiceField(
        label=_("Роль"),
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='user',
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

    class UserSettingsForm(forms.ModelForm):
   
     class Meta:
        model = UserSettings
        fields = ['theme', 'language', 'enable_notifications', 'show_completed_tasks', 'default_page_size']
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'enable_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_completed_tasks': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_page_size': forms.Select(attrs={'class': 'form-control'}),
        }