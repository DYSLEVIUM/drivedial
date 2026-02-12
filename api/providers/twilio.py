"""
Twilio Telephony Provider Implementation.

Handles Twilio-specific TwiML generation and WebSocket message parsing.
Audio format: g711_ulaw (μ-law) at 8kHz
"""

from typing import Optional, Dict, Any

from api.providers.base import TelephonyProvider, StreamStartMessage, IncomingAudioMessage


class TwilioProvider(TelephonyProvider):
    """
    Twilio telephony provider implementation.
    
    Twilio uses:
    - TwiML for HTTP responses
    - WebSocket with JSON messages for audio streaming
    - g711_ulaw audio format (same as OpenAI)
    """
    
    @property
    def provider_name(self) -> str:
        return "twilio"
    
    @property
    def audio_format(self) -> str:
        return "g711_ulaw"
    
    # HTTP Response Generation
    def generate_stream_response(
        self, 
        host: str, 
        ws_path: str, 
        protocol: str = "wss",
        from_number: Optional[str] = None,
        call_sid: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate TwiML response to initiate WebSocket streaming."""
        url = f"{protocol}://{host}/{ws_path}"
        
        # Build parameters for custom data
        params = ""
        if from_number:
            params += f'<Parameter name="from_number" value="{from_number}" />'
        if call_sid:
            params += f'<Parameter name="call_sid" value="{call_sid}" />'
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{url}">
            {params}
        </Stream>
    </Connect>
</Response>'''

    def generate_say_response(self, message: str, voice: str = "Polly.Aditi") -> str:
        """Generate TwiML response that speaks a message."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}">{message}</Say>
</Response>'''

    def generate_hangup_response(self) -> str:
        """Generate TwiML response that hangs up."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Hangup />
</Response>'''
    
    # WebSocket Message Parsing
    def parse_message(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Parse Twilio WebSocket message and return event type.
        
        Twilio events: 'start', 'media', 'stop', 'mark'
        """
        return data.get("event")
    
    def parse_start_message(self, data: Dict[str, Any]) -> StreamStartMessage:
        """Parse Twilio 'start' event."""
        start_data = data.get("start", {})
        custom_params = start_data.get("customParameters", {})
        
        return StreamStartMessage(
            stream_id=start_data.get("streamSid", ""),
            call_id=start_data.get("callSid", ""),
            phone_number=custom_params.get("from_number"),
            custom_params=custom_params
        )
    
    def parse_audio_message(self, data: Dict[str, Any]) -> Optional[IncomingAudioMessage]:
        """
        Parse Twilio 'media' event.
        
        Twilio already uses g711_ulaw, so no conversion needed.
        """
        media_data = data.get("media", {})
        payload = media_data.get("payload")
        
        if not payload:
            return None
        
        return IncomingAudioMessage(
            payload=payload,  # Already g711_ulaw base64
            call_id=data.get("streamSid", ""),
            raw_data=data
        )
    
    # WebSocket Message Formatting
    def format_audio_message(self, stream_id: str, audio_payload: str) -> Dict[str, Any]:
        """
        Format audio for sending to Twilio.
        
        Audio is already in g711_ulaw format from OpenAI.
        """
        return {
            "event": "media",
            "streamSid": stream_id,
            "media": {"payload": audio_payload}
        }
    
    def format_clear_message(self, stream_id: str) -> Dict[str, Any]:
        """Format Twilio clear buffer message."""
        return {
            "event": "clear",
            "streamSid": stream_id
        }
    
    def format_disconnect_message(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """
        Twilio doesn't support WebSocket-based disconnect.
        Call must be ended via REST API or TwiML.
        """
        return None
