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

# (optional for Piper) set envs in this shell:
export PIPER_BIN="/absolute/path/to/piper"
export PIPER_MODEL="/absolute/path/to/en_US-amy-medium.onnx"
export PIPER_CONFIG="/absolute/path/to/en_US-amy-medium.onnx.json"

# start server
uvicorn server:app --host 0.0.0.0 --port 8080

# client (interactive)
python3 client.py --engine kokoro
# or
python3 client.py --engine piper

------------------------------------------------------------
Docker (Python 3.9)
------------------------------------------------------------
docker build -t tts-ws:py39 .
docker run --rm -p 8080:8080 \
  -e PIPER_BIN="/piper/piper" \
  -e PIPER_MODEL="/models/en_US_amy/en_US-amy-medium.onnx" \
  -e PIPER_CONFIG="/models/en_US_amy/en_US-amy-medium.onnx.json" \
  -v /ABS/PATH/piper/bin/piper:/piper/piper:ro \
  -v /ABS/PATH/piper/models:/models:ro \
  tts-ws:py39
# then on host:
python3 client.py --engine piper   # or --engine kokoro

------------------------------------------------------------
Get Piper + a voice (to set PIPER_*)
------------------------------------------------------------
# 1) install Piper CLI
python3 -m pip install --upgrade pip
pip install piper-tts
which piper
export PIPER_BIN="$(which piper)"

# 2) download a voice (model + config)
mkdir -p ~/piper_voices/en_US-lessac
curl -L -o ~/piper_voices/en_US-lessac/en_US-lessac-medium.onnx \
  'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true'
curl -L -o ~/piper_voices/en_US-lessac/en_US-lessac-medium.onnx.json \
  'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true'

# 3) set env vars
export PIPER_MODEL="$HOME/piper_voices/en_US-lessac/en_US-lessac-medium.onnx"
export PIPER_CONFIG="$HOME/piper_voices/en_US-lessac/en_US-lessac-medium.onnx.json"

------------------------------------------------------------
Notes
------------------------------------------------------------
- Client plays audio locally via sounddevice. If silent, select the correct output device in your OS audio settings.
- Add new engines by dropping a file in backends/ (no changes to server.py / client.py).
"""