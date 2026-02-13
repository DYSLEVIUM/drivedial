"""
WebSocket URL routing for telephony providers.

Provides separate WebSocket endpoints for each telephony provider,
allowing multiple providers to be used simultaneously.
"""

from django.urls import re_path

from api.consumers import (
    MediaStreamConsumer,
    TwilioMediaStreamConsumer,
    OzonetelMediaStreamConsumer,
    VoBizMediaStreamConsumer,
)

websocket_urlpatterns = [
    # Default route - uses configured TELEPHONY_PROVIDER
    re_path(r"ws/media-stream/$", MediaStreamConsumer.as_asgi()),
    
    # Provider-specific routes
    re_path(r"ws/twilio-stream/$", TwilioMediaStreamConsumer.as_asgi()),
    re_path(r"ws/ozonetel-stream/$", OzonetelMediaStreamConsumer.as_asgi()),
    re_path(r"ws/vobiz-stream/$", VoBizMediaStreamConsumer.as_asgi()),
]
