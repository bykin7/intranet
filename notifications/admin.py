from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "recipient",
        "actor",
        "notification_type",
        "is_read",
        "created_at",
    )
    list_filter = (
        "notification_type",
        "is_read",
        "created_at",
    )
    search_fields = (
        "title",
        "text",
        "recipient__username",
        "recipient__profile__full_name",
        "actor__username",
        "actor__profile__full_name",
    )
    readonly_fields = ("created_at",)