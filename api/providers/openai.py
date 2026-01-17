import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

import aiohttp

from api.providers.base import VoiceProvider
from api.services.sse_manager import sse_manager
from api.services.analytics import analytics
from api.services.call_logger import CallLogger
from api.config.loader import get_agent_config
from api.tools.registry import execute_tool
from config import settings

logger = logging.getLogger("openai")


def get_tools() -> List[Dict[str, Any]]:
    config = get_agent_config()
    return config.get("tools", [])


async def web_search(query: str) -> Dict[str, Any]:
    config = get_agent_config()
    metadata = config.get("metadata", {})
    company = metadata.get("company", "Company")
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": f"You are a helpful assistant. Provide brief, factual information about {company} products and services."},
                        {"role": "user", "content": f"Brief info about: {query}"}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 150,
                },
                timeout=aiohttp.ClientTimeout(total=5.0)
            ) as resp:
                data = await resp.json()
                content = data.get("choices", [{}])[0].get(
                    "message", {}).get("content", "")
                return {"result": content, "source": "web_search"}
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return {"result": "Could not fetch information at the moment.", "source": "error"}




def build_system_prompt(customer_context: Optional[str] = None) -> str:
    config = get_agent_config()
    base_prompt = config.get("system_prompt", "")
    
    from api.data.store import store
    if hasattr(store, 'get_context_summary'):
        context_summary = store.get_context_summary()
        if context_summary:
            prompt = base_prompt.replace(
                "CONTEXT: You are selling cars.",
                f"CONTEXT: {context_summary}"
            ).replace(
                "CONTEXT: You are selling cars (Swift, Honda City, XUV700, Creta, Baleno).",
                f"CONTEXT: {context_summary}"
            )
        else:
            prompt = base_prompt
    else:
        prompt = base_prompt
    
    if customer_context:
        prompt += f"\n\n### DEDICATED CUSTOMER RELATIONSHIP\n{customer_context}\n\n**CRITICAL**: You are this customer's dedicated advisor. You remember everything about them from all previous calls. Reference specific details naturally throughout the conversation. Show you've been thinking about them. Use information from the keywords to make the conversation personal and relevant. Don't repeat basic introductions - you know them already. Pick up exactly where you left off."
    
    return prompt


class OpenAIVoiceProvider(VoiceProvider):
    AUDIO_CHUNK_DURATION_MS = 20

    def __init__(
        self,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        voice: Optional[str] = None,
        call_id: Optional[str] = None,
        customer_context: Optional[str] = None,
    ):
        config = get_agent_config()
        metadata = config.get("metadata", {})
        
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.system_prompt = system_prompt or build_system_prompt(customer_context)
        self.voice = voice or metadata.get("voice") or settings.OPENAI_VOICE
        self.temperature = settings.OPENAI_TEMPERATURE
        self.call_id = call_id
        self._is_returning_customer = customer_context is not None
        self._customer_context = customer_context

        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None

        self.on_transcript: Optional[Callable[[str, bool], None]] = None
        self.on_response_done: Optional[Callable[[], None]] = None
        self.on_end_call: Optional[Callable[[str], None]] = None
        self.on_transfer_call: Optional[Callable[[str, str], None]] = None

        self._is_user_speaking = False
        self._audio_delta_count = 0
        self._last_audio_send_time: float = 0
        self._estimated_playback_end: float = 0

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    def _is_audio_playing(self) -> bool:
        return time.time() * 1000 < self._estimated_playback_end

    async def connect(self) -> None:
        if self.is_connected:
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(
            settings.OPENAI_REALTIME_URL, headers=headers
        )

        if self.call_id:
            CallLogger.log_event(
                self.call_id, "Connected to OpenAI Realtime API")
            analytics.start_call(self.call_id)

        await self._configure_session()
        await self._send_initial_greeting()

    async def _configure_session(self) -> None:
        session_config = {
            "modalities": ["text", "audio"],
            "voice": self.voice,
            "instructions": self.system_prompt,
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "input_audio_transcription": {
                "model": "gpt-4o-transcribe"
            },
            "input_audio_noise_reduction": {
                "type": "far_field"
            },
            "turn_detection": {
                "type": "semantic_vad",
                "eagerness": "high",
                "create_response": True,
                "interrupt_response": True
            },
            "tools": get_tools(),
            "tool_choice": "auto",
            "temperature": self.temperature,
            "max_response_output_tokens": 1000,
        }

        await self._ws.send_json({
            "type": "session.update",
            "session": session_config
        })

        if self.call_id:
            CallLogger.log_event(self.call_id, "Session configured")

    async def _send_initial_greeting(self) -> None:
        config = get_agent_config()
        metadata = config.get("metadata", {})
        agent_name = metadata.get("name", "Agent")
        company = metadata.get("company", "Company")
        
        if self._is_returning_customer and self._customer_context:
            greeting_instruction = f"""You are {agent_name}, the dedicated Sales Specialist at {company} India. You have been managing this customer's account and remember all your previous conversations with them.

CUSTOMER RELATIONSHIP CONTEXT:
{self._customer_context}

You are their dedicated advisor - you think about them, remember important details, and always pick up where you left off. Greet them warmly and naturally reference something specific from your relationship history. Use their name if you know it. Show that you've been thinking about them and their needs.

Start something like "Namaste [Name]! Mai {agent_name} - aapke dedicated advisor from {company}. Aap kaise ho? Maine socha tha aapko call karun..." and naturally reference something from the context above.

Be brief, natural, warm, and show genuine care. 1-2 sentences max. ALWAYS speak in Hinglish and maintain Indian accent."""
        else:
            greeting_instruction = config.get("greeting_instruction", "Greet the customer warmly. Introduce yourself and ask how you can help. Be brief and natural.")
        
        await self._ws.send_json({
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"],
                "instructions": greeting_instruction
            }
        })

    async def disconnect(self) -> None:
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._session and not self._session.closed:
            await self._session.close()
        self._ws = None
        self._session = None

        if self.call_id:
            CallLogger.log_event(self.call_id, "Disconnected")
            analytics.end_call(self.call_id)
            cost_summary = analytics.calculate_cost(self.call_id)
            CallLogger.log_event(
                self.call_id, "Cost summary", str(cost_summary))

    async def send_audio(self, payload: str) -> None:
        if not self.is_connected:
            return
        await self._ws.send_json({
            "type": "input_audio_buffer.append",
            "audio": payload
        })

    async def cancel_response(self) -> None:
        pass

    async def listen(self) -> None:
        if self.call_id:
            CallLogger.log_event(self.call_id, "Listening started")
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(json.loads(msg.data))
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    if self.call_id:
                        CallLogger.log_error(self.call_id, "WebSocket error")
                    break
        except Exception as e:
            if self.call_id:
                CallLogger.log_error(self.call_id, f"Listener error: {e}")
            if self.on_error:
                await self.on_error(e)
        finally:
            await self.disconnect()

    async def _handle_message(self, data: dict) -> None:
        msg_type = data.get("type", "")
        handlers = {
            "response.audio.delta": self._handle_audio_delta,
            "input_audio_buffer.speech_started": self._handle_speech_started,
            "input_audio_buffer.speech_stopped": self._handle_speech_stopped,
            "conversation.item.input_audio_transcription.completed": self._handle_user_transcription,
            "response.audio_transcript.done": self._handle_assistant_transcription,
            "response.done": self._handle_response_done,
            "response.audio.done": self._handle_audio_done,
            "response.function_call_arguments.done": self._handle_function_call,
            "error": self._handle_error,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(data)

    async def _handle_audio_delta(self, data: dict) -> None:
        self._audio_delta_count += 1
        now = time.time() * 1000
        self._last_audio_send_time = now
        self._estimated_playback_end = now + \
            (self._audio_delta_count * self.AUDIO_CHUNK_DURATION_MS) + 500

        if self.on_audio:
            await self.on_audio(data.get("delta", ""))

    async def _handle_speech_started(self, data: dict) -> None:
        is_playing = self._is_audio_playing()
        self._is_user_speaking = True

        if self.call_id:
            CallLogger.log_event(
                self.call_id, f"Speech started, audio_playing={is_playing}")

        if self.on_interrupt:
            await self.on_interrupt()

    async def _handle_speech_stopped(self, data: dict) -> None:
        self._is_user_speaking = False

    async def _handle_user_transcription(self, data: dict) -> None:
        transcript = data.get("transcript", "")
        if transcript and self.call_id:
            CallLogger.log_user_speech(self.call_id, transcript)
            if self.on_transcript:
                await self.on_transcript(transcript, True)

    async def _handle_assistant_transcription(self, data: dict) -> None:
        transcript = data.get("transcript", "")
        if transcript and self.call_id:
            CallLogger.log_assistant_speech(self.call_id, transcript)
            if self.on_transcript:
                await self.on_transcript(transcript, False)

    async def _handle_response_done(self, data: dict) -> None:
        self._audio_delta_count = 0

        if self.on_response_done:
            await self.on_response_done()

        self._record_usage(data)

    async def _handle_audio_done(self, data: dict) -> None:
        pass

    async def _handle_function_call(self, data: dict) -> None:
        call_id = data.get("call_id", "")
        name = data.get("name", "")
        arguments_str = data.get("arguments", "{}")

        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError:
            arguments = {}

        if self.call_id:
            CallLogger.log_event(
                self.call_id, f"Tool: {name}", json.dumps(arguments))

        if name == "web_search":
            result = await web_search(arguments.get("query", ""))
        else:
            result = execute_tool(name, arguments)
            
            if name == "end_call" and self.on_end_call:
                await self.on_end_call(arguments.get("reason", "user_request"))
            elif name == "transfer_to_agent" and self.on_transfer_call:
                await self.on_transfer_call(
                    arguments.get("reason", "customer_escalation"),
                    arguments.get("query_type", "general")
                )
        
        if result and ("display" in name.lower() or "update" in name.lower()):
            print(f"\n{'='*60}")
            print(f"[TOOL CALL] {name}")
            print(f"[ARGUMENTS] {json.dumps(arguments, indent=2)}")
            print(f"[TOOL RESULT] {json.dumps(result, indent=2)}")
            
            if result and "url" in result and self.call_id:
                print(f"[SSE] Sending URL update to call_id: {self.call_id}")
                await sse_manager.send_url(
                    call_id=self.call_id,
                    url=result["url"],
                    car_slug=result.get("car_slug") or result.get("card_id") or result.get("item_id", ""),
                    color=result.get("color")
                )
                print(f"[SSE] Event pushed successfully!")
                print(f"[PROXY LINK] http://localhost:8000/item/{self.call_id}/")
                print(f"[URL] {result['url']}")
            elif result and "error" in result:
                print(f"[ERROR] {result['error']}")
            else:
                print(f"[ERROR] No URL generated - result: {result}")
            print(f"{'='*60}\n")

        result_str = json.dumps(
            result, ensure_ascii=False) if result is not None else "No results found"

        if self.call_id:
            count = len(result) if isinstance(
                result, list) else (1 if result else 0)
            CallLogger.log_event(self.call_id, f"Tool result: {count} items")

        await self._ws.send_json({
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": result_str
            }
        })

        await self._ws.send_json({"type": "response.create"})

    async def _handle_error(self, data: dict) -> None:
        error = data.get("error", {})
        error_msg = error.get("message", "Unknown error")
        error_code = error.get("code", "unknown")
        if self.call_id:
            CallLogger.log_error(
                self.call_id, f"OpenAI: {error_code} - {error_msg}")
        if self.on_error:
            await self.on_error(Exception(error_msg))

    def _record_usage(self, data: dict) -> None:
        if not self.call_id:
            return
        usage = data.get("response", {}).get("usage", {})
        if usage:
            tokens = {
                "text_input": usage.get("input_token_details", {}).get("text_tokens", 0),
                "text_output": usage.get("output_token_details", {}).get("text_tokens", 0),
                "audio_input": usage.get("input_token_details", {}).get("audio_tokens", 0),
                "audio_output": usage.get("output_token_details", {}).get("audio_tokens", 0),
            }
            CallLogger.log_tokens(self.call_id, "voice_agent", tokens)
            analytics.record_response_agent_usage(
                self.call_id,
                text_input=tokens["text_input"],
                text_output=tokens["text_output"],
                audio_input=tokens["audio_input"],
                audio_output=tokens["audio_output"],
            )
