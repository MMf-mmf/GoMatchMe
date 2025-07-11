from django.urls import path
from .consumers import ChatConsumer, NotificationsConsumer

websocket_urlpatterns = [
    path("ws/<str:conversation_name>/", ChatConsumer.as_asgi()),
    path("ws/notifications/", NotificationsConsumer.as_asgi()),
]