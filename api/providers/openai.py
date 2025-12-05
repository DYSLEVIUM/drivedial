import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

import aiohttp
from django.conf import settings

from api.data.store import store
from api.providers.base import VoiceProvider
from api.services.analytics import analytics
from api.services.call_logger import CallLogger

logger = logging.getLogger("openai")

TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "name": "search_cars",
        "description": "Search inventory for cars. Budget: '20 lakh' = 2000000. 'under X' = budget_max only.",
        "parameters": {
            "type": "object",
            "properties": {
                "budget_min": {"type": "integer", "description": "Min budget INR. Only for 'above X' or 'between X and Y'."},
                "budget_max": {"type": "integer", "description": "Max budget INR. For 'under X', 'within X' queries."},
                "brand": {"type": "string", "description": "Car brand"},
                "fuel_type": {"type": "string", "enum": ["Petrol", "Diesel"]},
                "transmission": {"type": "string", "enum": ["Manual", "Automatic", "CVT"]}
            },
            "required": []
        }
    },
    {
        "type": "function",
        "name": "get_car_details",
        "description": "Get details for a specific car by ID",
        "parameters": {
            "type": "object",
            "properties": {
                "car_id": {"type": "string", "description": "Car ID (e.g., 'swift-vxi', 'city-zx')"}
            },
            "required": ["car_id"]
        }
    },
    {
        "type": "function",
        "name": "check_availability",
        "description": "Check availability of cars from a brand",
        "parameters": {
            "type": "object",
            "properties": {
                "brand": {"type": "string", "description": "Brand name"}
            },
            "required": ["brand"]
        }
    },
    {
        "type": "function",
        "name": "web_search",
        "description": "Search the web for car reviews, comparisons, news, or general automotive info not in inventory",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query about cars, reviews, comparisons"}
            },
            "required": ["query"]
        }
    },
    {
        "type": "function",
        "name": "end_call",
        "description": "End the phone call. Use when: user wants to hang up, says goodbye, or after 3+ consecutive off-topic messages",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Reason for ending: 'user_request', 'off_topic', 'completed'"}
            },
            "required": ["reason"]
        }
    }
]


async def web_search(query: str) -> Dict[str, Any]:
    """Perform web search using OpenAI's web search or fallback to a simple response."""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant. Provide brief, factual information about cars."},
                        {"role": "user", "content": f"Brief info about: {query}"}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 150,
                },
                timeout=aiohttp.ClientTimeout(total=5.0)
            ) as resp:
                data = await resp.json()
                content = data.get("choices", [{}])[0].get(
                    "message", {}).get("content", "")
                return {"result": content, "source": "web_search"}
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return {"result": "Could not fetch information at the moment.", "source": "error"}


def execute_tool(name: str, arguments: dict) -> Any:
    if name == "search_cars":
        return store.search(
            budget_min=arguments.get("budget_min"),
            budget_max=arguments.get("budget_max"),
            brand=arguments.get("brand"),
            fuel_type=arguments.get("fuel_type"),
            transmission=arguments.get("transmission"),
        )
    elif name == "get_car_details":
        return store.get_car(arguments.get("car_id", ""))
    elif name == "check_availability":
        cars = store.search_by_brand(arguments.get("brand", ""))
        return [{"name": c["name"], "availability": c["availability"], "location": c["location"]} for c in cars]
    elif name == "end_call":
        return {"status": "ending", "reason": arguments.get("reason", "user_request")}
    return None


def build_system_prompt() -> str:
    base_prompt = getattr(settings, "OPENAI_SYSTEM_PROMPT", "")
    context_summary = store.get_context_summary()
    return base_prompt.replace(
        "CONTEXT: You are selling cars.",
        f"CONTEXT: {context_summary}"
    ).replace(
        "CONTEXT: You are selling cars (Swift, Honda City, XUV700, Creta, Baleno).",
        f"CONTEXT: {context_summary}"
    )


class OpenAIVoiceProvider(VoiceProvider):
    AUDIO_CHUNK_DURATION_MS = 20

    def __init__(
        self,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        voice: Optional[str] = None,
        call_id: Optional[str] = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.system_prompt = system_prompt or build_system_prompt()
        self.voice = voice or settings.OPENAI_VOICE
        self.temperature = settings.OPENAI_TEMPERATURE
        self.call_id = call_id

        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None

        self.on_transcript: Optional[Callable[[str, bool], None]] = None
        self.on_response_done: Optional[Callable[[], None]] = None
        self.on_end_call: Optional[Callable[[str], None]] = None

        self._is_user_speaking = False
        self._audio_delta_count = 0
        self._last_audio_send_time: float = 0
        self._estimated_playback_end: float = 0

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    def _is_audio_playing(self) -> bool:
        return time.time() * 1000 < self._estimated_playback_end

    async def connect(self) -> None:
        if self.is_connected:
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(
            settings.OPENAI_REALTIME_URL, headers=headers
        )

        if self.call_id:
            CallLogger.log_event(
                self.call_id, "Connected to OpenAI Realtime API")
            analytics.start_call(self.call_id)

        await self._configure_session()
        await self._send_initial_greeting()

    async def _configure_session(self) -> None:
        session_config = {
            "modalities": ["text", "audio"],
            "voice": self.voice,
            "instructions": self.system_prompt,
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "input_audio_transcription": {
                "model": "gpt-4o-transcribe"
            },
            "input_audio_noise_reduction": {
                "type": "far_field"
            },
            "turn_detection": {
                "type": "semantic_vad",
                "eagerness": "medium",
                "create_response": True,
                "interrupt_response": True
            },
            "tools": TOOLS,
            "tool_choice": "auto",
            "temperature": self.temperature,
            "max_response_output_tokens": 1000,
        }

        await self._ws.send_json({
            "type": "session.update",
            "session": session_config
        })

        if self.call_id:
            CallLogger.log_event(self.call_id, "Session configured")

    async def _send_initial_greeting(self) -> None:
        greeting_instruction = getattr(
            settings,
            "OPENAI_GREETING_INSTRUCTION",
            "Greet the customer warmly. Introduce yourself and ask if they are looking for a car. Be brief and natural."
        )
        await self._ws.send_json({
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"],
                "instructions": greeting_instruction
            }
        })

    async def disconnect(self) -> None:
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._session and not self._session.closed:
            await self._session.close()
        self._ws = None
        self._session = None

        if self.call_id:
            CallLogger.log_event(self.call_id, "Disconnected")
            analytics.end_call(self.call_id)
            cost_summary = analytics.calculate_cost(self.call_id)
            CallLogger.log_event(
                self.call_id, "Cost summary", str(cost_summary))

    async def send_audio(self, payload: str) -> None:
        if not self.is_connected:
            return
        await self._ws.send_json({
            "type": "input_audio_buffer.append",
            "audio": payload
        })

    async def cancel_response(self) -> None:
        pass

    async def listen(self) -> None:
        if self.call_id:
            CallLogger.log_event(self.call_id, "Listening started")
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(json.loads(msg.data))
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    if self.call_id:
                        CallLogger.log_error(self.call_id, "WebSocket error")
                    break
        except Exception as e:
            if self.call_id:
                CallLogger.log_error(self.call_id, f"Listener error: {e}")
            if self.on_error:
                await self.on_error(e)
        finally:
            await self.disconnect()

    async def _handle_message(self, data: dict) -> None:
        msg_type = data.get("type", "")
        handlers = {
            "response.audio.delta": self._handle_audio_delta,
            "input_audio_buffer.speech_started": self._handle_speech_started,
            "input_audio_buffer.speech_stopped": self._handle_speech_stopped,
            "conversation.item.input_audio_transcription.completed": self._handle_user_transcription,
            "response.audio_transcript.done": self._handle_assistant_transcription,
            "response.done": self._handle_response_done,
            "response.audio.done": self._handle_audio_done,
            "response.function_call_arguments.done": self._handle_function_call,
            "error": self._handle_error,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(data)

    async def _handle_audio_delta(self, data: dict) -> None:
        self._audio_delta_count += 1
        now = time.time() * 1000
        self._last_audio_send_time = now
        self._estimated_playback_end = now + \
            (self._audio_delta_count * self.AUDIO_CHUNK_DURATION_MS) + 500

        if self.on_audio:
            await self.on_audio(data.get("delta", ""))

    async def _handle_speech_started(self, data: dict) -> None:
        is_playing = self._is_audio_playing()
        self._is_user_speaking = True

        if self.call_id:
            CallLogger.log_event(
                self.call_id, f"Speech started, audio_playing={is_playing}")

        if self.on_interrupt:
            await self.on_interrupt()

    async def _handle_speech_stopped(self, data: dict) -> None:
        self._is_user_speaking = False

    async def _handle_user_transcription(self, data: dict) -> None:
        transcript = data.get("transcript", "")
        if transcript and self.call_id:
            CallLogger.log_user_speech(self.call_id, transcript)
            if self.on_transcript:
                await self.on_transcript(transcript, True)

    async def _handle_assistant_transcription(self, data: dict) -> None:
        transcript = data.get("transcript", "")
        if transcript and self.call_id:
            CallLogger.log_assistant_speech(self.call_id, transcript)
            if self.on_transcript:
                await self.on_transcript(transcript, False)

    async def _handle_response_done(self, data: dict) -> None:
        self._audio_delta_count = 0

        if self.on_response_done:
            await self.on_response_done()

        self._record_usage(data)

    async def _handle_audio_done(self, data: dict) -> None:
        pass

    async def _handle_function_call(self, data: dict) -> None:
        call_id = data.get("call_id", "")
        name = data.get("name", "")
        arguments_str = data.get("arguments", "{}")

        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError:
            arguments = {}

        if self.call_id:
            CallLogger.log_event(
                self.call_id, f"Tool: {name}", json.dumps(arguments))

        if name == "web_search":
            result = await web_search(arguments.get("query", ""))
        elif name == "end_call":
            result = execute_tool(name, arguments)
            if self.on_end_call:
                await self.on_end_call(arguments.get("reason", "user_request"))
        else:
            result = execute_tool(name, arguments)

        result_str = json.dumps(
            result, ensure_ascii=False) if result is not None else "No results found"

        if self.call_id:
            count = len(result) if isinstance(
                result, list) else (1 if result else 0)
            CallLogger.log_event(self.call_id, f"Tool result: {count} items")

        await self._ws.send_json({
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": result_str
            }
        })

        await self._ws.send_json({"type": "response.create"})

    async def _handle_error(self, data: dict) -> None:
        error = data.get("error", {})
        error_msg = error.get("message", "Unknown error")
        error_code = error.get("code", "unknown")
        if self.call_id:
            CallLogger.log_error(
                self.call_id, f"OpenAI: {error_code} - {error_msg}")
        if self.on_error:
            await self.on_error(Exception(error_msg))

    def _record_usage(self, data: dict) -> None:
        if not self.call_id:
            return
        usage = data.get("response", {}).get("usage", {})
        if usage:
            tokens = {
                "text_input": usage.get("input_token_details", {}).get("text_tokens", 0),
                "text_output": usage.get("output_token_details", {}).get("text_tokens", 0),
                "audio_input": usage.get("input_token_details", {}).get("audio_tokens", 0),
                "audio_output": usage.get("output_token_details", {}).get("audio_tokens", 0),
            }
            CallLogger.log_tokens(self.call_id, "voice_agent", tokens)
            analytics.record_response_agent_usage(
                self.call_id,
                text_input=tokens["text_input"],
                text_output=tokens["text_output"],
                audio_input=tokens["audio_input"],
                audio_output=tokens["audio_output"],
            )
