import logging
from datetime import date

from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.data.store import store
from api.providers import ProviderFactory
from api.services.analytics import analytics
from api.services.pricing import pricing_service

logger = logging.getLogger("api")


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        return Response({"status": "healthy", "service": "drivedial"})


class IncomingCallView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request) -> HttpResponse:
        host = request.get_host()
        call_sid = request.data.get("CallSid", "unknown")
        from_number = request.data.get("From", "unknown")

        logger.info(f"Incoming call: {call_sid} from {from_number}")

        telephony = ProviderFactory.get_telephony()
        twiml = telephony.generate_stream_response(host, "ws/media-stream/")
        return HttpResponse(twiml, content_type="text/xml")

    def get(self, request: Request) -> Response:
        return Response({
            "endpoint": "incoming-call",
            "method": "POST",
            "websocket": f"wss://{request.get_host()}/ws/media-stream/",
        })


class CallAnalyticsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request, call_id: str) -> Response:
        metrics = analytics.get_call(call_id)
        if not metrics:
            return Response({"error": "Call not found"}, status=404)

        cost = analytics.calculate_cost(call_id)
        return Response({
            "call_id": call_id,
            "started_at": metrics.started_at.isoformat(),
            "ended_at": metrics.ended_at.isoformat() if metrics.ended_at else None,
            "analytics": cost,
        })


class InventoryView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        return Response({
            "cars": store.inventory,
            "brands": store.get_all_brands(),
            "price_range": store.get_price_range(),
            "total": len(store.inventory),
        })

    def post(self, request: Request) -> Response:
        car_data = request.data
        required = ["id", "name", "brand", "price",
                    "price_display", "fuel_type", "transmission"]
        missing = [f for f in required if f not in car_data]
        if missing:
            return Response({"error": f"Missing fields: {missing}"}, status=400)

        defaults = {
            "mileage": "N/A",
            "year": date.today().year,
            "color": [],
            "features": [],
            "availability": "Contact for availability",
            "location": "Mumbai",
        }
        for key, val in defaults.items():
            car_data.setdefault(key, val)

        store.add_car(car_data)
        return Response({"status": "added", "car": car_data}, status=201)


class InventoryItemView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request, car_id: str) -> Response:
        car = store.get_car(car_id)
        if not car:
            return Response({"error": "Car not found"}, status=404)
        return Response(car)

    def patch(self, request: Request, car_id: str) -> Response:
        if not store.get_car(car_id):
            return Response({"error": "Car not found"}, status=404)

        updates = request.data
        store.update_car(car_id, updates)
        return Response({"status": "updated", "car": store.get_car(car_id)})

    def delete(self, request: Request, car_id: str) -> Response:
        if store.remove_car(car_id):
            return Response({"status": "deleted"})
        return Response({"error": "Car not found"}, status=404)


class UsageView(APIView):
    authentication_classes = []
    permission_classes = []

    async def get(self, request: Request) -> Response:
        start_date = request.query_params.get("start_date", str(date.today()))
        end_date = request.query_params.get("end_date", str(date.today()))

        usage = await pricing_service.fetch_usage(start_date, end_date)
        costs = await pricing_service.fetch_usage_costs(start_date, end_date)

        return Response({
            "start_date": start_date,
            "end_date": end_date,
            "usage": usage,
            "costs": costs,
        })


class PricingView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        model = request.query_params.get(
            "model", "gpt-4o-mini-realtime-preview-2024-12-17")
        return Response({
            "model": model,
            "pricing": pricing_service.get_pricing(model),
        })

    def post(self, request: Request) -> Response:
        model = request.data.get("model")
        pricing = request.data.get("pricing")
        if not model or not pricing:
            return Response({"error": "Model and pricing required"}, status=400)
        pricing_service.update_pricing(model, pricing)
        return Response({"status": "updated", "model": model, "pricing": pricing})
