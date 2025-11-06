FROM python:3.9-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make \
    libsndfile1 ffmpeg curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir kokoro piper-tts || true

RUN python3 -c "from kokoro import KPipeline; KPipeline(lang_code='a')"

RUN mkdir -p /app/models/en_US-lessac && \
    curl -L -o /app/models/en_US-lessac/en_US-lessac-medium.onnx \
      'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true' && \
    curl -L -o /app/models/en_US-lessac/en_US-lessac-medium.onnx.json \
      'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true'

COPY . .
EXPOSE 8880
CMD ["python3","server.py"]
