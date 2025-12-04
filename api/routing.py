from django.urls import re_path

from api.consumers import MediaStreamConsumer

websocket_urlpatterns = [
    re_path(r"ws/media-stream/$", MediaStreamConsumer.as_asgi()),
]
