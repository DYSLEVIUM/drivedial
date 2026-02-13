"""
Gemini Voice Provider — Google GenAI SDK (Live API).

Architecture:
                                                      ┌────────────────┐
  Consumer.send_audio(g711_ulaw) ────────────────────▸│  _audio_in_q   │
                                                      │  maxsize=50    │
                                                      └───────┬────────┘
                                                              │
                                                              ▼
                                                    ┌─────────────────┐
                                                    │ _send_audio_loop│
                                                    │ send_realtime_  │
                                                    │ input(audio=…)  │
                                                    └────────┬────────┘
                                                             │
                                                             ▼
                                                    ╔════════════════╗
                                                    ║  Gemini Live   ║
                                                    ║  API (WS)      ║
                                                    ╚════════╤═══════╝
                                                             │
                                                             ▼
                                                    ┌─────────────────┐
                                                    │ _receive_loop   │
                                                    │ session.receive │
                                                    └────┬───────┬────┘
                                                         │       │
               pcm8k (non-blocking put) ─────────────────┘       └──── tool_call
                                                         │                   │
                                                         ▼              start keyboard
                                                    ┌────────────────┐      │
                                                    │  _audio_out_q  │      │
                                                    │  RAW PCM 8kHz  │      │
                                                    │  (no maxsize)  │      │
                                                    └───────┬────────┘      │
                                                            │               │
                                                            ▼               │
                                                    ┌─────────────────────┐ │
                                                    │  _play_audio_loop   │ │
                                                    │                     │ │
                                                    │  Voice in queue?    │ │
                                                    │  YES → mix(pcm)    │ │
                                                    │  NO  → idle_chunk  │◂┘ keyboard in
                                                    │        (20ms tmout)│    idle frames
                                                    │  + office hum      │
                                                    │  + keyboard (opt)  │
                                                    │  → pcm→μ-law      │──▸ Telephony
                                                    └─────────────────────┘

Soundscape mixing (see soundscape.py):
  All mixing is done in LINEAR PCM16 at 8 kHz, BEFORE μ-law encoding.
  This prevents non-linear distortion artifacts.

  Pipeline:  Gemini PCM24k → pcm24k_to_pcm8k() → _audio_out_q
             → mixer.mix() [+office +keyboard] → pcm8k_to_g711_ulaw()
             → on_audio() → Telephony

  Continuous ambience: _ambient_fill_loop runs independently at 20ms
  intervals.  After a 60ms grace period (no voice chunks), it sends
  ambient-only frames to telephony.  During voice playback, the grace
  period keeps it silent — zero interference.  During tool calls,
  keyboard_active=True makes idle frames include click sounds.

Interruption flow (< 50ms):
  1. Gemini sends server_content.interrupted = True
  2. _receive_loop sees it IMMEDIATELY (not blocked on telephony send)
  3. _audio_out_q is cleared (discards un-sent PCM chunks)
  4. on_interrupt() sends "clear" to Twilio (discards already-sent buffer)

VAD (Voice Activity Detection) configuration:
  - start_of_speech_sensitivity = HIGH → catches quiet telephony speech
  - end_of_speech_sensitivity   = LOW  → allows natural pauses
  - prefix_padding_ms           = 150  → 150ms of speech before commit
  - silence_duration_ms         = 300  → 300ms silence before end-of-speech
  - turn_coverage = ONLY_ACTIVITY      → strips silence from context

SDK methods used (per Google docs — NO deprecated send()):
  - send_realtime_input(audio=…)       → streaming audio (low-latency, VAD)
  - send_client_content(turns=…)       → greeting text (turn-based, once)
  - send_tool_response(function_responses=…) → tool results

Audio formats:
  - Telephony  → g711_ulaw  @ 8 kHz
  - Gemini in  → PCM16      @ 16 kHz
  - Gemini out → PCM16      @ 24 kHz
  - Queue      → PCM16      @ 8 kHz  (raw, for linear-space mixing)

Reference:
  https://ai.google.dev/gemini-api/docs/live?example=mic-stream
  https://ai.google.dev/gemini-api/docs/live-guide
  https://ai.google.dev/gemini-api/docs/live-tools
"""

import asyncio
import audioop
import base64
import json
import logging
import os
import time
import traceback
import uuid
from typing import Any, Callable, Optional

from google import genai
from google.genai import types

from api.data.store import store
from api.data.inventory import generate_car_url
from api.providers.base import VoiceProvider
from api.providers.soundscape import SoundscapeMixer
from api.services.sse_manager import sse_manager
from api.providers.prompts import prompt_6
from api.services.analytics import analytics
from api.services.call_logger import CallLogger
from api.services.token_tracker import token_tracker, ModelType
from config import settings

logger = logging.getLogger("gemini")

# Suppress noisy third-party logs
for _name in ("websockets", "websockets.client",
              "google_genai", "google_genai.types"):
    logging.getLogger(_name).setLevel(logging.ERROR)


# ═══════════════════════════════════════════════════════════════════════════════
# Audio Conversion  (g711 μ-law 8 kHz ⇄ PCM16 16/24 kHz)
#
# All conversions use Python's built-in `audioop` module (C-optimized,
# ITU-T G.711 compliant).  This replaces the previous hand-rolled per-sample
# Python loops that were:
#   • Slow — ~24,000 Python iterations per second of audio
#   • Fragile — subtle encoding errors causing distortion
#   • Stateless — clicks at chunk boundaries due to no ratecv state
#
# `audioop.ratecv` maintains internal filter state between calls,
# eliminating inter-chunk discontinuities when the same state object
# is reused.  The GeminiVoiceProvider stores these states as instance
# variables (_upsample_state, _downsample_state).
# ═══════════════════════════════════════════════════════════════════════════════

# Gain factor for telephony → Gemini.
# μ-law decoded speech is typically ±1000-5000; Gemini VAD expects
# microphone-level audio (±5000-15000).  4× gain bridges the gap.
TELEPHONY_GAIN = 4


def g711_ulaw_to_pcm16k(ulaw_b64: str, upsample_state=None):
    """g711 μ-law 8 kHz → PCM16 16 kHz  (decode + gain + upsample).

    Args:
        ulaw_b64:       Base64-encoded μ-law audio
        upsample_state: ratecv state from the previous call (or None for first)

    Returns:
        (pcm16k_bytes, new_upsample_state)
    """
    raw = base64.b64decode(ulaw_b64)
    if not raw:
        return b"", upsample_state

    # μ-law → linear PCM16 at 8 kHz  (C-optimized, ITU-T G.711 exact)
    pcm8k = audioop.ulaw2lin(raw, 2)

    # Apply telephony gain  (audioop.mul is C-level, no Python loop)
    pcm8k = audioop.mul(pcm8k, 2, TELEPHONY_GAIN)

    # Upsample 8 kHz → 16 kHz  (with filter state for smooth boundaries)
    pcm16k, new_state = audioop.ratecv(pcm8k, 2, 1, 8000, 16000, upsample_state)
    return pcm16k, new_state


def pcm24k_to_pcm8k(pcm24k: bytes, downsample_state=None):
    """PCM16 24 kHz → PCM16 8 kHz  (downsample ×3, C-optimized).

    Returns raw PCM bytes — NO μ-law encoding.
    Soundscape mixing happens in linear PCM space before encoding.

    Args:
        pcm24k:           Raw PCM16 bytes at 24 kHz
        downsample_state: ratecv state from the previous call (or None)

    Returns:
        (pcm8k_bytes, new_downsample_state)
    """
    if len(pcm24k) < 6:  # need at least 3 samples (6 bytes)
        return b"", downsample_state

    pcm8k, new_state = audioop.ratecv(pcm24k, 2, 1, 24000, 8000, downsample_state)
    return pcm8k, new_state


def pcm8k_to_g711_ulaw(pcm8k: bytes) -> str:
    """PCM16 8 kHz → g711 μ-law base64  (encode only, no resampling).

    Called AFTER all linear-space mixing (voice + soundscape).
    Uses audioop.lin2ulaw — C-optimized, ITU-T G.711 exact.
    """
    if not pcm8k:
        return ""
    ulaw = audioop.lin2ulaw(pcm8k, 2)
    return base64.b64encode(ulaw).decode("ascii")


def pcm24k_to_g711_ulaw(pcm24k: bytes, downsample_state=None):
    """PCM16 24 kHz → g711 μ-law 8 kHz  (downsample + encode).

    Convenience wrapper — combines pcm24k_to_pcm8k + pcm8k_to_g711_ulaw.

    Returns:
        (ulaw_b64_str, new_downsample_state)
    """
    pcm8k, new_state = pcm24k_to_pcm8k(pcm24k, downsample_state)
    return pcm8k_to_g711_ulaw(pcm8k), new_state


# ═══════════════════════════════════════════════════════════════════════════════
# Tool definitions & execution
# ═══════════════════════════════════════════════════════════════════════════════

def _execute_tool(name: str, args: dict) -> Any:
    """Run a tool / function call and return its result."""
    if name == "search_cars":
        return store.search(
            budget_min=args.get("budget_min"),
            budget_max=args.get("budget_max"),
            brand=args.get("brand"),
            model=args.get("model"),
            fuel_type=args.get("fuel_type"),
            transmission=args.get("transmission"),
            sort_by="closest_to_budget",
            prefer_express=True,
        )
    if name == "get_car_details":
        return store.get_car(args.get("car_id", ""))
    if name == "end_call":
        return {"status": "ending", "reason": args.get("reason", "user_request")}
    if name == "transfer_to_agent":
        return {"status": "transferring", "reason": args.get("reason"),
                "query_type": args.get("query_type")}
    if name == "update_car_display":
        slug = args.get("car_slug", "")
        color = args.get("color")
        url = generate_car_url(slug, color)
        if url:
            return {"url": url, "car_slug": slug, "color": color,
                    "status": "display_updated"}
        return {"error": "Car not found"}
    return None


def _build_tools() -> list:
    """Build the Gemini function-declaration tools list."""
    S = genai.types.Schema
    T = genai.types.Type
    return [
        types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name="search_cars",
                description=(
                    "Search car inventory. Budget: '20 lakh' = 2000000. "
                    "When user says 'budget is X lakh', set budget_min=70%"
                    " of X, budget_max=X."
                ),
                parameters=S(type=T.OBJECT, properties={
                    "budget_min":   S(type=T.INTEGER),
                    "budget_max":   S(type=T.INTEGER),
                    "brand":        S(type=T.STRING),
                    "model":        S(type=T.STRING),
                    "fuel_type":    S(type=T.STRING),
                    "transmission": S(type=T.STRING),
                }),
            ),
            types.FunctionDeclaration(
                name="update_car_display",
                description="Show a car to the customer on their screen.",
                parameters=S(type=T.OBJECT, properties={
                    "car_slug": S(type=T.STRING),
                    "color":    S(type=T.STRING),
                }, required=["car_slug"]),
            ),
            types.FunctionDeclaration(
                name="end_call",
                description=(
                    "End the call when user says goodbye / bye / hang up"
                ),
                parameters=S(type=T.OBJECT, properties={
                    "reason": S(type=T.STRING),
                }, required=["reason"]),
            ),
            types.FunctionDeclaration(
                name="transfer_to_agent",
                description=(
                    "Transfer to human agent when user explicitly requests it"
                ),
                parameters=S(type=T.OBJECT, properties={
                    "reason":     S(type=T.STRING),
                    "query_type": S(type=T.STRING),
                }, required=["reason"]),
            ),
        ])
    ]


def _build_system_prompt(customer_context: Optional[str] = None) -> str:
    """Build full system prompt with inventory context."""
    base = prompt_6.system_prompt
    ctx = store.get_context_summary()
    prompt = base.replace(
        "CONTEXT: You are selling cars.", f"CONTEXT: {ctx}"
    ).replace(
        "CONTEXT: You are selling cars "
        "(Swift, Honda City, XUV700, Creta, Baleno).",
        f"CONTEXT: {ctx}",
    )
    if customer_context:
        prompt += f"\n\n### RETURNING CUSTOMER\n{customer_context}"
    return prompt


# ═══════════════════════════════════════════════════════════════════════════════
# GeminiVoiceProvider
# ═══════════════════════════════════════════════════════════════════════════════

class GeminiVoiceProvider(VoiceProvider):
    """
    Voice provider using the Google GenAI Live API.

    Three concurrent tasks run inside listen():
      1. _send_audio_loop   — reads _audio_in_q  → send_realtime_input
      2. _receive_loop      — session.receive()  → _audio_out_q / tool calls
      3. _play_audio_loop   — reads _audio_out_q → on_audio (telephony)
      4. _ambient_fill_loop — sends office hum when voice is idle

    This decoupled architecture guarantees:
      • The receive loop is NEVER blocked on telephony I/O.
      • Interruption signals are processed within one event-loop tick.
      • The output queue can be cleared instantly, discarding un-sent audio.
    """

    # ── construction ──────────────────────────────────────────────────────

    def __init__(
        self,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        voice: Optional[str] = None,
        call_id: Optional[str] = None,
        customer_context: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "")
        self.system_prompt = (
            system_prompt or _build_system_prompt(customer_context)
        )
        self.voice = voice or getattr(settings, "GEMINI_VOICE", "Kore")
        self.model = model or getattr(
            settings, "GEMINI_MODEL", "gemini-2.0-flash-live-001"
        )
        self.call_id = call_id
        self._customer_context = customer_context

        # session state
        self._session = None
        self._connected = False
        self._running = False

        # ── queues ────────────────────────────────────────────────────
        # INPUT queue: telephony → Gemini  (bounded = back-pressure)
        # 50 chunks × 20ms = 1 second buffer — handles network jitter
        self._audio_in_q: asyncio.Queue = asyncio.Queue(maxsize=50)
        # OUTPUT queue: Gemini → telephony (unbounded = instant put)
        self._audio_out_q: asyncio.Queue = asyncio.Queue()

        # callbacks (set by consumer)
        self.on_transcript: Optional[Callable] = None
        self.on_response_done: Optional[Callable] = None
        self.on_end_call: Optional[Callable] = None
        self.on_transfer_call: Optional[Callable] = None

        # stats
        self._chunks_sent = 0
        self._chunks_recv = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cached_tokens = 0

        # per-modality token accumulators (from usage_metadata)
        self._input_text_tokens = 0
        self._input_audio_tokens = 0
        self._output_text_tokens = 0
        self._output_audio_tokens = 0
        self._tool_use_tokens = 0
        self._thoughts_tokens = 0
        self._usage_count = 0  # number of usage_metadata messages received

        # cross-task timing (for stale-session detection)
        self._last_audio_sent_time: float = 0.0
        self._last_response_time: float = 0.0
        self._stale_warned: bool = False
        # timestamp of last voice chunk played — ambient loop uses this
        self._last_voice_play_ts: float = 0.0

        # audioop.ratecv filter state — maintains continuity between
        # audio chunks to eliminate inter-chunk clicks/pops.
        self._upsample_state = None     # 8 kHz → 16 kHz  (send path)
        self._downsample_state = None   # 24 kHz → 8 kHz  (receive path)

        # transcript accumulation buffers
        # Gemini streams transcriptions word-by-word; we accumulate
        # fragments and flush complete utterances to CallLogger.
        self._user_transcript_buf: str = ""
        self._assistant_transcript_buf: str = ""

        # soundscape mixer (office ambience + keyboard clicks)
        sounds_dir = os.path.join(
            str(settings.BASE_DIR), "api", "providers", "sounds"
        )
        self._soundscape: Optional[SoundscapeMixer] = SoundscapeMixer.create(
            office_path=os.path.join(sounds_dir, "office_sound.wav"),
            keyboard_path=os.path.join(sounds_dir, "keyboard.wav"),
        )

    # ── VoiceProvider interface ───────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._connected and self._session is not None

    async def connect(self) -> None:
        """Validate config.  Real connection happens in listen()."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")
        self._connected = True
        print(f"\n{'='*60}")
        print(f"[GEMINI] Model : {self.model}")
        print(f"[GEMINI] Voice : {self.voice}")
        print(f"{'='*60}\n")

    async def disconnect(self) -> None:
        self._running = False
        self._connected = False
        self._session = None
        # Stop keyboard if still active
        if self._soundscape:
            self._soundscape.stop_keyboard()
        # Flush any remaining transcript fragments
        self._flush_all_transcripts()
        if self.call_id:
            CallLogger.log_event(self.call_id, "Disconnected from Gemini")
            analytics.end_call(self.call_id)
            self._record_final_usage()
        print(
            f"[GEMINI] Disconnected "
            f"(sent={self._chunks_sent} recv={self._chunks_recv})"
        )

    # ── transcript accumulation ──────────────────────────────────────────

    def _flush_user_transcript(self) -> None:
        """Flush accumulated user transcript fragments as one log entry."""
        text = self._user_transcript_buf.strip()
        if text and self.call_id:
            CallLogger.log_user_speech(self.call_id, text)
        self._user_transcript_buf = ""

    def _flush_assistant_transcript(self) -> None:
        """Flush accumulated assistant transcript fragments as one log entry."""
        text = self._assistant_transcript_buf.strip()
        if text and self.call_id:
            CallLogger.log_assistant_speech(self.call_id, text)
        self._assistant_transcript_buf = ""

    def _flush_all_transcripts(self) -> None:
        """Flush both transcript buffers (e.g. on turn complete / disconnect)."""
        self._flush_user_transcript()
        self._flush_assistant_transcript()

    async def send_audio(self, payload: str) -> None:
        """Accept g711_ulaw base64 from telephony and queue for Gemini."""
        if not self._running or not self._session:
            return
        try:
            pcm, self._upsample_state = g711_ulaw_to_pcm16k(
                payload, self._upsample_state
            )

            # ── diagnostic: audio level monitoring ─────────────────
            # Log on first chunk and every 250 chunks (~5 seconds)
            should_log = (
                self._chunks_sent == 0
                or (self._chunks_sent > 0
                    and self._chunks_sent % 250 == 0)
            )
            if should_log and len(pcm) >= 4:
                rms = audioop.rms(pcm, 2)
                mn = audioop.minmax(pcm, 2)[0]
                mx = audioop.minmax(pcm, 2)[1]
                n = len(pcm) // 2
                label = (
                    "First" if self._chunks_sent == 0
                    else f"#{self._chunks_sent}"
                )
                print(
                    f"[GEMINI] [audio-diag] {label} chunk: "
                    f"{len(pcm)}B ({n} samples), "
                    f"min={mn} max={mx} rms={rms}"
                )
                if rms < 50:
                    print(
                        f"[GEMINI] ⚠ AUDIO LOW: RMS={rms} — "
                        f"appears to be silence/near-silence"
                    )

            msg = {"data": pcm, "mime_type": "audio/pcm;rate=16000"}
            try:
                self._audio_in_q.put_nowait(msg)
            except asyncio.QueueFull:
                try:
                    self._audio_in_q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                self._audio_in_q.put_nowait(msg)
        except Exception as e:
            if "closed" not in str(e).lower():
                logger.error(f"[GEMINI] send_audio error: {e}")
            else:
                print(
                    f"[GEMINI] send_audio: connection closed, "
                    f"dropping audio"
                )

    async def cancel_response(self) -> None:
        pass  # VAD handles interruptions natively

    # ── main session loop ─────────────────────────────────────────────────

    async def listen(self) -> None:
        """Connect to Gemini Live API and run bidirectional audio."""

        if self.call_id:
            CallLogger.log_event(self.call_id, "Connecting to Gemini")
            analytics.start_call(self.call_id)

        # --- client ---------------------------------------------------------
        client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=self.api_key,
        )

        # --- tools -----------------------------------------------------------
        tools = _build_tools()

        # --- VAD configuration -----------------------------------------------
        # Tuned for telephony: reject noise/breathing, allow natural pauses.
        #
        # start_of_speech_sensitivity = LOW
        #   → "detect the start of speech LESS often"
        #   → filters out ambient noise, breathing, mic pops
        #
        # end_of_speech_sensitivity = LOW
        #   → "end speech LESS often"
        #   → allows natural mid-sentence pauses without cutting off
        #
        # prefix_padding_ms = 150
        #   → 150 ms of speech must be detected before it's committed
        #   → short noises (< 300 ms) are ignored entirely
        #
        # silence_duration_ms = 300
        #   → 300 ms of silence required before speech is considered ended
        #   → natural pauses (< 700 ms) don't trigger end-of-speech
        #
        # turn_coverage = TURN_INCLUDES_ONLY_ACTIVITY
        #   → only actual speech is included in the user's turn
        #   → silence/noise is stripped from context
        vad_config = types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=False,
                # HIGH start sensitivity: detect speech start eagerly
                # (telephony audio is quieter than microphone audio)
                start_of_speech_sensitivity=(
                    types.StartSensitivity.START_SENSITIVITY_HIGH
                ),
                # LOW end sensitivity: allow natural mid-sentence pauses
                end_of_speech_sensitivity=(
                    types.EndSensitivity.END_SENSITIVITY_LOW
                ),
                prefix_padding_ms=150,
                silence_duration_ms=300,
            ),
            turn_coverage=types.TurnCoverage.TURN_INCLUDES_ONLY_ACTIVITY,
        )

        # --- session config --------------------------------------------------
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self.voice
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=self.system_prompt)],
                role="user",
            ),
            context_window_compression=types.ContextWindowCompressionConfig(
                trigger_tokens=25600,
                sliding_window=types.SlidingWindow(target_tokens=12800),
            ),
            # Disable thinking — adds seconds of latency
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            realtime_input_config=vad_config,
            tools=tools,
            # Enable transcription for conversation logs
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
        )

        n_tools = len(tools[0].function_declarations)
        snd = "ON" if self._soundscape else "OFF"
        print(
            f"[GEMINI] Connecting to {self.model} "
            f"(tools={n_tools}, VAD=HIGH/LOW/200/500, "
            f"gain={TELEPHONY_GAIN}x, think=OFF, soundscape={snd})…"
        )

        # --- session ---------------------------------------------------------
        try:
            async with client.aio.live.connect(
                model=f"models/{self.model}",
                config=config,
            ) as session:
                self._session = session
                self._running = True

                print("[GEMINI] ✓ Connected")
                if self.call_id:
                    CallLogger.log_event(
                        self.call_id, f"Connected ({self.model})"
                    )

                # send greeting via turn-based API (once, before realtime)
                await self._send_greeting(session)

                # run four concurrent loops
                send_task = asyncio.ensure_future(
                    self._send_audio_loop(session)
                )
                send_task._gemini_name = "send_audio_loop"
                recv_task = asyncio.ensure_future(
                    self._receive_loop(session)
                )
                recv_task._gemini_name = "receive_loop"
                play_task = asyncio.ensure_future(
                    self._play_audio_loop()
                )
                play_task._gemini_name = "play_audio_loop"
                ambient_task = asyncio.ensure_future(
                    self._ambient_fill_loop()
                )
                ambient_task._gemini_name = "ambient_fill_loop"

                all_tasks = [send_task, recv_task, play_task, ambient_task]
                task_names = {
                    id(send_task): "send_audio_loop",
                    id(recv_task): "receive_loop",
                    id(play_task): "play_audio_loop",
                    id(ambient_task): "ambient_fill_loop",
                }
                print("[GEMINI] All 4 tasks started")

                try:
                    done, pending = await asyncio.wait(
                        all_tasks,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    # Log which task(s) finished and why
                    for t in done:
                        tname = task_names.get(id(t), "unknown")
                        try:
                            exc = t.exception()
                        except asyncio.CancelledError:
                            print(f"[GEMINI] ⚠ Task '{tname}' was CANCELLED")
                            continue
                        if exc:
                            print(
                                f"[GEMINI] ✗ Task '{tname}' CRASHED: "
                                f"{type(exc).__name__}: {exc}"
                            )
                            logger.error(
                                f"[GEMINI] Task '{tname}' crashed",
                                exc_info=exc,
                            )
                        else:
                            print(
                                f"[GEMINI] Task '{tname}' exited normally"
                            )
                    pending_names = [
                        task_names.get(id(t), "?") for t in pending
                    ]
                    print(
                        f"[GEMINI] Stopping remaining tasks: "
                        f"{pending_names}"
                    )
                finally:
                    for t in all_tasks:
                        t.cancel()
                    await asyncio.gather(
                        *all_tasks, return_exceptions=True
                    )
                    print("[GEMINI] All tasks stopped")

        except asyncio.CancelledError:
            print("[GEMINI] Session cancelled (CancelledError)")
        except Exception as e:
            print(
                f"[GEMINI] ✗ SESSION ERROR: {type(e).__name__}: {e}\n"
                f"{traceback.format_exc()}"
            )
            logger.error(f"[GEMINI] Session error: {e}", exc_info=True)
            if self.call_id:
                CallLogger.log_error(self.call_id, f"Session error: {e}")
        finally:
            self._running = False
            print(
                f"[GEMINI] Session ending — "
                f"sent={self._chunks_sent} recv={self._chunks_recv}"
            )
            await self.disconnect()

    # ── greeting ──────────────────────────────────────────────────────────

    async def _send_greeting(self, session) -> None:
        """Send initial greeting via send_client_content (turn-based)."""
        instruction = getattr(
            settings, "GEMINI_GREETING_INSTRUCTION", None
        )
        if not instruction:
            if self._customer_context:
                instruction = (
                    "Greet this returning customer warmly in Hinglish. "
                    f"Context: {self._customer_context[:200]}. "
                    "1-2 sentences."
                )
            else:
                instruction = (
                    "Greet the customer. Say: Namaste, main Shivi "
                    "bol rahi hun AckoDrive se. Kya aap car dhundh "
                    "rahe hain?"
                )
        try:
            print(
                f"[GEMINI] Sending greeting "
                f"({len(instruction)} chars)…"
            )
            await session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=instruction)],
                ),
                turn_complete=True,
            )
            print("[GEMINI] ✓ Greeting sent successfully")
            if self.call_id:
                CallLogger.log_event(self.call_id, "Greeting sent")
        except Exception as e:
            print(
                f"[GEMINI] ✗ Greeting FAILED: "
                f"{type(e).__name__}: {e}"
            )
            logger.error(f"[GEMINI] Greeting error", exc_info=True)

    # ── TASK 1: send audio loop ───────────────────────────────────────────

    async def _send_audio_loop(self, session) -> None:
        """Read from _audio_in_q → send_realtime_input to Gemini."""
        print("[GEMINI] [send_audio_loop] Started")
        try:
            while self._running:
                try:
                    msg = await self._audio_in_q.get()
                    await session.send_realtime_input(audio=msg)

                    now = time.monotonic()
                    self._last_audio_sent_time = now
                    self._chunks_sent += 1

                    if self._chunks_sent == 1:
                        print("[GEMINI] ▶ First audio chunk sent")
                    elif self._chunks_sent % 500 == 0:
                        # stale check: audio flowing but no response
                        since_resp = (
                            now - self._last_response_time
                            if self._last_response_time > 0
                            else now - self._last_audio_sent_time
                        )
                        print(
                            f"[GEMINI] [send] {self._chunks_sent} chunks "
                            f"sent, in_q={self._audio_in_q.qsize()}, "
                            f"last_resp={since_resp:.1f}s ago"
                        )
                        if (since_resp > 15.0
                                and not self._stale_warned):
                            self._stale_warned = True
                            print(
                                f"[GEMINI] ⚠ STALE SESSION: "
                                f"{self._chunks_sent} chunks sent, "
                                f"no response for {since_resp:.1f}s. "
                                f"VAD may not be triggering — "
                                f"check audio format/quality."
                            )
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    err = str(e).lower()
                    print(
                        f"[GEMINI] [send_audio_loop] ERROR: "
                        f"{type(e).__name__}: {e}"
                    )
                    if "closed" in err or "cancelled" in err:
                        break
                    logger.error(
                        "[GEMINI] send_realtime_input error",
                        exc_info=True,
                    )
                    break
        except asyncio.CancelledError:
            pass
        print(
            f"[GEMINI] [send_audio_loop] Stopped "
            f"(total sent: {self._chunks_sent})"
        )

    # ── TASK 2: receive loop ──────────────────────────────────────────────

    async def _receive_loop(self, session) -> None:
        """Read responses from Gemini → _audio_out_q / tool calls."""
        print("[GEMINI] [receive_loop] Started")
        turn_count = 0
        turn_audio_chunks = 0
        turn_start_time = 0.0

        try:
            while self._running:
                try:
                    turn = session.receive()
                    turn_count += 1
                    turn_audio_chunks = 0
                    turn_start_time = time.monotonic()
                    first_transcript_time = 0.0  # for latency measurement
                    first_audio_time = 0.0
                    print(
                        f"[GEMINI] [recv] Turn {turn_count} — "
                        f"waiting for responses…"
                    )

                    async for response in turn:

                        # ── usage metadata (token tracking) ───────────
                        um = response.usage_metadata
                        if um is not None:
                            self._accumulate_usage(um)

                        # ── server content ─────────────────────────────
                        sc = response.server_content
                        if sc is not None:

                            # ── transcriptions (user & assistant) ──────
                            # Gemini streams transcriptions word-by-word.
                            # We accumulate fragments and flush complete
                            # utterances on speaker change / turn end.
                            it = sc.input_transcription
                            if it and it.text:
                                # Speaker changed to user → flush assistant
                                if self._assistant_transcript_buf:
                                    self._flush_assistant_transcript()
                                self._user_transcript_buf += it.text

                            ot = sc.output_transcription
                            if ot and ot.text:
                                if first_transcript_time == 0.0:
                                    first_transcript_time = (
                                        time.monotonic()
                                    )
                                # Speaker changed to assistant → flush user
                                if self._user_transcript_buf:
                                    self._flush_user_transcript()
                                self._assistant_transcript_buf += ot.text

                            # INTERRUPTION
                            if sc.interrupted:
                                # Flush partial transcripts before clearing
                                self._flush_all_transcripts()
                                print(
                                    f"[GEMINI] [recv] Turn {turn_count}: "
                                    f"INTERRUPTED (audio in out_q="
                                    f"{self._audio_out_q.qsize()})"
                                )
                                # Stop keyboard if active
                                if (self._soundscape
                                        and self._soundscape
                                        .keyboard_active):
                                    self._soundscape.stop_keyboard()
                                self._drain_output_queue()
                                if self.on_interrupt:
                                    await self.on_interrupt()
                                continue

                            # Model turn → audio / text
                            mt = sc.model_turn
                            if mt and mt.parts:
                                self._last_response_time = (
                                    time.monotonic()
                                )
                                self._stale_warned = False
                                for part in mt.parts:
                                    idata = part.inline_data
                                    if (idata and
                                            isinstance(idata.data, bytes)):
                                        self._chunks_recv += 1
                                        turn_audio_chunks += 1
                                        if turn_audio_chunks == 1:
                                            first_audio_time = (
                                                time.monotonic()
                                            )
                                            elapsed = (
                                                first_audio_time
                                                - turn_start_time
                                            )
                                            # Measure text→audio gap
                                            txt_gap = ""
                                            if first_transcript_time > 0:
                                                gap = (
                                                    first_audio_time
                                                    - first_transcript_time
                                                ) * 1000
                                                txt_gap = (
                                                    f" (transcript→audio "
                                                    f"gap: {gap:.0f}ms)"
                                                )
                                            print(
                                                f"[GEMINI] ◀ First audio "
                                                f"({len(idata.data)}B) "
                                                f"after {elapsed:.2f}s"
                                                f"{txt_gap}"
                                            )

                                        # Stop keyboard clicks as soon
                                        # as Gemini starts speaking
                                        if (self._soundscape
                                                and self._soundscape
                                                .keyboard_active):
                                            self._soundscape.stop_keyboard()
                                            print(
                                                "[GEMINI] ⌨ Keyboard "
                                                "stopped (voice resumed)"
                                            )

                                        # Downsample to 8kHz PCM (raw)
                                        # Mixing + μ-law encoding happens
                                        # in _play_audio_loop
                                        pcm8k, self._downsample_state = (
                                            pcm24k_to_pcm8k(
                                                idata.data,
                                                self._downsample_state,
                                            )
                                        )
                                        if pcm8k:
                                            self._audio_out_q.put_nowait(
                                                pcm8k
                                            )

                                    if part.text:
                                        print(
                                            f"[GEMINI] [recv] Text: "
                                            f"{part.text[:80]!r}"
                                        )
                                        # Buffer text (same as output_transcription)
                                        if self._user_transcript_buf:
                                            self._flush_user_transcript()
                                        self._assistant_transcript_buf += (
                                            part.text
                                        )
                            else:
                                # server_content with no model_turn
                                # and not interrupted — inspect fields
                                if not sc.interrupted:
                                    tc_flag = getattr(
                                        sc, "turn_complete", False
                                    )
                                    if not tc_flag:
                                        # Log all non-None fields
                                        fields = {}
                                        for attr in (
                                            "model_turn",
                                            "interrupted",
                                            "turn_complete",
                                            "input_transcription",
                                            "output_transcription",
                                            "grounding_metadata",
                                        ):
                                            v = getattr(sc, attr, None)
                                            if v is not None:
                                                fields[attr] = (
                                                    str(v)[:100]
                                                )
                                        print(
                                            f"[GEMINI] [recv] "
                                            f"server_content (no "
                                            f"model_turn) turn "
                                            f"{turn_count}: {fields}"
                                        )
                            continue

                        # ── tool call ──────────────────────────────────
                        tc = response.tool_call
                        if tc is not None:
                            n_funcs = len(tc.function_calls or [])
                            print(
                                f"[GEMINI] [recv] Turn {turn_count}: "
                                f"tool_call with {n_funcs} function(s)"
                            )
                            for fc in (tc.function_calls or []):
                                await self._handle_function_call(
                                    session, fc
                                )
                            continue

                        # ── unknown response type ──────────────────────
                        # Log anything we don't recognize
                        resp_attrs = []
                        for attr in (
                            "server_content", "tool_call",
                            "tool_call_cancellation",
                        ):
                            if getattr(response, attr, None) is not None:
                                resp_attrs.append(attr)
                        if not resp_attrs:
                            print(
                                f"[GEMINI] [recv] Turn {turn_count}: "
                                f"unknown response type: "
                                f"{type(response).__name__}"
                            )

                    # ── turn complete ───────────────────────────────────
                    # Flush any remaining transcript fragments
                    self._flush_all_transcripts()

                    elapsed = time.monotonic() - turn_start_time
                    print(
                        f"[GEMINI] Turn {turn_count} complete — "
                        f"{turn_audio_chunks} audio chunks in "
                        f"{elapsed:.2f}s "
                        f"(total: sent={self._chunks_sent} "
                        f"recv={self._chunks_recv}, "
                        f"out_q={self._audio_out_q.qsize()})"
                    )

                    if self.on_response_done:
                        await self.on_response_done()

                    # Loop back to session.receive() for next turn

                except asyncio.CancelledError:
                    raise  # let outer handler catch
                except Exception as e:
                    err_str = str(e).lower()
                    if "closed" in err_str or "cancelled" in err_str:
                        print(
                            f"[GEMINI] [recv] Connection closed "
                            f"(turn {turn_count}): {e}"
                        )
                        break
                    # Non-fatal — log full traceback and try to recover
                    print(
                        f"[GEMINI] [recv] ERROR in turn {turn_count}: "
                        f"{type(e).__name__}: {e}"
                    )
                    logger.error(
                        f"[GEMINI] Receive error (turn {turn_count})",
                        exc_info=True,
                    )
                    # Try next turn — if connection is dead,
                    # session.receive() will fail immediately
                    continue
        except asyncio.CancelledError:
            pass

        print(
            f"[GEMINI] [receive_loop] Stopped "
            f"(turns={turn_count}, total recv={self._chunks_recv})"
        )

    # ── TASK 3: play audio loop ───────────────────────────────────────────

    async def _play_audio_loop(self) -> None:
        """Read PCM8k from _audio_out_q → mix soundscape → encode → telephony.

        This is the ONLY place where μ-law encoding happens for voice.
        Soundscape mixing occurs in linear PCM16 space (mathematically
        correct) before the non-linear μ-law compression step.

        Voice path — ZERO added latency:
          Pure `await queue.get()`.  Returns the instant a chunk is
          available.  No timeouts, no task wrapping, no overhead.
          Updates `_last_voice_play_ts` so the ambient loop knows
          when to stay quiet.
        """
        print("[GEMINI] [play_audio_loop] Started")
        played = 0
        try:
            while self._running:
                try:
                    pcm8k = await self._audio_out_q.get()

                    now = time.monotonic()
                    # Timestamp for ambient grace period
                    self._last_voice_play_ts = now

                    # Mix soundscape in LINEAR PCM space
                    if self._soundscape:
                        pcm8k = self._soundscape.mix(pcm8k)

                    # Encode to μ-law (LAST step — after all mixing)
                    ulaw = pcm8k_to_g711_ulaw(pcm8k)
                    if ulaw and self.on_audio:
                        await self.on_audio(ulaw)
                    played += 1

                    # Log pipeline overhead for first chunk
                    if played == 1:
                        pipe_ms = (
                            time.monotonic() - now
                        ) * 1000
                        print(
                            f"[GEMINI] [play] First chunk "
                            f"pipeline: {pipe_ms:.1f}ms "
                            f"(mix+encode+send)"
                        )
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(
                        f"[GEMINI] [play_audio_loop] ERROR: "
                        f"{type(e).__name__}: {e}"
                    )
                    if "closed" in str(e).lower():
                        break
                    logger.error(
                        "[GEMINI] play_audio error", exc_info=True
                    )
                    break
        except asyncio.CancelledError:
            pass
        print(f"[GEMINI] [play_audio_loop] Stopped (played {played})")

    # ── TASK 4: ambient fill loop ────────────────────────────────────────

    async def _ambient_fill_loop(self) -> None:
        """Send continuous office ambience when voice is NOT playing.

        Runs independently at 20ms intervals (telephony frame rate).
        Uses a grace period after the last voice chunk to prevent
        ambient frames from being injected mid-speech:

          - During voice playback (chunks every ~20ms), grace period
            keeps this loop silent — zero interference with voice.
          - 60ms after the last voice chunk, ambient kicks in.
            The 60ms gap is imperceptible to humans.
          - During tool calls, keyboard_active makes idle frames
            include click sounds automatically.

        This ensures the caller always hears the office environment,
        even while speaking or during silence gaps.
        """
        IDLE_SAMPLES = 160      # 20ms of 8kHz = 160 samples
        GRACE_SEC = 0.06        # 60ms — absorbs inter-chunk jitter
        TICK = 0.02             # 20ms — matches telephony frame rate

        idle_sent = 0
        try:
            while self._running:
                await asyncio.sleep(TICK)

                if not self._soundscape:
                    continue

                # Don't send ambient too close to voice — avoids glitches
                elapsed = time.monotonic() - self._last_voice_play_ts
                if elapsed < GRACE_SEC:
                    continue

                pcm8k = self._soundscape.get_idle_chunk(IDLE_SAMPLES)
                ulaw = pcm8k_to_g711_ulaw(pcm8k)
                if ulaw and self.on_audio:
                    await self.on_audio(ulaw)
                idle_sent += 1
        except asyncio.CancelledError:
            pass
        print(
            f"[GEMINI] [ambient_fill_loop] Stopped "
            f"(sent {idle_sent} frames)"
        )

    # ── queue helpers ─────────────────────────────────────────────────────

    def _drain_output_queue(self) -> None:
        """Instantly discard all audio chunks in the output queue.

        Called on interruption and after turn completion.
        This is O(n) where n = queued chunks (typically < 20).
        """
        discarded = 0
        while not self._audio_out_q.empty():
            try:
                self._audio_out_q.get_nowait()
                discarded += 1
            except asyncio.QueueEmpty:
                break
        if discarded > 0:
            logger.info(f"[GEMINI] Drained {discarded} audio chunks")

    # ── tool call handling ────────────────────────────────────────────────

    async def _handle_function_call(self, session, fc) -> None:
        """Execute a function call and send the result back via
        send_tool_response."""
        name = "<unknown>"
        try:
            name = fc.name
            args = dict(fc.args) if fc.args else {}
            fc_id = getattr(fc, "id", None) or str(uuid.uuid4())

            print(f"[GEMINI] 🔧 Tool call: {name}({args}) id={fc_id}")
            if self.call_id:
                CallLogger.log_event(
                    self.call_id, f"Tool: {name}", json.dumps(args)
                )

            # Start keyboard clicks for audible "typing" feedback.
            # The _ambient_fill_loop generates idle frames continuously;
            # when keyboard is active, those frames include click sounds.
            if self._soundscape:
                self._soundscape.start_keyboard()
                print("[GEMINI] ⌨ Keyboard started (tool executing)")

            # execute
            t0 = time.monotonic()
            result = _execute_tool(name, args)
            exec_ms = (time.monotonic() - t0) * 1000
            print(
                f"[GEMINI] Tool '{name}' executed in {exec_ms:.0f}ms, "
                f"result type={type(result).__name__}"
            )

            # side-effects
            if name == "end_call" and self.on_end_call:
                await self.on_end_call(args.get("reason", "user_request"))
            elif name == "transfer_to_agent" and self.on_transfer_call:
                await self.on_transfer_call(
                    args.get("reason", ""), args.get("query_type", "")
                )
            elif name == "update_car_display" and result and "url" in result:
                if self.call_id:
                    await sse_manager.send_url(
                        call_id=self.call_id,
                        url=result["url"],
                        car_slug=result.get("car_slug", ""),
                        color=result.get("color"),
                    )
                    print(f"[GEMINI] Display → {result['url']}")

            # send result back to Gemini
            if result is not None:
                result_str = (
                    json.dumps(result, ensure_ascii=False)
                    if not isinstance(result, str)
                    else result
                )
                print(
                    f"[GEMINI] Sending tool response: "
                    f"{len(result_str)} chars for '{name}' id={fc_id}"
                )

                func_response = types.FunctionResponse(
                    name=name,
                    response={"result": result_str},
                    id=fc_id,
                )
                try:
                    await session.send_tool_response(
                        function_responses=func_response
                    )
                    print(
                        f"[GEMINI] ✓ Tool response sent for '{name}'"
                    )
                except Exception as send_err:
                    print(
                        f"[GEMINI] ✗ send_tool_response FAILED for "
                        f"'{name}': {type(send_err).__name__}: {send_err}"
                    )
                    logger.error(
                        f"[GEMINI] send_tool_response failed",
                        exc_info=True,
                    )
                    raise  # re-raise so receive_loop sees it

                if self.call_id:
                    count = len(result) if isinstance(result, list) else 1
                    CallLogger.log_event(
                        self.call_id, f"Tool result: {count} items"
                    )
            else:
                print(
                    f"[GEMINI] ⚠ Tool '{name}' returned None — "
                    f"no response sent to Gemini"
                )

        except Exception as e:
            print(
                f"[GEMINI] ✗ Function call error for '{name}': "
                f"{type(e).__name__}: {e}"
            )
            logger.error(
                f"[GEMINI] Function call error: {name}", exc_info=True
            )

    # ── token tracking ────────────────────────────────────────────────────

    def _accumulate_usage(self, um) -> None:
        """Accumulate token counts from a Gemini UsageMetadata message."""
        self._usage_count += 1

        prompt = um.prompt_token_count or 0
        response = um.response_token_count or 0
        cached = um.cached_content_token_count or 0
        tool_use = um.tool_use_prompt_token_count or 0
        thoughts = um.thoughts_token_count or 0
        total = um.total_token_count or 0

        self._total_input_tokens += prompt
        self._total_output_tokens += response
        self._total_cached_tokens += cached
        self._tool_use_tokens += tool_use
        self._thoughts_tokens += thoughts

        # per-modality breakdown (if available)
        for detail in (um.prompt_tokens_details or []):
            modality = str(getattr(detail, "modality", "")).upper()
            count = detail.token_count or 0
            if "AUDIO" in modality:
                self._input_audio_tokens += count
            elif "TEXT" in modality:
                self._input_text_tokens += count

        for detail in (um.response_tokens_details or []):
            modality = str(getattr(detail, "modality", "")).upper()
            count = detail.token_count or 0
            if "AUDIO" in modality:
                self._output_audio_tokens += count
            elif "TEXT" in modality:
                self._output_text_tokens += count

        for detail in (um.cache_tokens_details or []):
            modality = str(getattr(detail, "modality", "")).upper()
            count = detail.token_count or 0
            # cached tokens are input-side
            if "AUDIO" in modality:
                self._input_audio_tokens += count

        # Log periodic usage updates (every 5th usage message)
        if self._usage_count % 5 == 0 or self._usage_count == 1:
            print(
                f"[GEMINI] [tokens] #{self._usage_count}: "
                f"in={prompt} out={response} cached={cached} "
                f"total_accumulated: in={self._total_input_tokens} "
                f"out={self._total_output_tokens}"
            )

    def _record_final_usage(self) -> None:
        """Record accumulated token usage to the token tracker."""
        if not self.call_id:
            return

        # Per-modality breakdown: only fall back to totals-as-text
        # when NO per-modality data was received at all.
        # (Using `or` with int is wrong — 0 is valid and means "none of this modality".)
        has_input_breakdown = (
            self._input_text_tokens > 0 or self._input_audio_tokens > 0
        )
        has_output_breakdown = (
            self._output_text_tokens > 0 or self._output_audio_tokens > 0
        )

        if has_input_breakdown:
            in_text = self._input_text_tokens
            in_audio = self._input_audio_tokens
        else:
            # No per-modality data — assume all tokens are text
            in_text = self._total_input_tokens
            in_audio = 0

        if has_output_breakdown:
            out_text = self._output_text_tokens
            out_audio = self._output_audio_tokens
        else:
            out_text = self._total_output_tokens
            out_audio = 0

        usage = {
            "input_tokens": self._total_input_tokens,
            "output_tokens": self._total_output_tokens,
            "input_token_details": {
                "text_tokens": in_text,
                "audio_tokens": in_audio,
                "cached_tokens": self._total_cached_tokens,
            },
            "output_token_details": {
                "text_tokens": out_text,
                "audio_tokens": out_audio,
            },
        }

        token_tracker.record_voice_agent_usage(
            call_id=self.call_id,
            usage=usage,
            model_name=self.model,
        )

        # Also log to CallLogger
        tokens_log = {
            "text_input": in_text,
            "text_output": out_text,
            "audio_input": in_audio,
            "audio_output": out_audio,
            "cached_tokens": self._total_cached_tokens,
            "total_input": self._total_input_tokens,
            "total_output": self._total_output_tokens,
            "tool_use_tokens": self._tool_use_tokens,
            "thoughts_tokens": self._thoughts_tokens,
            "usage_updates": self._usage_count,
        }
        CallLogger.log_tokens(self.call_id, "voice_agent", tokens_log)

        # Also record in analytics (legacy)
        analytics.record_response_agent_usage(
            self.call_id,
            text_input=in_text,
            text_output=out_text,
            audio_input=in_audio,
            audio_output=out_audio,
        )

        print(
            f"[GEMINI] [tokens] FINAL: "
            f"in={self._total_input_tokens} "
            f"out={self._total_output_tokens} "
            f"cached={self._total_cached_tokens} "
            f"(text_in={in_text} audio_in={in_audio} "
            f"text_out={out_text} audio_out={out_audio} "
            f"tool={self._tool_use_tokens} "
            f"think={self._thoughts_tokens})"
        )


