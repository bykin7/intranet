from .models import Notification


def notifications_context(request):
    if not request.user.is_authenticated:
        return {
            "unread_notifications_count": 0,
            "last_notifications": [],
        }

    unread_notifications_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    last_notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("actor")
        .order_by("-created_at")[:5]
    )

    return {
        "unread_notifications_count": unread_notifications_count,
        "last_notifications": last_notifications,
    }