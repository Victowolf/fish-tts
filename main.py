import os
import uuid
import asyncio
import subprocess
import sys

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

        # Unique IDs
        file_id = str(uuid.uuid4())
        codes_file = f"codes_{file_id}.npy"

        # Step 1: text → semantic tokens
        res1 = subprocess.run([
            sys.executable,
            "fish-speech/fish_speech/models/text2semantic/inference.py",
            "--text", text,
            "--checkpoint-path", CHECKPOINT_DIR,
            "--half"
        ], capture_output=True, text=True)

        print("🔍 text2semantic stdout:", res1.stdout)
        print("❌ text2semantic stderr:", res1.stderr)

        if res1.returncode != 0:
            raise Exception("text2semantic failed")

        # ✅ FIX: correct path (output folder)
        codes_src = "output/codes_0.npy"

        if not os.path.exists(codes_src):
            raise Exception("codes file not found in output/")

        os.rename(codes_src, codes_file)

        # Step 2: semantic → waveform
        res2 = subprocess.run([
            sys.executable,
            "fish-speech/fish_speech/models/dac/inference.py",
            "-i", codes_file,
            "--checkpoint-path", f"{CHECKPOINT_DIR}/codec.pth"
        ], capture_output=True, text=True)

        print("🔍 DAC stdout:", res2.stdout)
        print("❌ DAC stderr:", res2.stderr)

        if res2.returncode != 0:
            raise Exception("DAC step failed")

        # ✅ Handle both possible output paths
        wav_src = "fake.wav"
        if not os.path.exists(wav_src):
            wav_src = "output/fake.wav"

        if not os.path.exists(wav_src):
            raise Exception("audio not generated")

        os.rename(wav_src, output_path)


@app.post("/tts")
async def tts(req: TTSRequest):
    file_id = str(uuid.uuid4())
    file_path = f"{AUDIO_DIR}/{file_id}.wav"

    await generate_audio(req.text, file_path)

    return {
        "url": f"/audio/{file_id}.wav"
    }