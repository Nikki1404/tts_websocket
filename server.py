#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, traceback, asyncio, websockets, yaml
from backends.loader import auto_import
from backends.base import get_backend
from backends.kokoro_backend import KokoroBackend

with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

auto_import("backends")
kokoro_pipeline = None

async def preload_kokoro():
    global kokoro_pipeline
    try:
        if CONFIG["kokoro"].get("preload", True):
            kb = KokoroBackend(config=CONFIG)
            async for kind, data in kb.stream({
                "text": "warmup",
                "voice": CONFIG["kokoro"]["voice"],
                "speed": CONFIG["kokoro"]["speed"]
            }):
                if kind == "done":
                    break
            kokoro_pipeline = kb._pipeline_cache.get(CONFIG["kokoro"]["lang"])
            print("[warmup] Kokoro model preloaded & cached.")
    except Exception as e:
        print(f"[warmup] Kokoro preload failed: {e}")

async def handle_ws(websocket):
    try:
        raw = await websocket.recv()
        payload = json.loads(raw)
        engine = (payload.get("engine") or "").lower()
        backend_cls = get_backend(engine)

        if not backend_cls:
            await websocket.send(json.dumps({"type": "done", "error": f"unknown engine '{engine}'"}))
            return

        backend = backend_cls(config=CONFIG)
        if isinstance(backend, KokoroBackend) and kokoro_pipeline is not None:
            backend._pipeline_cache[CONFIG["kokoro"]["lang"]] = kokoro_pipeline

        async for kind, data in backend.stream(payload):
            if kind in ("meta", "ttfa", "done"):
                await websocket.send(json.dumps({"type": kind, **data}))
                if kind == "done": break
            elif kind == "pcm":
                await websocket.send(data["bytes"])
    except Exception as e:
        traceback.print_exc()
        try: await websocket.send(json.dumps({"type":"done","error":str(e)}))
        except: pass

async def main():
    asyncio.create_task(preload_kokoro())
    host = CONFIG["server"]["host"]
    port = CONFIG["server"]["port"]
    max_size = CONFIG["server"].get("max_message_size", None)
    print(f"[server] WebSocket running at ws://{host}:{port}/ws")
    async with websockets.serve(handle_ws, host, port, max_size=max_size):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
