import os
import uuid
import asyncio
import requests
import base64

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

AUDIO_DIR = "static/audio"
FISH_API_URL = "http://localhost:8888/v1/tts"

os.makedirs(AUDIO_DIR, exist_ok=True)

app = FastAPI()
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

gpu_lock = asyncio.Lock()


class TTSRequest(BaseModel):
    text: str


async def generate_audio(text, output_path):
    async with gpu_lock:
        print(f"🎤 Generating: {text[:50]}")

        response = requests.post(
            FISH_API_URL,
            json={"text": text}
        )

        if response.status_code != 200:
            raise Exception(f"Fish API failed: {response.text}")

        # ✅ DIRECT AUDIO BYTES (NO JSON)
        with open(output_path, "wb") as f:
            f.write(response.content)

@app.post("/tts")
async def tts(req: TTSRequest):
    file_id = str(uuid.uuid4())
    file_path = f"{AUDIO_DIR}/{file_id}.wav"

    await generate_audio(req.text, file_path)

    return {
        "url": f"/audio/{file_id}.wav"
    }