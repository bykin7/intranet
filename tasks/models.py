from django.conf import settings
from django.db import models


class Task(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        IN_PROGRESS = "in_progress", "В работе"
        DONE = "done", "Выполнена"

    class Priority(models.TextChoices):
        LOW = "low", "Низкий"
        MEDIUM = "medium", "Средний"
        HIGH = "high", "Высокий"

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tasks",
        verbose_name="Постановщик",
    )

    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assigned_tasks",
        verbose_name="Исполнитель",
    )

    title = models.CharField(
        max_length=200,
        verbose_name="Название задачи",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Описание",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name="Статус",
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name="Приоритет",
    )

    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Срок выполнения",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    def __str__(self) -> str:
        return self.title


class TaskImage(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Задача",
    )

    image = models.ImageField(
        upload_to="tasks/gallery/",
        verbose_name="Фотография",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата загрузки",
    )

    class Meta:
        ordering = ["uploaded_at"]
        verbose_name = "Фотография задачи"
        verbose_name_plural = "Фотографии задачи"

    def __str__(self) -> str:
        return f"Фото к задаче {self.task_id}"