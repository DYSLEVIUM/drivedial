import json
import logging
import time
from typing import Callable, Dict, Optional

import aiohttp
from django.conf import settings

from api.data.store import store
from api.providers.base import VoiceProvider
from api.services.analytics import analytics
from api.services.call_logger import CallLogger

logger = logging.getLogger("openai")


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
        self.on_response_start: Optional[Callable[[], None]] = None
        self.on_response_done: Optional[Callable[[], None]] = None

        self._current_transcript = ""
        self._is_user_speaking = False
        self._has_active_response = False
        self._is_agent_speaking = False
        self._audio_delta_count = 0
        self._current_response_id = None
        self._last_agent_audio_time: float = 0  # For echo detection
        self._last_response_done_time: float = 0  # Track when response completed
        # Echo typically arrives within 100-500ms of agent audio
        # Reduced from 1500ms to avoid flagging legitimate user speech as echo
        self._echo_window_ms: float = 600
        # Don't trigger new response within 3s of last response completing
        self._response_cooldown_ms: float = 3000

        self._turn_detection_config: Dict = {
            "type": "server_vad",
            "threshold": 0.5,
            "prefix_padding_ms": 300,
            # Increased to 1000ms to allow natural pauses in speech
            # This prevents sentences from being split mid-way
            "silence_duration_ms": 800,
            "create_response": True,
        }

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

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

        await self._configure_session()
        await self._send_initial_greeting()

    async def _configure_session(self) -> None:
        await self._ws.send_json({
            "type": "session.update",
            "session": {
                "turn_detection": self._turn_detection_config,
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "voice": self.voice,
                "instructions": self.system_prompt,
                "modalities": ["text", "audio"],
                "temperature": self.temperature,
                "max_response_output_tokens": 1000,
                "input_audio_transcription": {"model": "whisper-1"},
            }
        })

    async def _send_initial_greeting(self) -> None:
        greeting_instruction = getattr(
            settings,
            "OPENAI_GREETING_INSTRUCTION",
            "Greet the customer warmly in Hinglish. Introduce yourself from Acko Drive and ask if they are looking for a car. Be brief and natural."
        )
        await self._ws.send_json({
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"],
                "instructions": greeting_instruction
            }
        })

    async def update_turn_detection(
        self,
        threshold: Optional[float] = None,
        silence_duration_ms: Optional[int] = None,
        prefix_padding_ms: Optional[int] = None,
    ) -> None:
        if not self.is_connected:
            return

        if threshold is not None:
            self._turn_detection_config["threshold"] = threshold
        if silence_duration_ms is not None:
            self._turn_detection_config["silence_duration_ms"] = silence_duration_ms
        if prefix_padding_ms is not None:
            self._turn_detection_config["prefix_padding_ms"] = prefix_padding_ms

        await self._ws.send_json({
            "type": "session.update",
            "session": {
                "turn_detection": self._turn_detection_config,
            }
        })

        if self.call_id:
            CallLogger.log_event(self.call_id, "Turn detection updated", str(
                self._turn_detection_config))

    async def disconnect(self) -> None:
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._session and not self._session.closed:
            await self._session.close()
        self._ws = None
        self._session = None

        if self.call_id:
            CallLogger.log_event(self.call_id, "Disconnected from OpenAI")

    async def send_audio(self, payload: str) -> None:
        if not self.is_connected:
            return
        await self._ws.send_json({
            "type": "input_audio_buffer.append",
            "audio": payload
        })

    async def cancel_response(self) -> None:
        if self.call_id:
            CallLogger.log_event(
                self.call_id,
                "DEBUG: cancel_response called",
                f"connected={self.is_connected}, active={self._has_active_response}, speaking={self._is_agent_speaking}"
            )
        if self.is_connected and self._has_active_response and self._is_agent_speaking:
            await self._ws.send_json({"type": "response.cancel"})
            self._has_active_response = False
            self._is_agent_speaking = False
            if self.call_id:
                CallLogger.log_event(self.call_id, "Response CANCELLED")

    async def inject_context(self, context: str, trigger_response: bool = True) -> None:
        if not self.is_connected or not context:
            return

        # Check if we're in cooldown (response just completed)
        time_since_last_response = (
            time.time() * 1000) - self._last_response_done_time
        in_cooldown = time_since_last_response < self._response_cooldown_ms

        if self.call_id:
            CallLogger.log_event(
                self.call_id,
                "DEBUG: inject_context",
                f"active_response={self._has_active_response}, agent_speaking={self._is_agent_speaking}, trigger={trigger_response}, cooldown={in_cooldown}"
            )
        await self._ws.send_json({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "system",
                "content": [{
                    "type": "input_text",
                    "text": f"[DATA FROM SYSTEM]: {context}"
                }]
            }
        })
        if self.call_id:
            CallLogger.log_context_injection(self.call_id, context)

        # Trigger a response so the agent speaks the injected data
        # But skip if: active response, or a response just completed (cooldown)
        if trigger_response and not self._has_active_response and not in_cooldown:
            if self.call_id:
                CallLogger.log_event(
                    self.call_id, "DEBUG: Triggering response after context injection")
            await self._ws.send_json({
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"],
                    "instructions": "Respond using the data that was just provided. Be concise and natural."
                }
            })
        elif in_cooldown and self.call_id:
            CallLogger.log_event(
                self.call_id,
                "DEBUG: Skipping response trigger (cooldown)",
                f"time_since_response={time_since_last_response:.0f}ms"
            )

    async def send_filler_response(self, text: str) -> None:
        if not self.is_connected:
            return
        await self._ws.send_json({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "assistant",
                "content": [{
                    "type": "input_text",
                    "text": text
                }]
            }
        })
        await self._ws.send_json({"type": "response.create"})
        if self.call_id:
            CallLogger.log_filler(self.call_id, text)

    async def trigger_response_with_context(self, context: str) -> None:
        if not self.is_connected:
            return
        await self._ws.send_json({
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"],
                "instructions": f"Use this data to respond: {context}"
            }
        })

    async def listen(self) -> None:
        if self.call_id:
            CallLogger.log_event(self.call_id, "Voice listener started")
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(json.loads(msg.data))
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    if self.call_id:
                        CallLogger.log_error(
                            self.call_id, "OpenAI WebSocket error")
                    break
        except Exception as e:
            if self.call_id:
                CallLogger.log_error(
                    self.call_id, f"OpenAI listener error: {e}")
            if self.on_error:
                await self.on_error(e)
        finally:
            await self.disconnect()

    async def _handle_message(self, data: dict) -> None:
        msg_type = data.get("type", "")

        if msg_type == "response.audio.delta" and self.on_audio:
            self._is_agent_speaking = True
            self._audio_delta_count += 1
            self._last_agent_audio_time = time.time() * 1000  # Track for echo detection
            await self.on_audio(data.get("delta", ""))

        elif msg_type == "input_audio_buffer.speech_started":
            was_agent_speaking = self._is_agent_speaking
            time_since_agent_audio = (
                time.time() * 1000) - self._last_agent_audio_time
            is_potential_echo = time_since_agent_audio < self._echo_window_ms

            self._is_user_speaking = True
            self._current_transcript = ""
            if self.call_id:
                CallLogger.log_event(
                    self.call_id,
                    "DEBUG: Speech started",
                    f"agent_speaking={was_agent_speaking}, active_response={self._has_active_response}, echo={is_potential_echo}"
                )

            # Allow barge-in (interrupt) only if:
            # 1. Agent is currently speaking
            # 2. This is NOT likely echo (enough time has passed since agent audio)
            if was_agent_speaking and not is_potential_echo and self.on_interrupt:
                if self.call_id:
                    CallLogger.log_event(
                        self.call_id, "DEBUG: Barge-in detected, interrupting")
                await self.on_interrupt()

        elif msg_type == "input_audio_buffer.speech_stopped":
            self._is_user_speaking = False
            if self.call_id:
                CallLogger.log_event(self.call_id, "DEBUG: Speech stopped")

        elif msg_type == "conversation.item.input_audio_transcription.completed":
            transcript = data.get("transcript", "")
            if transcript:
                # Echo detection: if transcript comes shortly after agent audio, it might be echo
                time_since_agent_audio = (
                    time.time() * 1000) - self._last_agent_audio_time
                is_potential_echo = time_since_agent_audio < self._echo_window_ms

                if self.call_id:
                    if is_potential_echo:
                        CallLogger.log_event(
                            self.call_id,
                            "DEBUG: Potential echo detected",
                            f"transcript='{transcript[:30]}...', time_since_agent={time_since_agent_audio:.0f}ms"
                        )
                    CallLogger.log_user_speech(self.call_id, transcript)

                # Still pass to transcript handler - let it decide based on intent
                if self.on_transcript:
                    await self.on_transcript(transcript, True)

        elif msg_type == "response.audio_transcript.done":
            transcript = data.get("transcript", "")
            if transcript:
                if self.call_id:
                    CallLogger.log_assistant_speech(self.call_id, transcript)
                if self.on_transcript:
                    await self.on_transcript(transcript, False)

        elif msg_type == "response.created":
            self._has_active_response = True
            self._audio_delta_count = 0
            response_id = data.get("response", {}).get("id", "unknown")
            self._current_response_id = response_id
            if self.call_id:
                CallLogger.log_event(
                    self.call_id,
                    "DEBUG: Response CREATED",
                    f"id={response_id}"
                )
            if self.on_response_start:
                await self.on_response_start()

        elif msg_type == "response.done":
            response = data.get("response", {})
            status = response.get("status", "unknown")
            status_details = response.get("status_details", {})
            response_id = response.get("id", "unknown")

            if self.call_id:
                CallLogger.log_event(
                    self.call_id,
                    "DEBUG: Response DONE",
                    f"id={response_id}, status={status}, details={status_details}, audio_deltas={self._audio_delta_count}"
                )

            self._has_active_response = False
            self._is_agent_speaking = False
            self._audio_delta_count = 0
            # Track when response completed (only for completed responses, not cancelled)
            if status == "completed":
                self._last_response_done_time = time.time() * 1000
            if self.on_response_done:
                await self.on_response_done()
            self._record_usage(data)

        elif msg_type == "response.output_item.added":
            if self.call_id:
                item = data.get("item", {})
                CallLogger.log_event(
                    self.call_id,
                    "DEBUG: Output item added",
                    f"type={item.get('type')}, id={item.get('id')}"
                )

        elif msg_type == "response.output_item.done":
            if self.call_id:
                item = data.get("item", {})
                CallLogger.log_event(
                    self.call_id,
                    "DEBUG: Output item done",
                    f"type={item.get('type')}, status={item.get('status')}"
                )

        elif msg_type == "response.content_part.done":
            if self.call_id:
                part = data.get("part", {})
                CallLogger.log_event(
                    self.call_id,
                    "DEBUG: Content part done",
                    f"type={part.get('type')}"
                )

        elif msg_type == "response.audio.done":
            if self.call_id:
                CallLogger.log_event(
                    self.call_id,
                    "DEBUG: Audio stream DONE",
                    f"deltas_sent={self._audio_delta_count}"
                )
            self._is_agent_speaking = False

        elif msg_type == "rate_limits.updated":
            # Ignore rate limit updates
            pass

        elif msg_type == "session.created" or msg_type == "session.updated":
            if self.call_id:
                CallLogger.log_event(self.call_id, f"DEBUG: {msg_type}")

        elif msg_type == "conversation.item.created":
            if self.call_id:
                item = data.get("item", {})
                CallLogger.log_event(
                    self.call_id,
                    "DEBUG: Conversation item created",
                    f"type={item.get('type')}, role={item.get('role')}"
                )

        elif msg_type == "error":
            error_msg = data.get("error", {}).get("message", "Unknown error")
            error_code = data.get("error", {}).get("code", "unknown")
            if self.call_id:
                CallLogger.log_error(
                    self.call_id, f"OpenAI error: {error_code} - {error_msg}")
            if self.on_error:
                await self.on_error(Exception(error_msg))

        else:
            # Log any unhandled message types (excluding frequent delta events)
            ignored_types = [
                "input_audio_buffer.committed",
                "input_audio_buffer.cleared",
                "response.audio_transcript.delta",
                "conversation.item.input_audio_transcription.delta",
                "response.content_part.added",
            ]
            if self.call_id and msg_type not in ignored_types:
                CallLogger.log_event(
                    self.call_id,
                    "DEBUG: Unhandled msg",
                    f"type={msg_type}"
                )

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
