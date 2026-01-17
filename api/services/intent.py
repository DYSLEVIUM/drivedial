import asyncio
import logging
from typing import Optional, Tuple

import aiohttp
from django.conf import settings

from api.config.loader import get_agent_config

logger = logging.getLogger("intent")


class IntentClassifier:
    def __init__(self):
        self.api_key = getattr(settings, "OPENAI_API_KEY", "")
        self.model = "gpt-4o-mini"
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=2.0)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def classify(self, transcript: str) -> Tuple[str, str]:
        if len(transcript.strip()) < 3:
            return "chat", "too_short"

        session = await self._get_session()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        config = get_agent_config()
        prompt_template = config.get("intent_classification_prompt",
                                     "You are classifying customer queries.\n\nQuery: \"{transcript}\"\n\nClassify into ONE of these:\n- FETCH: Customer wants specific data\n- CHAT: Greeting, acknowledgment, conversation\n- OFFTOPIC: Non-relevant topics\n\nRespond with ONLY one word: FETCH, CHAT, or OFFTOPIC")

        prompt = prompt_template.format(transcript=transcript)

        try:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                    "max_tokens": 100,
                }
            ) as resp:
                data = await resp.json()
                result = data.get("choices", [{}])[0].get(
                    "message", {}).get("content", "").strip().upper()

                if result == "FETCH":
                    return "fetch", "needs_data"
                elif result == "OFFTOPIC":
                    return "offtopic", "rejected"
                else:
                    return "chat", "conversation"

        except asyncio.TimeoutError:
            return "chat", "timeout"
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return "chat", "error"


intent_classifier = IntentClassifier()
