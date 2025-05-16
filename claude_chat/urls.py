from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    # Включаем все URL-маршруты из приложения chat
    path('', include('chat.urls')),
]