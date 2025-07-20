from django.contrib.auth.models import User
from django.db import models

class Task(models.Model):
    """Модель задачи"""
    PRIORITY_CHOICES = [
        (1, 'Высокий'),
        (2, 'Средний'),
        (3, 'Низкий'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    due_date = models.DateTimeField(verbose_name="Срок выполнения")
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2, verbose_name="Приоритет")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title
