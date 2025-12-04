import logging
from typing import Dict, Optional

import aiohttp
from django.conf import settings

logger = logging.getLogger("pricing")


class PricingService:
    _instance: Optional["PricingService"] = None
    _pricing_cache: Dict[str, Dict[str, float]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_default_pricing()
        return cls._instance

    def _init_default_pricing(self) -> None:
        self._pricing_cache = {
            "gpt-4o-mini-realtime-preview-2024-12-17": {
                "text_input": 0.60 / 1_000_000,
                "text_output": 2.40 / 1_000_000,
                "audio_input": 10.00 / 1_000_000,
                "audio_output": 20.00 / 1_000_000,
                "text_input_cached": 0.30 / 1_000_000,
                "audio_input_cached": 0.60 / 1_000_000,
            },
            "gpt-4o-realtime-preview-2024-12-17": {
                "text_input": 5.00 / 1_000_000,
                "text_output": 20.00 / 1_000_000,
                "audio_input": 100.00 / 1_000_000,
                "audio_output": 200.00 / 1_000_000,
                "text_input_cached": 2.50 / 1_000_000,
                "audio_input_cached": 20.00 / 1_000_000,
            },
            "gpt-4o-mini": {
                "text_input": 0.15 / 1_000_000,
                "text_output": 0.60 / 1_000_000,
                "text_input_cached": 0.075 / 1_000_000,
            },
            "gpt-4o": {
                "text_input": 2.50 / 1_000_000,
                "text_output": 10.00 / 1_000_000,
                "text_input_cached": 1.25 / 1_000_000,
            },
        }

    def get_pricing(self, model: str) -> Dict[str, float]:
        return self._pricing_cache.get(model, self._pricing_cache.get("gpt-4o-mini", {}))

    def get_pricing_display(self, model: str) -> Dict[str, str]:
        pricing = self.get_pricing(model)
        return {
            key: f"${value * 1_000_000:.2f}/1M tokens"
            for key, value in pricing.items()
        }

    def update_pricing(self, model: str, pricing: Dict[str, float]) -> None:
        self._pricing_cache[model] = pricing
        logger.info(f"Updated pricing for {model}")

    async def fetch_usage_costs(self, start_date: str, end_date: str) -> Dict:
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            return {"error": "No API key configured"}

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}"}
            params = {
                "start_date": start_date,
                "end_date": end_date,
            }
            try:
                async with session.get(
                    "https://api.openai.com/v1/organization/costs",
                    headers=headers,
                    params=params,
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        error = await resp.text()
                        logger.error(f"Failed to fetch costs: {error}")
                        return {"error": error}
            except Exception as e:
                logger.error(f"Error fetching costs: {e}")
                return {"error": str(e)}

    async def fetch_usage(self, start_date: str, end_date: str) -> Dict:
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            return {"error": "No API key configured"}

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}"}
            params = {
                "date": start_date,
            }
            try:
                async with session.get(
                    "https://api.openai.com/v1/usage",
                    headers=headers,
                    params=params,
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        error = await resp.text()
                        logger.error(f"Failed to fetch usage: {error}")
                        return {"error": error}
            except Exception as e:
                logger.error(f"Error fetching usage: {e}")
                return {"error": str(e)}


pricing_service = PricingService()
