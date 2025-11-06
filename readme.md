# Create a README.txt file with the requested short instructions
content = """TTS WebSocket (server & client)

Unified WS server + interactive client for multiple TTS backends (Kokoro, Piper).
Client is interactive when --text is omitted: type a line -> hear TTS -> repeat (/q to quit).

------------------------------------------------------------
Run locally
------------------------------------------------------------
# install
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install piper-tts
which piper
export PIPER_BIN="$(which piper)"

# 2) download a voice (model + config)
mkdir -p ~/piper_voices/en_US-lessac
curl -L -o ~/piper_voices/en_US-lessac/en_US-lessac-medium.onnx \
  'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true'
curl -L -o ~/piper_voices/en_US-lessac/en_US-lessac-medium.onnx.json \
  'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true'

# (optional for Piper) set envs in this shell:
export PIPER_MODEL="$HOME/piper_voices/en_US-lessac/en_US-lessac-medium.onnx"
export PIPER_CONFIG="$HOME/piper_voices/en_US-lessac/en_US-lessac-medium.onnx.json"

# start server
uvicorn server:app --host 0.0.0.0 --port 8080

# client (interactive)
python3 client.py --url ws://localhost:8880/ws

------------------------------------------------------------
Docker (Python 3.9)
------------------------------------------------------------
docker build -t tts-ws:py39 .
docker run -it --rm -p 8880:8880 tts_ws
 
python3 client.py --url ws://localhost:8880/ws

------------------------------------------------------------
Notes
------------------------------------------------------------
- Client plays audio locally via sounddevice. If silent, select the correct output device in your OS audio settings.
- Add new engines by dropping a file in backends/ (no changes to server.py / client.py).
"""
