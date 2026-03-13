from django.contrib import admin
from .models import ChatRoom, Message


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "author", "created_at")
    search_fields = ("body", "author__username", "room__name")
    list_filter = ("room", "created_at")
    ordering = ("-created_at",)
