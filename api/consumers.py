import asyncio
import json
import logging
import uuid
from typing import Optional

from channels.generic.websocket import AsyncWebsocketConsumer

from api.providers import ProviderFactory, VoiceProvider
from api.services.call_logger import CallLogger
from api.services.call_analyzer import call_analyzer
from api.services.sse_manager import sse_manager

logger = logging.getLogger("websocket")


class MediaStreamConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream_sid: Optional[str] = None
        self.call_id: Optional[str] = None
        self.phone_number: Optional[str] = None
        self.twilio_call_sid: Optional[str] = None
        self.voice_provider: Optional[VoiceProvider] = None
        self._task: Optional[asyncio.Task] = None
        self._ending_call: bool = False
        self._customer_context: Optional[str] = None

    async def connect(self) -> None:
        await self.accept()
        self.call_id = str(uuid.uuid4())[:8]
        CallLogger.get_logger(self.call_id)
        sse_manager.start_session(self.call_id)
        
        # Print proxy link for this call session
        print(f"\n{'='*60}")
        print(f"[NEW CALL SESSION] {self.call_id}")
        print(f"[PROXY LINK] http://localhost:8000/car/{self.call_id}/")
        print(f"{'='*60}\n")

    async def disconnect(self, close_code: int) -> None:
        if self.call_id:
            CallLogger.log_event(self.call_id, f"Disconnected: {close_code}")
            sse_manager.end_session(self.call_id)

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
            
            # Analyze and save call summary in background
            if self.phone_number:
                asyncio.create_task(self._analyze_and_save_call())

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
        start_data = data.get("start", {})
        self.stream_sid = start_data.get("streamSid")
        
        # Extract custom parameters (phone number, call SID)
        custom_params = start_data.get("customParameters", {})
        self.phone_number = custom_params.get("from_number", "unknown")
        self.twilio_call_sid = custom_params.get("call_sid")
        
        CallLogger.log_event(self.call_id, f"Stream: {self.stream_sid}")
        CallLogger.log_event(self.call_id, f"Phone: {self.phone_number}")
        
        # Check if returning customer and get context
        if self.phone_number and self.phone_number != "unknown":
            self._customer_context = await call_analyzer.get_customer_context(self.phone_number)
            if self._customer_context:
                CallLogger.log_event(self.call_id, "Returning customer detected")
                print(f"\n{'='*60}")
                print(f"[RETURNING CUSTOMER] {self.phone_number}")
                print(f"[CONTEXT] {self._customer_context[:200]}...")
                print(f"{'='*60}\n")
        
        self._task = asyncio.create_task(self._connect_voice_provider())

    async def _on_media(self, data: dict) -> None:
        if self.voice_provider and self.voice_provider.is_connected:
            payload = data.get("media", {}).get("payload", "")
            if payload:
                await self.voice_provider.send_audio(payload)

    async def _connect_voice_provider(self) -> None:
        try:
            self.voice_provider = ProviderFactory.get_voice(
                call_id=self.call_id,
                customer_context=self._customer_context
            )
            self.voice_provider.set_callbacks(
                on_audio=self._send_audio,
                on_interrupt=self._clear_twilio_buffer,
            )
            self.voice_provider.on_end_call = self._handle_end_call
            self.voice_provider.on_transfer_call = self._handle_transfer_call
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

    async def _handle_transfer_call(self, reason: str, query_type: str) -> None:
        if self._ending_call:
            return
        self._ending_call = True
        CallLogger.log_event(self.call_id, f"Transferring call: {reason} - {query_type}")
        # Give time for the bot to say the transfer message before ending
        await asyncio.sleep(5.0)
        await self.close()

    async def _analyze_and_save_call(self) -> None:
        """Analyze call log and save summary to database."""
        try:
            # Small delay to ensure log file is fully written
            await asyncio.sleep(2.0)
            
            analysis = await call_analyzer.analyze_call(self.call_id, self.phone_number)
            if analysis:
                await call_analyzer.save_analysis(analysis)
                print(f"\n{'='*60}")
                print(f"[CALL ANALYSIS SAVED] {self.call_id}")
                print(f"[PHONE] {self.phone_number}")
                print(f"[OUTCOME] {analysis.get('call_outcome')}")
                print(f"[LEAD QUALITY] {analysis.get('lead_quality')}")
                print(f"[SUMMARY] {analysis.get('summary', '')[:100]}...")
                print(f"{'='*60}\n")
        except Exception as e:
            logger.error(f"Error analyzing call {self.call_id}: {e}")
