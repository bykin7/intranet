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
    stores_list,
    store_detail,
    store_create,
    store_edit,
    store_assign_employees,
)
urlpatterns = [
    path("", feed_list, name="feed_list"),
    path("posts/new/", post_create, name="post_create"),
    path("posts/<int:post_id>/", post_detail, name="post_detail"),
    path("admin-log/", admin_log_view, name="admin_log"),
    path("profile/", profile_view, name="profile"),

    path("stores/", stores_list, name="stores_list"),
    path("stores/new/", store_create, name="store_create"),
    path("stores/<int:store_id>/", store_detail, name="store_detail"),
    path("stores/<int:store_id>/edit/", store_edit, name="store_edit"),
    path(
        "stores/<int:store_id>/employees/",
        store_assign_employees,
        name="store_assign_employees"
    ),
    path("employees/", employees_list, name="employees"),
    path("employees/<int:profile_id>/edit/", employee_edit, name="employee_edit"),
    path("employees/new/", employee_create, name="employee_create"),
    path("comments/<int:comment_id>/delete/", comment_delete, name="comment_delete"),
    path("posts/<int:post_id>/edit/", post_edit, name="post_edit"),
    path("posts/<int:post_id>/delete/", post_delete, name="post_delete"),
]