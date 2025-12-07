from django.urls import path

from api.views import (CallAnalyticsView, CarProxyView, CarSSEView,
                       HealthCheckView, IncomingCallView, InventoryItemView,
                       InventoryView, PricingView, UsageView)

app_name = "api"

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("incoming-call/", IncomingCallView.as_view(), name="incoming-call"),
    path("analytics/<str:call_id>/",
         CallAnalyticsView.as_view(), name="call-analytics"),
    path("inventory/", InventoryView.as_view(), name="inventory"),
    path("inventory/<str:car_id>/",
         InventoryItemView.as_view(), name="inventory-item"),
    path("usage/", UsageView.as_view(), name="usage"),
    path("pricing/", PricingView.as_view(), name="pricing"),
]
