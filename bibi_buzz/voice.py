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

from . import ktts

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


def room(y, wet=0.10, rt=0.55, seed=11):
    """A little room around a voice (FFT convolution with a decaying noise tail): the voice of something big, or something magic, sounds as if
    it stood in a hall.  Much softer and more natural than an echo; `wet` is the loudness of the tail compared with the voice."""
    pad = int(rt * 1.2 * SR)
    t = np.arange(pad) / SR
    ir = np.random.default_rng(seed).standard_normal(pad) * np.exp(-t * 6.9 / rt)
    on = int(0.015 * SR)
    ir[:on] *= np.linspace(0, 1, on)
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(y) + pad
    nfft = 1 << (L - 1).bit_length()
    w = np.fft.irfft(np.fft.rfft(y, nfft) * np.fft.rfft(ir, nfft), nfft)[:L]
    yy = np.concatenate([y, np.zeros(pad)])
    return yy + wet * w * (float(np.max(np.abs(y))) / (float(np.max(np.abs(w))) + 1e-9))


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
# Fairy-tale videos use several voices (narrator + one per character): items are (text, voice, rate, pitch, fx).
#
# fx is "" or a character effect: the same text-to-speech clip is made higher or deeper (the pitch AND the voice colour move together, like a smaller or
# a bigger person), wobbly, growly, nasal or echoing, so a mouse squeaks, a wolf growls, a granny quavers and a giant booms. fx is a "+" separated list of
# presets (FX_PRESETS) and key@value settings; a later setting wins over an earlier one ("pig+p@1.34" = the pig voice, but higher):
#   p@1.3          pitch factor (1.3 = 30 % higher, 0.8 = 20 % lower)      pm@1.06   multiplies the pitch factor
#   vib@5,0.45     wobble: speed in Hz, depth 0..1                          trem@50,0.12   growl: speed in Hz, depth 0..1
#   bass@3 treb@2  boost (dB) of the low / high end                         nasal@6   boost (dB) around 1.2 kHz (a snout)
#   lp@5500 hp@120 low-pass / high-pass filter (Hz)                         hall / echo@0.4 / chorus   room, big echo, shimmer
#   room@0.1,0.55  a soft natural room around the voice: loudness of the tail, length of the tail in seconds
# The natural voices of the tales (tales.TYPES) hardly use any effect: the text-to-speech voice itself is chosen, and its own pitch and speed
# (the "+30Hz" / "-12%" of a TYPE) are moved a little.  A "+X Hz" of the pitch setting is a factor of 1 + X / 150 on the whole melody of the voice
# (+45Hz = 30 % higher, -30Hz = 20 % lower), so the voice stays alive, which a resampled voice (p@) does not.
FX_PRESETS = {
    "boy": "p@0.82",                       # (on the child voice Ana: a bit lower than the girl)
    "tiny": "p@1.32",
    "elf": "p@1.36",
    "dwarf": "p@1.12+bass@2",
    "pig": "p@1.28+nasal@6",
    "hen": "p@1.12+vib@9,0.35",
    "goat": "vib@8,0.45",
    "hare": "p@1.08",
    "tortoise": "p@0.90+vib@4,0.25+lp@6500",
    "fox": "p@0.97+lp@6000",
    "bear": "p@0.86+bass@3",
    "lion": "p@0.80+bass@4+hall",
    "wolf": "p@0.82+bass@3+trem@52,0.10",
    "troll": "p@0.76+bass@5+trem@62,0.15+lp@5200",
    "giant": "p@0.72+bass@5+trem@46,0.14+hall",
    "oldwoman": "p@0.96+vib@5.2,0.45+lp@5500",
    "oldman": "p@0.92+vib@4.6,0.35+lp@6000",
    "witch": "p@0.84+vib@6,0.4+trem@40,0.12",
    "queen": "p@0.90+hall",
    "king": "p@0.85+bass@3+hall",
    "mirror": "p@0.92+echo@0.45+treb@2",
    "fairy": "p@1.06+chorus+treb@3+echo@0.25",
}


def _merge(out, new):
    for k, v in new.items():
        out[k] = [out.get(k, [1.0])[0] * v[0]] if k == "pm" else v                  # pm multiplies, every other setting is replaced by the later one


def fx_parse(spec, _depth=0):
    """-> {setting: [numbers]} of an effect spec; raises ValueError for a name that does not exist (so a typo shows up when a tale is built)."""
    out = {}
    for tok in (t.strip() for t in (spec or "").split("+")):
        if not tok:
            continue
        if "@" in tok:
            k, v = tok.split("@", 1)
            _merge(out, {k: [float(x) for x in v.split(",")]})
        elif tok in FX_PRESETS and _depth < 4:
            _merge(out, fx_parse(FX_PRESETS[tok], _depth + 1))
        elif tok in ("hall", "chorus"):
            out[tok] = [1.0]
        elif tok == "room":
            out[tok] = [0.10, 0.55]
        else:
            raise ValueError("unknown voice effect %r" % (tok,))
    return out


def fx_chain(spec, sr=SR):
    """The ffmpeg audio filter chain of an effect spec ("" when there is nothing to do)."""
    e = fx_parse(spec)
    if not e:
        return ""
    af = ["aresample=%d" % sr, "volume=0.8"]
    f = e.get("p", [1.0])[0] * e.get("pm", [1.0])[0]
    if abs(f - 1.0) > 0.005:                                                  # resample = pitch and voice colour together, atempo gives the length back
        af += ["asetrate=%d" % round(sr * f), "aresample=%d" % sr, "atempo=%.5f" % (1.0 / f)]
    if "vib" in e:
        af.append("vibrato=f=%.2f:d=%.3f" % tuple(e["vib"][:2]))
    if "trem" in e:
        af.append("tremolo=f=%.1f:d=%.3f" % tuple(e["trem"][:2]))
    if "bass" in e:
        af.append("bass=g=%.1f:f=140:w=0.7" % e["bass"][0])
    if "nasal" in e:
        af.append("equalizer=f=1250:t=q:w=1.1:g=%.1f" % e["nasal"][0])
    if "treb" in e:
        af.append("treble=g=%.1f:f=5000" % e["treb"][0])
    if "hp" in e:
        af.append("highpass=f=%d" % e["hp"][0])
    if "lp" in e:
        af.append("lowpass=f=%d" % e["lp"][0])
    if "hall" in e or "echo" in e or "chorus" in e:
        af.append("apad=pad_dur=0.6")                                          # room for the echo tail (silence at the end is trimmed again)
    if "hall" in e:
        af.append("aecho=0.8:0.7:45|90:0.25|0.15")
    if "echo" in e:
        a = e["echo"][0]
        af.append("aecho=0.8:0.88:140|280:%.2f|%.2f" % (a, a * 0.6))
    if "chorus" in e:
        af.append("chorus=0.7:0.9:55|65:0.4|0.3:0.25|0.35:2|2.3")
    af.append("alimiter=limit=0.9:attack=3:release=50:level=disabled")
    return ",".join(af)


STORY_RMS = 10 ** (-17.0 / 20)                                             # the loudest a story clip may be (RMS); the quieter ones stay at their peak limit


def _norm(item):
    """(text, voice, rate, pitch, fx) of an item; older items have no fx."""
    return tuple(item[:4]) + ((item[4] if len(item) > 4 else ""),)


def _tts_key(item):
    """The key of the plain text-to-speech clip (the same clip serves every effect)."""
    text, voice, rate, pitch, _fx = _norm(item)
    return hashlib.sha1(f"v2|{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:20]


def _key2(item):
    fx = _norm(item)[4]
    if not fx:
        return _tts_key(item)
    return hashlib.sha1(f"{_tts_key(item)}|fx={fx}".encode()).hexdigest()[:20]


def _fallback_voice(voice):
    """The voice to use when `voice` does not work: another voice of the same language."""
    return "tr-TR-EmelNeural" if voice.startswith("tr-") else VOICE


def _gen_edge2(todo, cache_dir):
    import edge_tts

    async def one(sem, item):
        text, voice, rate, pitch, _fx = _norm(item)
        mp3 = os.path.join(cache_dir, _tts_key(item) + ".mp3")
        async with sem:
            for attempt in range(5):
                v = voice if attempt < 3 else _fallback_voice(voice)     # a voice that is not available -> the language's default voice
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
        once = {}
        for it in todo:                                                  # one clip per (text, voice, rate, pitch), whatever the effect
            k = _tts_key(it)
            if k not in once and not (os.path.exists(os.path.join(cache_dir, k + ".mp3")) and os.path.getsize(os.path.join(cache_dir, k + ".mp3")) > 800):
                once[k] = it
        await asyncio.gather(*(one(sem, it) for it in once.values()))

    asyncio.run(run())


def _convert2(ffmpeg, cache_dir, item):
    fx = _norm(item)[4]
    src = os.path.join(cache_dir, _tts_key(item) + ".mp3")
    if not os.path.exists(src):                                          # (a clip of Kokoro, ktts.py, is a wav file)
        src = os.path.join(cache_dir, _tts_key(item) + ".k.wav")
    base = os.path.join(cache_dir, _key2(item))
    raw = base + ".raw.wav"
    chain = fx_chain(fx)
    plain = [ffmpeg, "-y", "-loglevel", "error", "-i", src, "-ar", str(SR), "-ac", "1", raw]
    if chain:
        r = subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", src, "-af", chain, "-ar", str(SR), "-ac", "1", raw], capture_output=True, text=True)
        if r.returncode:                                                 # an effect this ffmpeg cannot do: the plain voice is better than no voice
            print(f"[voice] effect {fx!r} failed ({r.stderr.strip()[:200]}); using the plain voice", flush=True)
            subprocess.run(plain, check=True)
    else:
        subprocess.run(plain, check=True)
    y = trim(_read_wav(raw))
    rm = fx_parse(fx).get("room")
    if rm and len(y):
        y = trim(room(y, rm[0], rm[1]))                                  # (the tail may be long: trim() cuts the silence again)
    peak = float(np.max(np.abs(y))) if len(y) else 1.0
    if peak > 1e-4:
        gain = 0.9 / peak
        rms = float(np.sqrt(np.mean(y ** 2)))
        if rms > 1e-5:
            gain = min(gain, STORY_RMS / rms)                            # a clip that is much louder than the others (a deep voice) is turned down to the same loudness
        y = y * gain
    _write_wav(base + ".wav", y)
    os.remove(raw)


def _edge_equivalent(item):
    """The Edge item that stands in for an item of a Kokoro voice spec: the voice (and rate, pitch) named after the bars of the spec, else the language's default voice."""
    text, voice, rate, pitch, fx = _norm(item)
    _eng, _body, (fv, fr, fp) = ktts.split_spec(voice)
    return (text, fv or _fallback_voice("tr-" if ktts.language(voice) == "tr" else ""), fr or rate, fp or pitch, fx)


def synth_items(items, ffmpeg, cache_dir):
    """Returns {item: float array (mono, 44.1 kHz)} for every (text, voice, rate, pitch[, fx]) of ONE story video.
    A voice that is a Kokoro spec ("k:af_heart|en-US-JennyNeural|-6%|+0Hz", ktts.py) is made by Kokoro first; whatever Kokoro cannot make is made by the Edge
    voice named in the spec, and when Edge fails too, by gTTS."""
    items = sorted({it for it in items if it[0]})
    os.makedirs(cache_dir, exist_ok=True)
    todo = [it for it in items if not os.path.exists(os.path.join(cache_dir, _key2(it) + ".wav"))]
    remap = {}
    kok = [it for it in todo if ktts.is_spec(_norm(it)[1])]
    if kok:
        kset = set(kok)
        todo = [it for it in todo if it not in kset]
        try:
            failed = set(ktts.make(kok, lambda it: os.path.join(cache_dir, _tts_key(it) + ".k.wav"), ffmpeg, log=lambda m: print(m, flush=True)))
        except BaseException as e:                                       # (nothing of Kokoro may stop a video)
            print(f"[voice] Kokoro failed ({e!r}); the Edge voices are used", flush=True)
            failed = set(kok)
        for it in kok:
            if it not in failed:
                try:
                    _convert2(ffmpeg, cache_dir, it)
                    continue
                except Exception as e:
                    print(f"[voice] a Kokoro clip could not be converted ({e!r}); the Edge voice is used", flush=True)
            alt = _edge_equivalent(it)
            remap[it] = alt
            if not os.path.exists(os.path.join(cache_dir, _key2(alt) + ".wav")):
                todo.append(alt)
        todo = list(dict.fromkeys(todo))
    if todo:
        try:
            _gen_edge2(todo, cache_dir)
            for it in todo:
                _convert2(ffmpeg, cache_dir, it)
        except Exception as e:
            print(f"[voice] edge-tts failed ({e!r}); falling back to gTTS (one voice) for this video", flush=True)
            for it in todo:
                alt = (it[0], "gtts-tr" if it[1].startswith("tr-") else "gtts-en-us", "", "", _norm(it)[4])
                remap[it] = alt
            alt_todo = [a for a in set(remap.values()) if a[1].startswith("gtts-") and not os.path.exists(os.path.join(cache_dir, _key2(a) + ".wav"))]
            try:
                from gtts import gTTS
                for a in alt_todo:
                    mp3 = os.path.join(cache_dir, _tts_key(a) + ".mp3")
                    for attempt in range(4):
                        try:
                            if a[1] == "gtts-tr":
                                gTTS(a[0], lang="tr").save(mp3)
                            else:
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

    def resolve(it):                                                     # (a Kokoro item -> its Edge stand-in -> its gTTS stand-in)
        for _ in range(4):
            if it not in remap:
                break
            it = remap[it]
        return it

    return {it: _read_wav(os.path.join(cache_dir, _key2(resolve(it)) + ".wav")) for it in items}
