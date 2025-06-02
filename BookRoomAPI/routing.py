from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/test/", consumers.TestConsumer.as_asgi()),
    path('ws/chat/<int:relato_id>/', consumers.ChatConsumer.as_asgi()),
]
