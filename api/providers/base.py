from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any


@dataclass
class IncomingAudioMessage:
    """Normalized audio message from any telephony provider."""
    payload: str  # Base64 encoded audio (converted to g711_ulaw for OpenAI)
    call_id: str  # Provider-specific call identifier
    raw_data: Dict[str, Any]  # Original provider message


@dataclass
class StreamStartMessage:
    """Normalized stream start message."""
    stream_id: str
    call_id: str
    phone_number: Optional[str] = None
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}


class VoiceProvider(ABC):
    """Abstract base class for voice AI providers (e.g., OpenAI Realtime)."""
    
    on_audio: Optional[Callable[[str], None]] = None
    on_interrupt: Optional[Callable[[], None]] = None
    on_error: Optional[Callable[[Exception], None]] = None

    def set_callbacks(
        self,
        on_audio: Optional[Callable] = None,
        on_interrupt: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> None:
        self.on_audio = on_audio
        self.on_interrupt = on_interrupt
        self.on_error = on_error

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def send_audio(self, payload: str) -> None:
        pass

    @abstractmethod
    async def listen(self) -> None:
        pass


class TelephonyProvider(ABC):
    """
    Abstract base class for telephony providers (e.g., Twilio, Ozonetel).
    
    Handles both HTTP response generation and WebSocket message parsing/formatting.
    """
    
    # Provider identification
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'twilio', 'ozonetel')."""
        pass
    
    @property
    @abstractmethod
    def audio_format(self) -> str:
        """Return the native audio format (e.g., 'g711_ulaw', 'pcm16')."""
        pass
    
    # HTTP Response Generation
    @abstractmethod
    def generate_stream_response(self, host: str, ws_path: str, **kwargs) -> str:
        """Generate the initial HTTP response to initiate WebSocket streaming."""
        pass

    @abstractmethod
    def generate_say_response(self, message: str) -> str:
        """Generate a response that speaks a message."""
        pass

    @abstractmethod
    def generate_hangup_response(self) -> str:
        """Generate a response that hangs up the call."""
        pass
    
    # WebSocket Message Parsing
    @abstractmethod
    def parse_message(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Parse incoming WebSocket message and return event type.
        
        Returns: Event type string ('start', 'media', 'stop', None for unknown)
        """
        pass
    
    @abstractmethod
    def parse_start_message(self, data: Dict[str, Any]) -> StreamStartMessage:
        """Parse a 'start' event and extract stream metadata."""
        pass
    
    @abstractmethod
    def parse_audio_message(self, data: Dict[str, Any]) -> Optional[IncomingAudioMessage]:
        """
        Parse a 'media' event and extract audio data.
        
        Returns audio payload in g711_ulaw format (converting if necessary).
        """
        pass
    
    # WebSocket Message Formatting (for sending)
    @abstractmethod
    def format_audio_message(self, stream_id: str, audio_payload: str) -> Dict[str, Any]:
        """
        Format audio data for sending back to the telephony provider.
        
        Args:
            stream_id: The stream identifier
            audio_payload: Base64 encoded g711_ulaw audio from OpenAI
            
        Returns: Dictionary to be JSON-serialized and sent over WebSocket
        """
        pass
    
    @abstractmethod
    def format_clear_message(self, stream_id: str) -> Dict[str, Any]:
        """Format a message to clear the audio buffer (for interruptions)."""
        pass
    
    @abstractmethod
    def format_disconnect_message(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """
        Format a message to disconnect the call.
        
        Returns None if the provider doesn't support WebSocket-based disconnect.
        """
        pass
