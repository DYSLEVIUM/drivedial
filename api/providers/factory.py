from django.conf import settings

from api.providers.base import TelephonyProvider, VoiceProvider


class ProviderFactory:
    @staticmethod
    def get_voice(provider: str = None, call_id: str = None) -> VoiceProvider:
        provider = provider or getattr(settings, "VOICE_PROVIDER", "openai")

        if provider == "openai":
            from api.providers.openai import OpenAIVoiceProvider
            return OpenAIVoiceProvider(call_id=call_id)
        else:
            raise ValueError(f"Unknown voice provider: {provider}")

    @staticmethod
    def get_telephony(provider: str = None) -> TelephonyProvider:
        provider = provider or getattr(
            settings, "TELEPHONY_PROVIDER", "twilio")

        if provider == "twilio":
            from api.providers.twilio import TwilioProvider
            return TwilioProvider()
        else:
            raise ValueError(f"Unknown telephony provider: {provider}")
