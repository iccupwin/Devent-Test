from django.db import models

class User(models.Model):
    """
    Простая модель пользователя
    """
    username = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username

class Conversation(models.Model):
    """
    Модель для представления беседы с Claude
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title} ({self.user.username})"

class Message(models.Model):
    """
    Модель для представления сообщения в беседе
    """
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('assistant', 'Ассистент')
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role} - {self.content[:50]}..."