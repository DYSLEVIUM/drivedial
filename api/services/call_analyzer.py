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
    
    ANALYSIS_PROMPT = """You are analyzing a sales call log from Acko Drive (a car sales platform). 
Extract key information and provide a structured analysis.

CALL LOG:
{log_content}

Analyze this call and return a JSON object with these exact fields:
{{
    "summary": "2-3 sentence summary of the call - what customer wanted, what was discussed, outcome",
    "customer_name": "Customer's name if mentioned, null otherwise",
    "lead_quality": "HOT (ready to buy), WARM (interested but hesitant), or COLD (just browsing/not interested)",
    "purchase_likelihood": "HIGH (likely to buy soon), MEDIUM (may buy), LOW (unlikely)",
    "call_outcome": "BOOKING_CONFIRMED, INTERESTED, CALLBACK_REQUESTED, TRANSFERRED, DROPPED, or NOT_INTERESTED",
    "preferred_car": "The main car customer showed interest in (model name), null if none",
    "preferred_color": "Color preference if mentioned, null otherwise",
    "budget_range": "Budget mentioned (e.g., '10-12 lakh'), null if not discussed",
    "cars_discussed": ["list", "of", "car", "models", "discussed"],
    "objections": ["list of objections/concerns raised by customer, e.g., 'price too high', 'delivery time', 'safety concerns'"]
}}

IMPORTANT:
- For lead_quality: HOT = asked about booking/delivery/colors, WARM = asked questions/compared options, COLD = vague/ended quickly
- For call_outcome: If call ended abruptly without clear outcome, use DROPPED
- Extract actual car model names (e.g., "Grand Vitara", "Brezza", "Nexon") not full variant names
- Return ONLY valid JSON, no explanations."""

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
            logger.error(f"Error analyzing call {call_id}: {e}")
        
        return self._get_default_analysis(call_id, phone_number, log_content)
    
    def _get_default_analysis(self, call_id: str, phone_number: str, log_content: str) -> Dict[str, Any]:
        """Return default analysis when GPT fails."""
        return {
            'call_id': call_id,
            'phone_number': phone_number,
            'summary': 'Call ended without detailed interaction.',
            'customer_name': None,
            'lead_quality': 'COLD',
            'purchase_likelihood': 'LOW',
            'call_outcome': 'DROPPED',
            'preferred_car': None,
            'preferred_color': None,
            'budget_range': None,
            'cars_discussed': [],
            'objections': [],
            'call_duration_seconds': self._calculate_duration(log_content),
        }
    
    async def _call_gpt(self, conversation: str) -> Optional[Dict[str, Any]]:
        """Call GPT to analyze the conversation."""
        prompt = self.ANALYSIS_PROMPT.format(log_content=conversation[:8000])  # Limit content
        
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
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse GPT response: {e}")
                    return None
    
    async def save_analysis(self, analysis: Dict[str, Any]) -> bool:
        """Save the analysis to the database."""
        from api.models import CallSummary
        
        try:
            summary = CallSummary(
                call_id=analysis['call_id'],
                phone_number=analysis['phone_number'],
                customer_name=analysis.get('customer_name'),
                summary=analysis.get('summary', ''),
                lead_quality=analysis.get('lead_quality', 'WARM'),
                purchase_likelihood=analysis.get('purchase_likelihood', 'MEDIUM'),
                call_outcome=analysis.get('call_outcome', 'DROPPED'),
                cars_discussed=analysis.get('cars_discussed', []),
                preferred_car=analysis.get('preferred_car'),
                preferred_color=analysis.get('preferred_color'),
                budget_range=analysis.get('budget_range'),
                objections=analysis.get('objections', []),
                call_duration_seconds=analysis.get('call_duration_seconds', 0),
                is_latest=True,
            )
            
            # Use sync_to_async for Django ORM operations
            from asgiref.sync import sync_to_async
            await sync_to_async(summary.save)()
            
            logger.info(f"Saved call summary for {analysis['call_id']}: {analysis.get('call_outcome')}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving call summary: {e}")
            return False
    
    async def get_customer_context(self, phone_number: str) -> Optional[str]:
        """Get context string for a returning customer."""
        from api.models import CallSummary
        from asgiref.sync import sync_to_async
        
        try:
            latest = await sync_to_async(CallSummary.get_latest_for_phone)(phone_number)
            if latest:
                return await sync_to_async(latest.to_context_string)()
        except Exception as e:
            logger.error(f"Error getting customer context: {e}")
        
        return None


# Singleton instance
call_analyzer = CallAnalyzer()
