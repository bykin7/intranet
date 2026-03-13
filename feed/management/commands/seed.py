from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from feed.models import Post
from tasks.models import Task
from chat.models import ChatRoom, Message


class Command(BaseCommand):
    help = "Заполняет базу тестовыми данными (пользователи, посты, задачи, чаты)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("▶ Запуск seed-команды"))

        admin = self.get_or_create_user(
            username="admin",
            password="admin123",
            is_staff=True,
            is_superuser=True,
        )

        user1 = self.get_or_create_user("ivan", "ivan123")
        user2 = self.get_or_create_user("olga", "olga123")

        users = [admin, user1, user2]

        self.create_posts(admin)
        self.create_tasks(admin, users)
        self.create_chats_and_messages(users)

        self.stdout.write(self.style.SUCCESS("✅ Seed-команда выполнена успешно"))

    # ---------- helpers ----------

    def get_or_create_user(self, username, password, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
            self.stdout.write(f"👤 Создан пользователь: {username}")
        else:
            self.stdout.write(f"👤 Пользователь уже есть: {username}")
        return user

    def create_posts(self, author):
        titles = [
            "Добро пожаловать в HappyTogether",
            "График работы на неделю",
            "Важная информация для сотрудников",
        ]

        for title in titles:
            Post.objects.get_or_create(
                title=title,
                defaults={
                    "body": "Это тестовый пост, созданный seed-командой.",
                    "author": author,
                    "created_at": timezone.now(),
                },
            )

        self.stdout.write("📰 Посты готовы")

    def create_tasks(self, creator, users):
        titles = [
            "Проверить склад",
            "Обновить ценники",
            "Подготовить отчёт",
        ]

        for title in titles:
            Task.objects.get_or_create(
                title=title,
                defaults={
                    "description": "Тестовая задача",
                    "created_by": creator,
                    "assignee": random.choice(users),
                    "due_date": timezone.now().date() + timedelta(days=3),
                },
            )

        self.stdout.write("✅ Задачи готовы")

    def create_chats_and_messages(self, users):
        room_names = ["Общий чат", "Склад", "Касса"]

        for name in room_names:
            room, _ = ChatRoom.objects.get_or_create(name=name)

            if not room.messages.exists():
                for user in users:
                    Message.objects.create(
                        room=room,
                        author=user,
                        body=f"Привет! Это сообщение от {user.username}",
                    )

        self.stdout.write("💬 Чаты и сообщения готовы")
