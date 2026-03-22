import os
import uuid
import asyncio
import subprocess
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

AUDIO_DIR = "static/audio"
CHECKPOINT_DIR = "checkpoints/s2-pro"

os.makedirs(AUDIO_DIR, exist_ok=True)

app = FastAPI()
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

gpu_lock = asyncio.Lock()


class TTSRequest(BaseModel):
    text: str


# 🔥 REAL PIPELINE USING FISH COMMANDS
async def generate_audio(text, output_path):
    async with gpu_lock:
        print(f"🎤 Generating: {text[:50]}")

        # Step 1: Generate semantic tokens
        subprocess.run([
            "python",
            "fish_speech/models/text2semantic/inference.py",
            "--text", text
        ], check=True)

        # Step 2: Convert to waveform
        subprocess.run([
            "python",
            "fish_speech/models/dac/inference.py",
            "-i", "codes_0.npy"
        ], check=True)

        # Step 3: Move output
        if os.path.exists("fake.wav"):
            os.rename("fake.wav", output_path)
        else:
            raise Exception("Audio generation failed")


@app.post("/tts")
async def tts(req: TTSRequest):
    file_id = str(uuid.uuid4())
    file_path = f"{AUDIO_DIR}/{file_id}.wav"

    await generate_audio(req.text, file_path)

    return {
        "url": f"/audio/{file_id}.wav"
    }