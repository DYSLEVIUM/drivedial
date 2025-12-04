import asyncio
import json
import logging
import random
from typing import List, Optional

import aiohttp
from django.conf import settings

logger = logging.getLogger("filler")

FALLBACK_FILLERS = [
    "Hmm... ek second...",
    "Acha, dekhta hoon...",
    "Ji, ek minute...",
    "Dekhiye...",
    "Toh...",
]


class FillerGenerator:
    def __init__(self):
        self.api_key = getattr(settings, "OPENAI_API_KEY", "")
        self.model = "gpt-4o-mini"
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: List[str] = []
        self._cache_lock = asyncio.Lock()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_filler(self, context: str = "cars") -> str:
        async with self._cache_lock:
            if self._cache:
                return self._cache.pop(0)

        try:
            filler = await asyncio.wait_for(
                self._generate(context),
                timeout=1.5
            )
            if filler:
                return filler
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            logger.error(f"Filler generation error: {e}")

        return random.choice(FALLBACK_FILLERS)

    async def _generate(self, context: str) -> str:
        session = await self._get_session()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        prompt = f"""Short filler for car sales agent checking system. Context: {context}
Under 6 words. Hinglish. Example: "Hmm... ek second..."
Just the text:"""

        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 20,
            },
            timeout=aiohttp.ClientTimeout(total=1.5)
        ) as resp:
            data = await resp.json()
            filler = data.get("choices", [{}])[0].get(
                "message", {}).get("content", "").strip()
            return filler.strip('"\'') if filler else ""

    async def prefetch_cache(self, count: int = 3) -> None:
        asyncio.create_task(self._fill_cache(count))

    async def _fill_cache(self, count: int) -> None:
        session = await self._get_session()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        prompt = f"""Generate {count} short fillers for car sales agent checking system.
Hinglish. Under 6 words each.
Return JSON: {{"fillers": ["...", "..."]}}"""

        try:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8,
                    "max_tokens": 100,
                    "response_format": {"type": "json_object"},
                },
                timeout=aiohttp.ClientTimeout(total=3.0)
            ) as resp:
                data = await resp.json()
                content = data.get("choices", [{}])[0].get(
                    "message", {}).get("content", "")
                parsed = json.loads(content)
                fillers = parsed.get("fillers", [])
                if fillers:
                    async with self._cache_lock:
                        self._cache.extend(fillers)
        except Exception as e:
            logger.error(f"Cache fill error: {e}")


filler_generator = FillerGenerator()
