from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Включаем все URL-маршруты из приложения chat
    path('', include('chat.urls')),
]