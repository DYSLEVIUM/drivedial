import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from django.core.asgi import get_asgi_application
from django.conf import settings

from api.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_asgi_app = get_asgi_application()


# In development/debug mode, allow all WebSocket origins
# This is needed for Ozonetel and other telephony providers to connect
if getattr(settings, 'DEBUG', True):
    websocket_application = URLRouter(websocket_urlpatterns)
else:
    websocket_application = AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": websocket_application,
})
