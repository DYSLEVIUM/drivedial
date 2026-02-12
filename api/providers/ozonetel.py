"""
Ozonetel Telephony Provider Implementation.

Handles Ozonetel-specific KooKoo XML generation and WebSocket message parsing.
Audio format: PCM linear 16-bit at 8kHz

Based on Ozonetel Bi-Directional Stream documentation:
- XML response initiates WebSocket streaming
- Audio data sent as JSON with PCM16 samples
- Supports clearBuffer and callDisconnect commands
"""

from typing import Optional, Dict, Any, List

from api.providers.base import TelephonyProvider, StreamStartMessage, IncomingAudioMessage
from api.providers.audio_utils import pcm16_samples_to_ulaw_base64, ulaw_base64_to_pcm16_samples


class OzonetelProvider(TelephonyProvider):
    """
    Ozonetel telephony provider implementation.
    
    Ozonetel uses:
    - KooKoo XML for HTTP responses
    - WebSocket with JSON messages containing PCM16 samples
    - PCM linear 16-bit 8kHz audio format
    """
    
    @property
    def provider_name(self) -> str:
        return "ozonetel"
    
    @property
    def audio_format(self) -> str:
        return "pcm16"
    
    # HTTP Response Generation
    def generate_stream_response(
        self, 
        host: str, 
        ws_path: str, 
        protocol: str = "wss",
        sip_number: Optional[str] = None,
        is_sip: bool = True,
        **kwargs
    ) -> str:
        """
        Generate KooKoo XML response to initiate WebSocket streaming.
        
        Args:
            host: Server hostname
            ws_path: WebSocket path (e.g., 'ws/ozonetel-stream/')
            protocol: Protocol to use ('ws' or 'wss')
            sip_number: SIP registration number
            is_sip: Whether this is a SIP call
        """
        url = f"{protocol}://{host}/{ws_path}"
        is_sip_attr = "true" if is_sip else "false"
        sip_content = sip_number or ""
        
        # Return minimal XML without extra whitespace (per KooKoo spec)
        return f'<response><stream is_sip="{is_sip_attr}" url="{url}">{sip_content}</stream></response>'

    def generate_say_response(self, message: str, **kwargs) -> str:
        """Generate KooKoo XML response that speaks a message."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<response>
    <playtext>{message}</playtext>
</response>'''

    def generate_hangup_response(self) -> str:
        """Generate KooKoo XML response that hangs up."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<response>
    <hangup/>
</response>'''
    
    # WebSocket Message Parsing
    def parse_message(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Parse Ozonetel WebSocket message and return event type.
        
        Ozonetel message types: 'media', 'connected', 'disconnected'
        """
        msg_type = data.get("type")
        
        # Map Ozonetel types to normalized types
        if msg_type == "media":
            return "media"
        elif msg_type == "connected":
            return "start"
        elif msg_type == "disconnected":
            return "stop"
        
        return msg_type
    
    def parse_start_message(self, data: Dict[str, Any]) -> StreamStartMessage:
        """
        Parse Ozonetel 'connected' event or first message.
        
        Ozonetel may not send a separate start message, so we extract
        from the first media message's ucid.
        """
        ucid = data.get("ucid", "")
        
        return StreamStartMessage(
            stream_id=ucid,
            call_id=ucid,
            phone_number=data.get("caller_id"),  # If provided
            custom_params=data
        )
    
    def parse_audio_message(self, data: Dict[str, Any]) -> Optional[IncomingAudioMessage]:
        """
        Parse Ozonetel 'media' event.
        
        Ozonetel sends PCM16 samples as an array of integers.
        We convert to g711_ulaw for OpenAI.
        
        Expected format:
        {
            "type": "media",
            "ucid": "111XXXXXXXX71",
            "data": {
                "samples": [8, 8, 8, ...],
                "bitsPerSample": 16,
                "sampleRate": 8000,
                "channelCount": 1,
                "numberOfFrames": 80,
                "type": "data"
            }
        }
        """
        if data.get("type") != "media":
            return None
        
        audio_data = data.get("data", {})
        samples = audio_data.get("samples", [])
        
        if not samples:
            return None
        
        # Convert PCM16 samples to g711_ulaw base64 for OpenAI
        ulaw_payload = pcm16_samples_to_ulaw_base64(samples)
        
        return IncomingAudioMessage(
            payload=ulaw_payload,
            call_id=data.get("ucid", ""),
            raw_data=data
        )
    
    # WebSocket Message Formatting
    def format_audio_message(self, stream_id: str, audio_payload: str) -> Dict[str, Any]:
        """
        Format audio for sending to Ozonetel.
        
        Converts g711_ulaw from OpenAI to PCM16 samples for Ozonetel.
        
        Args:
            stream_id: The UCID
            audio_payload: Base64 encoded g711_ulaw audio from OpenAI
        """
        # Convert g711_ulaw to PCM16 samples
        pcm_samples = ulaw_base64_to_pcm16_samples(audio_payload)
        
        return {
            "type": "media",
            "ucid": stream_id,
            "data": {
                "samples": pcm_samples,
                "bitsPerSample": 16,
                "sampleRate": 8000,
                "channelCount": 1,
                "numberOfFrames": len(pcm_samples),
                "type": "data"
            }
        }
    
    def format_clear_message(self, stream_id: str) -> Dict[str, Any]:
        """Format Ozonetel clear buffer command."""
        return {
            "command": "clearBuffer"
        }
    
    def format_disconnect_message(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """
        Format Ozonetel call disconnect command.
        
        This allows handling normal IVR flow like transferring to human agents.
        """
        return {
            "command": "callDisconnect"
        }

