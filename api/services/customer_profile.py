import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from asgiref.sync import sync_to_async
from django.conf import settings

from api.models import CallSummaryShort, CustomerProfile

logger = logging.getLogger("customer_profile")


class CustomerProfileService:
    """Manages customer profiles with rolling summaries and keywords."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY

    async def generate_call_summary(self, call_id: str, phone_number: str, full_summary: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate 3-line call summary and extract keywords."""
        prompt = f"""You are analyzing a sales call. Generate a concise summary and extract important keywords.

CALL DETAILS:
- Call ID: {call_id}
- Customer: {analysis.get('customer_name', 'Unknown')}
- Full Summary: {full_summary}
- Preferred Item: {analysis.get('preferred_item', 'None')}
- Budget: {analysis.get('budget_range', 'Not discussed')}
- Outcome: {analysis.get('call_outcome', 'Unknown')}
- Items Discussed: {', '.join(analysis.get('items_discussed', []))}
- Objections: {', '.join(analysis.get('objections', []))}

Generate:
1. A 3-line summary (exactly 3 lines, each line should be a complete sentence)
2. Up to 5 important keywords/phrases that capture:
   - Personal context (e.g., "planning to buy house", "family expanding")
   - Preferences (e.g., "prefers premium features", "budget conscious")
   - Life events (e.g., "recently got promoted", "moving to new city")
   - Important details that may not be in the summary but are valuable for future conversations

Return JSON:
{{
    "summary": "Line 1\\nLine 2\\nLine 3",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}"""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 300,
                    "response_format": {"type": "json_object"}
                }

                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10.0)
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"GPT API error: {resp.status}")
                        return None

                    data = await resp.json()
                    content = data.get("choices", [{}])[0].get(
                        "message", {}).get("content", "")

                    try:
                        result = json.loads(content)
                        summary = result.get("summary", "")
                        keywords = result.get("keywords", [])[:5]

                        if not summary:
                            lines = full_summary.split('.')[:3]
                            summary = '.\n'.join([l.strip()
                                                 for l in lines if l.strip()])

                        return {
                            "summary": summary,
                            "keywords": keywords if keywords else []
                        }
                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Failed to parse GPT response: {e}, using fallback")
                        lines = full_summary.split('.')[:3]
                        fallback_summary = '.\n'.join(
                            [l.strip() for l in lines if l.strip()])
                        return {
                            "summary": fallback_summary,
                            "keywords": []
                        }
        except Exception as e:
            logger.error(f"Error generating call summary: {e}, using fallback")
            lines = full_summary.split('.')[:3]
            fallback_summary = '.\n'.join(
                [l.strip() for l in lines if l.strip()])
            return {
                "summary": fallback_summary,
                "keywords": []
            }

    async def update_rolling_summary(self, phone_number: str, new_call_summary: str, new_keywords: List[str]) -> bool:
        """Update rolling summary using LLM to merge new call with existing summary."""
        profile, created = await sync_to_async(CustomerProfile.objects.get_or_create)(
            phone_number=phone_number,
            defaults={"rolling_summary": new_call_summary,
                      "keywords": new_keywords, "total_calls": 1}
        )

        if not created:
            existing_summary = profile.rolling_summary
            existing_keywords = profile.keywords or []

            prompt = f"""You are maintaining a rolling summary of customer interactions. Merge the new call information into the existing summary.

EXISTING ROLLING SUMMARY (3 lines):
{existing_summary}

NEW CALL SUMMARY (3 lines):
{new_call_summary}

EXISTING KEYWORDS: {', '.join(existing_keywords[-20:])}
NEW KEYWORDS: {', '.join(new_keywords)}

Create a NEW 3-line rolling summary that:
1. Captures the most important information from BOTH the existing summary and new call
2. Maintains continuity and shows the relationship evolution
3. Is exactly 3 lines (each line is a complete sentence)
4. Focuses on what's most relevant for future conversations

Also, merge keywords intelligently:
- Keep important existing keywords that are still relevant
- Add new important keywords
- Remove outdated or less relevant keywords
- Maximum 50 keywords total

Return JSON:
{{
    "summary": "Line 1\\nLine 2\\nLine 3",
    "keywords": ["keyword1", "keyword2", ...]
}}"""

            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    }

                    payload = {
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 400,
                        "response_format": {"type": "json_object"}
                    }

                    async with session.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=15.0)
                    ) as resp:
                        if resp.status != 200:
                            logger.error(f"GPT API error: {resp.status}")
                            return False

                        data = await resp.json()
                        content = data.get("choices", [{}])[0].get(
                            "message", {}).get("content", "")

                        try:
                            result = json.loads(content)
                            profile.rolling_summary = result.get(
                                "summary", new_call_summary)
                            merged_keywords = result.get(
                                "keywords", existing_keywords + new_keywords)
                            profile.keywords = merged_keywords[:50] if isinstance(
                                merged_keywords, list) else (existing_keywords + new_keywords)[:50]
                            profile.total_calls += 1
                            await sync_to_async(profile.save)()
                            return True
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Failed to parse GPT response: {e}, using fallback merge")
                            profile.rolling_summary = f"{existing_summary}\n{new_call_summary}"
                            profile.keywords = (
                                existing_keywords + new_keywords)[:50]
                            profile.total_calls += 1
                            await sync_to_async(profile.save)()
                            return True
            except Exception as e:
                logger.error(
                    f"Error updating rolling summary: {e}, using fallback merge")
                profile.rolling_summary = f"{existing_summary}\n{new_call_summary}"
                profile.keywords = (existing_keywords + new_keywords)[:50]
                profile.total_calls += 1
                await sync_to_async(profile.save)()
                return True
        else:
            return True

    async def save_call_summary(self, call_id: str, phone_number: str, summary: str, keywords: List[str]) -> bool:
        """Save the 3-line call summary."""
        try:
            call_summary = CallSummaryShort(
                call_id=call_id,
                phone_number=phone_number,
                summary=summary,
                keywords=keywords
            )
            await sync_to_async(call_summary.save)()
            return True
        except Exception as e:
            logger.error(f"Error saving call summary: {e}")
            return False

    async def get_customer_profile(self, phone_number: str) -> Optional[CustomerProfile]:
        """Get customer profile for a phone number."""
        try:
            return await sync_to_async(CustomerProfile.objects.filter(phone_number=phone_number).first)()
        except Exception as e:
            logger.error(f"Error getting customer profile: {e}")
            return None

    async def update_profile_metadata(self, phone_number: str, call_id: str, customer_name: Optional[str] = None) -> bool:
        """Update profile metadata after a call."""
        try:
            profile = await self.get_customer_profile(phone_number)
            if profile:
                profile.last_call_id = call_id
                if customer_name:
                    profile.customer_name = customer_name
                await sync_to_async(profile.save)()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating profile metadata: {e}")
            return False


customer_profile_service = CustomerProfileService()
