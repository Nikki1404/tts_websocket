import asyncio, time, os
from typing import Dict, AsyncGenerator, Tuple
from .base import Backend, register

@register
class PiperBackend(Backend):
    name = "piper"

    def __init__(self, config=None):
        self.config = config or {}

    async def stream(self, payload: Dict) -> AsyncGenerator[Tuple[str, Dict], None]:
        cfg = self.config.get("piper", {})
        piper_bin = payload.get("piper_bin") or cfg.get("bin", "piper")
        model = payload.get("model") or cfg.get("model")
        config = payload.get("config") or cfg.get("config")
        extra = payload.get("extra_flags") or cfg.get("extra_flags", "")
        text = (payload.get("text") or "").strip()

        if not text:
            yield ("done", {"error": "empty text"}); return
        if not model or not config:
            yield ("done", {"error": "missing model/config"}); return

        # --- build the proper command ---
        cmd = (
            f'{piper_bin} --model "{model}" --config "{config}" '
            f'--output_raw --output_file /dev/stdout {extra}'
        )

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as e:
            yield ("done", {"error": f"failed to start piper: {e}"}); return

        t0 = time.perf_counter()
        try:
            proc.stdin.write(text.encode("utf-8"))
            await proc.stdin.drain()
            proc.stdin.close()
        except Exception as e:
            yield ("done", {"error": f"failed to write to piper stdin: {e}"}); return

        # --- signal client ---
        yield ("meta", {"sample_rate": 22050, "channels": 1, "sample_format": "s16"})
        yield ("ttfa", {"ms": (time.perf_counter() - t0) * 1000.0})

        total_audio = b""
        try:
            while True:
                chunk = await proc.stdout.read(4096)
                if not chunk:
                    break
                total_audio += chunk
                yield ("pcm", {"bytes": chunk})
                await asyncio.sleep(0)
        except Exception as e:
            yield ("done", {"error": f"stream read failed: {e}"}); return

        await proc.wait()
        total_ms = (time.perf_counter() - t0) * 1000.0
        audio_ms = (len(total_audio) / (2 * 22050)) * 1000.0
        rtf = (total_ms / 1000.0) / (audio_ms / 1000.0) if audio_ms > 0 else None
        yield ("done", {"total_ms": total_ms, "audio_ms": audio_ms, "rtf": rtf, "error": None})
