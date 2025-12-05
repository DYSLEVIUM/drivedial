import asyncio
import json
import logging
import uuid
from typing import Optional

from channels.generic.websocket import AsyncWebsocketConsumer

from api.providers import ProviderFactory, VoiceProvider
from api.services.call_logger import CallLogger

logger = logging.getLogger("websocket")


class MediaStreamConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream_sid: Optional[str] = None
        self.call_id: Optional[str] = None
        self.voice_provider: Optional[VoiceProvider] = None
        self._task: Optional[asyncio.Task] = None
        self._ending_call: bool = False

    async def connect(self) -> None:
        await self.accept()
        self.call_id = str(uuid.uuid4())[:8]
        CallLogger.get_logger(self.call_id)

    async def disconnect(self, close_code: int) -> None:
        if self.call_id:
            CallLogger.log_event(self.call_id, f"Disconnected: {close_code}")

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self.voice_provider:
            await self.voice_provider.disconnect()

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
                on_interrupt=self._clear_twilio_buffer,
            )
            self.voice_provider.on_end_call = self._handle_end_call
            await self.voice_provider.connect()
            await self.voice_provider.listen()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            CallLogger.log_error(self.call_id, f"Voice provider error: {e}")

    async def _send_audio(self, delta: str) -> None:
        if self.stream_sid:
            await self.send(json.dumps({
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {"payload": delta},
            }))

    async def _clear_twilio_buffer(self) -> None:
        if self.stream_sid:
            await self.send(json.dumps({"event": "clear", "streamSid": self.stream_sid}))

    async def _handle_end_call(self, reason: str) -> None:
        if self._ending_call:
            return
        self._ending_call = True
        CallLogger.log_event(self.call_id, f"Ending call: {reason}")
        await asyncio.sleep(2.0)
        await self.close()
