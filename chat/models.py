# chat/models.py - расширение модели User

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Расширенная модель пользователя с ролями и интеграцией Planfix
    """
    ROLE_CHOICES = (
        ('user', _('Пользователь')),
        ('admin', _('Администратор')),
    )
    
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    password = models.CharField(_('password'), max_length=128)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    planfix_user_id = models.CharField(max_length=100, blank=True, null=True)
    planfix_api_token = models.CharField(max_length=255, blank=True, null=True)
    last_active = models.DateTimeField(auto_now=True)
    preferred_ai_model = models.CharField(max_length=50, default='claude')

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def is_admin(self):
        return self.role == 'admin'

    def __str__(self):
        return self.username

class AIModel(models.Model):
    """
    Модель для хранения информации о доступных ИИ-моделях
    """
    MODEL_TYPES = (
        ('claude', 'Claude AI'),
        ('gpt', 'ChatGPT'),
        ('deepseek', 'DeepSeek'),
    )
    
    name = models.CharField(max_length=50)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    version = models.CharField(max_length=50)
    api_base_url = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('ИИ-модель')
        verbose_name_plural = _('ИИ-модели')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.version})"

class Conversation(models.Model):
    """
    Расширенная модель беседы с привязкой к проектам и задачам Planfix
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255)
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, related_name='conversations')
    planfix_task_id = models.CharField(max_length=100, blank=True, null=True)
    planfix_project_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    summary = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Беседа')
        verbose_name_plural = _('Беседы')
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['planfix_task_id']),
            models.Index(fields=['planfix_project_id']),
        ]
    
    def get_related_task_info(self):
        """Получить информацию о связанной задаче из Planfix"""
        if self.planfix_task_id:
            from chat.planfix_service import get_task_by_id
            return get_task_by_id(self.planfix_task_id)
        return None
    
    def __str__(self):
        return self.title

class Message(models.Model):
    """
    Расширенная модель сообщений с метаданными и поддержкой различных ИИ
    """
    ROLE_CHOICES = (
        ('user', _('Пользователь')),
        ('assistant', _('Ассистент')),
        ('system', _('Система')),
    )
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    tokens = models.IntegerField(default=0)  # Количество токенов для расчета стоимости
    ai_model_used = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    metadata = models.JSONField(default=dict, blank=True)  # Для дополнительных данных от ИИ
    
    class Meta:
        ordering = ['created_at']
        verbose_name = _('Сообщение')
        verbose_name_plural = _('Сообщения')
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.role} - {self.content[:50]}..."
    

class PlanfixCache(models.Model):
    """
    Модель для отслеживания и управления кэшированием данных Planfix
    """
    cache_name = models.CharField(max_length=100, unique=True)
    last_update = models.DateTimeField(auto_now=True)
    is_valid = models.BooleanField(default=True)
    entries_count = models.IntegerField(default=0)
    update_duration = models.FloatField(default=0.0)  # Время обновления в секундах
    
    class Meta:
        verbose_name = _('Кэш Planfix')
        verbose_name_plural = _('Кэши Planfix')
    
    def __str__(self):
        return f"{self.cache_name} ({self.entries_count} entries)"

class PlanfixTask(models.Model):
    """
    Модель для хранения ключевой информации о задачах Planfix для аналитики
    """
    task_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=100)
    project_id = models.CharField(max_length=100, null=True, blank=True)
    project_name = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    assignee = models.CharField(max_length=255, null=True, blank=True)
    assigner = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    is_overdue = models.BooleanField(default=False)
    last_sync = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Задача Planfix')
        verbose_name_plural = _('Задачи Planfix')
        indexes = [
            models.Index(fields=['task_id']),
            models.Index(fields=['project_id']),
            models.Index(fields=['status']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['is_overdue']),
        ]
    
    def __str__(self):
        return f"{self.name} (ID: {self.task_id})"
        
class AnalyticsEvent(models.Model):
    """
    Модель для отслеживания событий в системе для аналитики
    """
    EVENT_TYPES = (
        ('conversation_start', _('Начало беседы')),
        ('conversation_end', _('Завершение беседы')),
        ('message_sent', _('Отправлено сообщение')),
        ('ai_response', _('Ответ ИИ')),
        ('task_integration', _('Интеграция с задачей')),
        ('cache_refresh', _('Обновление кэша')),
        ('login', _('Вход в систему')),
        ('logout', _('Выход из системы')),
        ('error', _('Ошибка')),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    planfix_task_id = models.CharField(max_length=100, null=True, blank=True)
    planfix_project_id = models.CharField(max_length=100, null=True, blank=True)
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = _('Событие аналитики')
        verbose_name_plural = _('События аналитики')
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'event_type']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.timestamp}"

class UserMetrics(models.Model):
    """
    Модель для хранения агрегированных метрик пользователей
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metrics')
    day = models.DateField()
    conversations_count = models.IntegerField(default=0)
    messages_sent = models.IntegerField(default=0)
    tokens_used = models.IntegerField(default=0)
    tasks_integrated = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    
    class Meta:
        verbose_name = _('Метрика пользователя')
        verbose_name_plural = _('Метрики пользователей')
        unique_together = ['user', 'day']
        indexes = [
            models.Index(fields=['user', 'day']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.day}"

class AIModelMetrics(models.Model):
    """
    Модель для хранения метрик использования ИИ-моделей
    """
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='metrics')
    day = models.DateField()
    requests_count = models.IntegerField(default=0)
    tokens_used = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    error_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = _('Метрика ИИ-модели')
        verbose_name_plural = _('Метрики ИИ-моделей')
        unique_together = ['ai_model', 'day']
        indexes = [
            models.Index(fields=['ai_model', 'day']),
        ]
    
    def __str__(self):
        return f"{self.ai_model.name} - {self.day}"
    

class ConversationTag(models.Model):
   
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#0071e3')  # HEX-код цвета для отображения в UI
    
    class Meta:
        verbose_name = _('Тег беседы')
        verbose_name_plural = _('Теги бесед')
    
    def __str__(self):
        return self.name

class ConversationAnalytics(models.Model):
    """
    Расширенная аналитика по беседам для более детального анализа
    """
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE, related_name='analytics')
    total_messages = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)  # среднее время ответа в секундах
    user_sentiment = models.FloatField(null=True, blank=True)  # оценка тональности беседы (-1.0 - 1.0)
    satisfaction_rating = models.IntegerField(null=True, blank=True)  # оценка удовлетворенности пользователя (1-5)
    tags = models.ManyToManyField(ConversationTag, blank=True, related_name='conversations')
    
    first_message_time = models.DateTimeField(null=True, blank=True)
    last_message_time = models.DateTimeField(null=True, blank=True)
    total_duration = models.DurationField(null=True, blank=True)  # общая длительность беседы
    
    # Связь с Planfix
    related_planfix_tasks = models.IntegerField(default=0)  # количество связанных задач
    
    class Meta:
        verbose_name = _('Аналитика беседы')
        verbose_name_plural = _('Аналитика бесед')
    
    def __str__(self):
        return f"Аналитика для беседы {self.conversation.title}"
    
    def update_analytics(self):
        """Обновление аналитики на основе текущих данных беседы"""
        messages = self.conversation.messages.all()
        self.total_messages = messages.count()
        self.total_tokens = messages.aggregate(Sum('tokens'))['tokens__sum'] or 0
        
        if messages.exists():
            self.first_message_time = messages.order_by('created_at').first().created_at
            self.last_message_time = messages.order_by('-created_at').first().created_at
            if self.first_message_time and self.last_message_time:
                self.total_duration = self.last_message_time - self.first_message_time
        
        # Посчитать связанные задачи Planfix
        if self.conversation.planfix_task_id:
            self.related_planfix_tasks = 1
        
        self.save()

class MessageFeedback(models.Model):
    """
    Модель для сохранения обратной связи по сообщениям от ИИ
    """
    FEEDBACK_CHOICES = (
        ('helpful', _('Полезно')),
        ('not_helpful', _('Не полезно')),
        ('partially_helpful', _('Частично полезно')),
    )
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_feedback')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Обратная связь по сообщению')
        verbose_name_plural = _('Обратная связь по сообщениям')
        unique_together = ('message', 'user')  # Один пользователь может оставить только один отзыв на сообщение
    
    def __str__(self):
        return f"{self.user.username} - {self.feedback_type}"