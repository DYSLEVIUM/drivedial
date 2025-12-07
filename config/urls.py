from django.contrib import admin
from django.urls import include, path

from api.views import CarProxyView, CarSSEView, CarTestView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("car/<str:call_id>/", CarProxyView.as_view(), name="car-proxy"),
    path("car/<str:call_id>/events/", CarSSEView.as_view(), name="car-sse"),
    path("car/<str:call_id>/test/", CarTestView.as_view(), name="car-test"),
]
