"""
Soundscape Mixer — Ambient audio overlay for voice calls.

Adds environmental presence to AI voice output:
  • Office Ambience : Continuous low-level background hum (always on)
  • Keyboard Clicks : Triggered during tool execution / data fetching

Architecture:
  All mixing is performed in LINEAR PCM16 space at 8 kHz (telephony rate)
  BEFORE μ-law encoding.  Mixing in compressed μ-law domain would introduce
  non-linear distortion; mixing in linear PCM is mathematically correct.

  ┌──────────────────┐
  │ Gemini PCM 24kHz │
  └────────┬─────────┘
           │ pcm24k_to_pcm8k()      ← downsample only, no encoding
           ▼
  ┌──────────────────┐      ┌───────────────────────┐
  │ Voice PCM  8kHz  │ ──▸  │   SoundscapeMixer     │
  └──────────────────┘      │   .mix(voice_pcm)     │
                            │   + office ambience   │
                            │   + keyboard (if on)  │
                            └────────┬──────────────┘
                                     │
                                     ▼
                            ┌───────────────────────┐
                            │ Mixed PCM 8kHz        │
                            └────────┬──────────────┘
                                     │ pcm8k_to_g711_ulaw()   ← encode last
                                     ▼
                            ┌───────────────────────┐
                            │ μ-law base64          │ ──▸ Telephony
                            └───────────────────────┘

  During tool calls (no Gemini voice):
    _keyboard_fill_loop pushes silence frames into _audio_out_q.
    _play_audio_loop mixes them with office + keyboard → telephony.

Sample caching:
  WAV files are loaded and resampled ONCE (on first call).  Subsequent
  calls reuse the cached samples.  Each call gets its own SoundscapeMixer
  instance with independent playback positions.

Usage:
  mixer = SoundscapeMixer.create("sounds/office.wav", "sounds/keyboard.wav")
  if mixer:
      mixed = mixer.mix(voice_pcm_bytes)    # voice + ambient
      idle  = mixer.get_idle_chunk(160)      # ambient only (20ms)
"""

import array
import logging
import os
import wave
from typing import Optional

logger = logging.getLogger("soundscape")

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Gain levels relative to full-scale PCM16 (±32 767).
# Calibrated for TELEPHONY: μ-law encoding crushes very small PCM values
# to zero, so gains must be high enough for the ambient signal to exceed
# the μ-law noise floor (~200 PCM units).  Voice peaks at ~3000-8000.
OFFICE_GAIN = 0.65           # 65% — clearly audible hum on telephony
KEYBOARD_GAIN = 1.0          # 100% — click events fully audible
KEYBOARD_SOLO_BOOST = 1.2    # 1.2× louder when no voice is present

# Target sample rate — telephony standard
TARGET_RATE = 8000  # 8 kHz


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level sample cache (loaded once, shared across all calls)
# ═══════════════════════════════════════════════════════════════════════════════

_cached_office: Optional[array.array] = None
_cached_keyboard: Optional[array.array] = None
_cache_loaded: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# SoundscapeMixer
# ═══════════════════════════════════════════════════════════════════════════════

class SoundscapeMixer:
    """
    Mixes ambient soundscape audio into voice PCM in linear space.

    All internal buffers are mono PCM16 signed at 8 kHz.
    Sounds loop seamlessly for continuous ambience.

    Thread-safety: NOT thread-safe.  Designed for single-event-loop access
    from _play_audio_loop and _keyboard_fill_loop (same asyncio loop).
    """

    __slots__ = (
        "_office", "_keyboard",
        "_off_pos", "_kb_pos",
        "_off_gain", "_kb_gain", "_kb_solo_boost",
        "_kb_active",
    )

    def __init__(
        self,
        office_samples: array.array,
        keyboard_samples: array.array,
        office_gain: float = OFFICE_GAIN,
        keyboard_gain: float = KEYBOARD_GAIN,
    ):
        self._office = office_samples          # shared, read-only
        self._keyboard = keyboard_samples      # shared, read-only
        self._off_gain = office_gain
        self._kb_gain = keyboard_gain
        self._kb_solo_boost = KEYBOARD_SOLO_BOOST

        # Per-instance playback positions (looping)
        self._off_pos = 0
        self._kb_pos = 0
        self._kb_active = False

    # ── factory ────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        office_path: str,
        keyboard_path: str,
        office_gain: float = OFFICE_GAIN,
        keyboard_gain: float = KEYBOARD_GAIN,
    ) -> Optional["SoundscapeMixer"]:
        """
        Create a SoundscapeMixer, loading WAV files on first call.

        Returns None if files are missing or unreadable — the caller
        should proceed without soundscape (graceful degradation).
        """
        global _cached_office, _cached_keyboard, _cache_loaded

        if not _cache_loaded:
            _cache_loaded = True
            try:
                if not os.path.isfile(office_path):
                    print(
                        f"[Soundscape] Office sound not found: {office_path}"
                    )
                    return None
                if not os.path.isfile(keyboard_path):
                    print(
                        f"[Soundscape] Keyboard sound not found: "
                        f"{keyboard_path}"
                    )
                    return None

                _cached_office = _load_wav_mono_8k(office_path)
                _cached_keyboard = _load_wav_mono_8k(keyboard_path)

                if len(_cached_office) < TARGET_RATE:
                    print(
                        f"[Soundscape] ⚠ Office sound too short "
                        f"({len(_cached_office)} samples, need ≥{TARGET_RATE})"
                    )
                    _cached_office = None
                    return None
                if len(_cached_keyboard) < TARGET_RATE // 10:
                    print(
                        f"[Soundscape] ⚠ Keyboard sound too short "
                        f"({len(_cached_keyboard)} samples)"
                    )
                    _cached_keyboard = None
                    return None

                print(
                    f"[Soundscape] ✓ Loaded — "
                    f"office: {len(_cached_office)/TARGET_RATE:.1f}s, "
                    f"keyboard: {len(_cached_keyboard)/TARGET_RATE:.1f}s  "
                    f"(gains: office={office_gain}, keyboard={keyboard_gain})"
                )
            except Exception as e:
                logger.error(
                    f"[Soundscape] Failed to load sounds: {e}",
                    exc_info=True,
                )
                return None

        if _cached_office is None or _cached_keyboard is None:
            return None

        return cls(_cached_office, _cached_keyboard, office_gain, keyboard_gain)

    # ── mixing ─────────────────────────────────────────────────────────

    def mix(self, voice_pcm8k: bytes) -> bytes:
        """
        Mix ambient sound into voice PCM.

        Args:
            voice_pcm8k: Raw PCM16 LE bytes at 8 kHz (voice from Gemini)

        Returns:
            Mixed PCM16 bytes at 8 kHz (same length as input)
        """
        voice = array.array("h")
        voice.frombytes(voice_pcm8k)
        n = len(voice)
        if n == 0:
            return voice_pcm8k

        office = self._office
        off_len = len(office)
        off_gain = self._off_gain
        off_pos = self._off_pos

        kb_active = self._kb_active
        keyboard = self._keyboard
        kb_len = len(keyboard)
        kb_gain = self._kb_gain
        kb_pos = self._kb_pos

        for i in range(n):
            s = voice[i]

            # Office ambience — always on
            s += int(office[off_pos % off_len] * off_gain)
            off_pos += 1

            # Keyboard clicks — only when active
            if kb_active:
                s += int(keyboard[kb_pos % kb_len] * kb_gain)
                kb_pos += 1

            # Clamp to signed 16-bit
            if s > 32767:
                s = 32767
            elif s < -32768:
                s = -32768
            voice[i] = s

        self._off_pos = off_pos % off_len
        if kb_active:
            self._kb_pos = kb_pos % kb_len

        return voice.tobytes()

    def get_idle_chunk(self, n_samples: int) -> bytes:
        """
        Generate an ambient-only chunk (no voice signal).

        Used during tool-call gaps when Gemini is not generating audio.
        The voice is silence; only background sounds are present.

        Args:
            n_samples: Number of samples (e.g. 160 = 20ms at 8kHz)

        Returns:
            Raw PCM16 bytes at 8 kHz
        """
        out = array.array("h")

        office = self._office
        off_len = len(office)
        off_gain = self._off_gain
        off_pos = self._off_pos

        keyboard = self._keyboard
        kb_len = len(keyboard)
        # Keyboard is louder when solo — no competing voice
        kb_gain = self._kb_gain * self._kb_solo_boost
        kb_pos = self._kb_pos
        kb_active = self._kb_active

        for _ in range(n_samples):
            s = int(office[off_pos % off_len] * off_gain)

            if kb_active:
                s += int(keyboard[kb_pos % kb_len] * kb_gain)
                kb_pos += 1

            if s > 32767:
                s = 32767
            elif s < -32768:
                s = -32768
            out.append(s)
            off_pos += 1

        self._off_pos = off_pos % off_len
        if kb_active:
            self._kb_pos = kb_pos % kb_len

        return out.tobytes()

    # ── keyboard control ───────────────────────────────────────────────

    def start_keyboard(self) -> None:
        """Begin keyboard click overlay (on tool-call start)."""
        self._kb_active = True
        self._kb_pos = 0

    def stop_keyboard(self) -> None:
        """Stop keyboard click overlay (when model resumes speaking)."""
        self._kb_active = False

    @property
    def keyboard_active(self) -> bool:
        return self._kb_active


# ═══════════════════════════════════════════════════════════════════════════════
# WAV loading & resampling
# ═══════════════════════════════════════════════════════════════════════════════

def _load_wav_mono_8k(path: str) -> array.array:
    """
    Load a WAV file and convert to mono PCM16 signed at 8 kHz.

    Handles:
      - Any sample rate (resampled via linear interpolation)
      - Mono or multi-channel (mixed down to mono)
      - 8-bit, 16-bit, or 24-bit sample width
    """
    with wave.open(path, "rb") as w:
        channels = w.getnchannels()
        sample_width = w.getsampwidth()
        rate = w.getframerate()
        n_frames = w.getnframes()
        raw = w.readframes(n_frames)

    duration = n_frames / rate if rate > 0 else 0
    print(
        f"[Soundscape] Loading {os.path.basename(path)}: "
        f"{channels}ch, {sample_width * 8}bit, {rate}Hz, {duration:.1f}s"
    )

    # ── parse to 16-bit signed samples ─────────────────────────────
    if sample_width == 2:
        samples = array.array("h")
        samples.frombytes(raw)
    elif sample_width == 1:
        # 8-bit unsigned → 16-bit signed
        samples = array.array("h", [(b - 128) << 8 for b in raw])
    elif sample_width == 3:
        # 24-bit little-endian → 16-bit (take upper 2 bytes)
        samples = array.array("h")
        for i in range(0, len(raw), 3):
            val = raw[i + 1] | (raw[i + 2] << 8)
            if val >= 32768:
                val -= 65536
            samples.append(val)
    else:
        raise ValueError(
            f"Unsupported WAV sample width: {sample_width} bytes"
        )

    # ── multi-channel → mono mixdown ───────────────────────────────
    if channels > 1:
        mono = array.array("h")
        for i in range(0, len(samples), channels):
            total = 0
            count = min(channels, len(samples) - i)
            for c in range(count):
                total += samples[i + c]
            mono.append(total // channels)
        samples = mono

    # ── resample to 8 kHz ──────────────────────────────────────────
    if rate != TARGET_RATE:
        samples = _resample(samples, rate, TARGET_RATE)

    return samples


def _resample(
    samples: array.array, from_rate: int, to_rate: int
) -> array.array:
    """
    Resample PCM16 via linear interpolation.

    Not audiophile-grade, but perfectly adequate for background ambience
    where high-frequency fidelity is irrelevant.
    """
    ratio = from_rate / to_rate
    in_len = len(samples)
    out_len = int(in_len / ratio)
    out = array.array("h")

    for i in range(out_len):
        pos = i * ratio
        idx = int(pos)
        frac = pos - idx

        if idx + 1 < in_len:
            val = int(samples[idx] * (1.0 - frac) + samples[idx + 1] * frac)
        else:
            val = samples[min(idx, in_len - 1)]

        if val > 32767:
            val = 32767
        elif val < -32768:
            val = -32768
        out.append(val)

    return out

