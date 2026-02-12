"""
Provider system for DriveDial.

This module provides pluggable providers for:
- Voice AI (e.g., OpenAI Realtime)
- Telephony (e.g., Twilio, Ozonetel)

Usage:
    from api.providers import ProviderFactory
    
    # Get configured telephony provider
    telephony = ProviderFactory.get_telephony()
    
    # Get specific provider
    telephony = ProviderFactory.get_telephony("ozonetel")
    
    # Get voice provider with call context
    voice = ProviderFactory.get_voice(call_id="abc123")
"""

from api.providers.base import (
    VoiceProvider, 
    TelephonyProvider,
    IncomingAudioMessage,
    StreamStartMessage,
)
from api.providers.factory import (
    ProviderFactory,
    register_telephony_provider,
    register_voice_provider,
)

__all__ = [
    # Base classes
    "VoiceProvider", 
    "TelephonyProvider",
    "IncomingAudioMessage",
    "StreamStartMessage",
    # Factory
    "ProviderFactory",
    "register_telephony_provider",
    "register_voice_provider",
]
