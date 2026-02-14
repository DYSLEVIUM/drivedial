import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger("token_tracker")

# CONFIGURATION
USD_TO_INR = Decimal("90.00")


class ModelType(str, Enum):
    """Supported model types for tracking."""
    VOICE_AGENT = "voice_agent"  # Realtime API
    CALL_ANALYSIS = "call_analysis"  # Post-call analysis
    WEB_SEARCH = "web_search"  # Web search queries
    FUNCTION_CALL = "function_call"  # Tool overhead
    OTHER = "other"


@dataclass
class TokenUsageRecord:
    """Single token usage record from one API invocation."""
    model_type: ModelType
    model_name: str
    timestamp: datetime

    # Input tokens
    input_tokens_text: int = 0
    input_tokens_audio: int = 0
    input_tokens_cached: int = 0

    # Output tokens
    output_tokens_text: int = 0
    output_tokens_audio: int = 0

    # Raw totals from API
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    context: Optional[str] = None


@dataclass
class ModelUsageSummary:
    """Aggregated usage for a single model type."""
    model_type: ModelType
    model_name: str
    invocation_count: int = 0

    # Aggregated input tokens
    total_input_text: int = 0
    total_input_audio: int = 0
    total_input_cached: int = 0

    # Aggregated output tokens
    total_output_text: int = 0
    total_output_audio: int = 0

    # Cost in USD (Internal storage)
    cost_usd: Decimal = Decimal("0")

    @property
    def cost_inr(self) -> Decimal:
        """Returns cost converted to INR."""
        return self.cost_usd * USD_TO_INR

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type.value,
            "model_name": self.model_name,
            "invocations": self.invocation_count,
            "input": {
                "text_tokens": self.total_input_text,
                "audio_tokens": self.total_input_audio,
                "cached_tokens": self.total_input_cached,
            },
            "output": {
                "text_tokens": self.total_output_text,
                "audio_tokens": self.total_output_audio,
            },
            # Return both USD and INR for clarity
            "cost_usd": float(self.cost_usd.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
            "cost_inr": float(self.cost_inr.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        }


@dataclass
class CallTokenAnalysis:
    """Complete token analysis for a single call."""
    call_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    records: List[TokenUsageRecord] = field(default_factory=list)
    summaries: Dict[ModelType, ModelUsageSummary] = field(default_factory=dict)

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cached_tokens: int = 0

    # Internal storage in USD
    total_cost_usd: Decimal = Decimal("0")

    @property
    def total_cost_inr(self) -> Decimal:
        return self.total_cost_usd * USD_TO_INR

    def add_record(self, record: TokenUsageRecord) -> None:
        self.records.append(record)
        self._update_summary(record)
        self._update_totals(record)

    def _update_summary(self, record: TokenUsageRecord) -> None:
        key = record.model_type
        if key not in self.summaries:
            self.summaries[key] = ModelUsageSummary(
                model_type=record.model_type,
                model_name=record.model_name,
            )

        s = self.summaries[key]
        s.invocation_count += 1
        s.total_input_text += record.input_tokens_text
        s.total_input_audio += record.input_tokens_audio
        s.total_input_cached += record.input_tokens_cached
        s.total_output_text += record.output_tokens_text
        s.total_output_audio += record.output_tokens_audio

    def _update_totals(self, record: TokenUsageRecord) -> None:
        self.total_input_tokens += record.total_input_tokens
        self.total_output_tokens += record.total_output_tokens
        self.total_cached_tokens += record.input_tokens_cached

    def to_log_string(self) -> str:
        lines = [
            "=" * 60,
            f" CALL ANALYSIS: {self.call_id}",
            "=" * 60,
            # SHOW FINAL COST IN INR
            f"Total Cost:   ₹{float(self.total_cost_inr):.4f} INR  (${float(self.total_cost_usd):.6f} USD)",
            f"Total Tokens: {self.total_input_tokens + self.total_output_tokens:,}",
            f"Cached Ratio: {(self.total_cached_tokens / max(1, self.total_input_tokens) * 100):.1f}%",
            "-" * 60,
        ]
        for m_type, s in self.summaries.items():
            lines.append(f"[{m_type.value.upper()}] {s.model_name}")
            lines.append(f"  In:  TXT {s.total_input_text} | AUD {s.total_input_audio} | CACHED {s.total_input_cached}")
            lines.append(f"  Out: TXT {s.total_output_text} | AUD {s.total_output_audio}")
            lines.append(f"  Cost: ₹{float(s.cost_inr):.4f}")
            lines.append("")
        return "\n".join(lines)


class TokenTracker:
    _instance: Optional["TokenTracker"] = None
    _calls: Dict[str, CallTokenAnalysis] = {}

    # ---------------------------------------------------------
    # PRICING CONFIGURATION (USD)
    # Stored as raw USD per token (Price / 1,000,000)
    # ---------------------------------------------------------
    PRICING: Dict[str, Dict[str, Decimal]] = {

        # 1. GPT-4o MINI REALTIME (Preview 2024-12-17)
        "gpt-4o-mini-realtime-preview-2024-12-17": {
            "text_input": Decimal("0.60") / Decimal("1000000"),
            "text_input_cached": Decimal("0.30") / Decimal("1000000"),
            "text_output": Decimal("2.40") / Decimal("1000000"),
            "audio_input": Decimal("10.00") / Decimal("1000000"),
            "audio_input_cached": Decimal("0.30") / Decimal("1000000"),
            "audio_output": Decimal("20.00") / Decimal("1000000"),
        },

        # 2. GPT-4o REALTIME (Preview 2025-06-03)
        "gpt-4o-realtime-preview-2025-06-03": {
            "text_input": Decimal("5.00") / Decimal("1000000"),
            "text_input_cached": Decimal("2.50") / Decimal("1000000"),
            "text_output": Decimal("20.00") / Decimal("1000000"),
            "audio_input": Decimal("40.00") / Decimal("1000000"),
            "audio_input_cached": Decimal("2.50") / Decimal("1000000"),
            "audio_output": Decimal("80.00") / Decimal("1000000"),
        },

        # 3. GPT REALTIME MINI (2025-12-15)
        # Note: Text Cached is $0.06
        "gpt-realtime-mini-2025-12-15": {
            "text_input": Decimal("0.60") / Decimal("1000000"),
            "text_input_cached": Decimal("0.06") / Decimal("1000000"),
            "text_output": Decimal("2.40") / Decimal("1000000"),
            "audio_input": Decimal("10.00") / Decimal("1000000"),
            "audio_input_cached": Decimal("0.30") / Decimal("1000000"),
            "audio_output": Decimal("20.00") / Decimal("1000000"),
        },

        # 4. GPT REALTIME (2025-08-28)
        "gpt-realtime-2025-08-28": {
            "text_input": Decimal("4.00") / Decimal("1000000"),
            "text_input_cached": Decimal("0.40") / Decimal("1000000"),
            "text_output": Decimal("16.00") / Decimal("1000000"),
            "audio_input": Decimal("32.00") / Decimal("1000000"),
            "audio_input_cached": Decimal("0.40") / Decimal("1000000"),
            "audio_output": Decimal("64.00") / Decimal("1000000"),
        },

        # ---------------------------------------------------------
        # GEMINI MODELS (Google)
        # ---------------------------------------------------------

        # 5. Gemini 2.0 Flash Live (Multimodal Live API)
        "gemini-2.5-flash-native-audio-preview-12-2025": {
            "text_input": Decimal("0.50") / Decimal("1000000"),
            "text_input_cached": Decimal("0.50") / Decimal("1000000"),
            "text_output": Decimal("2.00") / Decimal("1000000"),
            "audio_input": Decimal("3.00") / Decimal("1000000"),
            "audio_input_cached": Decimal("3.00") / Decimal("1000000"),
            "audio_output": Decimal("12.00") / Decimal("1000000"),
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def start_call(self, call_id: str) -> CallTokenAnalysis:
        analysis = CallTokenAnalysis(call_id=call_id, started_at=datetime.now())
        self._calls[call_id] = analysis
        return analysis

    def end_call(self, call_id: str) -> Optional[CallTokenAnalysis]:
        if call_id not in self._calls: return None
        analysis = self._calls[call_id]
        analysis.ended_at = datetime.now()
        self._calculate_costs(analysis)  # Final Cost Calculation
        return analysis

    def record_voice_agent_usage(self, call_id: str, usage: Dict[str, Any], model_name: str) -> None:
        """
        Record usage from Realtime API.
        Must provide model_name (e.g. 'gpt-4o-mini-realtime-preview-2024-12-17')
        """
        if call_id not in self._calls: self.start_call(call_id)

        in_details = usage.get("input_token_details", {})
        out_details = usage.get("output_token_details", {})

        record = TokenUsageRecord(
            model_type=ModelType.VOICE_AGENT,
            model_name=model_name,
            timestamp=datetime.now(),
            input_tokens_text=in_details.get("text_tokens") or usage.get("prompt_tokens_text", 0),
            input_tokens_audio=in_details.get("audio_tokens") or usage.get("prompt_tokens_audio", 0),
            input_tokens_cached=in_details.get("cached_tokens") or usage.get("prompt_tokens_cached", 0),
            output_tokens_text=out_details.get("text_tokens") or usage.get("completion_tokens_text", 0),
            output_tokens_audio=out_details.get("audio_tokens") or usage.get("completion_tokens_audio", 0),
            total_input_tokens=usage.get("input_tokens") or usage.get("prompt_tokens", 0),
            total_output_tokens=usage.get("output_tokens") or usage.get("completion_tokens", 0),
        )
        self._calls[call_id].add_record(record)

    def _calculate_costs(self, analysis: CallTokenAnalysis) -> None:
        """
        Calculates cost in USD first, then logs in INR.
        Uses Text-First Caching logic.
        """
        total_cost_usd = Decimal("0")

        for _, summary in analysis.summaries.items():
            model_name = summary.model_name
            rates = None

            # 1. Exact Match Logic
            if model_name in self.PRICING:
                rates = self.PRICING[model_name]
            else:
                # 2. Fallback: Check if known key is substring of model name
                for key in self.PRICING:
                    if key in model_name:
                        rates = self.PRICING[key]
                        break

            # 3. Last Resort Fallback (Use Mini rates if unknown)
            if not rates:
                rates = self.PRICING["gpt-4o-mini-realtime-preview-2024-12-17"]
                logger.warning(f"Unknown model '{model_name}'. Using fallback pricing.")

            cost = Decimal("0")

            # --- OUTPUT COST (USD) ---
            cost += Decimal(summary.total_output_text) * rates["text_output"]
            cost += Decimal(summary.total_output_audio) * rates["audio_output"]

            # --- INPUT COST (Caching Logic) ---
            # Assumption: Cached tokens apply to TEXT inputs first, then AUDIO.

            total_cached = summary.total_input_cached

            # Step A: Apply cache to Text
            text_cached_count = min(total_cached, summary.total_input_text)
            text_paid_count = max(0, summary.total_input_text - text_cached_count)

            # Step B: Apply remaining cache to Audio
            remaining_cache = total_cached - text_cached_count
            audio_cached_count = min(remaining_cache, summary.total_input_audio)
            audio_paid_count = max(0, summary.total_input_audio - audio_cached_count)

            # Step C: Calculate Input Costs (USD)
            cost += Decimal(text_paid_count) * rates["text_input"]
            cost += Decimal(text_cached_count) * rates["text_input_cached"]

            cost += Decimal(audio_paid_count) * rates["audio_input"]
            cost += Decimal(audio_cached_count) * rates["audio_input_cached"]

            summary.cost_usd = cost
            total_cost_usd += cost

        analysis.total_cost_usd = total_cost_usd

    def get_analysis_log(self, call_id: str) -> str:
        return self._calls[call_id].to_log_string() if call_id in self._calls else "Call not found"

    def cleanup_call(self, call_id: str) -> None:
        if call_id in self._calls:
            del self._calls[call_id]


token_tracker = TokenTracker()