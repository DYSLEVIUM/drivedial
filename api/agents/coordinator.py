import asyncio
import logging
from typing import Callable, Optional, Tuple

from api.agents.data_agent import DataAgent
from api.services.analytics import LatencyTracker, analytics
from api.services.call_logger import CallLogger
from api.services.intent import intent_classifier

logger = logging.getLogger("coordinator")

REJECTION_MESSAGE = (
    "Sir, main sirf car sales aur gaadi ke baare mein help kar sakta hoon. "
    "Kya aap kisi car ke baare mein jaanna chahte hain?"
)


class AgentCoordinator:
    def __init__(self, call_id: str):
        self.call_id = call_id
        self.data_agent = DataAgent(call_id)
        self._pending_data: Optional[str] = None
        self._data_ready_event = asyncio.Event()
        self.on_inject_context: Optional[Callable[[str], None]] = None
        self.on_inject_rejection: Optional[Callable[[str], None]] = None
        self._intent_task: Optional[asyncio.Task] = None
        self._filler_task: Optional[asyncio.Task] = None
        self._data_fetch_in_progress = False  # Prevent duplicate fetches

        analytics.start_call(call_id)

    async def close(self) -> None:
        for task in [self._intent_task, self._filler_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        await asyncio.gather(
            self.data_agent.close(),
            intent_classifier.close(),
            return_exceptions=True
        )
        analytics.end_call(self.call_id)
        cost_summary = analytics.calculate_cost(self.call_id)
        CallLogger.log_event(self.call_id, "Cost summary", str(cost_summary))

    async def process_transcript(self, transcript: str) -> Tuple[Optional[str], str]:
        intent, reason = await intent_classifier.classify(transcript)
        CallLogger.log_event(self.call_id, f"Intent: {intent}", reason)

        if intent == "offtopic":
            if self.on_inject_rejection:
                await self.on_inject_rejection(REJECTION_MESSAGE)
            return None, "offtopic"

        if intent != "fetch":
            return None, "chat"

        # Prevent duplicate data fetches - if one is already in progress, skip
        if self._data_fetch_in_progress:
            CallLogger.log_event(
                self.call_id, "Data fetch SKIPPED", "already in progress")
            return None, "fetch_skipped"

        self._data_fetch_in_progress = True
        CallLogger.log_event(
            self.call_id, "Data fetch triggered", transcript[:50])

        async def on_data_ready(data: str):
            self._data_fetch_in_progress = False
            self._pending_data = data
            self._data_ready_event.set()
            if self.on_inject_context and data:
                await self.on_inject_context(data)

        self.data_agent.on_data_ready = on_data_ready
        asyncio.create_task(self.data_agent.fetch_data_async(transcript))

        # Filler disabled - it was causing interruption of ongoing responses
        # The voice agent will naturally handle the pause while data is fetched
        return None, "fetch"

    async def wait_for_data(self, timeout: float = 5.0) -> Optional[str]:
        try:
            await asyncio.wait_for(self._data_ready_event.wait(), timeout)
            self._data_ready_event.clear()
            data = self._pending_data
            self._pending_data = None
            return data
        except asyncio.TimeoutError:
            return None

    def get_pending_data(self) -> Optional[str]:
        if self._pending_data:
            data = self._pending_data
            self._pending_data = None
            self._data_ready_event.clear()
            return data
        return None

    def record_latency(self, latency_ms: float) -> None:
        analytics.record_latency(self.call_id, latency_ms)

    def create_latency_tracker(self) -> LatencyTracker:
        return LatencyTracker(analytics, self.call_id)
