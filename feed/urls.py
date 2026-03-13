from django.urls import path
from .views import (
    feed_list,
    post_create,
    post_detail,
    post_edit,
    post_delete,
    comment_delete,
    admin_log_view,
    profile_view,
    employees_list,
    employee_edit,
    employee_create,
)
urlpatterns = [
    path("", feed_list, name="feed_list"),
    path("posts/new/", post_create, name="post_create"),
    path("posts/<int:post_id>/", post_detail, name="post_detail"),
    path("admin-log/", admin_log_view, name="admin_log"),
    path("profile/", profile_view, name="profile"),
    path("employees/", employees_list, name="employees"),
    path("employees/<int:profile_id>/edit/", employee_edit, name="employee_edit"),
    path("employees/new/", employee_create, name="employee_create"),
    path("comments/<int:comment_id>/delete/", comment_delete, name="comment_delete"),
    path("posts/<int:post_id>/edit/", post_edit, name="post_edit"),
    path("posts/<int:post_id>/delete/", post_delete, name="post_delete"),
]