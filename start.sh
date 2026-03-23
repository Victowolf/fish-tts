#!/bin/bash

set -e

echo "🚀 Starting Fish Speech Server..."

# System deps
apt update && apt install -y \
    python3-venv python3-pip git \
    portaudio19-dev libsox-dev ffmpeg

# Create environment
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip

# Clone Fish repo
rm -rf fish-speech || true
git clone https://github.com/fishaudio/fish-speech.git

cd fish-speech

# Install Fish (GPU)
pip install -e .[cu126]

cd ..

# Install API deps
pip install fastapi uvicorn pydantic requests

echo "📥 Downloading model weights..."
hf download fishaudio/s2-pro --local-dir checkpoints/s2-pro

echo "🔥 Starting Fish API server..."

python fish-speech/tools/api_server.py \
    --listen 0.0.0.0:8888 \
    --compile &

# 🔥 WAIT UNTIL API IS READY
echo "⏳ Waiting for Fish API..."

for i in {1..60}; do
  if curl -s http://localhost:8888/docs > /dev/null; then
    echo "✅ Fish API is ready!"
    break
  fi
  echo "Waiting... ($i)"
  sleep 2
done

echo "🔥 Starting FastAPI..."

uvicorn main:app --host 0.0.0.0 --port 8000