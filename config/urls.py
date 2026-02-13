from django.contrib import admin
from django.urls import include, path

from api.views import CarProxyView, CarSSEView, CarTestView, VoBizIncomingCallView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("car/<str:call_id>/", CarProxyView.as_view(), name="car-proxy"),
    path("car/<str:call_id>/events/", CarSSEView.as_view(), name="car-sse"),
    path("car/<str:call_id>/test/", CarTestView.as_view(), name="car-test"),
    
    # VoBiz answer_url webhook (must be at root path for telephony callbacks)
    path("webhooks/vobiz/", VoBizIncomingCallView.as_view(), name="vobiz-webhook"),
    # Also support path with trailing slug for custom identifiers
    path("webhooks/vobiz/<path:extra>/", VoBizIncomingCallView.as_view(), name="vobiz-webhook-extra"),
]
