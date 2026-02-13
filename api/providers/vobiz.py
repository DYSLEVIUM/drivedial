"""
VoBiz Telephony Provider Implementation.

Audio: g711_ulaw (μ-law) at 8kHz, base64 encoded
Protocol: WebSocket with JSON messages
Events: start, media, stop, playedStream, clearedAudio

VoBiz is an enterprise telephony platform providing:
- SIP Trunk Provisioning with auto-generated domains
- Intelligent Least-Cost Routing (LCR)
- Number Management with auto-billing
- Real-time Billing and CDR processing
- Multi-tenancy with sub-account support

Reference: https://www.docs.vobiz.ai/
"""

import hashlib
import hmac
import logging
from typing import Optional, Dict, Any

from api.providers.base import (
    IncomingAudioMessage,
    StreamStartMessage,
    TelephonyProvider,
)

logger = logging.getLogger(__name__)


class VoBizProvider(TelephonyProvider):
    """
    VoBiz telephony provider implementation.

    VoBiz uses XML for call control (similar to TwiML) and WebSocket
    for real-time audio streaming. Audio format is g711_ulaw.

    Configuration env vars:
        VOBIZ_AUTH_ID        – Account ID from console.vobiz.ai  (e.g. MA_XXXXXXX)
        VOBIZ_AUTH_TOKEN     – Auth token from console.vobiz.ai
        VOBIZ_FROM_NUMBER    – Outbound caller-ID  (e.g. +918071387318)
    """

    @property
    def provider_name(self) -> str:
        return "vobiz"

    @property
    def audio_format(self) -> str:
        return "g711_ulaw"

    # =========================================================================
    # Webhook Signature Validation
    # =========================================================================

    def validate_webhook_signature(
        self,
        request_body: Dict[str, Any],
        signature: Optional[str],
        auth_token: Optional[str] = None,
    ) -> bool:
        """
        Validate VoBiz webhook signature (HMAC-SHA256).

        The signature is passed in the X-Vobiz-Signature header.
        """
        if not signature:
            logger.warning("Missing VoBiz signature header")
            return False

        if not auth_token:
            from django.conf import settings
            auth_token = getattr(settings, "VOBIZ_AUTH_TOKEN", "")

        if not auth_token:
            logger.error("VoBiz auth_token not configured")
            return False

        try:
            import json as _json
            sorted_params = sorted(request_body.items())
            canonical_string = "&".join(
                f"{k}={v}" for k, v in sorted_params if v is not None
            )
            expected_signature = hmac.new(
                auth_token.encode("utf-8"),
                canonical_string.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"VoBiz signature validation error: {e}")
            return False

    # =========================================================================
    # HTTP Response Generation (XML)
    # =========================================================================

    def generate_stream_response(
        self,
        host: str,
        ws_path: str,
        protocol: str = "wss",
        **kwargs: Any,
    ) -> str:
        """
        Generate VoBiz XML response to initiate WebSocket streaming.

        VoBiz Stream format (from https://www.docs.vobiz.ai/xml/stream):
        - URL goes as element content, not attribute
        - bidirectional="true"  for two-way audio
        - keepCallAlive="true"  to keep call active during stream
        - contentType           for audio format

        Args:
            host:     Server hostname
            ws_path:  WebSocket path  (e.g. 'ws/vobiz-stream/')
            protocol: 'ws' or 'wss'
            **kwargs:
                from_number          – caller phone number
                to_number            – callee phone number
                call_id              – VoBiz call UUID
                status_callback_url  – Optional callback URL
        """
        websocket_url = f"{protocol}://{host}/{ws_path}"

        # Build extraHeaders for passing call metadata to WebSocket
        extra_headers_parts = []
        if kwargs.get("from_number"):
            extra_headers_parts.append(f'from={kwargs["from_number"]}')
        if kwargs.get("call_id"):
            extra_headers_parts.append(f'callid={kwargs["call_id"]}')
        if kwargs.get("to_number"):
            extra_headers_parts.append(f'to={kwargs["to_number"]}')

        extra_headers = ",".join(extra_headers_parts) if extra_headers_parts else ""

        # Build Stream element attributes
        attrs = [
            'bidirectional="true"',
            'keepCallAlive="true"',
            'contentType="audio/x-mulaw;rate=8000"',
        ]
        if extra_headers:
            attrs.append(f'extraHeaders="{extra_headers}"')
        if kwargs.get("status_callback_url"):
            attrs.append(f'statusCallbackUrl="{kwargs["status_callback_url"]}"')
            attrs.append('statusCallbackMethod="POST"')

        attrs_str = " ".join(attrs)

        # VoBiz format: URL is element content, not attribute
        return (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f"<Response>"
            f"<Stream {attrs_str}>{websocket_url}</Stream>"
            f"</Response>"
        )

    def generate_say_response(self, message: str, **kwargs: Any) -> str:
        """Generate VoBiz XML response to speak a message using TTS."""
        language = kwargs.get("language", "en-IN")
        loop = kwargs.get("loop", 1)
        voice = kwargs.get("voice", "")

        attrs = f'language="{language}" loop="{loop}"'
        if voice:
            attrs += f' voice="{voice}"'

        return (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f"<Response><Speak {attrs}>{message}</Speak></Response>"
        )

    def generate_hangup_response(self) -> str:
        """Generate VoBiz XML response to end the call."""
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Hangup/></Response>'

    # =========================================================================
    # WebSocket Message Parsing
    # =========================================================================

    def parse_message(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Parse VoBiz WebSocket message type.

        VoBiz WebSocket events:
        - start:         Stream started
        - media:         Audio data
        - stop:          Stream stopped
        - playedStream:  Checkpoint reached
        - clearedAudio:  Audio buffer cleared
        """
        return data.get("event", "")

    def parse_start_message(self, data: Dict[str, Any]) -> StreamStartMessage:
        """
        Parse VoBiz stream start message.

        Example payload:
        {
            "event": "start",
            "streamId": "227d997a-...",
            "callUUID": "9a0e0208-...",
            "from": "918071387423",
            "to": "919624705678",
            "extraHeaders": {"from": "918071387423", "callid": "xxx", "to": "xxx"}
        }
        """
        stream_id = (
            data.get("streamId")
            or data.get("StreamID")
            or data.get("stream_id", "")
        )
        call_id = (
            data.get("callUUID")
            or data.get("CallUUID")
            or data.get("call_id", "")
        )

        extra_headers = data.get("extraHeaders", {})
        from_number = (
            data.get("from")
            or data.get("From")
            or extra_headers.get("from")
        )
        to_number = (
            data.get("to")
            or data.get("To")
            or extra_headers.get("to")
        )

        return StreamStartMessage(
            stream_id=stream_id,
            call_id=call_id,
            phone_number=from_number,
            custom_params={
                "from": from_number,
                "to": to_number,
                "extra_headers": extra_headers,
            },
        )

    def parse_audio_message(
        self, data: Dict[str, Any]
    ) -> Optional[IncomingAudioMessage]:
        """
        Parse VoBiz media message.

        VoBiz media format:
        {
            "event": "media",
            "media": {
                "contentType": "audio/x-mulaw",
                "sampleRate": 8000,
                "payload": "<base64>"
            },
            "streamId": "xxx"
        }
        """
        media = data.get("media", {})
        payload = media.get("payload")
        if not payload:
            return None

        # VoBiz audio/x-mulaw is the same as g711_ulaw — no conversion needed
        return IncomingAudioMessage(
            payload=payload,
            call_id=data.get("streamId", ""),
            raw_data=data,
        )

    # =========================================================================
    # WebSocket Message Formatting
    # =========================================================================

    def format_audio_message(
        self, stream_id: str, audio_payload: str
    ) -> Dict[str, Any]:
        """
        Format outgoing audio message for VoBiz.

        VoBiz bidirectional format:
        - event:    "playAudio"
        - streamId: the stream identifier (MUST match the incoming stream)
        - media:    {contentType, sampleRate, payload}
        """
        return {
            "event": "playAudio",
            "streamId": stream_id,
            "media": {
                "contentType": "audio/x-mulaw",
                "sampleRate": 8000,
                "payload": audio_payload,
            },
        }

    def format_clear_message(self, stream_id: str) -> Dict[str, Any]:
        """Format buffer clear command for VoBiz."""
        return {
            "event": "clearAudio",
            "streamId": stream_id,
        }

    def format_mark_message(
        self, stream_id: str, mark_name: str
    ) -> Dict[str, Any]:
        """
        Format checkpoint message for tracking audio playback.

        VoBiz sends a 'playedStream' callback when this checkpoint is reached.
        """
        return {
            "event": "checkpoint",
            "streamId": stream_id,
            "name": mark_name,
        }

    def format_disconnect_message(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """
        Format a message to disconnect the call.

        VoBiz supports a Hangup command via the WebSocket.
        """
        return {
            "event": "hangup",
            "streamId": stream_id,
        }

