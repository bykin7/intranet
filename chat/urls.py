from django.urls import path
from .views import (
    chat_home,
    private_chat_create,
    private_chat_detail,
    private_message_delete,
    group_chat_create,
    group_chat_detail,
    group_chat_add_member,
    group_chat_remove_member,
    group_chat_delete,
    group_message_delete,
)

urlpatterns = [
    path("", chat_home, name="chat_home"),

    path("private/new/", private_chat_create, name="private_chat_create"),
    path("private/<int:chat_id>/", private_chat_detail, name="private_chat_detail"),
    path("private/message/<int:message_id>/delete/", private_message_delete, name="private_message_delete"),

    path("group/new/", group_chat_create, name="group_chat_create"),
    path("group/<int:group_id>/", group_chat_detail, name="group_chat_detail"),
    path("group/<int:group_id>/add-member/", group_chat_add_member, name="group_chat_add_member"),
    path("group/<int:group_id>/remove-member/<int:member_id>/", group_chat_remove_member, name="group_chat_remove_member"),
    path("group/<int:group_id>/delete/", group_chat_delete, name="group_chat_delete"),
    path("group/message/<int:message_id>/delete/", group_message_delete, name="group_message_delete"),
]