"""Text-to-speech clips (edge-tts, with a gTTS fallback), cached, silence-trimmed and loudness-matched.

The voice is NEVER sped up or slowed down to fit the picture: the timeline (schedule.py) is built
from the real clip durations, so voice and music always stay in sync at the natural speaking speed.
"""
import asyncio
import hashlib
import os
import subprocess
import sys
import wave

import numpy as np

SR = 44100
VOICE = "en-US-AnaNeural"      # child-friendly voice
RATE = "-8%"                   # a little slower than normal, easier for small children
PITCH = "+8Hz"


def _key(text, voice):
    return hashlib.sha1(f"{voice}|{RATE}|{PITCH}|{text}".encode()).hexdigest()[:20]


def _read_wav(path):
    with wave.open(path, "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)
    return data


def _write_wav(path, y):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


def trim(y):
    """Cut leading/trailing silence so that the first word starts exactly on the beat."""
    if len(y) == 0:
        return y
    peak = float(np.max(np.abs(y)))
    if peak < 1e-4:
        return y
    thr = max(0.008, 0.04 * peak)
    idx = np.where(np.abs(y) > thr)[0]
    a = max(0, int(idx[0]) - int(0.02 * SR))
    b = min(len(y), int(idx[-1]) + int(0.06 * SR))
    y = y[a:b]
    f = int(0.008 * SR)            # gentle fades avoid clicks
    if len(y) > 2 * f:
        y = y.copy()
        y[:f] *= np.linspace(0, 1, f)
        y[-f:] *= np.linspace(1, 0, f)
    return y


def _gen_edge(todo, cache_dir, voice):
    import edge_tts

    async def one(sem, t):
        mp3 = os.path.join(cache_dir, _key(t, voice) + ".mp3")
        async with sem:
            for attempt in range(4):
                try:
                    await asyncio.wait_for(edge_tts.Communicate(t, voice, rate=RATE, pitch=PITCH).save(mp3), 60)
                    if os.path.getsize(mp3) > 800:
                        return
                except Exception:
                    pass
                await asyncio.sleep(1.5 * (attempt + 1))
            raise RuntimeError("text-to-speech failed for: " + t)

    async def run():
        sem = asyncio.Semaphore(4)
        await asyncio.gather(*(one(sem, t) for t in todo))

    asyncio.run(run())


def _gen_gtts(todo, cache_dir, voice):
    from gtts import gTTS
    for t in todo:
        mp3 = os.path.join(cache_dir, _key(t, voice) + ".mp3")
        for attempt in range(4):
            try:
                gTTS(t, lang="en", tld="us").save(mp3)
                if os.path.getsize(mp3) > 800:
                    break
            except Exception:
                pass
            import time
            time.sleep(1.5 * (attempt + 1))
        else:
            raise RuntimeError("gTTS failed for: " + t)


def _convert(ffmpeg, cache_dir, text, voice):
    base = os.path.join(cache_dir, _key(text, voice))
    raw = base + ".raw.wav"
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", base + ".mp3", "-ar", str(SR), "-ac", "1", raw], check=True)
    y = trim(_read_wav(raw))
    peak = float(np.max(np.abs(y))) if len(y) else 1.0
    if peak > 1e-4:
        y = y * (0.9 / peak)
    _write_wav(base + ".wav", y)
    os.remove(raw)


def synth_all(texts, ffmpeg, cache_dir, voice=VOICE):
    """Returns {text: float array (mono, 44.1 kHz)} for every non-empty text of ONE video (one voice per video)."""
    texts = sorted({t for t in texts if t})
    os.makedirs(cache_dir, exist_ok=True)

    def todo_for(v):
        return [t for t in texts if not os.path.exists(os.path.join(cache_dir, _key(t, v) + ".wav"))]

    todo = todo_for(voice)
    if todo:
        try:
            _gen_edge(todo, cache_dir, voice)
            for t in todo:
                _convert(ffmpeg, cache_dir, t, voice)
        except Exception as e:
            print(f"[voice] edge-tts failed ({e!r}); falling back to gTTS for this video", flush=True)
            voice = "gtts-en-us"
            todo = todo_for(voice)
            try:
                _gen_gtts(todo, cache_dir, voice)
                for t in todo:
                    _convert(ffmpeg, cache_dir, t, voice)
            except Exception as e2:
                sys.exit(f"[voice] no text-to-speech engine worked ({e2!r}). Check the internet connection.")
    return {t: _read_wav(os.path.join(cache_dir, _key(t, voice) + ".wav")) for t in texts}


# ---------------------------------------------------------------------------------------------------------- stories
# Fairy-tale videos use several voices (narrator + one per character): items are (text, voice, rate, pitch).
def _key2(item):
    text, voice, rate, pitch = item
    return hashlib.sha1(f"v2|{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:20]


def _gen_edge2(todo, cache_dir):
    import edge_tts

    async def one(sem, item):
        text, voice, rate, pitch = item
        mp3 = os.path.join(cache_dir, _key2(item) + ".mp3")
        async with sem:
            for attempt in range(5):
                v = voice if attempt < 3 else VOICE            # a voice that is not available -> the default voice
                try:
                    await asyncio.wait_for(edge_tts.Communicate(text, v, rate=rate, pitch=pitch).save(mp3), 60)
                    if os.path.getsize(mp3) > 800:
                        return
                except Exception:
                    pass
                await asyncio.sleep(1.5 * (attempt + 1))
            raise RuntimeError("text-to-speech failed for: " + text)

    async def run():
        sem = asyncio.Semaphore(4)
        await asyncio.gather(*(one(sem, it) for it in todo))

    asyncio.run(run())


def _convert2(ffmpeg, cache_dir, item):
    base = os.path.join(cache_dir, _key2(item))
    raw = base + ".raw.wav"
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", base + ".mp3", "-ar", str(SR), "-ac", "1", raw], check=True)
    y = trim(_read_wav(raw))
    peak = float(np.max(np.abs(y))) if len(y) else 1.0
    if peak > 1e-4:
        y = y * (0.9 / peak)
    _write_wav(base + ".wav", y)
    os.remove(raw)


def synth_items(items, ffmpeg, cache_dir):
    """Returns {item: float array (mono, 44.1 kHz)} for every (text, voice, rate, pitch) of ONE story video."""
    items = sorted({it for it in items if it[0]})
    os.makedirs(cache_dir, exist_ok=True)
    todo = [it for it in items if not os.path.exists(os.path.join(cache_dir, _key2(it) + ".wav"))]
    remap = {}
    if todo:
        try:
            _gen_edge2(todo, cache_dir)
            for it in todo:
                _convert2(ffmpeg, cache_dir, it)
        except Exception as e:
            print(f"[voice] edge-tts failed ({e!r}); falling back to gTTS (one voice) for this video", flush=True)
            for it in todo:
                alt = (it[0], "gtts-en-us", "", "")
                remap[it] = alt
            alt_todo = [a for a in set(remap.values()) if not os.path.exists(os.path.join(cache_dir, _key2(a) + ".wav"))]
            try:
                from gtts import gTTS
                for a in alt_todo:
                    mp3 = os.path.join(cache_dir, _key2(a) + ".mp3")
                    for attempt in range(4):
                        try:
                            gTTS(a[0], lang="en", tld="us").save(mp3)
                            if os.path.getsize(mp3) > 800:
                                break
                        except Exception:
                            pass
                        import time
                        time.sleep(1.5 * (attempt + 1))
                    else:
                        raise RuntimeError("gTTS failed for: " + a[0])
                    _convert2(ffmpeg, cache_dir, a)
            except Exception as e2:
                sys.exit(f"[voice] no text-to-speech engine worked ({e2!r}). Check the internet connection.")
    return {it: _read_wav(os.path.join(cache_dir, _key2(remap.get(it, it)) + ".wav")) for it in items}
