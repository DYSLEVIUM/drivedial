import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp
from django.conf import settings

logger = logging.getLogger("call_analyzer")


class CallAnalyzer:
    """Analyzes call logs and generates structured summaries using GPT."""

    def _get_analysis_prompt(self) -> str:
        from api.config.loader import get_agent_config
        config = get_agent_config()
        metadata = config.get("metadata", {})
        company = metadata.get("company", "Company")
        product_name = config.get("product_name", "product")

        return f"""You are analyzing a sales call log from {company}. 
Extract key information and provide a structured analysis.

CALL LOG:
{{log_content}}

Analyze this call and return a JSON object with these exact fields:
{{
    "summary": "2-3 sentence summary of the call - what customer wanted, what was discussed, outcome based on everything that is relevant to credit cards",
    "customer_name": "Customer's name if mentioned, null otherwise",
    "lead_quality": "HOT (ready to buy), WARM (interested but hesitant), or COLD (just browsing/not interested)",
    "purchase_likelihood": "HIGH (likely to buy soon), MEDIUM (may buy), LOW (unlikely)",
    "call_outcome": "BOOKING_CONFIRMED, INTERESTED, CALLBACK_REQUESTED, TRANSFERRED, DROPPED, or NOT_INTERESTED",
    "preferred_item": "The main {product_name} or product customer showed interest in, null if none",
    "preferred_color": "Color/preference if mentioned, null otherwise",
    "budget_range": "Budget mentioned, null if not discussed",
    "items_discussed": ["list", "of", "{product_name}s", "or", "products", "discussed"],
    "objections": ["list of objections/concerns raised by customer"]
}}

IMPORTANT:
- For lead_quality: HOT = asked about booking/delivery, WARM = asked questions/compared options, COLD = vague/ended quickly
- For call_outcome: Use CALLBACK_REQUESTED if customer explicitly asked to call back later, at a specific time, or said they're busy now but want to talk later. Examples: "call me later", "call me at 2:30", "call back tomorrow", "I'm busy now, call later"
- For call_outcome: If call ended abruptly without clear outcome, use DROPPED
- Return ONLY valid JSON, no explanations, no markdown code blocks, just the raw JSON object.
CRITICAL:
- Do not miss any information that is relevant to credit cards.
- Do not keep any information that is irrelevant to credit cards."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.logs_dir = settings.BASE_DIR / "logs" / "calls"

    def _find_log_file(self, call_id: str) -> Optional[Path]:
        """Find the log file for a given call_id."""
        if not self.logs_dir.exists():
            return None

        for log_file in self.logs_dir.glob(f"{call_id}_*.log"):
            return log_file
        return None

    def _read_log_file(self, log_path: Path) -> str:
        """Read and return log file contents."""
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading log file {log_path}: {e}")
            return ""

    def _extract_conversation(self, log_content: str) -> str:
        """Extract only the conversation parts from the log."""
        lines = []
        for line in log_content.split('\n'):
            # Include user and assistant speech, and key events
            if any(tag in line for tag in ['[USER]', '[ASSISTANT]', '[EVENT] Tool:', 'CALL STARTED', 'CALL ENDED']):
                # Clean up the line
                lines.append(line)
        return '\n'.join(lines)

    def _calculate_duration(self, log_content: str) -> int:
        """Calculate call duration from log timestamps."""
        timestamps = re.findall(r'(\d{2}:\d{2}:\d{2})', log_content)
        if len(timestamps) >= 2:
            try:
                start = datetime.strptime(timestamps[0], '%H:%M:%S')
                end = datetime.strptime(timestamps[-1], '%H:%M:%S')
                duration = (end - start).total_seconds()
                return max(0, int(duration))
            except:
                pass
        return 0

    async def analyze_call(self, call_id: str, phone_number: str) -> Optional[Dict[str, Any]]:
        """Analyze a call log and return structured data."""
        log_path = self._find_log_file(call_id)
        if not log_path:
            logger.warning(f"No log file found for call {call_id}")
            return None

        log_content = self._read_log_file(log_path)
        if not log_content:
            return None

        # Extract conversation for analysis
        conversation = self._extract_conversation(log_content)
        if len(conversation) < 100:  # Too short to analyze
            logger.warning(f"Call {call_id} too short to analyze")
            return self._get_default_analysis(call_id, phone_number, log_content)

        # Calculate duration
        duration = self._calculate_duration(log_content)

        try:
            analysis = await self._call_gpt(conversation)
            if analysis:
                analysis['call_id'] = call_id
                analysis['phone_number'] = phone_number
                analysis['call_duration_seconds'] = duration
                return analysis
        except Exception as e:
            logger.error(f"Error analyzing call {call_id}: {e}", exc_info=True)

        return self._get_default_analysis(call_id, phone_number, log_content)

    def _get_default_analysis(self, call_id: str, phone_number: str, log_content: str) -> Dict[str, Any]:
        """Return default analysis when GPT fails."""
        call_outcome = 'DROPPED'
        summary = 'Call ended without detailed interaction.'

        log_lower = log_content.lower()
        callback_keywords = [
            'call me later', 'call back', 'callback', 'call me at', 'call me tomorrow',
            'call later', 'call back later', 'call me back', 'kall karo', 'call karo',
            'baad mein call', 'phir call', '2:30', '3:30', '4:30', '5:30',
            'busy', 'abhi time nahi', 'time nahi hai'
        ]

        if any(keyword in log_lower for keyword in callback_keywords):
            call_outcome = 'CALLBACK_REQUESTED'
            summary = 'Customer requested a callback at a later time. Call ended without detailed interaction.'

        return {
            'call_id': call_id,
            'phone_number': phone_number,
            'summary': summary,
            'customer_name': None,
            'lead_quality': 'COLD',
            'purchase_likelihood': 'LOW',
            'call_outcome': call_outcome,
            'preferred_item': None,
            'preferred_color': None,
            'budget_range': None,
            'items_discussed': [],
            'objections': [],
            'call_duration_seconds': self._calculate_duration(log_content),
        }

    def _normalize_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize analysis to use generic preferred_item field."""
        normalized = analysis.copy()

        preferred_item = (
            normalized.get('preferred_item') or
            normalized.get('preferred_car') or
            normalized.get('preferred_card') or
            None
        )
        normalized['preferred_item'] = preferred_item

        if 'preferred_car' in normalized:
            del normalized['preferred_car']
        if 'preferred_card' in normalized:
            del normalized['preferred_card']

        items_discussed = (
            normalized.get('items_discussed') or
            normalized.get('cars_discussed') or
            normalized.get('cards_discussed') or
            []
        )
        normalized['items_discussed'] = items_discussed

        if 'cars_discussed' in normalized:
            del normalized['cars_discussed']
        if 'cards_discussed' in normalized:
            del normalized['cards_discussed']

        return normalized

    async def _call_gpt(self, conversation: str) -> Optional[Dict[str, Any]]:
        """Call GPT to analyze the conversation."""
        prompt_template = self._get_analysis_prompt()
        prompt = f"""{prompt_template.replace("{log_content}", conversation[:8000])}"""

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 800,
                "response_format": {"type": "json_object"}
            }

            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30.0)
            ) as resp:
                if resp.status != 200:
                    logger.error(f"GPT API error: {resp.status}")
                    return None

                data = await resp.json()
                content = data.get("choices", [{}])[0].get(
                    "message", {}).get("content", "")

                if not content:
                    logger.error("Empty response from GPT API")
                    return None

                content = content.strip()

                if content.startswith("```"):
                    lines = content.split("\n")
                    content = "\n".join(
                        lines[1:-1]) if len(lines) > 2 else content
                    content = content.strip()

                if content.startswith("```json"):
                    content = content[7:].strip()
                if content.endswith("```"):
                    content = content[:-3].strip()

                try:
                    analysis = json.loads(content)
                    if not isinstance(analysis, dict):
                        logger.error(
                            f"GPT response is not a dict: {type(analysis)}")
                        return None
                    return self._normalize_analysis(analysis)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse GPT response: {e}")
                    logger.error(
                        f"Response content (first 500 chars): {content[:500]}")
                    return None

    async def save_analysis(self, analysis: Dict[str, Any]) -> bool:
        """Save the analysis to the database."""
        from api.models import CallSummary
        from api.services.customer_profile import customer_profile_service

        normalized = self._normalize_analysis(analysis)

        try:
            summary = CallSummary(
                call_id=normalized['call_id'],
                phone_number=normalized['phone_number'],
                customer_name=normalized.get('customer_name'),
                summary=normalized.get('summary', ''),
                lead_quality=normalized.get('lead_quality', 'WARM'),
                purchase_likelihood=normalized.get(
                    'purchase_likelihood', 'MEDIUM'),
                call_outcome=normalized.get('call_outcome', 'DROPPED'),
                items_discussed=normalized.get('items_discussed', []),
                preferred_item=normalized.get('preferred_item'),
                preferred_color=normalized.get('preferred_color'),
                budget_range=normalized.get('budget_range'),
                objections=normalized.get('objections', []),
                call_duration_seconds=normalized.get(
                    'call_duration_seconds', 0),
                is_latest=True,
            )

            from asgiref.sync import sync_to_async
            await sync_to_async(summary.save)()

            call_summary_data = await customer_profile_service.generate_call_summary(
                normalized['call_id'],
                normalized['phone_number'],
                normalized.get('summary', ''),
                normalized
            )

            if call_summary_data:
                await customer_profile_service.save_call_summary(
                    normalized['call_id'],
                    normalized['phone_number'],
                    call_summary_data['summary'],
                    call_summary_data.get('keywords', [])
                )

                await customer_profile_service.update_rolling_summary(
                    normalized['phone_number'],
                    call_summary_data['summary'],
                    call_summary_data.get('keywords', [])
                )

                await customer_profile_service.update_profile_metadata(
                    normalized['phone_number'],
                    normalized['call_id'],
                    normalized.get('customer_name')
                )
            else:
                logger.warning(
                    f"Failed to generate call summary for {normalized['call_id']}, skipping profile update")

            logger.info(
                f"Saved call summary for {analysis['call_id']}: {analysis.get('call_outcome')}")
            return True

        except Exception as e:
            logger.error(f"Error saving call summary: {e}")
            return False

    async def get_customer_context(self, phone_number: str) -> Optional[str]:
        """Get context string for a returning customer using rolling summary."""
        from api.services.customer_profile import customer_profile_service

        try:
            profile = await customer_profile_service.get_customer_profile(phone_number)
            if profile:
                return profile.to_context_string()
        except Exception as e:
            logger.error(f"Error getting customer context: {e}")

        return None


# Singleton instance
call_analyzer = CallAnalyzer()
