import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from api.services.pricing import pricing_service

logger = logging.getLogger("analytics")


@dataclass
class TokenUsage:
    text_input: int = 0
    text_output: int = 0
    audio_input: int = 0
    audio_output: int = 0


@dataclass
class CallMetrics:
    call_id: str
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    response_agent_usage: TokenUsage = field(default_factory=TokenUsage)
    data_agent_usage: TokenUsage = field(default_factory=TokenUsage)
    data_fetches: int = 0
    avg_response_latency_ms: float = 0.0
    latency_samples: List[float] = field(default_factory=list)

    def record_latency(self, latency_ms: float) -> None:
        self.latency_samples.append(latency_ms)
        self.avg_response_latency_ms = sum(
            self.latency_samples) / len(self.latency_samples)


class Analytics:
    def __init__(self):
        self._calls: Dict[str, CallMetrics] = {}
        self._current_call_id: Optional[str] = None

    def start_call(self, call_id: str) -> CallMetrics:
        metrics = CallMetrics(call_id=call_id)
        self._calls[call_id] = metrics
        self._current_call_id = call_id
        logger.info(f"[Analytics] Call started: {call_id}")
        return metrics

    def end_call(self, call_id: str) -> Optional[CallMetrics]:
        if call_id not in self._calls:
            return None
        metrics = self._calls[call_id]
        metrics.ended_at = datetime.now()
        self._log_call_summary(metrics)
        return metrics

    def get_call(self, call_id: str) -> Optional[CallMetrics]:
        return self._calls.get(call_id)

    def record_response_agent_usage(
        self,
        call_id: str,
        text_input: int = 0,
        text_output: int = 0,
        audio_input: int = 0,
        audio_output: int = 0,
    ) -> None:
        if call_id not in self._calls:
            return
        usage = self._calls[call_id].response_agent_usage
        usage.text_input += text_input
        usage.text_output += text_output
        usage.audio_input += audio_input
        usage.audio_output += audio_output

    def record_data_agent_usage(
        self,
        call_id: str,
        text_input: int = 0,
        text_output: int = 0,
    ) -> None:
        if call_id not in self._calls:
            return
        usage = self._calls[call_id].data_agent_usage
        usage.text_input += text_input
        usage.text_output += text_output
        self._calls[call_id].data_fetches += 1

    def record_latency(self, call_id: str, latency_ms: float) -> None:
        if call_id not in self._calls:
            return
        self._calls[call_id].record_latency(latency_ms)

    def calculate_cost(
        self,
        call_id: str,
        response_model: str = "gpt-4o-mini-realtime-preview-2024-12-17",
        data_model: str = "gpt-4o-mini",
    ) -> Dict:
        if call_id not in self._calls:
            return {"error": "Call not found"}

        metrics = self._calls[call_id]
        response_pricing = pricing_service.get_pricing(response_model)
        data_pricing = pricing_service.get_pricing(data_model)

        response_cost = (
            metrics.response_agent_usage.text_input * response_pricing.get("text_input", 0) +
            metrics.response_agent_usage.text_output * response_pricing.get("text_output", 0) +
            metrics.response_agent_usage.audio_input * response_pricing.get("audio_input", 0) +
            metrics.response_agent_usage.audio_output *
            response_pricing.get("audio_output", 0)
        )

        data_cost = (
            metrics.data_agent_usage.text_input * data_pricing.get("text_input", 0) +
            metrics.data_agent_usage.text_output *
            data_pricing.get("text_output", 0)
        )

        return {
            "response_agent": {
                "model": response_model,
                "tokens": {
                    "text_input": metrics.response_agent_usage.text_input,
                    "text_output": metrics.response_agent_usage.text_output,
                    "audio_input": metrics.response_agent_usage.audio_input,
                    "audio_output": metrics.response_agent_usage.audio_output,
                },
                "cost_usd": round(response_cost, 6),
            },
            "data_agent": {
                "model": data_model,
                "tokens": {
                    "text_input": metrics.data_agent_usage.text_input,
                    "text_output": metrics.data_agent_usage.text_output,
                },
                "cost_usd": round(data_cost, 6),
                "fetches": metrics.data_fetches,
            },
            "total_cost_usd": round(response_cost + data_cost, 6),
            "avg_latency_ms": round(metrics.avg_response_latency_ms, 2),
        }

    def _log_call_summary(self, metrics: CallMetrics) -> None:
        cost = self.calculate_cost(metrics.call_id)
        duration = (metrics.ended_at -
                    metrics.started_at).total_seconds() if metrics.ended_at else 0
        logger.info(
            f"[Analytics] Call ended: {metrics.call_id} | "
            f"Duration: {duration:.1f}s | "
            f"Cost: ${cost['total_cost_usd']:.4f} | "
            f"Avg Latency: {cost['avg_latency_ms']}ms | "
            f"Data Fetches: {cost['data_agent']['fetches']}"
        )


class LatencyTracker:
    def __init__(self, analytics_instance: Analytics, call_id: str):
        self.analytics = analytics_instance
        self.call_id = call_id
        self._start: Optional[float] = None

    def start(self) -> None:
        self._start = time.perf_counter()

    def stop(self) -> float:
        if self._start is None:
            return 0.0
        latency_ms = (time.perf_counter() - self._start) * 1000
        self.analytics.record_latency(self.call_id, latency_ms)
        self._start = None
        return latency_ms

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


analytics = Analytics()
