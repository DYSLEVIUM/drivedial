import asyncio
import json
import logging
import uuid
from typing import Optional

from channels.generic.websocket import AsyncWebsocketConsumer

from api.agents import AgentCoordinator
from api.providers import ProviderFactory, VoiceProvider
from api.services.call_logger import CallLogger

logger = logging.getLogger("websocket")


class MediaStreamConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream_sid: Optional[str] = None
        self.call_id: Optional[str] = None
        self.voice_provider: Optional[VoiceProvider] = None
        self.coordinator: Optional[AgentCoordinator] = None
        self._task: Optional[asyncio.Task] = None
        self._latency_tracker = None
        self._awaiting_data = False
        self._transcript_task: Optional[asyncio.Task] = None
        self._pending_context: Optional[str] = None
        self._response_in_progress = False

    async def connect(self) -> None:
        await self.accept()
        self.call_id = str(uuid.uuid4())[:8]
        CallLogger.get_logger(self.call_id)

    async def disconnect(self, close_code: int) -> None:
        if self.call_id:
            CallLogger.log_event(self.call_id, f"Disconnected: {close_code}")

        tasks_to_cancel = [self._task, self._transcript_task]
        for task in tasks_to_cancel:
            if task and not task.done():
                task.cancel()

        await asyncio.gather(*[t for t in tasks_to_cancel if t], return_exceptions=True)

        if self.voice_provider:
            await self.voice_provider.disconnect()
        if self.coordinator:
            await self.coordinator.close()

        if self.call_id:
            CallLogger.close_logger(self.call_id)

    async def receive(self, text_data: str = None, bytes_data: bytes = None) -> None:
        if not text_data:
            return

        try:
            data = json.loads(text_data)
            event = data.get("event", "")

            if event == "start":
                asyncio.create_task(self._on_start(data))
            elif event == "media":
                asyncio.create_task(self._on_media(data))
            elif event == "stop":
                CallLogger.log_event(self.call_id, "Stream stopped")
        except Exception as e:
            CallLogger.log_error(self.call_id, f"Error: {e}")

    async def _on_start(self, data: dict) -> None:
        self.stream_sid = data.get("start", {}).get("streamSid")
        CallLogger.log_event(self.call_id, f"Stream: {self.stream_sid}")
        self.coordinator = AgentCoordinator(self.call_id)
        self._task = asyncio.create_task(self._connect_voice_provider())

    async def _on_media(self, data: dict) -> None:
        if self.voice_provider and self.voice_provider.is_connected:
            payload = data.get("media", {}).get("payload", "")
            if payload:
                await self.voice_provider.send_audio(payload)

    async def _connect_voice_provider(self) -> None:
        try:
            self.voice_provider = ProviderFactory.get_voice(
                call_id=self.call_id)

            self.voice_provider.set_callbacks(
                on_audio=self._send_audio,
                on_interrupt=self._handle_interrupt,
            )
            self.voice_provider.on_transcript = self._handle_transcript
            self.voice_provider.on_response_start = self._on_response_start
            self.voice_provider.on_response_done = self._on_response_done

            self.coordinator.on_inject_context = self._inject_data_context
            self.coordinator.on_inject_rejection = self._inject_rejection

            await self.voice_provider.connect()
            await self.voice_provider.listen()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            CallLogger.log_error(self.call_id, f"Voice provider error: {e}")

    async def _send_audio(self, delta: str) -> None:
        if self.stream_sid:
            if not hasattr(self, '_audio_chunk_count'):
                self._audio_chunk_count = 0
            self._audio_chunk_count += 1
            await self.send(json.dumps({
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {"payload": delta},
            }))

    async def _handle_interrupt(self) -> None:
        CallLogger.log_event(
            self.call_id,
            "DEBUG: _handle_interrupt called",
            f"stream_sid={self.stream_sid is not None}"
        )
        if self.stream_sid:
            await self.send(json.dumps({"event": "clear", "streamSid": self.stream_sid}))
            if self.voice_provider:
                await self.voice_provider.cancel_response()

    async def _handle_transcript(self, transcript: str, is_user: bool) -> None:
        if not is_user or not transcript.strip():
            return

        if self._latency_tracker:
            self._latency_tracker.stop()
        self._latency_tracker = self.coordinator.create_latency_tracker()
        self._latency_tracker.start()

        self._transcript_task = asyncio.create_task(
            self._process_transcript_async(transcript)
        )

    async def _process_transcript_async(self, transcript: str) -> None:
        try:
            filler, intent = await self.coordinator.process_transcript(transcript)
            if intent == "fetch":
                self._awaiting_data = True
                # Send filler response while waiting for data
                # Note: Disabled filler to avoid interrupting ongoing responses
                # If needed, uncomment: await self.voice_provider.send_filler_response(filler)
        except Exception as e:
            CallLogger.log_error(
                self.call_id, f"Transcript processing error: {e}")

    async def _inject_data_context(self, data: str) -> None:
        if not data or not self.voice_provider:
            return
        # If a response is in progress, queue the context for later injection
        if self._response_in_progress:
            CallLogger.log_event(
                self.call_id,
                "DEBUG: Context queued",
                f"response_in_progress=True, data_len={len(data)}"
            )
            self._pending_context = data
            self._awaiting_data = True
            return
        CallLogger.log_event(
            self.call_id,
            "DEBUG: Context injecting",
            f"response_in_progress=False, data_len={len(data)}"
        )
        await self.voice_provider.inject_context(data)
        self._awaiting_data = False

    async def _inject_rejection(self, message: str) -> None:
        if not message or not self.voice_provider:
            return
        CallLogger.log_event(self.call_id, "Off-topic rejection sent")
        await self.voice_provider.inject_context(f"[RESPOND WITH]: {message}")

    async def _on_response_start(self) -> None:
        self._response_in_progress = True
        CallLogger.log_event(
            self.call_id,
            "DEBUG: Response START",
            f"pending_context={self._pending_context is not None}, awaiting_data={self._awaiting_data}"
        )

    async def _on_response_done(self) -> None:
        audio_chunks = getattr(self, '_audio_chunk_count', 0)
        CallLogger.log_event(
            self.call_id,
            "DEBUG: Response END",
            f"pending_context={self._pending_context is not None}, awaiting_data={self._awaiting_data}, audio_chunks_sent={audio_chunks}"
        )
        self._audio_chunk_count = 0
        self._response_in_progress = False

        if self._latency_tracker:
            latency = self._latency_tracker.stop()
            CallLogger.log_latency(self.call_id, latency)
            self._latency_tracker = None

        # Inject any pending context now that the response is complete
        if self._pending_context:
            CallLogger.log_event(
                self.call_id,
                "DEBUG: Injecting queued context"
            )
            context = self._pending_context
            self._pending_context = None
            await self.voice_provider.inject_context(context)
            self._awaiting_data = False
        elif self._awaiting_data:
            data = self.coordinator.get_pending_data()
            if data:
                CallLogger.log_event(
                    self.call_id,
                    "DEBUG: Injecting pending data"
                )
                await self.voice_provider.inject_context(data)
                self._awaiting_data = False
