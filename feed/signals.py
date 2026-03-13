import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

logger = logging.getLogger("happytogether")


@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    ip = request.META.get("REMOTE_ADDR")
    logger.info(f"LOGIN user={user.username} ip={ip}")


@receiver(user_logged_out)
def log_user_logged_out(sender, request, user, **kwargs):
    ip = request.META.get("REMOTE_ADDR") if request else None
    name = getattr(user, "username", None)
    logger.info(f"LOGOUT user={name} ip={ip}")


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    ip = request.META.get("REMOTE_ADDR") if request else None
    username = credentials.get("username")
    logger.info(f"LOGIN_FAILED username={username} ip={ip}")
