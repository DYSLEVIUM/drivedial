"""
Audio conversion utilities for telephony providers.

Uses Python's built-in `audioop` module (C-optimized, ITU-T G.711 compliant)
for all μ-law ↔ PCM conversions.  This replaces the previous hand-rolled
per-sample Python loops that were slow and prone to subtle encoding errors.

Supported conversions:
  - g711_ulaw (μ-law 8 kHz) ↔ PCM16 (linear 16-bit)
  - PCM16 sample lists ↔ raw bytes ↔ base64
  - Ozonetel PCM16 sample-array format ↔ g711_ulaw base64

Note: `audioop` was deprecated in Python 3.11 and removed in 3.13.
      For Python ≥ 3.13 consider the `audioop-lts` PyPI package.
"""

import audioop
import base64
import struct
from typing import List


# ═══════════════════════════════════════════════════════════════════════════════
# Core μ-law ↔ PCM conversion  (C-optimized via audioop)
# ═══════════════════════════════════════════════════════════════════════════════

def pcm16_bytes_to_ulaw_bytes(pcm_bytes: bytes) -> bytes:
    """Convert raw PCM16 LE bytes to raw μ-law bytes.  (No base64.)"""
    return audioop.lin2ulaw(pcm_bytes, 2)


def ulaw_bytes_to_pcm16_bytes(ulaw_bytes: bytes) -> bytes:
    """Convert raw μ-law bytes to raw PCM16 LE bytes.  (No base64.)"""
    return audioop.ulaw2lin(ulaw_bytes, 2)


# ═══════════════════════════════════════════════════════════════════════════════
# Base64-encoded conversions  (used by Twilio / VoBiz / OpenAI paths)
# ═══════════════════════════════════════════════════════════════════════════════

def pcm16_bytes_to_ulaw_base64(pcm_bytes: bytes) -> str:
    """PCM16 LE bytes → base64-encoded μ-law."""
    return base64.b64encode(audioop.lin2ulaw(pcm_bytes, 2)).decode("ascii")


def ulaw_base64_to_pcm16_bytes(ulaw_base64: str) -> bytes:
    """Base64-encoded μ-law → raw PCM16 LE bytes."""
    return audioop.ulaw2lin(base64.b64decode(ulaw_base64), 2)


def pcm16_base64_to_ulaw_base64(pcm16_base64: str) -> str:
    """Base64 PCM16 → base64 μ-law."""
    pcm = base64.b64decode(pcm16_base64)
    return base64.b64encode(audioop.lin2ulaw(pcm, 2)).decode("ascii")


def ulaw_base64_to_pcm16_base64(ulaw_base64: str) -> str:
    """Base64 μ-law → base64 PCM16."""
    pcm = audioop.ulaw2lin(base64.b64decode(ulaw_base64), 2)
    return base64.b64encode(pcm).decode("ascii")


# ═══════════════════════════════════════════════════════════════════════════════
# Ozonetel helpers  (PCM16 sample-list ↔ g711_ulaw base64)
# ═══════════════════════════════════════════════════════════════════════════════

def pcm16_samples_to_ulaw_base64(samples: List[int]) -> str:
    """
    Convert PCM16 sample list → base64 μ-law.

    Args:
        samples: List of 16-bit signed integers (-32768 … 32767)
    Returns:
        Base64 encoded μ-law bytes
    """
    # Pack samples into raw PCM16 LE bytes
    clamped = [max(-32768, min(32767, s)) for s in samples]
    pcm_bytes = struct.pack(f"<{len(clamped)}h", *clamped)
    return base64.b64encode(audioop.lin2ulaw(pcm_bytes, 2)).decode("ascii")


def ulaw_base64_to_pcm16_samples(ulaw_base64: str) -> List[int]:
    """
    Convert base64 μ-law → PCM16 sample list.

    Returns:
        List of 16-bit signed integers
    """
    ulaw_bytes = base64.b64decode(ulaw_base64)
    pcm_bytes = audioop.ulaw2lin(ulaw_bytes, 2)
    n = len(pcm_bytes) // 2
    return list(struct.unpack(f"<{n}h", pcm_bytes))


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience aliases for Gemini provider
# ═══════════════════════════════════════════════════════════════════════════════

def g711_ulaw_to_pcm16(ulaw_base64: str) -> bytes:
    """
    Base64 g711 μ-law → raw PCM16 LE bytes.

    Used by Gemini provider to convert telephony audio to Gemini format.
    """
    return audioop.ulaw2lin(base64.b64decode(ulaw_base64), 2)


def pcm16_to_g711_ulaw(pcm16_bytes: bytes) -> str:
    """
    Raw PCM16 LE bytes → base64 g711 μ-law.

    Used by Gemini provider to convert Gemini output to telephony format.
    """
    return base64.b64encode(audioop.lin2ulaw(pcm16_bytes, 2)).decode("ascii")
