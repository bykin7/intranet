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

    image = models.ImageField(
        "Фотография",
        upload_to="feed/posts/",
        blank=True,
        null=True
    )

    stores = models.ManyToManyField(
        "Store",
        verbose_name="Магазины",
        blank=True,
        related_name="posts"
    )

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

class Store(models.Model):
    name = models.CharField("Название магазина", max_length=150)
    address = models.CharField("Адрес", max_length=255, blank=True)
    phone = models.CharField("Рабочий телефон", max_length=30, blank=True)
    is_active = models.BooleanField("Активен", default=True)

    worker_user = models.OneToOneField(
        User,
        verbose_name="Рабочий аккаунт магазина",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="store_worker_account"
    )

    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return self.name

class Profile(models.Model):

    POSITION_CHOICES = [
        ("admin", "Администратор"),
        ("supervisor", "Супервайзер (СВ)"),
        ("security", "Служба безопасности (СБ)"),
        ("cashier", "Кассир"),
        ("loss_prevention", "Специалист по предотвращению потерь"),
        ("sysadmin", "Системный администратор"),
        ("worker", "Рабочий"),
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

    store = models.ForeignKey(
    Store,
    verbose_name="Основной магазин",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="employees"
    )

    managed_stores = models.ManyToManyField(
    Store,
    verbose_name="Доступные магазины",
    blank=True,
    related_name="managers"
    )

class PostImage(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Новость"
    )
    image = models.ImageField(
        "Фотография",
        upload_to="feed/posts/gallery/"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Фотография новости"
        verbose_name_plural = "Фотографии новости"

    def __str__(self):
        return f"Фото для новости {self.post_id}"