"""
Provider Factory for Voice AI and Telephony providers.

Implements the Factory Pattern for loose coupling between the application
and specific provider implementations. Provider selection is driven by
configuration settings.

Supported Telephony Providers:
- twilio: Twilio Media Streams
- ozonetel: Ozonetel Bi-Directional Stream
- vobiz: VoBiz Bi-Directional Stream

Supported Voice Providers:
- openai: OpenAI Realtime API
- gemini: Google Gemini Live API
"""

from typing import Optional, Dict, Type

from django.conf import settings

from api.providers.base import TelephonyProvider, VoiceProvider


# Registry of telephony providers
_telephony_providers: Dict[str, Type[TelephonyProvider]] = {}

# Registry of voice providers
_voice_providers: Dict[str, Type[VoiceProvider]] = {}


def register_telephony_provider(name: str, provider_class: Type[TelephonyProvider]) -> None:
    """Register a telephony provider class."""
    _telephony_providers[name.lower()] = provider_class


def register_voice_provider(name: str, provider_class: Type[VoiceProvider]) -> None:
    """Register a voice provider class."""
    _voice_providers[name.lower()] = provider_class


# Register built-in providers
def _register_builtin_providers():
    """Lazily register built-in providers."""
    if "twilio" not in _telephony_providers:
        from api.providers.twilio import TwilioProvider
        register_telephony_provider("twilio", TwilioProvider)
    
    if "ozonetel" not in _telephony_providers:
        from api.providers.ozonetel import OzonetelProvider
        register_telephony_provider("ozonetel", OzonetelProvider)
    
    if "vobiz" not in _telephony_providers:
        from api.providers.vobiz import VoBizProvider
        register_telephony_provider("vobiz", VoBizProvider)
    
    if "openai" not in _voice_providers:
        from api.providers.openai import OpenAIVoiceProvider
        register_voice_provider("openai", OpenAIVoiceProvider)
    
    if "gemini" not in _voice_providers:
        from api.providers.gemini import GeminiVoiceProvider
        register_voice_provider("gemini", GeminiVoiceProvider)


class ProviderFactory:
    """
    Factory class for creating provider instances.
    
    Provider selection is driven by Django settings:
    - TELEPHONY_PROVIDER: 'twilio', 'ozonetel', or 'vobiz'
    - VOICE_PROVIDER: 'openai'
    
    Usage:
        # Get default telephony provider from settings
        telephony = ProviderFactory.get_telephony()
        
        # Get specific telephony provider
        telephony = ProviderFactory.get_telephony("ozonetel")
        
        # Get voice provider with call context
        voice = ProviderFactory.get_voice(call_id="abc123", customer_context="...")
    """
    
    @staticmethod
    def get_voice(
        provider: str = None, 
        call_id: str = None,
        customer_context: Optional[str] = None
    ) -> VoiceProvider:
        """
        Get a voice provider instance.
        
        Args:
            provider: Provider name (defaults to settings.VOICE_PROVIDER)
            call_id: Unique call identifier
            customer_context: Optional context for returning customers
            
        Returns:
            Configured VoiceProvider instance
            
        Raises:
            ValueError: If provider is not registered
        """
        _register_builtin_providers()
        
        provider = (provider or getattr(settings, "VOICE_PROVIDER", "openai")).lower()

        if provider not in _voice_providers:
            available = list(_voice_providers.keys())
            raise ValueError(
                f"Unknown voice provider: {provider}. "
                f"Available providers: {available}"
            )
        
        provider_class = _voice_providers[provider]
        
        # Special handling for providers with call context
        if provider in ("openai", "gemini"):
            return provider_class(call_id=call_id, customer_context=customer_context)
        
        return provider_class()

    @staticmethod
    def get_telephony(provider: str = None) -> TelephonyProvider:
        """
        Get a telephony provider instance.
        
        Args:
            provider: Provider name (defaults to settings.TELEPHONY_PROVIDER)
            
        Returns:
            Configured TelephonyProvider instance
            
        Raises:
            ValueError: If provider is not registered
        """
        _register_builtin_providers()
        
        provider = (provider or getattr(settings, "TELEPHONY_PROVIDER", "twilio")).lower()
        
        if provider not in _telephony_providers:
            available = list(_telephony_providers.keys())
            raise ValueError(
                f"Unknown telephony provider: {provider}. "
                f"Available providers: {available}"
            )
        
        return _telephony_providers[provider]()
    
    @staticmethod
    def get_telephony_by_route(route_name: str) -> TelephonyProvider:
        """
        Get telephony provider based on WebSocket route.
        
        This allows different WebSocket endpoints to use different providers.
        
        Args:
            route_name: WebSocket route identifier (e.g., 'twilio', 'ozonetel')
            
        Returns:
            TelephonyProvider for the specified route
        """
        _register_builtin_providers()
        
        # Route mapping - can be extended via settings
        route_mapping = getattr(settings, "TELEPHONY_ROUTE_MAPPING", {
            "twilio": "twilio",
            "ozonetel": "ozonetel",
            "media-stream": "twilio",  # Default Twilio route
            "ozonetel-stream": "ozonetel",
        })
        
        provider_name = route_mapping.get(route_name.lower(), route_name.lower())
        return ProviderFactory.get_telephony(provider_name)
    
    @staticmethod
    def list_telephony_providers() -> list:
        """List all registered telephony providers."""
        _register_builtin_providers()
        return list(_telephony_providers.keys())
    
    @staticmethod
    def list_voice_providers() -> list:
        """List all registered voice providers."""
        _register_builtin_providers()
        return list(_voice_providers.keys())
