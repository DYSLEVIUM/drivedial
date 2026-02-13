import asyncio
import json
import logging
from datetime import date

import requests as http_requests
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
    """
    Handle incoming calls from telephony providers.
    
    Uses the configured TELEPHONY_PROVIDER to generate appropriate response.
    For Twilio: Returns TwiML to initiate WebSocket streaming
    For Ozonetel: Returns KooKoo XML to initiate WebSocket streaming
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request) -> HttpResponse:
        host = request.get_host()
        
        # Extract call info (Twilio format)
        call_sid = request.data.get("CallSid", "unknown")
        from_number = request.data.get("From", "unknown")

        logger.info(f"Incoming call: {call_sid} from {from_number}")

        telephony = ProviderFactory.get_telephony()
        response_xml = telephony.generate_stream_response(
            host, 
            "ws/media-stream/",
            from_number=from_number,
            call_sid=call_sid
        )
        return HttpResponse(response_xml, content_type="text/xml")

    def get(self, request: Request) -> Response:
        telephony = ProviderFactory.get_telephony()
        return Response({
            "endpoint": "incoming-call",
            "method": "POST",
            "provider": telephony.provider_name,
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
        <a href="https://ackodrive.com/cars/">Visit Acko Drive</a>
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
                    <a href="https://ackodrive.com/cars/" style="display: inline-block; background: linear-gradient(135deg, #00d9ff, #0099cc); color: #000; padding: 12px 24px; border-radius: 8px; font-weight: 600; text-decoration: none;">Visit Acko Drive</a>
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



class OzonetelIncomingCallView(APIView):
    """
    Handle incoming calls specifically from Ozonetel.
    
    Returns KooKoo XML to initiate bi-directional WebSocket streaming.
    This endpoint handles different Ozonetel events:
    - NewCall: Initial call setup - return stream XML to start WebSocket
    - Stream: Polling while call is active - return continue/hangup based on status
    - Hangup: Call ended - acknowledge
    
    Query Parameters from Ozonetel:
    - event: NewCall, Stream, Hangup
    - sid: Session ID
    - cid: Caller ID
    - status: not_answered, answered, etc.
    - called_number: The number being called
    """
    authentication_classes = []
    permission_classes = []

    def _handle_ozonetel_request(self, request: Request) -> HttpResponse:
        """Common handler for GET and POST requests."""
        # Get host from X-Forwarded-Host (for ngrok/proxies) or fallback to Host header
        host = request.META.get('HTTP_X_FORWARDED_HOST') or request.get_host()
        
        # Determine WebSocket protocol based on X-Forwarded-Proto or scheme
        forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO', '')
        is_secure = forwarded_proto == 'https' or request.is_secure()
        ws_protocol = "wss" if is_secure else "ws"
        
        # Extract parameters from either query params (GET) or data (POST)
        params = request.query_params if request.method == "GET" else request.data
        
        event = params.get("event", "")
        sid = params.get("sid", "")
        cid = params.get("cid", "")
        called_number = params.get("called_number", "")
        status = params.get("status", "")
        message = params.get("message", "")
        
        # Get configured SIP number for streaming
        sip_number = getattr(settings, "OZONETEL_SIP_NUMBER", "")
        
        logger.info(
            f"Ozonetel {event}: sid={sid}, cid={cid}, status={status}, "
            f"message={message}, called={called_number}, host={host}, proto={ws_protocol}"
        )

        telephony = ProviderFactory.get_telephony("ozonetel")
        
        if event == "NewCall":
            # Initial call - return stream XML to initiate WebSocket
            ws_url = f"{ws_protocol}://{host}/ws/ozonetel-stream/"
            logger.info(f"Ozonetel NewCall: Starting WebSocket stream for sid={sid}, URL={ws_url}")
            response_xml = telephony.generate_stream_response(
                host, 
                "ws/ozonetel-stream/",
                protocol=ws_protocol,
                sip_number=sip_number,
                is_sip=True
            )
            logger.info(f"Ozonetel response XML: {response_xml}")
            return HttpResponse(response_xml, content_type="application/xml")
        
        elif event == "Stream":
            # Polling during call - check status
            if status == "not_answered":
                # Call still ringing, continue waiting
                # Return empty response or collectdtmf to keep IVR active
                response_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<response>
    <collectdtmf l="1" t="1"/>
</response>'''
            elif status == "answered":
                # Call answered - this shouldn't happen during streaming
                # Return stream XML in case it's needed
                response_xml = telephony.generate_stream_response(
                    host, 
                    "ws/ozonetel-stream/",
                    sip_number=sip_number,
                    is_sip=True
                )
            else:
                # Unknown status, return empty response
                response_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<response/>'''
            return HttpResponse(response_xml, content_type="application/xml")
        
        elif event == "Hangup":
            # Call ended - acknowledge
            logger.info(f"Ozonetel Hangup: sid={sid}, status={status}")
            response_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<response/>'''
            return HttpResponse(response_xml, content_type="application/xml")
        
        else:
            # Unknown event - return stream XML as default (backward compat)
            logger.warning(f"Ozonetel unknown event: {event}")
            response_xml = telephony.generate_stream_response(
                host, 
                "ws/ozonetel-stream/",
                sip_number=sip_number,
                is_sip=True
            )
            return HttpResponse(response_xml, content_type="application/xml")

    def get(self, request: Request) -> HttpResponse:
        """Handle GET request from Ozonetel IVR."""
        event = request.GET.get('event')
        if event != 'NewCall':
            response_xml = "<response> <hangup/> </response> "
            return HttpResponse(response_xml, content_type="application/xml")
        return self._handle_ozonetel_request(request)
    
    def post(self, request: Request) -> HttpResponse:
        """Handle POST request from Ozonetel IVR."""
        return self._handle_ozonetel_request(request)


# Backward compatibility alias
Ozonetel = OzonetelIncomingCallView


class OzonetelDebugView(APIView):
    """Debug view to test Ozonetel XML response generation."""
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        """Show what XML response would be sent to Ozonetel."""
        host = request.META.get('HTTP_X_FORWARDED_HOST') or request.get_host()
        forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO', '')
        is_secure = forwarded_proto == 'https' or request.is_secure()
        ws_protocol = "wss" if is_secure else "ws"
        
        sip_number = getattr(settings, "OZONETEL_SIP_NUMBER", "")
        
        telephony = ProviderFactory.get_telephony("ozonetel")
        response_xml = telephony.generate_stream_response(
            host,
            "ws/ozonetel-stream/",
            protocol=ws_protocol,
            sip_number=sip_number,
            is_sip=True
        )
        
        return Response({
            "host": host,
            "protocol": ws_protocol,
            "sip_number": sip_number or "(not configured)",
            "websocket_url": f"{ws_protocol}://{host}/ws/ozonetel-stream/",
            "xml_response": response_xml,
            "request_headers": {
                "Host": request.META.get('HTTP_HOST', ''),
                "X-Forwarded-Host": request.META.get('HTTP_X_FORWARDED_HOST', ''),
                "X-Forwarded-Proto": request.META.get('HTTP_X_FORWARDED_PROTO', ''),
            }
        })


# =============================================================================
# VoBiz Telephony
# =============================================================================

class VoBizIncomingCallView(APIView):
    """
    Webhook endpoint that VoBiz calls when an outbound call is answered.

    VoBiz sends a POST/GET to the answer_url configured in the outbound call
    request. We respond with XML that initiates a bidirectional WebSocket
    stream (identical pattern to Twilio / Ozonetel incoming-call endpoints).
    """
    authentication_classes = []
    permission_classes = []

    def _handle(self, request: Request) -> HttpResponse:
        host = request.META.get("HTTP_X_FORWARDED_HOST") or request.get_host()
        forwarded_proto = request.META.get("HTTP_X_FORWARDED_PROTO", "")
        is_secure = forwarded_proto == "https" or request.is_secure()
        ws_protocol = "wss" if is_secure else "ws"

        # VoBiz may pass these as query-params or POST body
        params = request.query_params if request.method == "GET" else request.data
        call_uuid = params.get("CallUUID", params.get("callUUID", "unknown"))
        from_number = params.get("From", params.get("from", "unknown"))
        to_number = params.get("To", params.get("to", "unknown"))

        logger.info(
            f"VoBiz webhook: callUUID={call_uuid}, from={from_number}, "
            f"to={to_number}, host={host}, proto={ws_protocol}"
        )

        telephony = ProviderFactory.get_telephony("vobiz")
        response_xml = telephony.generate_stream_response(
            host,
            "ws/vobiz-stream/",
            protocol=ws_protocol,
            from_number=from_number,
            to_number=to_number,
            call_id=call_uuid,
        )
        logger.info(f"VoBiz response XML: {response_xml}")
        return HttpResponse(response_xml, content_type="application/xml")

    def get(self, request: Request) -> HttpResponse:
        return self._handle(request)

    def post(self, request: Request) -> HttpResponse:
        return self._handle(request)


class OutboundCallView(APIView):
    """
    Provider-agnostic outbound call API.

    Reads TELEPHONY_PROVIDER (or accepts ?provider= override) to decide
    which telephony platform to use for placing the call.

    Currently supported: vobiz.

    POST /api/outbound-call/
    Body:
      {
        "to":       "+917541918820",        # required
        "from":     "+918071387318",        # optional – falls back to env
        "provider": "vobiz"                 # optional – falls back to TELEPHONY_PROVIDER
      }
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request) -> Response:
        to_number = request.data.get("to")
        if not to_number:
            return Response({"error": "Missing required field: to"}, status=400)

        provider_name = (
            request.data.get("provider")
            or request.query_params.get("provider")
            or getattr(settings, "TELEPHONY_PROVIDER", "twilio")
        ).lower()

        # ── VoBiz outbound ────────────────────────────────────────────
        if provider_name == "vobiz":
            return self._vobiz_outbound(request, to_number)

        # ── Unsupported provider ──────────────────────────────────────
        return Response(
            {"error": f"Outbound calls not supported for provider: {provider_name}"},
            status=400,
        )

    # -----------------------------------------------------------------
    # VoBiz
    # -----------------------------------------------------------------
    def _vobiz_outbound(self, request: Request, to_number: str) -> Response:
        auth_id = getattr(settings, "VOBIZ_AUTH_ID", "")
        auth_token = getattr(settings, "VOBIZ_AUTH_TOKEN", "")
        from_number = (
            request.data.get("from")
            or getattr(settings, "VOBIZ_FROM_NUMBER", "")
        )

        if not auth_id or not auth_token:
            return Response(
                {"error": "VOBIZ_AUTH_ID and VOBIZ_AUTH_TOKEN must be set in env"},
                status=500,
            )
        if not from_number:
            return Response(
                {"error": "Missing 'from' number. Set VOBIZ_FROM_NUMBER in env or pass in body"},
                status=400,
            )

        # Build the answer_url pointing back to our VoBiz webhook
        host = request.META.get("HTTP_X_FORWARDED_HOST") or request.get_host()
        forwarded_proto = request.META.get("HTTP_X_FORWARDED_PROTO", "")
        is_secure = forwarded_proto == "https" or request.is_secure()
        http_protocol = "https" if is_secure else "http"
        answer_url = f"{http_protocol}://{host}/webhooks/vobiz/"

        # Allow caller to override answer_url (e.g. with a cloudflare tunnel)
        answer_url = request.data.get("answer_url", answer_url)

        api_url = f"https://api.vobiz.ai/api/v1/Account/{auth_id}/Call/"
        payload = {
            "from": from_number,
            "to": to_number,
            "answer_url": answer_url,
        }
        headers = {
            "X-Auth-ID": auth_id,
            "X-Auth-Token": auth_token,
            "Content-Type": "application/json",
        }

        logger.info(
            f"VoBiz outbound call: from={from_number} to={to_number} "
            f"answer_url={answer_url}"
        )

        try:
            resp = http_requests.post(api_url, json=payload, headers=headers, timeout=15)
            resp_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"raw": resp.text}
            logger.info(f"VoBiz API response ({resp.status_code}): {resp_data}")

            if resp.status_code >= 400:
                return Response(
                    {"error": "VoBiz API error", "status": resp.status_code, "detail": resp_data},
                    status=502,
                )

            return Response({
                "status": "initiated",
                "provider": "vobiz",
                "to": to_number,
                "from": from_number,
                "answer_url": answer_url,
                "vobiz_response": resp_data,
            })
        except http_requests.RequestException as exc:
            logger.error(f"VoBiz outbound call failed: {exc}")
            return Response(
                {"error": f"Failed to reach VoBiz API: {exc}"},
                status=502,
            )