import asyncio
import logging
from typing import Optional, Tuple

import aiohttp
from django.conf import settings

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

        prompt = f"""You are classifying customer queries for a car dealership.

Query: "{transcript}"

Classify into ONE of these:
- FETCH: Customer wants specific car data - prices, specs, features, availability, comparisons, tire size, mileage, engine, dimensions, colors, variants, test drive, financing, EMI, budget queries
- CHAT: Greeting, acknowledgment, laughter, filler words, clarification, general car conversation, or explaining concepts
- OFFTOPIC: Query is clearly asking about non-car topics (politics, weather, personal life, other products)

IMPORTANT - These are CHAT, not OFFTOPIC:
- Laughter: "ha ha ha", "haha", "hehe" → CHAT
- Acknowledgments: "ok", "okay", "theek hai", "accha", "hmm", "haan", "ji" → CHAT
- Greetings: "hello", "hi", "bye", "thank you", "goodbye" → CHAT
- Filler sounds: "uh", "um", random sounds → CHAT

Examples:
- "Ha, ha, ha, ha, ha." → CHAT (laughter)
- "tire size kya hai?" → FETCH
- "10 lakh budget" → FETCH
- "thank you bye" → CHAT
- "what is the weather?" → OFFTOPIC

Respond with ONLY one word: FETCH, CHAT, or OFFTOPIC"""

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
