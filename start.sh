#!/bin/bash

set -e

echo "🚀 Starting Fish Speech Server..."

# -----------------------------
# System dependencies
# -----------------------------
apt update && apt install -y \
    python3-venv python3-pip git curl \
    portaudio19-dev libsox-dev ffmpeg

# -----------------------------
# Create virtual environment
# -----------------------------
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip

# -----------------------------
# 🔥 FORCE CORRECT TORCH STACK
# -----------------------------
echo "📦 Installing PyTorch + Torchaudio (stable combo)..."

pip install torch==2.2.2 torchaudio==2.2.2 \
    --index-url https://download.pytorch.org/whl/cu121

# Optional: ensure torchvision doesn't break things
pip uninstall -y torchvision || true

# -----------------------------
# Clone Fish repo
# -----------------------------
echo "📥 Cloning Fish Speech repo..."

rm -rf fish-speech || true
git clone https://github.com/fishaudio/fish-speech.git

cd fish-speech

# -----------------------------
# 🔥 Install Fish WITHOUT deps
# -----------------------------
echo "⚙️ Installing Fish (without overriding torch)..."

pip install -e . --no-deps

cd ..

# -----------------------------
# Install API dependencies
# -----------------------------
pip install fastapi uvicorn pydantic requests

# -----------------------------
# Sanity check (VERY IMPORTANT)
# -----------------------------
echo "🧪 Verifying torchaudio..."

python - <<EOF
import torch
import torchaudio
print("Torch:", torch.__version__)
print("Torchaudio:", torchaudio.__version__)
print("Backends:", torchaudio.list_audio_backends())
EOF

# -----------------------------
# Download model weights
# -----------------------------
echo "📥 Downloading model weights..."

hf download fishaudio/s2-pro --local-dir checkpoints/s2-pro

# -----------------------------
# Start Fish API server
# -----------------------------
echo "🔥 Starting Fish API server..."

python fish-speech/tools/api_server.py \
    --listen 0.0.0.0:8888 \
    --compile &

# -----------------------------
# Wait for Fish API to be ready
# -----------------------------
echo "⏳ Waiting for Fish API..."

for i in {1..60}; do
  if curl -s http://localhost:8888/docs > /dev/null; then
    echo "✅ Fish API is ready!"
    break
  fi
  echo "Waiting... ($i)"
  sleep 2
done

# -----------------------------
# Start your FastAPI wrapper
# -----------------------------
echo "🔥 Starting FastAPI..."

uvicorn main:app --host 0.0.0.0 --port 8000