import asyncio
import json
import logging
from datetime import date

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.data.store import store
from api.providers import ProviderFactory
from api.services.analytics import analytics
from api.services.pricing import pricing_service
from api.services.sse_manager import sse_manager

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
        required = ["slug", "name", "model_name", "variant_name", "brand_name", 
                    "market_price", "acko_price", "savings", "fuel_type", "transmission"]
        missing = [f for f in required if f not in car_data]
        if missing:
            return Response({"error": f"Missing fields: {missing}"}, status=400)

        defaults = {
            "mileage": "N/A",
            "color": [],
            "features": [],
            "waiting_period": "Contact for availability",
            "is_express_delivery": False,
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
        model = request.query_params.get("model", settings.OPENAI_MODEL)
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


class CarProxyView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request, call_id: str) -> HttpResponse:
        # Check if session is active - return 404 if ended
        if not sse_manager.is_session_active(call_id):
            return HttpResponse(
                '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Session Ended - Acko Drive</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .container {
            text-align: center;
            padding: 40px;
        }
        h1 { font-size: 72px; color: #00d9ff; margin-bottom: 20px; }
        p { font-size: 18px; color: #888; margin-bottom: 30px; }
        a { 
            display: inline-block;
            background: linear-gradient(135deg, #00d9ff, #0099cc);
            color: #000;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>404</h1>
        <p>This call session has ended.</p>
        <a href="https://ackodrive.com">Visit Acko Drive</a>
    </div>
</body>
</html>''',
                content_type='text/html',
                status=404
            )
        
        current = sse_manager.get_current_url(call_id)
        initial_url = current.url if current else ""
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acko Drive - Car Preview</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            min-height: 100vh;
        }}
        .loading {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            z-index: 100;
            transition: opacity 0.5s ease;
        }}
        .loading.hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        .spinner {{
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #00d9ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        .loading-text {{
            margin-top: 20px;
            color: #888;
            font-size: 14px;
        }}
        .waiting {{
            color: #00d9ff;
            font-size: 18px;
            margin-bottom: 10px;
        }}
        iframe {{
            width: 100%;
            height: 100vh;
            border: none;
        }}
        .toast {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: linear-gradient(135deg, #00d9ff, #0099cc);
            color: #000;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            z-index: 1000;
            transition: transform 0.3s ease;
            box-shadow: 0 4px 20px rgba(0,217,255,0.3);
        }}
        .toast.show {{
            transform: translateX(-50%) translateY(0);
        }}
    </style>
</head>
<body>
    <div class="loading" id="loading">
        <div class="waiting">Acko Drive</div>
        <div class="spinner"></div>
        <div class="loading-text">Waiting for car selection...</div>
    </div>
    <iframe id="carFrame" src=""></iframe>
    <div class="toast" id="toast">Car updated!</div>

    <script>
        const callId = "{call_id}";
        const iframe = document.getElementById('carFrame');
        const loading = document.getElementById('loading');
        const toast = document.getElementById('toast');
        let hasLoaded = false;

        function showCar(url) {{
            iframe.src = url;
            if (!hasLoaded) {{
                loading.classList.add('hidden');
                hasLoaded = true;
            }} else {{
                toast.classList.add('show');
                setTimeout(() => toast.classList.remove('show'), 3000);
            }}
        }}

        const initialUrl = "{initial_url}";
        if (initialUrl) {{
            showCar(initialUrl);
        }}

        const evtSource = new EventSource('/car/' + callId + '/events/');
        
        evtSource.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            if (data.type === 'session_ended') {{
                evtSource.close();
                showSessionEnded();
                return;
            }}
            if (data.url) {{
                showCar(data.url);
            }}
        }};

        evtSource.onerror = function(err) {{
            console.error('SSE error:', err);
            // Reload page to show 404 if session ended
            setTimeout(() => location.reload(), 1000);
        }};

        function showSessionEnded() {{
            document.body.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; text-align: center; padding: 40px;">
                    <h1 style="font-size: 72px; color: #00d9ff; margin-bottom: 20px;">Session Ended</h1>
                    <p style="font-size: 18px; color: #888; margin-bottom: 30px;">This call session has ended.</p>
                    <a href="https://ackodrive.com" style="display: inline-block; background: linear-gradient(135deg, #00d9ff, #0099cc); color: #000; padding: 12px 24px; border-radius: 8px; font-weight: 600; text-decoration: none;">Visit Acko Drive</a>
                </div>
            `;
        }}
    </script>
</body>
</html>'''
        return HttpResponse(html, content_type='text/html')


class CarSSEView(View):
    async def get(self, request, call_id: str) -> StreamingHttpResponse:
        # Check if session is active
        if not sse_manager.is_session_active(call_id):
            return HttpResponse(
                '{"error": "Session ended"}',
                content_type='application/json',
                status=404
            )

        async def event_stream():
            queue = sse_manager.register(call_id)
            try:
                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield sse_manager.to_sse_data(event)
                        # Stop streaming if session ended
                        if isinstance(event, dict) and event.get("type") == "session_ended":
                            break
                    except asyncio.TimeoutError:
                        # Check if session is still active during keepalive
                        if not sse_manager.is_session_active(call_id):
                            yield f"data: {json.dumps({'type': 'session_ended'})}\n\n"
                            break
                        yield ": keepalive\n\n"
            except (asyncio.CancelledError, GeneratorExit):
                pass
            finally:
                sse_manager.unregister(call_id)

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

@method_decorator(csrf_exempt, name='dispatch')
class CarTestView(View):
    async def post(self, request, call_id: str) -> HttpResponse:
        body = json.loads(request.body) if request.body else {}
        car_slug = body.get("car_slug", "toyota-rumion-s-cng")
        color = body.get("color")
        
        # Check if session is active
        if not sse_manager.is_session_active(call_id):
            return HttpResponse(
                json.dumps({"error": "Session not active or ended"}),
                content_type='application/json',
                status=404
            )
        
        from api.data.inventory import generate_car_url
        url = generate_car_url(car_slug, color)
        
        if not url:
            return HttpResponse(
                json.dumps({"error": "Invalid car_slug or color"}),
                content_type='application/json',
                status=400
            )
        
        await sse_manager.send_url(call_id, url, car_slug, color)
        print(f"\n[TEST] Sent URL update: {url}\n")
        
        return HttpResponse(
            json.dumps({
                "status": "sent",
                "call_id": call_id,
                "url": url,
                "car_slug": car_slug,
                "color": color
            }),
            content_type='application/json'
        )
