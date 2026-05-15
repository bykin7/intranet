from .models import Notification


def create_notification(
    recipient,
    title,
    text="",
    url="",
    actor=None,
    notification_type="system",
):
    if not recipient:
        return None

    if not getattr(recipient, "is_authenticated", False):
        return None

    if actor and actor == recipient:
        return None

    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        title=title,
        text=text,
        url=url,
    )


def create_notifications(
    recipients,
    title,
    text="",
    url="",
    actor=None,
    notification_type="system",
):
    created_notifications = []

    for recipient in recipients:
        notification = create_notification(
            recipient=recipient,
            actor=actor,
            notification_type=notification_type,
            title=title,
            text=text,
            url=url,
        )

        if notification:
            created_notifications.append(notification)

    return created_notifications