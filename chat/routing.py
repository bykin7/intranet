from django.urls import re_path
from .consumers import PrivateChatConsumer, GroupChatConsumer

websocket_urlpatterns = [
    re_path(r"^ws/chat/private/(?P<chat_id>\d+)/$", PrivateChatConsumer.as_asgi()),
    re_path(r"^ws/chat/group/(?P<group_id>\d+)/$", GroupChatConsumer.as_asgi()),
]