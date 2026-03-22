#!/bin/bash

set -e

echo "🚀 Starting Fish Speech Server..."

# System deps (VERY IMPORTANT from docs)
apt update && apt install -y \
    python3-venv python3-pip git \
    portaudio19-dev libsox-dev ffmpeg

# Clone Fish repo
rm -rf fish-speech || true
git clone https://github.com/fishaudio/fish-speech.git

cd fish-speech

# Install Fish (GPU version)
pip install -e .[cu126]

cd ..

# Create venv for API
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "📥 Downloading model weights..."

hf download fishaudio/s2-pro --local-dir checkpoints/s2-pro

echo "🔥 Starting FastAPI..."

uvicorn main:app --host 0.0.0.0 --port 8000