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
│   ├── factory.py      # Provider factory
│   ├── openai.py       # OpenAI Realtime provider
│   └── twilio.py       # Twilio telephony provider
├── consumers.py        # WebSocket handler
├── views.py            # HTTP endpoints
└── middleware.py       # Request logging
```

## Adding New Providers

### Voice Provider

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

Then register in `factory.py`:

```python
if provider == "my_voice":
    from api.providers.my_voice import MyVoiceProvider
    return MyVoiceProvider()
```

### Telephony Provider

```python
# api/providers/my_telephony.py
from api.providers.base import TelephonyProvider

class MyTelephonyProvider(TelephonyProvider):
    def generate_stream_response(self, host: str, ws_path: str) -> str: ...
    def generate_say_response(self, message: str) -> str: ...
    def generate_hangup_response(self) -> str: ...
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_PROVIDER` | openai | Voice AI provider |
| `TELEPHONY_PROVIDER` | twilio | Telephony provider |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `OPENAI_MODEL` | gpt-4o-mini-realtime-preview-2024-12-17 | Model |
| `OPENAI_VOICE` | ash | Voice (ash, coral, verse) |
| `OPENAI_SYSTEM_PROMPT` | - | AI system prompt |

## License

MIT
