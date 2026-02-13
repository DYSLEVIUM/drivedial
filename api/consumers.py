"""
WebSocket consumers for telephony providers.

Provider-agnostic implementation that uses the TelephonyProvider abstraction
for message parsing and formatting. The same consumer can handle multiple
telephony providers (Twilio, Ozonetel, etc.) based on configuration.

Race-condition guard:
  VoBiz (and some other providers) may send the first 'media' event BEFORE
  the 'start' event reaches the consumer, or both arrive so close together
  that asyncio.create_task() for _on_start hasn't executed yet when the
  first _on_media runs.  Both code paths call _connect_voice_provider(),
  resulting in TWO voice-provider sessions (TWO Gemini WebSockets) running
  simultaneously — doubling all audio output and causing garbled playback.

  Fix: _connect_voice_provider is guarded by a boolean flag
  (_voice_provider_connecting).  Only the FIRST caller proceeds;
  subsequent callers return immediately.
"""

import asyncio
import json
import logging
import uuid
from typing import Optional

from channels.generic.websocket import AsyncWebsocketConsumer

from api.providers import ProviderFactory, VoiceProvider
from api.providers.base import TelephonyProvider
from api.services.call_logger import CallLogger
from api.services.call_analyzer import call_analyzer
from api.services.sse_manager import sse_manager
from api.services.token_tracker import token_tracker

logger = logging.getLogger("websocket")


class BaseMediaStreamConsumer(AsyncWebsocketConsumer):
    """
    Base WebSocket consumer for telephony media streams.

    This is provider-agnostic and uses the TelephonyProvider abstraction
    for message parsing and formatting.
    """

    # Override in subclass or set via route
    telephony_provider_name: Optional[str] = None


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream_id: Optional[str] = None
        self.call_id: Optional[str] = None
        self.phone_number: Optional[str] = None
        self.provider_call_id: Optional[str] = None

        self.voice_provider: Optional[VoiceProvider] = None
        self.telephony_provider: Optional[TelephonyProvider] = None

        self._task: Optional[asyncio.Task] = None
        self._ending_call: bool = False
        self._customer_context: Optional[str] = None
        self._first_media_received: bool = False

        # ── voice provider guard ──────────────────────────────────
        # Prevents duplicate voice-provider creation when both
        # _on_start and _on_media race to call _connect_voice_provider.
        self._voice_provider_connecting: bool = False

        # ── diagnostics ───────────────────────────────────────────
        self._media_in_count: int = 0
        self._media_out_count: int = 0

    # ──────────────────────────────────────────────────────────────
    #  Provider resolution
    # ──────────────────────────────────────────────────────────────

    def get_telephony_provider(self) -> TelephonyProvider:
        if self.telephony_provider_name:
            return ProviderFactory.get_telephony(self.telephony_provider_name)

        route_name = (
            self.scope.get("url_route", {}).get("kwargs", {}).get("provider", "")
        )
        if route_name:
            return ProviderFactory.get_telephony_by_route(route_name)

        return ProviderFactory.get_telephony()

    # ──────────────────────────────────────────────────────────────
    #  Lifecycle
    # ──────────────────────────────────────────────────────────────

    async def connect(self) -> None:
        await self.accept()
        self.call_id = str(uuid.uuid4())[:8]
        self.telephony_provider = self.get_telephony_provider()
        CallLogger.get_logger(self.call_id)
        CallLogger.log_event(
            self.call_id,
            f"Connected via {self.telephony_provider.provider_name}"
        )
        sse_manager.start_session(self.call_id)
        token_tracker.start_call(self.call_id)

        print(f"\n{'='*60}")
        print(f"[NEW CALL SESSION] {self.call_id}")
        print(f"[PROVIDER] {self.telephony_provider.provider_name}")
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
            print(
                f"[WS-DIAG] {self.call_id} | "
                f"media_in={self._media_in_count} "
                f"media_out={self._media_out_count}"
            )

            if self.phone_number:
                await self._analyze_and_save_call()

            self._log_token_analysis_final()
            CallLogger.close_logger(self.call_id)

    # ──────────────────────────────────────────────────────────────
    #  Token tracking
    # ──────────────────────────────────────────────────────────────

    def _log_token_analysis_final(self) -> None:
        if not self.call_id:
            return

        analysis = token_tracker.end_call(self.call_id)
        if not analysis:
            return

        analysis_string = analysis.to_log_string()
        CallLogger.log_token_analysis_final(self.call_id, analysis_string)

        print(f"\n{'='*60}")
        print(f"[TOKEN ANALYSIS] {self.call_id}")
        print(f"Total Input: {analysis.total_input_tokens:,} tokens")
        print(f"Total Output: {analysis.total_output_tokens:,} tokens")
        print(f"Cached: {analysis.total_cached_tokens:,} tokens")
        print(f"Total Cost: ${float(analysis.total_cost_usd):.6f}")
        print(f"{'='*60}\n")

        token_tracker.cleanup_call(self.call_id)

    # ──────────────────────────────────────────────────────────────
    #  WebSocket receive (from telephony)
    # ──────────────────────────────────────────────────────────────

    async def receive(self, text_data: str = None, bytes_data: bytes = None) -> None:
        if not text_data:
            return

        try:
            data = json.loads(text_data)
            event_type = self.telephony_provider.parse_message(data)

            if event_type == "start":
                asyncio.create_task(self._on_start(data))
            elif event_type == "media":
                # Direct await (not create_task) to preserve strict ordering
                await self._on_media(data)
            elif event_type == "stop":
                CallLogger.log_event(self.call_id, "Stream stopped")
            # VoBiz ack events — just ignore
            elif event_type in ("playedStream", "clearedAudio"):
                pass
        except Exception as e:
            CallLogger.log_error(self.call_id, f"Error: {e}")

    # ──────────────────────────────────────────────────────────────
    #  Event handlers
    # ──────────────────────────────────────────────────────────────

    async def _on_start(self, data: dict) -> None:
        """Handle stream start event."""
        start_msg = self.telephony_provider.parse_start_message(data)

        self.stream_id = start_msg.stream_id
        self.provider_call_id = start_msg.call_id
        self.phone_number = (
            start_msg.phone_number
            or start_msg.custom_params.get("from_number", "unknown")
        )

        CallLogger.log_event(self.call_id, f"Stream: {self.stream_id}")
        CallLogger.log_event(self.call_id, f"Phone: {self.phone_number}")

        if self.phone_number and self.phone_number != "unknown":
            self._customer_context = await call_analyzer.get_customer_context(
                self.phone_number
            )
            if self._customer_context:
                CallLogger.log_event(self.call_id, "Returning customer detected")
                print(f"\n{'='*60}")
                print(f"[RETURNING CUSTOMER] {self.phone_number}")
                print(f"[CONTEXT] {self._customer_context[:200]}...")
                print(f"{'='*60}\n")

        self._task = asyncio.create_task(self._connect_voice_provider())

    async def _on_media(self, data: dict) -> None:
        """Handle incoming audio from telephony provider."""
        # Late-start initialisation (providers that don't send 'start')
        if not self._first_media_received:
            self._first_media_received = True
            if not self.stream_id:
                start_msg = self.telephony_provider.parse_start_message(data)
                self.stream_id = start_msg.stream_id
                self.provider_call_id = start_msg.call_id
                CallLogger.log_event(
                    self.call_id, f"Stream (from media): {self.stream_id}"
                )
                self._task = asyncio.create_task(self._connect_voice_provider())

        self._media_in_count += 1

        # ── forward to voice provider ───────────────────────────
        if self.voice_provider and self.voice_provider.is_connected:
            audio_msg = self.telephony_provider.parse_audio_message(data)
            if audio_msg and audio_msg.payload:
                await self.voice_provider.send_audio(audio_msg.payload)

    async def _connect_voice_provider(self) -> None:
        """
        Connect to the voice AI provider.  **Idempotent** — safe to call
        from both _on_start and _on_media; only the first caller proceeds.
        """
        # ── guard: prevent duplicate sessions ─────────────────────
        if self._voice_provider_connecting:
            logger.info(
                f"[{self.call_id}] Voice provider already connecting — "
                f"skipping duplicate"
            )
            return
        self._voice_provider_connecting = True

        try:
            self.voice_provider = ProviderFactory.get_voice(
                call_id=self.call_id,
                customer_context=self._customer_context,
            )
            self.voice_provider.set_callbacks(
                on_audio=self._send_audio,
                on_interrupt=self._clear_buffer,
            )
            self.voice_provider.on_end_call = self._handle_end_call
            self.voice_provider.on_transfer_call = self._handle_transfer_call
            await self.voice_provider.connect()
            await self.voice_provider.listen()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            CallLogger.log_error(self.call_id, f"Voice provider error: {e}")
        finally:
            self._voice_provider_connecting = False

    # ──────────────────────────────────────────────────────────────
    #  Audio output  (AI → telephony)
    # ──────────────────────────────────────────────────────────────

    async def _send_audio(self, audio_payload: str) -> None:
        """Send audio back to telephony provider."""
        if self.stream_id:
            self._media_out_count += 1
            message = self.telephony_provider.format_audio_message(
                self.stream_id, audio_payload
            )
            await self.send(json.dumps(message))

    async def _clear_buffer(self) -> None:
        """Clear audio buffer (for handling interruptions)."""
        if self.stream_id:
            message = self.telephony_provider.format_clear_message(self.stream_id)
            await self.send(json.dumps(message))

    # ──────────────────────────────────────────────────────────────
    #  Call control
    # ──────────────────────────────────────────────────────────────

    async def _handle_end_call(self, reason: str) -> None:
        if self._ending_call:
            return
        self._ending_call = True
        CallLogger.log_event(self.call_id, f"Ending call: {reason}")

        disconnect_msg = self.telephony_provider.format_disconnect_message(
            self.stream_id
        )
        if disconnect_msg:
            await self.send(json.dumps(disconnect_msg))

        await asyncio.sleep(2.0)
        await self.close()

    async def _handle_transfer_call(self, reason: str, query_type: str) -> None:
        if self._ending_call:
            return
        self._ending_call = True
        CallLogger.log_event(
            self.call_id, f"Transferring call: {reason} - {query_type}"
        )

        disconnect_msg = self.telephony_provider.format_disconnect_message(
            self.stream_id
        )
        if disconnect_msg:
            await self.send(json.dumps(disconnect_msg))

        await asyncio.sleep(5.0)
        await self.close()

    async def _analyze_and_save_call(self) -> None:
        try:
            await asyncio.sleep(2.0)

            analysis = await call_analyzer.analyze_call(
                self.call_id, self.phone_number
            )
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


# ═════════════════════════════════════════════════════════════════
#  Provider-specific subclasses
# ═════════════════════════════════════════════════════════════════


class MediaStreamConsumer(BaseMediaStreamConsumer):
    """Default media stream consumer using configured telephony provider."""
    pass


class TwilioMediaStreamConsumer(BaseMediaStreamConsumer):
    """Twilio-specific consumer. No echo guard needed (Twilio doesn't echo)."""
    telephony_provider_name = "twilio"


class OzonetelMediaStreamConsumer(BaseMediaStreamConsumer):
    """Ozonetel-specific consumer."""
    telephony_provider_name = "ozonetel"


class VoBizMediaStreamConsumer(BaseMediaStreamConsumer):
    """VoBiz-specific media stream consumer."""
    telephony_provider_name = "vobiz"
