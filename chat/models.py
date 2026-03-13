from django.conf import settings
from django.db import models


class ChatRoom(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self) -> str:
        return self.name


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.author}: {self.body[:30]}"

class Group(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_groups"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user.username} -> {self.group.name}"


class PrivateChat(models.Model):
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="private_chats_as_user1"
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="private_chats_as_user2"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user1", "user2"],
                name="unique_private_chat_pair"
            )
        ]

    def __str__(self):
        return f"{self.user1.username} ↔ {self.user2.username}"


class PrivateMessage(models.Model):
    chat = models.ForeignKey(
        PrivateChat,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.username}: {self.body[:30]}"


class GroupChat(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_group_chats"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class GroupChatMember(models.Model):
    group = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_chat_memberships"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user.username} -> {self.group.name}"


class GroupChatMessage(models.Model):
    group = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.username} @ {self.group.name}: {self.body[:30]}"


class PrivateChatRead(models.Model):
    chat = models.ForeignKey(
        PrivateChat,
        on_delete=models.CASCADE,
        related_name="read_states"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    last_read_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("chat", "user")

    def __str__(self):
        return f"{self.user.username} read private chat {self.chat.id}"


class GroupChatRead(models.Model):
    group = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        related_name="read_states"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    last_read_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("group", "user")

    def __str__(self):
        return f"{self.user.username} read group {self.group.id}"