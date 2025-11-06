import os, time, asyncio, numpy as np
from typing import Dict, AsyncGenerator, Tuple
from .base import Backend, register

def _float_to_s16(x: np.ndarray) -> bytes:
    x = np.clip(x.astype(np.float32), -1.0, 1.0)
    return (x * 32767.0).astype(np.int16).tobytes()

@register
class KokoroBackend(Backend):
    name = "kokoro"
    _pipeline_cache = {}

    def __init__(self, config=None):
        self.config = config or {}
        self._sr = 24000
        self._KPipeline = None
        self._err = None
        try:
            from kokoro import KPipeline
            self._KPipeline = KPipeline
        except Exception as e:
            self._err = f"Kokoro import failed: {e}"

    async def stream(self, payload: Dict) -> AsyncGenerator[Tuple[str, Dict], None]:
        if self._KPipeline is None:
            yield ("done", {"error": self._err or "kokoro not installed"})
            return

        text = (payload.get("text") or "").strip()
        if not text:
            yield ("done", {"error": "empty text"})
            return

        cfg = self.config.get("kokoro", {})
        voice = payload.get("voice", cfg.get("voice", "af_heart"))
        speed = float(payload.get("speed", cfg.get("speed", 1.0)))
        lang  = payload.get("lang", cfg.get("lang", "a"))

        if lang not in self._pipeline_cache:
            t0 = time.perf_counter()
            self._pipeline_cache[lang] = self._KPipeline(lang_code=lang)
            print(f"[kokoro] Pipeline loaded for {lang} in {(time.perf_counter()-t0):.2f}s")

        pipeline = self._pipeline_cache[lang]
        yield ("meta", {"sample_rate": self._sr, "channels": 1, "sample_format": "s16"})

        t0 = time.perf_counter()
        ttfa_sent = False
        total_samples = 0
        try:
            for (_gs, _ps, audio) in pipeline(text, voice=voice, speed=speed, split_pattern=r"\n+"):
                if not ttfa_sent:
                    yield ("ttfa", {"ms": (time.perf_counter()-t0)*1000.0})
                    ttfa_sent = True
                a = np.asarray(audio, dtype=np.float32).reshape(-1)
                total_samples += a.size
                chunk_size = 2400  # stream in 0.1s chunks
                for i in range(0, len(a), chunk_size):
                    yield ("pcm", {"bytes": _float_to_s16(a[i:i+chunk_size])})
                    await asyncio.sleep(0)
        except Exception as e:
            yield ("done", {"error": f"kokoro synth failed: {e}"})
            return

        total_ms = (time.perf_counter()-t0)*1000.0
        audio_ms = (total_samples/self._sr)*1000.0
        rtf = (total_ms/1000.0)/(audio_ms/1000.0) if audio_ms>0 else None
        yield ("done", {"total_ms":total_ms,"audio_ms":audio_ms,"rtf":rtf,"error":None})
