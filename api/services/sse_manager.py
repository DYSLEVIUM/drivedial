import asyncio
import json
from typing import Dict, Optional, Set
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
        self._active_sessions: Set[str] = set()
        self._debug = True  # Enable debug logging

    def start_session(self, call_id: str) -> None:
        """Mark a session as active when a call starts."""
        self._active_sessions.add(call_id)
        if self._debug:
            print(f"[SSE_MANAGER] Session started: {call_id}")

    def end_session(self, call_id: str) -> None:
        """Mark a session as ended and clean up data."""
        self._active_sessions.discard(call_id)
        self._current_urls.pop(call_id, None)
        # Send session_ended event to any connected clients
        if call_id in self._queues:
            try:
                self._queues[call_id].put_nowait({"type": "session_ended"})
            except asyncio.QueueFull:
                pass

    def is_session_active(self, call_id: str) -> bool:
        """Check if a call session is still active."""
        return call_id in self._active_sessions

    def register(self, call_id: str) -> asyncio.Queue:
        if call_id not in self._queues:
            self._queues[call_id] = asyncio.Queue()
            if self._debug:
                print(f"[SSE_MANAGER] Queue registered for call_id: {call_id}")
        return self._queues[call_id]

    def unregister(self, call_id: str) -> None:
        self._queues.pop(call_id, None)

    def get_current_url(self, call_id: str) -> Optional[CarUrlEvent]:
        return self._current_urls.get(call_id)

    async def send_url(self, call_id: str, url: str, car_slug: str, color: Optional[str] = None) -> None:
        event = CarUrlEvent(url=url, car_slug=car_slug, color=color)
        self._current_urls[call_id] = event
        
        if self._debug:
            print(f"[SSE_MANAGER] send_url called")
            print(f"[SSE_MANAGER] call_id: {call_id}")
            print(f"[SSE_MANAGER] url: {url}")
            print(f"[SSE_MANAGER] car_slug: {car_slug}, color: {color}")
            print(f"[SSE_MANAGER] Session active: {call_id in self._active_sessions}")
            print(f"[SSE_MANAGER] Queue exists: {call_id in self._queues}")
            print(f"[SSE_MANAGER] Active sessions: {self._active_sessions}")
        
        if call_id in self._queues:
            await self._queues[call_id].put(event)
            if self._debug:
                print(f"[SSE_MANAGER] Event queued successfully!")
        else:
            if self._debug:
                print(f"[SSE_MANAGER] WARNING: No queue for call_id {call_id} - no client connected to SSE")

    def to_sse_data(self, event) -> str:
        # Handle session_ended event
        if isinstance(event, dict) and event.get("type") == "session_ended":
            return f"data: {json.dumps({'type': 'session_ended'})}\n\n"
        
        data = json.dumps({
            "url": event.url,
            "car_slug": event.car_slug,
            "color": event.color
        })
        return f"data: {data}\n\n"


sse_manager = SSEManager()

