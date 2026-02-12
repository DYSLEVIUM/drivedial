import asyncio
import json
import os
import ssl
import sys
import aiohttp

# 1. HARDCODED CONFIGURATION (To ensure no ENV variables override it)
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-2.0-flash-exp"  # <--- This is the critical fix
URL = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={API_KEY}"


async def main():
    print(f"--- Gemini Live Test ({MODEL}) ---")

    # SSL Context (Fixes local certificate issues)
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession() as session:
        try:
            async with session.ws_connect(URL, ssl=ssl_ctx) as ws:
                print("✓ Connected to WebSocket")

                # 2. SEND SETUP
                msg_setup = {
                    "setup": {
                        "model": f"models/{MODEL}",
                        "generation_config": {
                            "response_modalities": ["AUDIO"],
                            "speech_config": {
                                "voice_config": {"prebuilt_voice_config": {"voice_name": "Puck"}}
                            }
                        }
                    }
                }
                await ws.send_json(msg_setup)
                print("✓ Setup sent")

                # 3. SEND PROMPT IMMEDIATELY (Do not wait)
                msg_prompt = {
                    "client_content": {
                        "turns": [{"role": "user", "parts": [{"text": "Say hello!"}]}],
                        "turn_complete": True
                    }
                }
                await ws.send_json(msg_prompt)
                print("✓ Prompt sent... waiting for audio...")

                # 4. LISTEN
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        # Check for Audio
                        if "serverContent" in data:
                            if "modelTurn" in data["serverContent"]:
                                parts = data["serverContent"]["modelTurn"].get("parts", [])
                                for p in parts:
                                    if "inlineData" in p:
                                        print("!!! SUCCESS: Audio Data Received !!!")
                                        return
                        if "error" in data:
                            print(f"ERROR: {data['error']}")
                            return
        except Exception as e:
            print(f"Exception: {e}")
