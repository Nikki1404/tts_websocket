#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio, json, os, numpy as np, websockets

try:
    import sounddevice as sd
except Exception:
    sd = None


async def tts_once(url, payload):
    async with websockets.connect(url, max_size=None) as ws:
        await ws.send(json.dumps(payload))
        sr = 24000
        stream = None
        try:
            while True:
                msg = await ws.recv()
                if isinstance(msg, bytes):
                    a = np.frombuffer(msg, dtype=np.int16).astype(np.float32) / 32767.0
                    if sd is not None:
                        if stream is None:
                            stream = sd.OutputStream(samplerate=sr, channels=1, dtype="float32")
                            stream.start()
                        stream.write(a.reshape(-1, 1))
                else:
                    data = json.loads(msg)
                    t = data.get("type")
                    if t == "meta":
                        sr = int(data.get("sample_rate") or sr)
                    elif t == "ttfa":
                        print(f"[ttfa] {data['ms']:.1f} ms")
                    elif t == "done":
                        if data.get("error"):
                            print("[done:ERROR]", data["error"])
                        else:
                            print(f"[done] gen={data['total_ms']:.1f} ms, audio={data['audio_ms']:.1f} ms, rtf={data['rtf']}")
                        break
        finally:
            if stream is not None:
                stream.stop()
                stream.close()


async def fetch_engines_from_server(url):
    """Try to get list of available TTS engines from the server."""
    engines_url = url.replace("/ws", "/engines")
    try:
        async with websockets.connect(engines_url) as ws:
            msg = await ws.recv()
            data = json.loads(msg)
            return data.get("engines", [])
    except Exception:
        return []


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="ws://localhost:8080/ws")
    ap.add_argument("--text", help="if provided, synthesize once and exit")
    args = ap.parse_args()

    # Try to dynamically load engine list
    try:
        # Local import of backends for dynamic detection
        import backends.loader
        from backends.base import _BACKENDS
        backends.loader.auto_import("backends")
        engine_names = list(_BACKENDS.keys())
    except Exception:
        # Fallback: ask the server
        engine_names = asyncio.get_event_loop().run_until_complete(fetch_engines_from_server(args.url))

    if not engine_names:
        engine_names = ["kokoro", "piper"]
        print("[warn] Could not detect engines dynamically. Using defaults.")

    print("Select TTS engine:")
    for i, e in enumerate(engine_names, 1):
        print(f"{i}. {e}")
    choice = input(f"Enter choice [1-{len(engine_names)}]: ").strip()

    try:
        idx = int(choice) - 1
        engine = engine_names[idx]
    except Exception:
        engine = engine_names[0]
        print(f"Invalid choice, defaulting to {engine}")

    def payload(txt: str):
        base = {"engine": engine, "text": txt}
        if engine == "kokoro":
            base.update({"voice": "af_heart", "lang": os.getenv("KOKORO_LANG", "a"), "speed": 1.0})
        elif engine == "piper":
            base.update({
                "model": os.getenv("PIPER_MODEL"),
                "config": os.getenv("PIPER_CONFIG"),
                "piper_bin": os.getenv("PIPER_BIN", "piper"),
                "extra_flags": os.getenv("PIPER_EXTRA_FLAGS", "")
            })
        return base

    async def run():
        if args.text:
            await tts_once(args.url, payload(args.text))
            return
        print(f"\n[Connected → {engine.upper()} engine | {args.url}]\n(Type '/q' to quit)\n")
        while True:
            try:
                line = input("🗣️  > ").strip()
            except EOFError:
                break
            if not line:
                continue
            if line in {"/q", "/quit", "/exit"}:
                break
            try:
                await tts_once(args.url, payload(line))
            except Exception as e:
                print(f"[warn] {e}")

    asyncio.run(run())
