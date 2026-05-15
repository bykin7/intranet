from django.urls import path

from .views import (
    notification_open,
    notifications_list,
    notifications_mark_all_read,
)

urlpatterns = [
    path("", notifications_list, name="notifications_list"),
    path("<int:notification_id>/open/", notification_open, name="notification_open"),
    path("read-all/", notifications_mark_all_read, name="notifications_mark_all_read"),
]