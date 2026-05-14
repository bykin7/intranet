import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from .models import (
    GroupChat,
    GroupChatMember,
    GroupChatMessage,
    PrivateChat,
    PrivateMessage,
)


def safe_full_name(user):
    try:
        if hasattr(user, "profile") and user.profile.full_name:
            return user.profile.full_name
    except Exception:
        pass
    return user.username


class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.room_group_name = f"private_chat_{self.chat_id}"

        user = self.scope["user"]
        has_access = await self.user_has_access(user, self.chat_id)

        if not user.is_authenticated:
            await self.close()
            return

        if not has_access:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            user = self.scope["user"]

            event_type = data.get("type", "message")

            if event_type == "typing":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "private_typing_event",
                        "author_username": user.username,
                        "author_display": safe_full_name(user),
                        "is_typing": bool(data.get("is_typing", False)),
                    }
                )
                return

            body = data.get("body", "").strip()
            if not body:
                return

            message = await self.create_private_message(self.chat_id, user, body)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "private_chat_message",
                    "message_id": message["id"],
                    "author_username": message["author_username"],
                    "author_display": message["author_display"],
                    "body": message["body"],
                    "created_at": message["created_at"],
                    "time_only": message["time_only"],
                }
            )
        except Exception as e:
            print("PRIVATE WS RECEIVE ERROR:", repr(e))

    async def private_chat_message(self, event):
        user = self.scope["user"]
        is_own = event["author_username"] == user.username

        await self.send(text_data=json.dumps({
            "event": "message",
            "message_id": event["message_id"],
            "author": event["author_display"],
            "author_username": event["author_username"],
            "body": event["body"],
            "created_at": event["created_at"],
            "time_only": event["time_only"],
            "is_own": is_own,
        }))

    async def private_typing_event(self, event):
        user = self.scope["user"]

        await self.send(text_data=json.dumps({
            "event": "typing",
            "author": event["author_display"],
            "author_username": event["author_username"],
            "is_typing": event["is_typing"],
            "is_own": event["author_username"] == user.username,
        }))

    @database_sync_to_async
    def user_has_access(self, user, chat_id):
        try:
            chat = PrivateChat.objects.get(id=chat_id)
            return user == chat.user1 or user == chat.user2
        except PrivateChat.DoesNotExist:
            return False

    @database_sync_to_async
    def create_private_message(self, chat_id, user, body):
        chat = PrivateChat.objects.get(id=chat_id)
        message = PrivateMessage.objects.create(
            chat=chat,
            author=user,
            body=body,
        )

        local_dt = timezone.localtime(message.created_at)

        return {
            "id": message.id,
            "author_username": message.author.username,
            "author_display": safe_full_name(message.author),
            "body": message.body,
            "created_at": local_dt.strftime("%d.%m.%Y %H:%M"),
            "time_only": local_dt.strftime("%H:%M"),
        }


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]
        self.room_group_name = f"group_chat_{self.group_id}"

        user = self.scope["user"]
        is_member = await self.user_is_member(user, self.group_id)

        if not user.is_authenticated:
            await self.close()
            return

        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            user = self.scope["user"]

            event_type = data.get("type", "message")

            if event_type == "typing":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "group_typing_event",
                        "author_username": user.username,
                        "author_display": safe_full_name(user),
                        "is_typing": bool(data.get("is_typing", False)),
                    }
                )
                return

            body = data.get("body", "").strip()
            if not body:
                return

            message = await self.create_group_message(self.group_id, user, body)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "group_chat_message",
                    "message_id": message["id"],
                    "author_username": message["author_username"],
                    "author_display": message["author_display"],
                    "body": message["body"],
                    "created_at": message["created_at"],
                    "time_only": message["time_only"],
                    "is_owner_author": message["is_owner_author"],
                }
            )
        except Exception as e:
            print("GROUP WS RECEIVE ERROR:", repr(e))

    async def group_chat_message(self, event):
        user = self.scope["user"]
        is_own = event["author_username"] == user.username

        await self.send(text_data=json.dumps({
            "event": "message",
            "message_id": event["message_id"],
            "author": event["author_display"],
            "author_username": event["author_username"],
            "body": event["body"],
            "created_at": event["created_at"],
            "time_only": event["time_only"],
            "is_own": is_own,
            "is_owner_author": event["is_owner_author"],
        }))

    async def group_typing_event(self, event):
        user = self.scope["user"]

        await self.send(text_data=json.dumps({
            "event": "typing",
            "author": event["author_display"],
            "author_username": event["author_username"],
            "is_typing": event["is_typing"],
            "is_own": event["author_username"] == user.username,
        }))

    @database_sync_to_async
    def user_is_member(self, user, group_id):
        return GroupChatMember.objects.filter(
            group_id=group_id,
            user=user
        ).exists()

    @database_sync_to_async
    def create_group_message(self, group_id, user, body):
        group = GroupChat.objects.get(id=group_id)
        message = GroupChatMessage.objects.create(
            group=group,
            author=user,
            body=body,
        )

        local_dt = timezone.localtime(message.created_at)

        return {
            "id": message.id,
            "author_username": message.author.username,
            "author_display": safe_full_name(message.author),
            "body": message.body,
            "created_at": local_dt.strftime("%d.%m.%Y %H:%M"),
            "time_only": local_dt.strftime("%H:%M"),
            "is_owner_author": message.author == group.owner,
        }