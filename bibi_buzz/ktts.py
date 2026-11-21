"""Kokoro text-to-speech for the narrator and the characters of the fairy tales.

English: Kokoro-82M, Turkish: the Turkish fine-tune of it (empiriolabsai/kokoro-turkish).  Both are open neural voices (Apache 2.0) that run on the CPU of the
render machine: no account, no paid service; only data (weights and voices) is downloaded, once, from Hugging Face.  They sound much more like people than a plain
Edge voice that is pushed far up or down in pitch, so the tales ask for them first (voice.py) and fall back to the Edge voice of the same character whenever
anything at all goes wrong (a library that is not installed, a download that fails, a clip of the wrong length): a video is never lost because of them.

A voice spec is the `voice` of an item of voice.py:
    "k:af_heart"                 English (Kokoro-82M): one voice, or voices that are averaged:  "k:af_heart,af_sarah"
    "kt:elif=0.7,emre=0.3"       Turkish (Kokoro-Turkish): a mix of its two voices, elif (woman) and emre (man), with weights
and, after a bar, the Edge voice (with its own rate and pitch) that takes over when Kokoro cannot run:   "k:af_heart|en-US-JennyNeural|-6%|+0Hz"
The rate "-6%" of an item is a speed of 0.94; the pitch "+20Hz" is a pitch factor of 1 + 20 / 150 (the way the tales have always said it), made afterwards by
ffmpeg's rubberband with the formants moving along (a smaller or a bigger person), not by Kokoro itself.
"""
import os
import re
import subprocess
import tempfile
import time
import wave

import numpy as np

KSR = 24000                                   # the sample rate of both models
EN_REPO = "hexgrad/Kokoro-82M"
TR_REPO = "empiriolabsai/kokoro-turkish"
_S = {}                                       # what is loaded (the models), and what is known to be broken


# ------------------------------------------------------------------------------------------------------------------------ specs
def enabled(lang):
    """True when the Kokoro voices are asked for this language: environment BIBI_KOKORO="en,tr" (or "all") and the library is installed."""
    want = {x.strip() for x in os.environ.get("BIBI_KOKORO", "").lower().replace(";", ",").split(",") if x.strip()}
    if not ({lang, "all"} & want):
        return False
    try:
        import importlib.util
        return importlib.util.find_spec("kokoro") is not None
    except Exception:
        return False


def is_spec(voice):
    return isinstance(voice, str) and (voice.startswith("k:") or voice.startswith("kt:"))


def split_spec(voice):
    """-> (engine 'k' or 'kt', the voices, the Edge stand-in as (voice, rate, pitch) with '' for what is not said)."""
    head, *fb = voice.split("|")
    eng, _, body = head.partition(":")
    fb = (fb + ["", "", ""])[:3]
    return eng, body, (fb[0], fb[1], fb[2])


def language(voice):
    return "tr" if voice.startswith("kt:") else "en"


def speed_of(rate):
    """'-6%' -> 0.94"""
    m = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*%\s*", rate or "")
    return min(1.5, max(0.6, 1.0 + float(m.group(1)) / 100.0)) if m else 1.0


def pitch_factor(pitch):
    """'+20Hz' -> 1.1333 (a '+X Hz' is a factor of 1 + X / 150 on the whole melody of the voice)"""
    m = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*Hz\s*", pitch or "")
    return min(1.8, max(0.55, 1.0 + float(m.group(1)) / 150.0)) if m else 1.0


def blend_of(body):
    """'elif=0.7,emre=0.3' -> {'elif': 0.7, 'emre': 0.3}; 'elif' -> {'elif': 1.0}"""
    out = {}
    for part in body.split(","):
        part = part.strip()
        if not part:
            continue
        name, _, w = part.partition("=")
        out[name.strip()] = float(w) if w else 1.0
    if not out:
        raise ValueError("no voice in %r" % body)
    return out


def sentences(text, limit=230):
    """The text in pieces of at most `limit` characters, cut after . ! ? or … (and, when a sentence is longer, after , ; :)."""
    parts = [p for p in re.split(r"(?<=[.!?…])\s+", text.strip()) if p]
    out = []
    for p in parts:
        while len(p) > limit:
            cut = max((m.end() for m in re.finditer(r"[,;:]\s", p[:limit])), default=0) or p.rfind(" ", 0, limit)
            if cut <= 0:
                cut = limit
            out.append(p[:cut].strip())
            p = p[cut:].strip()
        if p:
            out.append(p)
    return out


# ------------------------------------------------------------------------------------------------------------------------ wav files
def write_wav(path, y, sr=KSR):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(np.asarray(y, dtype=np.float64), -1, 1) * 32767).astype(np.int16).tobytes())


def read_wav(path):
    with wave.open(path, "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)
        return data, w.getframerate()


def pitch_shift(y, factor, ffmpeg="ffmpeg", sr=KSR):
    """The pitch x factor, the formants move along (a smaller / a bigger person).  rubberband when this ffmpeg has it, else resampling."""
    if abs(factor - 1.0) < 0.01:
        return y
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "in.wav"), os.path.join(d, "out.wav")
        write_wav(src, y, sr)
        tries = ["rubberband=pitch=%.4f:formant=shifted:pitchq=quality" % factor,
                 "asetrate=%d,aresample=%d,atempo=%.5f" % (round(sr * factor), sr, 1.0 / factor)]
        for chain in tries:
            r = subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", src, "-af", chain, "-ar", str(sr), "-ac", "1", dst], capture_output=True, text=True)
            if r.returncode == 0 and os.path.exists(dst):
                z, _ = read_wav(dst)
                if len(z) > 0:
                    return z
        raise RuntimeError("the pitch of a clip could not be changed: " + r.stderr.strip()[:200])


# ------------------------------------------------------------------------------------------------------------------------ the models
def _en_pipeline(code):
    key = ("en", code)
    if key not in _S:
        from kokoro import KModel, KPipeline
        if "en-model" not in _S:
            _S["en-model"] = KModel(repo_id=EN_REPO).eval()
        _S[key] = KPipeline(lang_code=code, repo_id=EN_REPO, model=_S["en-model"])
    return _S[key]


def _speak_en(text, body, speed):
    pipe = _en_pipeline("b" if body.strip()[:1] == "b" else "a")                 # bf_ / bm_ voices are British, af_ / am_ American
    parts = []
    for _gs, _ps, au in pipe(text, voice=body, speed=speed, split_pattern=r"\n+"):
        if au is not None:
            parts.append(au.numpy() if hasattr(au, "numpy") else np.asarray(au))
    if not parts:
        raise RuntimeError("Kokoro made no audio")
    return np.concatenate(parts).astype(np.float64)


def _tr_model():
    if "tr" not in _S:
        from huggingface_hub import hf_hub_download
        from kokoro import KModel
        from .g2p_tr import TurkishG2P                                          # (kept in this repository: no code of the model's page is run)
        g2p = TurkishG2P()                                                      # (fails at once when the espeak-ng program is missing)
        net = KModel(repo_id=TR_REPO, config=hf_hub_download(TR_REPO, "config.json"), model=hf_hub_download(TR_REPO, "kokoro-turkish.pth")).eval()
        _S["tr"] = (g2p, net, {})
    return _S["tr"]


def _loaded(eng):
    """Loads the model of an engine once; when that does not work the engine is marked as broken, so that no line tries again."""
    if ("dead", eng) in _S:
        raise RuntimeError("Kokoro (%s) does not work on this machine: %s" % (eng, _S[("dead", eng)]))
    try:
        return _en_pipeline("a") if eng == "k" else _tr_model()
    except Exception as e:
        _S[("dead", eng)] = repr(e)[:200]
        raise


def _tr_style(blend):
    import torch
    from huggingface_hub import hf_hub_download
    cache = _tr_model()[2]
    out, total = None, 0.0
    for name, w in blend.items():
        if name not in cache:
            cache[name] = torch.load(hf_hub_download(TR_REPO, "voices/%s.pt" % name), weights_only=True)
        out = cache[name] * w if out is None else out + cache[name] * w
        total += w
    return out / total


def _speak_tr(text, blend, speed):
    import torch
    g2p, net, _ = _tr_model()
    style = _tr_style(blend)
    out = []
    for piece in sentences(text, 230):
        ph, _ = g2p(piece)
        if not ph:
            continue
        with torch.no_grad():
            au = net(ph[:480], style[min(len(ph), 480) - 1], speed)
        out += [np.asarray(au.numpy() if hasattr(au, "numpy") else au, dtype=np.float64), np.zeros(int(0.10 * KSR))]
    if not out:
        raise RuntimeError("Kokoro-Turkish made no audio")
    return np.concatenate(out[:-1])


def speak(text, voice, rate, pitch, ffmpeg="ffmpeg"):
    """The clip (float array, 24 kHz) of a text in a voice spec; raises when it cannot be made or does not look like speech."""
    eng, body, _fb = split_spec(voice)
    if eng not in ("k", "kt"):
        raise ValueError("not a Kokoro voice: %r" % (voice,))
    _loaded(eng)
    speed = speed_of(rate)
    y = _speak_en(text, body, speed) if eng == "k" else _speak_tr(text, blend_of(body), speed)
    if not np.all(np.isfinite(y)) or len(y) < 0.2 * KSR or float(np.max(np.abs(y))) < 1e-3:
        raise RuntimeError("the clip is empty or broken")
    secs, n = len(y) / float(KSR), len(text.strip())
    if not (0.03 * n <= secs <= max(0.30 * n, 2.5)):                             # people say 6 to 25 characters a second; a clip far outside is a failure of the model
        raise RuntimeError("the clip has the wrong length: %.1f s for %d characters" % (secs, n))
    f = pitch_factor(pitch)
    return pitch_shift(y, f, ffmpeg) if abs(f - 1.0) >= 0.01 else y


def make(items, path_of, ffmpeg="ffmpeg", log=print):
    """Writes the 24 kHz clip of every item (text, voice spec, rate, pitch, ...) to path_of(item).  Returns the items that could NOT be made:
    the caller takes the Edge voice of the spec for those."""
    failed = []
    t0 = time.time()
    seconds = 0.0
    for it in items:
        text, voice, rate, pitch = it[0], it[1], it[2], it[3]
        try:
            y = speak(text, voice, rate, pitch, ffmpeg)
            write_wav(path_of(it), y, KSR)
            seconds += len(y) / float(KSR)
        except Exception as e:
            log("[ktts] %s failed for %r: %s" % (voice, text[:50], repr(e)[:200]))
            failed.append(it)
    done = len(items) - len(failed)
    log("[ktts] %d of %d clips made (%.0f s of speech in %.0f s of work); %d will use the Edge voice" % (done, len(items), seconds, time.time() - t0, len(failed)))
    return failed


# ------------------------------------------------------------------------------------------------------------------------ the characters
# The same TYPES as tales.TYPES, with Kokoro voices: type -> ((English spec, rate, pitch, effect), (Turkish spec, rate, pitch, effect)).
# English: the voices of Kokoro-82M that its authors grade best are af_heart, af_bella (A), then af_kore, af_sarah, af_aoede, am_fenrir, am_michael, am_puck (C+),
# bf_emma, af_nicole (B-), bm_george, bm_fable (C).  A character is a voice, a speed and a pitch factor (children and small animals are a voice moved up, giants and
# trolls a voice moved down: the formants move with it, so it is a smaller or a bigger person).
# Turkish: the model has only two voices, elif (woman) and emre (man); the pitch offsets are the ones the Edge casting has used (Emel and Ahmet).
KTYPES = {
    "nar": (("k:af_heart", "-8%", "+0Hz", ""), ("kt:elif", "-5%", "+0Hz", "")),
    # people
    "girl": (("k:af_bella", "-2%", "+24Hz", ""), ("kt:elif", "-2%", "+45Hz", "")),
    "teen": (("k:af_kore", "-2%", "+10Hz", ""), ("kt:elif", "-2%", "+15Hz", "")),
    "boy": (("k:am_puck", "+4%", "+30Hz", ""), ("kt:emre", "+4%", "+40Hz", "")),
    "baby": (("k:af_bella", "+0%", "+60Hz", ""), ("kt:elif", "+0%", "+70Hz", "")),
    "woman": (("k:af_bella", "-4%", "+0Hz", ""), ("kt:elif=0.8,emre=0.2", "-8%", "-8Hz", "")),
    "granny": (("k:bf_emma", "-14%", "-14Hz", ""), ("kt:elif", "-14%", "-25Hz", "lp@7000")),
    "fakegranny": (("k:am_michael", "-8%", "+45Hz", ""), ("kt:emre", "-8%", "+60Hz", "")),
    "man": (("k:am_michael", "-6%", "+0Hz", ""), ("kt:emre", "-6%", "+0Hz", "")),
    "grandpa": (("k:bm_fable", "-14%", "-10Hz", ""), ("kt:emre", "-12%", "-14Hz", "lp@7000")),
    "prince": (("k:am_puck", "+0%", "+5Hz", ""), ("kt:emre", "-2%", "+8Hz", "")),
    "king": (("k:bm_george", "-14%", "-20Hz", "room@0.07,0.5"), ("kt:emre", "-14%", "-28Hz", "room@0.07,0.5")),
    "lord": (("k:bm_fable", "-8%", "-6Hz", ""), ("kt:emre", "-10%", "-20Hz", "")),
    "queen": (("k:bf_emma", "-10%", "-12Hz", "room@0.06,0.5"), ("kt:elif", "-12%", "-22Hz", "room@0.06,0.5")),
    "stepmother": (("k:af_nicole", "-12%", "-14Hz", ""), ("kt:elif=0.8,emre=0.2", "-10%", "-20Hz", "")),
    "stepsister": (("k:af_kore", "+6%", "+18Hz", ""), ("kt:elif", "+6%", "+30Hz", "")),
    "witch": (("k:af_nicole", "-14%", "-30Hz", ""), ("kt:elif", "-14%", "-40Hz", "lp@7000")),
    # magic folk
    "fairy": (("k:af_aoede", "-8%", "+20Hz", "room@0.12,0.8"), ("kt:elif", "-14%", "+0Hz", "room@0.14,0.9")),
    "mirror": (("k:bm_fable", "-18%", "-8Hz", "room@0.16,0.9"), ("kt:emre", "-16%", "-10Hz", "room@0.16,0.9")),
    "dwarf": (("k:am_michael", "+6%", "-8Hz", ""), ("kt:emre", "+8%", "+22Hz", "")),
    "elf": (("k:am_puck", "+10%", "+30Hz", ""), ("kt:emre", "+10%", "+50Hz", "")),
    "elfgirl": (("k:af_bella", "+10%", "+40Hz", ""), ("kt:elif", "+10%", "+55Hz", "")),
    "troll": (("k:am_fenrir", "-16%", "-35Hz", "bass@2"), ("kt:emre", "-16%", "-42Hz", "bass@2")),
    "giant": (("k:am_fenrir", "-16%", "-45Hz", "room@0.10,0.7"), ("kt:emre", "-18%", "-58Hz", "room@0.10,0.7")),
    # animals
    "pig": (("k:am_puck", "+2%", "+20Hz", ""), ("kt:emre", "+4%", "+25Hz", "")),
    "wolf": (("k:am_fenrir", "-10%", "-28Hz", "bass@2"), ("kt:emre", "-10%", "-36Hz", "bass@2")),
    "hare": (("k:am_puck", "+8%", "+25Hz", ""), ("kt:emre", "+8%", "+55Hz", "")),
    "tortoise": (("k:am_michael", "-20%", "-10Hz", "lp@7000"), ("kt:emre", "-20%", "-14Hz", "lp@7000")),
    "bear": (("k:am_fenrir", "-12%", "-15Hz", ""), ("kt:emre", "-12%", "-38Hz", "")),
    "mamabear": (("k:af_nicole", "-8%", "-22Hz", ""), ("kt:elif", "-10%", "-26Hz", "")),
    "goat_little": (("k:am_puck", "+4%", "+35Hz", ""), ("kt:elif", "+4%", "+60Hz", "")),
    "goat_mid": (("k:am_michael", "+0%", "+10Hz", ""), ("kt:emre", "+2%", "+30Hz", "")),
    "goat_big": (("k:am_fenrir", "-14%", "-20Hz", "bass@2"), ("kt:emre", "-10%", "-36Hz", "bass@2")),
    "hen": (("k:af_kore", "+4%", "+15Hz", ""), ("kt:elif", "+2%", "+40Hz", "")),
    "fox": (("k:bm_fable", "-4%", "+0Hz", ""), ("kt:emre", "-4%", "+12Hz", "")),
    "tiny": (("k:af_bella", "+8%", "+70Hz", ""), ("kt:elif", "+8%", "+75Hz", "")),
    "lion": (("k:am_fenrir", "-12%", "-38Hz", "room@0.10,0.8"), ("kt:emre", "-12%", "-44Hz", "room@0.10,0.8")),
}


def cast(typ, lang, edge, off=0):
    """(voice spec with its Edge stand-in, rate, pitch, effect) of a character type in a language, or None when Kokoro has no voice for it.
    `edge` is the (voice, rate, pitch, effect) the Edge casting (tales.TYPES) gives the same character, `off` a pitch offset in Hz that tells two characters of one type apart."""
    if typ not in KTYPES:
        return None
    v, r, p, fx = KTYPES[typ][0 if lang == "en" else 1]
    if off:
        p = "%+dHz" % (int(p[:-2]) + off)
    return ("%s|%s|%s|%s" % (v, edge[0], edge[1], edge[2]), r, p, fx)
