from django.urls import path

from api.views import (
    CallAnalyticsView, 
    CarProxyView, 
    CarSSEView,
    HealthCheckView, 
    IncomingCallView, 
    InventoryItemView,
    InventoryView, 
    PricingView, 
    UsageView, 
    OzonetelIncomingCallView,
    OzonetelDebugView,
    OutboundCallView,
)

app_name = "api"

urlpatterns = [
    # Health check
    path("health/", HealthCheckView.as_view(), name="health-check"),
    
    # Telephony incoming call endpoints
    path("incoming-call/", IncomingCallView.as_view(), name="incoming-call"),
    path("ozonetel-start/", OzonetelIncomingCallView.as_view(), name="ozonetel-start"),
    path("ozonetel-debug/", OzonetelDebugView.as_view(), name="ozonetel-debug"),
    
    # Outbound calls (provider-agnostic)
    path("outbound-call/", OutboundCallView.as_view(), name="outbound-call"),
    
    # Call analytics
    path("analytics/<str:call_id>/", CallAnalyticsView.as_view(), name="call-analytics"),
    
    # Inventory management
    path("inventory/", InventoryView.as_view(), name="inventory"),
    path("inventory/<str:car_id>/", InventoryItemView.as_view(), name="inventory-item"),
    
    # Usage and pricing
    path("usage/", UsageView.as_view(), name="usage"),
    path("pricing/", PricingView.as_view(), name="pricing"),
]
