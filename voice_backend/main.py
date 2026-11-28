
import os
import json
import base64
import logging

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocketDisconnect
from google import genai
from google.genai import types

app = FastAPI()

logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("GEMINI_API_KEY", "")
TOKEN = os.getenv("NOVA_VOICE_ACCESS_TOKEN", "")
ORIGINS = [
    x.strip()
    for x in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if x.strip()
]

MODEL = os.getenv(
    "GEMINI_LIVE_MODEL",
    "gemini-2.5-flash-native-audio-preview-12-2025"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return {"status": "NOVA Live Voice online"}

@app.websocket("/ws")
async def voice(ws: WebSocket):

    origin = ws.headers.get("origin", "")
    token = ws.query_params.get("token", "")

    if ORIGINS and origin not in ORIGINS:
        await ws.close(code=1008)
        return

    if not TOKEN or token != TOKEN:
        await ws.close(code=1008)
        return

    if not API_KEY:
        await ws.close(code=1011)
        return

    await ws.accept()

    client = genai.Client(api_key=API_KEY)

    config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": (
            "You are NOVA AI, a friendly multilingual assistant. "
            "Speak naturally. Understand Hindi, Hinglish, "
            "Urdu and English. Reply in the language the user speaks."
        ),
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {
                    "voice_name": "Kore"
                }
            }
        }
    }

    try:
        async with client.aio.live.connect(
            model=MODEL,
            config=config
        ) as session:

            await ws.send_json({"type": "connected"})

            async def send_audio():
                while True:
                    message = await ws.receive_text()
                    data = json.loads(message)

                    if data.get("type") == "audio":
                        audio = base64.b64decode(data["data"])

                        await session.send_realtime_input(
                            audio=types.Blob(
                                data=audio,
                                mime_type="audio/pcm;rate=16000"
                            )
                        )

                    elif data.get("type") == "text":
                        await session.send_realtime_input(
                            text=data.get("text", "")
                        )

                    elif data.get("type") == "stop":
                        return

            async def receive_ai():
                async for response in session.receive():

                    if response.server_content:
                        content = response.server_content

                        if content.model_turn:
                            for part in content.model_turn.parts:

                                if part.inline_data:
                                    encoded = base64.b64encode(
                                        part.inline_data.data
                                    ).decode("ascii")

                                    await ws.send_json({
                                        "type": "audio",
                                        "data": encoded,
                                        "mime_type": (
                                            part.inline_data.mime_type
                                        )
                                    })

                                if part.text:
                                    await ws.send_json({
                                        "type": "text",
                                        "data": part.text
                                    })

                        if content.interrupted:
                            await ws.send_json({
                                "type": "interrupted"
                            })

                        if content.turn_complete:
                            await ws.send_json({
                                "type": "turn_complete"
                            })

            import asyncio

            s = asyncio.create_task(send_audio())
            r = asyncio.create_task(receive_ai())

            done, pending = await asyncio.wait(
                [s, r],
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

    except WebSocketDisconnect:
        logging.info("User disconnected")

    except Exception as e:
        logging.exception("NOVA Live error")

        try:
            await ws.send_json({
                "type": "error",
                "message": str(e)[:300]
            })
        except Exception:
            pass

    finally:
        try:
            await ws.close()
        except Exception:
            pass
