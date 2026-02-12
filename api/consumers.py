"""
WebSocket consumers for telephony providers.

Provider-agnostic implementation that uses the TelephonyProvider abstraction
for message parsing and formatting. The same consumer can handle multiple
telephony providers (Twilio, Ozonetel, etc.) based on configuration.
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
    for parsing and formatting messages. Subclasses can specify which
    telephony provider to use.
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

    def get_telephony_provider(self) -> TelephonyProvider:
        """
        Get the telephony provider for this consumer.
        
        Override this method or set telephony_provider_name for custom behavior.
        """
        if self.telephony_provider_name:
            return ProviderFactory.get_telephony(self.telephony_provider_name)
        
        # Try to determine from route
        route_name = self.scope.get("url_route", {}).get("kwargs", {}).get("provider", "")
        if route_name:
            return ProviderFactory.get_telephony_by_route(route_name)
        
        # Default to configured provider
        return ProviderFactory.get_telephony()

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
        
        # Start token tracking for this call
        token_tracker.start_call(self.call_id)
        
        # Print proxy link for this call session
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
            # Analyze and save call summary (this may also track tokens)
            if self.phone_number:
                # Run synchronously to ensure tokens are tracked before final analysis
                await self._analyze_and_save_call()
            
            # Finalize token tracking and log TOKEN_ANALYSIS_FINAL
            self._log_token_analysis_final()
            
            CallLogger.close_logger(self.call_id)
            
    def _log_token_analysis_final(self) -> None:
        """Finalize token tracking and log the comprehensive analysis."""
        if not self.call_id:
            return
        
        # End tracking and get analysis
        analysis = token_tracker.end_call(self.call_id)
        if not analysis:
            return
        
        # Log the final analysis to the call log file
        analysis_string = analysis.to_log_string()
        CallLogger.log_token_analysis_final(self.call_id, analysis_string)
        
        # Print summary to console
        print(f"\n{'='*60}")
        print(f"[TOKEN ANALYSIS] {self.call_id}")
        print(f"Total Input: {analysis.total_input_tokens:,} tokens")
        print(f"Total Output: {analysis.total_output_tokens:,} tokens")
        print(f"Cached: {analysis.total_cached_tokens:,} tokens")
        print(f"Total Cost: ${float(analysis.total_cost_usd):.6f}")
        print(f"{'='*60}\n")
        
        # Cleanup memory
        token_tracker.cleanup_call(self.call_id)

    async def receive(self, text_data: str = None, bytes_data: bytes = None) -> None:

        if not text_data:
            return

        try:
            data = json.loads(text_data)
            event_type = self.telephony_provider.parse_message(data)

            if event_type == "start":
                asyncio.create_task(self._on_start(data))
            elif event_type == "media":
                asyncio.create_task(self._on_media(data))
            elif event_type == "stop":
                CallLogger.log_event(self.call_id, "Stream stopped")
        except Exception as e:
            CallLogger.log_error(self.call_id, f"Error: {e}")

    async def _on_start(self, data: dict) -> None:
        """Handle stream start event."""
        start_msg = self.telephony_provider.parse_start_message(data)
        
        self.stream_id = start_msg.stream_id
        self.provider_call_id = start_msg.call_id
        self.phone_number = start_msg.phone_number or start_msg.custom_params.get("from_number", "unknown")
        
        CallLogger.log_event(self.call_id, f"Stream: {self.stream_id}")
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
        """Handle incoming audio from telephony provider."""
        # For providers that don't send explicit start, initialize on first media
        if not self._first_media_received:
            self._first_media_received = True
            if not self.stream_id:
                # Extract stream ID from first media message
                start_msg = self.telephony_provider.parse_start_message(data)
                self.stream_id = start_msg.stream_id
                self.provider_call_id = start_msg.call_id
                CallLogger.log_event(self.call_id, f"Stream (from media): {self.stream_id}")
                self._task = asyncio.create_task(self._connect_voice_provider())
        
        if self.voice_provider and self.voice_provider.is_connected:
            audio_msg = self.telephony_provider.parse_audio_message(data)
            if audio_msg and audio_msg.payload:
                await self.voice_provider.send_audio(audio_msg.payload)

    async def _connect_voice_provider(self) -> None:
        """Connect to the voice AI provider."""
        try:
            self.voice_provider = ProviderFactory.get_voice(
                call_id=self.call_id,
                customer_context=self._customer_context
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

    async def _send_audio(self, audio_payload: str) -> None:
        """Send audio back to telephony provider."""
        if self.stream_id:
            message = self.telephony_provider.format_audio_message(
                self.stream_id, 
                audio_payload
            )
            await self.send(json.dumps(message))

    async def _clear_buffer(self) -> None:
        """Clear audio buffer (for handling interruptions)."""
        if self.stream_id:
            message = self.telephony_provider.format_clear_message(self.stream_id)
            await self.send(json.dumps(message))

    async def _handle_end_call(self, reason: str) -> None:
        """Handle call end request from AI."""
        if self._ending_call:
            return
        self._ending_call = True
        CallLogger.log_event(self.call_id, f"Ending call: {reason}")
        
        # Try to send disconnect command if supported
        disconnect_msg = self.telephony_provider.format_disconnect_message(self.stream_id)
        if disconnect_msg:
            await self.send(json.dumps(disconnect_msg))
        
        await asyncio.sleep(2.0)
        await self.close()

    async def _handle_transfer_call(self, reason: str, query_type: str) -> None:
        """Handle call transfer request from AI."""
        if self._ending_call:
            return
        self._ending_call = True
        CallLogger.log_event(self.call_id, f"Transferring call: {reason} - {query_type}")
        
        # Try to send disconnect command to return to IVR
        disconnect_msg = self.telephony_provider.format_disconnect_message(self.stream_id)
        if disconnect_msg:
            await self.send(json.dumps(disconnect_msg))
        
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


class MediaStreamConsumer(BaseMediaStreamConsumer):
    """
    Default media stream consumer using configured telephony provider.
    
    This maintains backward compatibility with existing Twilio integration
    while supporting the new provider-agnostic architecture.
    """
    pass


class TwilioMediaStreamConsumer(BaseMediaStreamConsumer):
    """Twilio-specific media stream consumer."""
    telephony_provider_name = "twilio"


class OzonetelMediaStreamConsumer(BaseMediaStreamConsumer):
    """Ozonetel-specific media stream consumer."""
    telephony_provider_name = "ozonetel"
