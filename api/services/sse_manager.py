import asyncio
import json
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class CarUrlEvent:
    url: str
    car_slug: str
    color: Optional[str] = None


class SSEManager:
    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._current_urls: Dict[str, CarUrlEvent] = {}

    def register(self, call_id: str) -> asyncio.Queue:
        if call_id not in self._queues:
            self._queues[call_id] = asyncio.Queue()
        return self._queues[call_id]

    def unregister(self, call_id: str) -> None:
        self._queues.pop(call_id, None)

    def get_current_url(self, call_id: str) -> Optional[CarUrlEvent]:
        return self._current_urls.get(call_id)

    async def send_url(self, call_id: str, url: str, car_slug: str, color: Optional[str] = None) -> None:
        event = CarUrlEvent(url=url, car_slug=car_slug, color=color)
        self._current_urls[call_id] = event
        
        if call_id in self._queues:
            await self._queues[call_id].put(event)

    def to_sse_data(self, event: CarUrlEvent) -> str:
        data = json.dumps({
            "url": event.url,
            "car_slug": event.car_slug,
            "color": event.color
        })
        return f"data: {data}\n\n"


sse_manager = SSEManager()

