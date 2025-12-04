import asyncio
import json
import logging
from typing import Any, Callable, Optional

import aiohttp
from django.conf import settings

from api.data.store import store
from api.services.analytics import analytics
from api.services.call_logger import CallLogger

logger = logging.getLogger("data_agent")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_cars",
            "description": "Search for cars based on budget range, brand, fuel type, or transmission",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget_min": {
                        "type": "integer",
                        "description": "Minimum budget in INR (e.g., 1000000 for 10 lakh)"
                    },
                    "budget_max": {
                        "type": "integer",
                        "description": "Maximum budget in INR (e.g., 1500000 for 15 lakh)"
                    },
                    "brand": {
                        "type": "string",
                        "description": "Car brand name (e.g., Maruti, Honda, Mahindra, Hyundai)"
                    },
                    "fuel_type": {
                        "type": "string",
                        "enum": ["Petrol", "Diesel"],
                        "description": "Fuel type preference"
                    },
                    "transmission": {
                        "type": "string",
                        "enum": ["Manual", "Automatic", "CVT"],
                        "description": "Transmission type preference"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_car_details",
            "description": "Get detailed information about a specific car by its ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "car_id": {
                        "type": "string",
                        "description": "The unique identifier of the car"
                    }
                },
                "required": ["car_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check availability of cars from a specific brand",
            "parameters": {
                "type": "object",
                "properties": {
                    "brand": {
                        "type": "string",
                        "description": "Brand name to check availability for"
                    }
                },
                "required": ["brand"]
            }
        }
    }
]


def execute_tool(name: str, arguments: dict) -> Any:
    if name == "search_cars":
        return store.search(
            budget_min=arguments.get("budget_min"),
            budget_max=arguments.get("budget_max"),
            brand=arguments.get("brand"),
            fuel_type=arguments.get("fuel_type"),
            transmission=arguments.get("transmission"),
        )
    elif name == "get_car_details":
        return store.get_car(arguments.get("car_id", ""))
    elif name == "check_availability":
        cars = store.search_by_brand(arguments.get("brand", ""))
        return [{"name": c["name"], "availability": c["availability"], "location": c["location"]} for c in cars]
    return None


class DataAgent:
    def __init__(self, call_id: str):
        self.call_id = call_id
        self.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o-mini"
        self._session: Optional[aiohttp.ClientSession] = None
        self._pending_task: Optional[asyncio.Task] = None
        self.on_data_ready: Optional[Callable[[str], None]] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=5.0)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._pending_task and not self._pending_task.done():
            self._pending_task.cancel()
            try:
                await self._pending_task
            except asyncio.CancelledError:
                pass
        if self._session and not self._session.closed:
            await self._session.close()

    async def fetch_data(self, user_query: str) -> str:
        self._pending_task = asyncio.create_task(self._do_fetch(user_query))
        return await self._pending_task

    async def fetch_data_async(self, user_query: str) -> None:
        self._pending_task = asyncio.create_task(
            self._do_fetch_and_callback(user_query))

    async def _do_fetch_and_callback(self, user_query: str) -> None:
        try:
            result = await self._do_fetch(user_query)
            if self.on_data_ready:
                await self.on_data_ready(result)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            CallLogger.log_error(self.call_id, f"Data fetch error: {e}")

    async def _do_fetch(self, user_query: str) -> str:
        CallLogger.log_data_query(self.call_id, user_query)
        session = await self._get_session()

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a data retrieval assistant for a car dealership. "
                    "Use the provided tools to fetch car information. "
                    "Parse Indian price formats: '15 lakh' = 1500000, '10L' = 1000000, '8.5 lakh' = 850000. "
                    "\n\nBUDGET INTERPRETATION (CRITICAL):\n"
                    "- When user says 'X lakh budget' or 'under X lakh', set budget_max=X, do NOT set budget_min.\n"
                    "- Only set budget_min when user explicitly says 'between X and Y' or 'minimum X'.\n"
                    "- Example: '10 lakh budget' → budget_max=1000000 (NO budget_min)\n"
                    "- Example: '10-15 lakh' → budget_min=1000000, budget_max=1500000\n"
                    "\n\nCRITICAL RULES:\n"
                    "- ONLY report data returned by tools. NEVER invent cars, prices, or features.\n"
                    "- If no results found, say 'Is range mein abhi koi car available nahi hai.'\n"
                    "- Use EXACT prices from data. Do not round or estimate.\n"
                    "- Do NOT add discounts, offers, or features not in the data.\n"
                    "\n\nOUTPUT FORMAT:\n"
                    "- Brief summary in Hinglish (2 sentences max)\n"
                    "- State car name, exact price, and availability\n"
                    "- Example: 'Sir, aapke budget mein Honda City V hai - 12 lakh, immediately available.'"
                )
            },
            {"role": "user", "content": user_query}
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        input_tokens = 0
        output_tokens = 0

        try:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "tools": TOOLS,
                    "tool_choice": "auto",
                    "temperature": 0.3,
                }
            ) as resp:
                data = await resp.json()

            if "usage" in data:
                input_tokens += data["usage"].get("prompt_tokens", 0)
                output_tokens += data["usage"].get("completion_tokens", 0)

            message = data.get("choices", [{}])[0].get("message", {})
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                content = message.get("content", "")
                CallLogger.log_data_result(self.call_id, content)
                CallLogger.log_tokens(self.call_id, "data_agent", {
                                      "input": input_tokens, "output": output_tokens})
                analytics.record_data_agent_usage(
                    self.call_id, input_tokens, output_tokens)
                return content

            messages.append(message)

            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                CallLogger.log_data_tool_call(
                    self.call_id, func_name, func_args)

                result = execute_tool(func_name, func_args)
                result_json = json.dumps(result, ensure_ascii=False)
                result_json_pretty = json.dumps(
                    result, ensure_ascii=False, indent=2)
                CallLogger.log_event(
                    self.call_id,
                    f"Tool {func_name} returned {len(result) if isinstance(result, list) else 1} items",
                    f"\n{result_json_pretty}"
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result_json
                })

            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                }
            ) as resp:
                data = await resp.json()

            if "usage" in data:
                input_tokens += data["usage"].get("prompt_tokens", 0)
                output_tokens += data["usage"].get("completion_tokens", 0)

            final_result = data.get("choices", [{}])[0].get(
                "message", {}).get("content", "")
            CallLogger.log_data_result(self.call_id, final_result)
            CallLogger.log_tokens(self.call_id, "data_agent", {
                                  "input": input_tokens, "output": output_tokens})
            analytics.record_data_agent_usage(
                self.call_id, input_tokens, output_tokens)

            return final_result

        except Exception as e:
            CallLogger.log_error(self.call_id, f"Data agent API error: {e}")
            analytics.record_data_agent_usage(
                self.call_id, input_tokens, output_tokens)
            return ""
