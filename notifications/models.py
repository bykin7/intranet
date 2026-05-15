from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ("private_message", "Личное сообщение"),
        ("group_message", "Групповое сообщение"),
        ("task", "Задача"),
        ("post", "Новость"),
        ("comment", "Комментарий"),
        ("group", "Группа"),
        ("system", "Системное уведомление"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Получатель",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_notifications",
        verbose_name="Автор действия",
    )

    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        default="system",
        verbose_name="Тип уведомления",
    )

    title = models.CharField(
        max_length=180,
        verbose_name="Заголовок",
    )

    text = models.TextField(
        blank=True,
        verbose_name="Текст",
    )

    url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Ссылка",
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="Прочитано",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.recipient.username}: {self.title}"