# DriveDial - AI Voice Sales Agent

Modular Django voice AI with pluggable providers for telephony and voice AI.

## Quick Start

```bash
uv sync
cp env.example .env  # Edit with your API keys
uv run python manage.py runserver_ngrok
```

## Architecture

```
api/
├── providers/           # Pluggable provider system
│   ├── base.py         # Abstract interfaces
│   ├── factory.py      # Provider factory with registry
│   ├── audio_utils.py  # Audio format conversion (PCM16 <-> g711_ulaw)
│   ├── openai.py       # OpenAI Realtime voice provider
│   ├── twilio.py       # Twilio telephony provider
│   └── ozonetel.py     # Ozonetel telephony provider
├── consumers.py        # Provider-agnostic WebSocket handlers
├── views.py            # HTTP endpoints
└── middleware.py       # Request logging
```

## Telephony Providers

DriveDial supports multiple telephony providers through a factory pattern. Switch providers by changing a single environment variable.

### Supported Providers

| Provider | Audio Format | WebSocket Route | HTTP Endpoint |
|----------|-------------|-----------------|---------------|
| Twilio | g711_ulaw (8kHz) | `/ws/twilio-stream/` | `/api/incoming-call/` |
| Ozonetel | PCM16 (8kHz) | `/ws/ozonetel-stream/` | `/api/ozonetel-start/` |

### Switching Providers

```bash
# In .env file
TELEPHONY_PROVIDER=twilio    # Default
TELEPHONY_PROVIDER=ozonetel  # Switch to Ozonetel
```

### Using Multiple Providers Simultaneously

Different WebSocket endpoints can use different providers:

```python
# ws/twilio-stream/ -> Always uses Twilio
# ws/ozonetel-stream/ -> Always uses Ozonetel
# ws/media-stream/ -> Uses configured TELEPHONY_PROVIDER
```

## Adding New Telephony Providers

### Step 1: Create Provider Class

```python
# api/providers/my_telephony.py
from api.providers.base import TelephonyProvider, StreamStartMessage, IncomingAudioMessage

class MyTelephonyProvider(TelephonyProvider):
    @property
    def provider_name(self) -> str:
        return "my_provider"
    
    @property
    def audio_format(self) -> str:
        return "pcm16"  # or "g711_ulaw"
    
    # HTTP Response Generation
    def generate_stream_response(self, host: str, ws_path: str, **kwargs) -> str:
        """Return XML/JSON to initiate WebSocket streaming."""
        ...
    
    def generate_say_response(self, message: str) -> str:
        """Return response that speaks a message."""
        ...
    
    def generate_hangup_response(self) -> str:
        """Return response that hangs up."""
        ...
    
    # WebSocket Message Parsing
    def parse_message(self, data: dict) -> str:
        """Return event type: 'start', 'media', 'stop'."""
        ...
    
    def parse_start_message(self, data: dict) -> StreamStartMessage:
        """Parse stream start event."""
        ...
    
    def parse_audio_message(self, data: dict) -> IncomingAudioMessage:
        """Parse audio and convert to g711_ulaw if needed."""
        ...
    
    # WebSocket Message Formatting
    def format_audio_message(self, stream_id: str, audio_payload: str) -> dict:
        """Format audio for sending (convert from g711_ulaw if needed)."""
        ...
    
    def format_clear_message(self, stream_id: str) -> dict:
        """Format buffer clear command."""
        ...
    
    def format_disconnect_message(self, stream_id: str) -> dict:
        """Format disconnect command (or None if not supported)."""
        ...
```

### Step 2: Register Provider

```python
# In api/providers/factory.py
from api.providers.my_telephony import MyTelephonyProvider
register_telephony_provider("my_provider", MyTelephonyProvider)
```

### Step 3: Add WebSocket Consumer (Optional)

```python
# In api/consumers.py
class MyProviderMediaStreamConsumer(BaseMediaStreamConsumer):
    telephony_provider_name = "my_provider"

# In api/routing.py
re_path(r"ws/my-provider-stream/$", MyProviderMediaStreamConsumer.as_asgi()),
```

## Audio Format Handling

OpenAI Realtime API uses g711_ulaw (μ-law) format. Providers with different formats are automatically converted:

```python
from api.providers.audio_utils import (
    pcm16_samples_to_ulaw_base64,  # Ozonetel -> OpenAI
    ulaw_base64_to_pcm16_samples,  # OpenAI -> Ozonetel
)
```

## Adding New Voice Providers

```python
# api/providers/my_voice.py
from api.providers.base import VoiceProvider

class MyVoiceProvider(VoiceProvider):
    @property
    def is_connected(self) -> bool: ...
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def send_audio(self, payload: str) -> None: ...
    async def listen(self) -> None: ...
```

Register in factory:

```python
    from api.providers.my_voice import MyVoiceProvider
register_voice_provider("my_voice", MyVoiceProvider)
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_PROVIDER` | openai | Voice AI provider |
| `TELEPHONY_PROVIDER` | twilio | Telephony provider (twilio, ozonetel) |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `OPENAI_MODEL` | gpt-4o-mini-realtime-preview-2024-12-17 | Model |
| `OPENAI_VOICE` | coral | Voice (ash, coral, verse) |
| `OZONETEL_API_KEY` | - | Ozonetel API key |
| `OZONETEL_SIP_NUMBER` | - | SIP registration number |

## WebSocket Endpoints

| Endpoint | Provider | Description |
|----------|----------|-------------|
| `/ws/media-stream/` | Configured | Uses TELEPHONY_PROVIDER setting |
| `/ws/twilio-stream/` | Twilio | Always uses Twilio |
| `/ws/ozonetel-stream/` | Ozonetel | Always uses Ozonetel |

## HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/incoming-call/` | POST | Twilio incoming call webhook |
| `/api/ozonetel-start/` | GET/POST | Ozonetel IVR initiation |
| `/api/health/` | GET | Health check |
| `/api/inventory/` | GET/POST | Car inventory |
| `/api/analytics/<call_id>/` | GET | Call analytics |

## License

MIT
