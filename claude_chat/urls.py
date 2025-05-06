from django.urls import path, include

urlpatterns = [
    # Включаем все URL-маршруты из приложения chat
    path('', include('chat.urls')),
]