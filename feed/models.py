from django.conf import settings
from django.db import models


class Post(models.Model):
    class Audience(models.TextChoices):
        ALL = "all", "Все"
        DEPARTMENT = "department", "Мой отдел"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()

    is_pinned = models.BooleanField(default=False)
    audience = models.CharField(
        max_length=20,
        choices=Audience.choices,
        default=Audience.ALL,
        verbose_name="Кому показывать",
)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Комментарий от {self.author} к {self.post}"
from django.contrib.auth.models import User


class Profile(models.Model):

    POSITION_CHOICES = [
        ("admin", "Администратор"),
        ("supervisor", "Супервайзер (СВ)"),
        ("security", "Служба безопасности (СБ)"),
        ("cashier", "Кассир"),
        ("loss_prevention", "Специалист по предотвращению потерь"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    full_name = models.CharField("ФИО", max_length=255, blank=True)
    position = models.CharField(
        "Должность",
        max_length=50,
        choices=POSITION_CHOICES,
        blank=True
    )
    department = models.CharField("Отдел", max_length=255, blank=True)
    phone = models.CharField("Телефон", max_length=50, blank=True)

    def __str__(self):
        return self.user.username
