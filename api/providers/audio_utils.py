"""
Audio conversion utilities for telephony providers.

Handles conversion between different audio formats:
- g711_ulaw (μ-law): Used by Twilio and OpenAI Realtime API
- PCM16 (Linear 16-bit): Used by Ozonetel
"""

import base64
import struct
from typing import List

# μ-law encoding/decoding tables and constants
ULAW_BIAS = 0x84
ULAW_CLIP = 32635

# μ-law to linear conversion table
ULAW_TO_LINEAR_TABLE = [
    -32124, -31100, -30076, -29052, -28028, -27004, -25980, -24956,
    -23932, -22908, -21884, -20860, -19836, -18812, -17788, -16764,
    -15996, -15484, -14972, -14460, -13948, -13436, -12924, -12412,
    -11900, -11388, -10876, -10364, -9852, -9340, -8828, -8316,
    -7932, -7676, -7420, -7164, -6908, -6652, -6396, -6140,
    -5884, -5628, -5372, -5116, -4860, -4604, -4348, -4092,
    -3900, -3772, -3644, -3516, -3388, -3260, -3132, -3004,
    -2876, -2748, -2620, -2492, -2364, -2236, -2108, -1980,
    -1884, -1820, -1756, -1692, -1628, -1564, -1500, -1436,
    -1372, -1308, -1244, -1180, -1116, -1052, -988, -924,
    -876, -844, -812, -780, -748, -716, -684, -652,
    -620, -588, -556, -524, -492, -460, -428, -396,
    -372, -356, -340, -324, -308, -292, -276, -260,
    -244, -228, -212, -196, -180, -164, -148, -132,
    -120, -112, -104, -96, -88, -80, -72, -64,
    -56, -48, -40, -32, -24, -16, -8, 0,
    32124, 31100, 30076, 29052, 28028, 27004, 25980, 24956,
    23932, 22908, 21884, 20860, 19836, 18812, 17788, 16764,
    15996, 15484, 14972, 14460, 13948, 13436, 12924, 12412,
    11900, 11388, 10876, 10364, 9852, 9340, 8828, 8316,
    7932, 7676, 7420, 7164, 6908, 6652, 6396, 6140,
    5884, 5628, 5372, 5116, 4860, 4604, 4348, 4092,
    3900, 3772, 3644, 3516, 3388, 3260, 3132, 3004,
    2876, 2748, 2620, 2492, 2364, 2236, 2108, 1980,
    1884, 1820, 1756, 1692, 1628, 1564, 1500, 1436,
    1372, 1308, 1244, 1180, 1116, 1052, 988, 924,
    876, 844, 812, 780, 748, 716, 684, 652,
    620, 588, 556, 524, 492, 460, 428, 396,
    372, 356, 340, 324, 308, 292, 276, 260,
    244, 228, 212, 196, 180, 164, 148, 132,
    120, 112, 104, 96, 88, 80, 72, 64,
    56, 48, 40, 32, 24, 16, 8, 0,
]


def linear_to_ulaw(sample: int) -> int:
    """Convert a single 16-bit linear PCM sample to μ-law."""
    # Get the sign and magnitude
    sign = (sample >> 8) & 0x80
    if sign:
        sample = -sample
    
    # Clip the magnitude
    if sample > ULAW_CLIP:
        sample = ULAW_CLIP
    
    # Add bias
    sample = sample + ULAW_BIAS
    
    # Find the segment
    exponent = 7
    exp_mask = 0x4000
    for _ in range(8):
        if sample & exp_mask:
            break
        exponent -= 1
        exp_mask >>= 1
    
    # Combine the sign, exponent, and mantissa
    mantissa = (sample >> (exponent + 3)) & 0x0F
    ulaw_byte = ~(sign | (exponent << 4) | mantissa)
    
    return ulaw_byte & 0xFF


def ulaw_to_linear(ulaw_byte: int) -> int:
    """Convert a single μ-law byte to 16-bit linear PCM."""
    return ULAW_TO_LINEAR_TABLE[ulaw_byte]


def pcm16_samples_to_ulaw_base64(samples: List[int]) -> str:
    """
    Convert PCM16 samples (list of integers) to base64-encoded μ-law bytes.
    
    Args:
        samples: List of 16-bit signed integers (-32768 to 32767)
        
    Returns:
        Base64 encoded string of μ-law bytes
    """
    ulaw_bytes = bytearray()
    for sample in samples:
        # Clamp to 16-bit signed range
        sample = max(-32768, min(32767, sample))
        ulaw_bytes.append(linear_to_ulaw(sample))
    
    return base64.b64encode(bytes(ulaw_bytes)).decode('ascii')


def ulaw_base64_to_pcm16_samples(ulaw_base64: str) -> List[int]:
    """
    Convert base64-encoded μ-law bytes to PCM16 samples.
    
    Args:
        ulaw_base64: Base64 encoded string of μ-law bytes
        
    Returns:
        List of 16-bit signed integers
    """
    ulaw_bytes = base64.b64decode(ulaw_base64)
    samples = []
    for byte in ulaw_bytes:
        samples.append(ulaw_to_linear(byte))
    return samples


def pcm16_bytes_to_ulaw_base64(pcm_bytes: bytes) -> str:
    """
    Convert raw PCM16 bytes (little-endian) to base64-encoded μ-law.
    
    Args:
        pcm_bytes: Raw PCM16 bytes (little-endian, 16-bit signed)
        
    Returns:
        Base64 encoded string of μ-law bytes
    """
    # Unpack as little-endian signed 16-bit integers
    num_samples = len(pcm_bytes) // 2
    samples = struct.unpack(f'<{num_samples}h', pcm_bytes[:num_samples * 2])
    return pcm16_samples_to_ulaw_base64(list(samples))


def ulaw_base64_to_pcm16_bytes(ulaw_base64: str) -> bytes:
    """
    Convert base64-encoded μ-law to raw PCM16 bytes (little-endian).
    
    Args:
        ulaw_base64: Base64 encoded string of μ-law bytes
        
    Returns:
        Raw PCM16 bytes (little-endian, 16-bit signed)
    """
    samples = ulaw_base64_to_pcm16_samples(ulaw_base64)
    return struct.pack(f'<{len(samples)}h', *samples)


def pcm16_base64_to_ulaw_base64(pcm16_base64: str) -> str:
    """
    Convert base64-encoded PCM16 to base64-encoded μ-law.
    
    Args:
        pcm16_base64: Base64 encoded PCM16 bytes
        
    Returns:
        Base64 encoded μ-law bytes
    """
    pcm_bytes = base64.b64decode(pcm16_base64)
    return pcm16_bytes_to_ulaw_base64(pcm_bytes)


def ulaw_base64_to_pcm16_base64(ulaw_base64: str) -> str:
    """
    Convert base64-encoded μ-law to base64-encoded PCM16.
    
    Args:
        ulaw_base64: Base64 encoded μ-law bytes
        
    Returns:
        Base64 encoded PCM16 bytes
    """
    pcm_bytes = ulaw_base64_to_pcm16_bytes(ulaw_base64)
    return base64.b64encode(pcm_bytes).decode('ascii')


# Convenience aliases for Gemini provider
def g711_ulaw_to_pcm16(ulaw_base64: str) -> bytes:
    """
    Convert base64-encoded g711 μ-law audio to raw PCM16 bytes.
    
    Used by Gemini provider to convert telephony audio (g711_ulaw)
    to Gemini's expected format (PCM16).
    
    Args:
        ulaw_base64: Base64 encoded g711 μ-law audio from telephony
        
    Returns:
        Raw PCM16 bytes (little-endian, 16-bit signed)
    """
    return ulaw_base64_to_pcm16_bytes(ulaw_base64)


def pcm16_to_g711_ulaw(pcm16_bytes: bytes) -> str:
    """
    Convert raw PCM16 bytes to base64-encoded g711 μ-law audio.
    
    Used by Gemini provider to convert Gemini's output (PCM16)
    to telephony format (g711_ulaw).
    
    Args:
        pcm16_bytes: Raw PCM16 bytes from Gemini
        
    Returns:
        Base64 encoded g711 μ-law audio for telephony
    """
    return pcm16_bytes_to_ulaw_base64(pcm16_bytes)

