"""Kokoro text-to-speech for the narrator and the characters of the fairy tales.

English: Kokoro-82M, Turkish: the Turkish fine-tune of it (empiriolabsai/canora-turkish, called kokoro-turkish until 21 Nov 2026).  Both are open neural voices (Apache 2.0) that run on the CPU of the
render machine: no account, no paid service; only data (weights and voices) is downloaded, once, from Hugging Face.  They sound much more like people than a plain
Edge voice that is pushed far up or down in pitch, so the tales ask for them first (voice.py) and fall back to the Edge voice of the same character whenever
anything at all goes wrong (a library that is not installed, a download that fails, a clip of the wrong length): a video is never lost because of them.

A voice spec is the `voice` of an item of voice.py:
    "k:af_heart"                 English (Kokoro-82M): one voice, or voices that are averaged:  "k:af_heart,af_sarah"
    "kt:elif=0.7,emre=0.3"       Turkish (Kokoro-Turkish): a mix of its two voices, elif (woman) and emre (man), with weights
and, after a bar, the Edge voice (with its own rate and pitch) that takes over when Kokoro cannot run:   "k:af_heart|en-US-JennyNeural|-6%|+0Hz"
The rate "-6%" of an item is a speed of 0.94; the pitch "+20Hz" is a pitch factor of 1 + 20 / 150 (the way the tales have always said it): a smaller or a bigger
person, made by shift_voice (the clip is played that many times faster, so the formants move along with the pitch; Kokoro speaks that many times slower first, so
that the length stays) - not by a pitch shifter, which made the voices sound processed.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import wave

import numpy as np

KSR = 24000                                   # the sample rate of both models
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # the folder that holds the package bibi_buzz: the worker is started from there
EN_REPO = "hexgrad/Kokoro-82M"
TR_REPOS = ("empiriolabsai/canora-turkish", "empiriolabsai/kokoro-turkish")     # (the Turkish model was called kokoro-turkish until 21 Nov 2026, when its page was renamed and its
TR_WEIGHTS = ("canora-turkish.pth", "kokoro-turkish.pth")                       # weights file with it: the names it has had are tried one after the other, the new one first)
TR_REPO = TR_REPOS[0]
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


def shift_voice(y, factor):
    """The voice of a smaller (factor > 1) or a bigger (factor < 1) person: the clip is played `factor` times faster (band-limited resampling), so the pitch AND the
    formants move together, as they do between a child and a grown-up; there is none of the phase-vocoder noise of a pitch shifter, which made the voices
    sound processed (in the first test the pitch shifter cost a character voice most of its naturalness).  speak() makes the clip `factor` times slower first,
    so that its length stays the length that was asked for."""
    if abs(factor - 1.0) < 0.01 or len(y) < 16:
        return y
    pad = int(0.05 * KSR)
    z = np.concatenate([np.zeros(pad), np.asarray(y, dtype=np.float64), np.zeros(pad)])
    n, m = len(z), int(round(len(z) / factor))
    X = np.fft.rfft(z)
    k = min(len(X), m // 2 + 1)
    Y = np.zeros(m // 2 + 1, dtype=np.complex128)
    Y[:k] = X[:k]
    if factor > 1.0:                                                     # (the part of the sound that no longer fits is cut off gently: no ringing)
        w = max(8, int(0.04 * k))
        Y[k - w:k] *= 0.5 * (1.0 + np.cos(np.linspace(0.0, np.pi, w)))
    out = np.fft.irfft(Y, m) * (m / float(n))
    cut = int(round(pad / factor))
    return out[cut:len(out) - cut]


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


def _tr_fetch():
    """-> (the repo, the path of its config.json, the path of its weights file) of the Turkish model.  The page of the model was renamed (and its weights file with it)
    on 21 Nov 2026, so the repos and file names it has had are tried one after the other; a .pth file in the top folder of the repo is tried first (whatever it is called)."""
    from huggingface_hub import hf_hub_download, list_repo_files
    last = None
    for repo in TR_REPOS:
        names = list(TR_WEIGHTS)
        try:
            names = [f for f in list_repo_files(repo) if f.endswith(".pth") and "/" not in f] + names
        except Exception as e:
            last = e
        for n in dict.fromkeys(names):
            try:
                weights = hf_hub_download(repo, n)
                return repo, hf_hub_download(repo, "config.json"), weights
            except Exception as e:
                last = e
    raise RuntimeError("the Turkish model could not be fetched: %r" % (last,))


def _tr_model():
    if "tr" not in _S:
        from kokoro import KModel
        from .g2p_tr import TurkishG2P                                          # (kept in this repository: no code of the model's page is run)
        g2p = TurkishG2P()                                                      # (fails at once when the espeak-ng program is missing)
        repo, config, weights = _tr_fetch()
        net = KModel(repo_id=repo, config=config, model=weights).eval()
        _S["tr-repo"] = repo
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


_PACK_NAME = re.compile(r"^(elif|emre|[a-z]{2}_[a-z]+)$")


def _tr_pack(name):
    """The voice pack (one style for every length of the phonemes) of a voice for the Turkish model: elif and emre are the model's own; a name like af_kore is a
    voice of Kokoro-82M, whose style the Turkish fine-tune may still understand (the speaker comes along; whether it sounds right is measured, tools/speech_lab.py)."""
    if not _PACK_NAME.match(name):
        raise ValueError("not a voice name: %r" % (name,))
    cache = _tr_model()[2]
    if name not in cache:
        import torch
        from huggingface_hub import hf_hub_download
        repo = _S.get("tr-repo", TR_REPO) if name in ("elif", "emre") else EN_REPO
        cache[name] = torch.load(hf_hub_download(repo, "voices/%s.pt" % name), weights_only=True)
    return cache[name]


def _tr_style(blend):
    """The style of a blend of voices.  A voice pack is 256 numbers per length of the phonemes: the first 128 are the TIMBRE (they go to the decoder of the model: who it sounds
    like), the last 128 the way of SPEAKING (durations, pitch, energy: they go to its predictor).  A name may say which half it gives: "af_kore:t" is the timbre of af_kore only,
    "elif:p" the way of speaking of elif only, so "elif:p=1,af_kore:t=1" speaks the Turkish the way elif does with another person's voice (the pronunciation stays Turkish, and
    the speaking stays a woman's: take a timbre of the same sex).  A name without a half is the whole pack: the old blends (kt:elif=0.7,emre=0.3) give the very same style as before."""
    import torch
    half = {"t": [None, 0.0], "p": [None, 0.0]}
    for key, w in blend.items():
        name, _, part = key.partition(":")
        if part not in ("", "t", "p"):
            raise ValueError("not a half of a voice: %r" % (key,))
        pack = _tr_pack(name)
        for h, sl in (("t", slice(0, 128)), ("p", slice(128, 256))):
            if part in ("", h):
                x = pack[..., sl] * w
                if half[h][0] is not None and x.shape != half[h][0].shape:
                    raise ValueError("the voices %s do not fit together" % ", ".join(blend))
                half[h][0] = x if half[h][0] is None else half[h][0] + x
                half[h][1] += w
    for h in ("t", "p"):
        if half[h][0] is None or abs(half[h][1]) < 0.2:
            raise ValueError("the weights of %r add up to nothing (%s)" % (blend, h))
    return torch.cat([half["t"][0] / half["t"][1], half["p"][0] / half["p"][1]], dim=-1)


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
    """The clip (float array, 24 kHz) of a text in a voice spec; raises when it cannot be made or does not look like speech.
    A pitch other than +0Hz makes a smaller or a bigger person (shift_voice): Kokoro speaks `factor` times slower, the clip is then played `factor` times faster."""
    eng, body, _fb = split_spec(voice)
    if eng not in ("k", "kt"):
        raise ValueError("not a Kokoro voice: %r" % (voice,))
    _loaded(eng)
    f = pitch_factor(pitch)
    if abs(f - 1.0) < 0.01:
        f = 1.0
    speed = min(2.0, max(0.5, speed_of(rate) / f))
    y = _speak_en(text, body, speed) if eng == "k" else _speak_tr(text, blend_of(body), speed)
    if not np.all(np.isfinite(y)) or len(y) < 0.2 * KSR or float(np.max(np.abs(y))) < 1e-3:
        raise RuntimeError("the clip is empty or broken")
    y = shift_voice(y, f)
    secs, n = len(y) / float(KSR), len(text.strip())
    if not (0.03 * n <= secs <= max(0.30 * n, 2.5)):                             # people say 6 to 25 characters a second; a clip far outside is a failure of the model
        raise RuntimeError("the clip has the wrong length: %.1f s for %d characters" % (secs, n))
    return y


def _work(rows, ffmpeg, log, progress=None):
    """rows: [(text, voice spec, rate, pitch, path)].  Writes the 24 kHz clip of every row to its path (a half-written file is never left behind) and
    returns the rows that could not be made.  `progress` is a file that always holds the number of the row in work, so that whoever started a worker that
    died or hung knows which row did it."""
    failed = []
    t0 = time.time()
    seconds = 0.0
    for i, row in enumerate(rows):
        text, voice, rate, pitch, path = row
        if progress:
            with open(progress, "w") as f:
                f.write(str(i))
        try:
            y = speak(text, voice, rate, pitch, ffmpeg)
            write_wav(path + ".part", y, KSR)
            os.replace(path + ".part", path)
            seconds += len(y) / float(KSR)
        except Exception as e:
            log("[ktts] %s failed for %r: %s" % (voice, text[:50], repr(e)[:200]))
            failed.append(row)
    log("[ktts] %d of %d clips made (%.0f s of speech in %.0f s of work)" % (len(rows) - len(failed), len(rows), seconds, time.time() - t0))
    return failed


def _made(path):
    return os.path.exists(path) and os.path.getsize(path) > 1000


def make(items, path_of, ffmpeg="ffmpeg", log=print):
    """Writes the 24 kHz clip of every item (text, voice spec, rate, pitch, ...) to path_of(item).  Returns the items that could NOT be made:
    the caller takes the Edge voice of the spec for those.
    The neural models run in a SEPARATE python process (a worker: `python -m bibi_buzz.ktts job.json`), so that whatever can go wrong in them (a crash, an
    out-of-memory kill, a hang, torch's threads next to the frame-drawing processes of the video) can never stop the video: a worker that does not finish in
    time is stopped, and one that dies is started once more for what is still missing.  BIBI_KOKORO_INPROC=1 does the work in this process (tests)."""
    items = list(items)
    rows = {}                                                           # one clip per file: the effect of an item does not change the clip
    for it in items:
        rows.setdefault(path_of(it), (it[0], it[1], it[2], it[3], path_of(it)))
    t0 = time.time()
    if os.environ.get("BIBI_KOKORO_INPROC"):
        _work(list(rows.values()), ffmpeg, log)
    else:
        skip = set()                                                     # the rows that killed or hung a worker: not tried again
        stuck = 0
        for attempt in range(4):
            todo = [r for r in rows.values() if not _made(r[4]) and r[4] not in skip]
            if not todo:
                break
            if stuck >= 2:                                               # two workers in a row that made nothing: the models do not run here
                log("[ktts] two Kokoro workers in a row made no clip; the Edge voice is used for the rest")
                break
            chars = sum(len(r[0]) for r in todo)
            budget = int(os.environ.get("BIBI_KOKORO_BUDGET") or min(5400, 600 + 0.25 * chars))        # seconds: a clip of speech is made in far less than the 12 characters a second it holds
            clean = False
            with tempfile.TemporaryDirectory() as d:
                job = os.path.join(d, "job.json")
                with open(job, "w", encoding="utf-8") as f:
                    json.dump({"ffmpeg": ffmpeg, "rows": todo}, f)
                try:
                    r = subprocess.run([sys.executable, "-m", "bibi_buzz.ktts", job], cwd=ROOT, timeout=budget, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
                    out = r.stdout or ""
                    clean = r.returncode == 0
                except subprocess.TimeoutExpired as e:
                    out = e.stdout if isinstance(e.stdout, str) else (e.stdout or b"").decode("utf-8", "replace")
                    log("[ktts] the Kokoro worker did not finish in %d s and was stopped" % budget)
                except Exception as e:
                    out = ""
                    log("[ktts] the Kokoro worker could not be started: %r" % (e,))
                lines = [ln for ln in out.splitlines() if ln.strip()]
                for ln in lines:
                    if ln.startswith("[ktts]"):
                        log(ln)
                if not clean:
                    if lines:
                        log("[ktts] the Kokoro worker ended badly; the last of its output: " + " | ".join(ln.strip()[-160:] for ln in lines[-6:]))
                    try:
                        with open(job + ".at") as f:
                            bad = todo[int(f.read().strip())]
                        skip.add(bad[4])
                        log("[ktts] the row that was in work: %r" % (bad[0][:60],))
                    except Exception:
                        skip.update(r[4] for r in todo[:1])              # (nothing known: the first row it had)
            if clean:
                break                                                    # (a clean worker that left clips out had a reason for each: no second try)
            stuck = stuck + 1 if not any(_made(r[4]) for r in todo) else 0
    failed = [it for it in items if not _made(path_of(it))]
    made = len(rows) - len({path_of(it) for it in failed})
    log("[ktts] %d of %d clips made in %.0f s; %d item(s) will use the Edge voice" % (made, len(rows), time.time() - t0, len(failed)))
    return failed


def _main(argv):
    """The worker: python -m bibi_buzz.ktts job.json  (job: {"ffmpeg": ..., "rows": [[text, voice, rate, pitch, path], ...]})"""
    if len(argv) != 1:
        print("usage: python -m bibi_buzz.ktts job.json")
        return 2
    with open(argv[0], encoding="utf-8") as f:
        job = json.load(f)
    _work([tuple(r) for r in job["rows"]], job.get("ffmpeg", "ffmpeg"), lambda m: print(m, flush=True), progress=argv[0] + ".at")
    return 0


# ------------------------------------------------------------------------------------------------------------------------ the characters
# The same TYPES as tales.TYPES, with Kokoro voices: type -> ((English spec, rate, pitch, effect), (Turkish spec, rate, pitch, effect)).  A spec in the pair may also be
# a tuple of up to three such entries (see _pick): the voice of the type and the voices of a second and a third character of that type in one tale.
# A character is a voice, a speed and a pitch: "+53Hz" is a factor of 1 + 53/150 = 1.35 (shift_voice resamples, so the formants move with the pitch: a voice moved up is a
# smaller person, a voice moved down a bigger one), and an effect (room = a hall, lp = a veiled voice, bass = a heavier one).
# The voices were not chosen by taste but by MEASUREMENT: tools/speech_lab.py (the "palette" job) lets every voice speak a calm and a lively line at several sizes and
# measures the naturalness (UTMOS), the words a listener would miss (Whisper) and the pitch (F0) of each; a search over that table then gave every type of a tale a
# voice and a size such that two characters who speak in the same tale are never the same voice at nearly the same pitch (a mother is not a daughter, the three pigs are three
# voices), a man and a woman are never next to each other in pitch, and no voice is moved so far that it stops sounding like a person (UTMOS and Whisper fall quickly
# beyond that: women's voices keep their naturalness up to a factor of about 1.2, men's up to 1.4, a few voices further).
# English: Kokoro-82M, 15 of its voices are used.  The narrator stays af_heart (the voice its authors grade best).
# Turkish: the model has only two voices, elif (woman) and emre (man), so the other characters are their BLENDS (kt:elif=0.6,emre=0.4 is a lower woman,
# kt:elif=-0.25,emre=1.25 a man deeper than emre, kt:elif=1.25,emre=-0.25 a brighter woman than elif) at a size.  English voices on the Turkish model were tried too
# ("kt:af_kore"): they separate the characters better, but they mispronounce about one word in eight, which is not acceptable in a tale for children, so they are not used.
KTYPES = {
    "nar": (("k:af_heart", "-8%", "+0Hz", ""), ("kt:elif", "-5%", "+0Hz", "")),
    "girl": ((("k:af_sarah", "-2%", "+30Hz", ""), ("k:bf_isabella", "-2%", "+30Hz", "")), (("kt:elif=0.8,emre=0.2", "-2%", "+30Hz", ""), ("kt:elif=1.25,emre=-0.25", "-2%", "+22Hz", ""))),
    "teen": (("k:af_river", "-2%", "+0Hz", ""), ("kt:elif=0.8,emre=0.2", "-2%", "+30Hz", "")),
    "boy": ((("k:am_eric", "+4%", "+30Hz", ""), ("k:am_eric", "+4%", "+30Hz", "")), (("kt:elif=0.2,emre=0.8", "+4%", "+30Hz", ""), ("kt:elif=0.6,emre=0.4", "+4%", "+8Hz", ""))),
    "baby": (("k:bf_isabella", "+0%", "+53Hz", ""), ("kt:elif=1.25,emre=-0.25", "+0%", "+22Hz", "")),
    "woman": (("k:af_sky", "-4%", "-8Hz", ""), ("kt:elif=0.6,emre=0.4", "-8%", "+8Hz", "")),
    "granny": ((("k:af_kore", "-14%", "-15Hz", ""), None, ("k:af_river", "-14%", "+0Hz", "")), (("kt:elif=0.8,emre=0.2", "-14%", "-23Hz", "lp@7000"), None, ("kt:elif=0.4,emre=0.6", "-14%", "-15Hz", "lp@7000"))),
    "fakegranny": (("k:am_eric", "-8%", "+8Hz", ""), ("kt:elif=0.4,emre=0.6", "-8%", "-15Hz", "")),
    "man": (("k:am_adam", "-6%", "+0Hz", ""), ("kt:emre", "-6%", "-23Hz", "")),
    "grandpa": (("k:am_echo", "-14%", "-23Hz", ""), ("kt:elif=-0.25,emre=1.25", "-12%", "-23Hz", "lp@7000")),
    "prince": (("k:bm_george", "+0%", "+0Hz", ""), ("kt:emre", "-2%", "+0Hz", "")),
    "king": (("k:am_echo", "-14%", "+0Hz", "room@0.07,0.5"), ("kt:elif=-0.25,emre=1.25", "-14%", "+0Hz", "room@0.07,0.5")),
    "lord": (("k:am_echo", "-8%", "-8Hz", ""), ("kt:elif=0.2,emre=0.8", "-10%", "-23Hz", "")),
    "queen": (("k:af_sky", "-10%", "-8Hz", "room@0.06,0.5"), ("kt:elif=0.6,emre=0.4", "-12%", "+8Hz", "room@0.06,0.5")),
    "stepmother": (("k:af_kore", "-12%", "+0Hz", ""), ("kt:elif=0.4,emre=0.6", "-10%", "-8Hz", "")),
    "stepsister": ((("k:bf_isabella", "+6%", "+30Hz", ""), ("k:af_bella", "+6%", "+0Hz", "")), (("kt:elif=0.8,emre=0.2", "+6%", "-15Hz", ""), ("kt:elif=1.25,emre=-0.25", "+6%", "+22Hz", ""))),
    "witch": (("k:af_kore", "-14%", "-15Hz", ""), ("kt:elif=0.8,emre=0.2", "-14%", "-23Hz", "lp@7000")),
    "fairy": (("k:af_sarah", "-8%", "+30Hz", "room@0.12,0.8"), ("kt:elif=0.6,emre=0.4", "-14%", "+15Hz", "room@0.14,0.9")),
    "mirror": (("k:am_echo", "-18%", "+0Hz", "room@0.16,0.9"), ("kt:elif=-0.25,emre=1.25", "-16%", "+0Hz", "room@0.16,0.9")),
    "dwarf": (("k:am_eric", "+6%", "+8Hz", ""), ("kt:elif=0.4,emre=0.6", "+8%", "-15Hz", "")),
    "elf": (("k:am_eric", "+10%", "+53Hz", ""), ("kt:elif=0.4,emre=0.6", "+10%", "+8Hz", "")),
    "elfgirl": (("k:bf_isabella", "+10%", "+30Hz", ""), ("kt:elif=1.25,emre=-0.25", "+10%", "+22Hz", "")),
    "troll": (("k:am_onyx", "-16%", "+0Hz", "bass@2"), ("kt:elif=-0.25,emre=1.25", "-16%", "-23Hz", "bass@2")),
    "giant": (("k:am_fenrir", "-16%", "-45Hz", "room@0.10,0.7"), ("kt:emre", "-18%", "-58Hz", "room@0.10,0.7")),
    "pig": ((("k:am_puck", "+2%", "+60Hz", ""), ("k:bm_george", "+2%", "+0Hz", ""), ("k:am_eric", "+2%", "+53Hz", "")), (("kt:emre", "+4%", "+15Hz", ""), ("kt:elif=0.2,emre=0.8", "+4%", "+8Hz", ""), ("kt:elif=0.4,emre=0.6", "+4%", "+8Hz", ""))),
    "wolf": (("k:am_echo", "-10%", "-8Hz", "bass@2"), ("kt:elif=-0.25,emre=1.25", "-10%", "-23Hz", "bass@2")),
    "hare": (("k:am_fenrir", "+8%", "+45Hz", ""), ("kt:elif=0.6,emre=0.4", "+8%", "+8Hz", "")),
    "tortoise": (("k:am_adam", "-20%", "+0Hz", "lp@7000"), ("kt:elif=-0.25,emre=1.25", "-20%", "-23Hz", "lp@7000")),
    "bear": (("k:am_onyx", "-12%", "+15Hz", ""), ("kt:emre", "-12%", "-23Hz", "")),
    "mamabear": (("k:af_kore", "-8%", "+0Hz", ""), ("kt:elif=0.6,emre=0.4", "-10%", "+0Hz", "")),
    "goat_little": (("k:am_eric", "+4%", "+53Hz", ""), ("kt:elif=0.6,emre=0.4", "+4%", "+0Hz", "")),
    "goat_mid": (("k:bm_george", "+0%", "+0Hz", ""), ("kt:elif=0.2,emre=0.8", "+2%", "+15Hz", "")),
    "goat_big": (("k:am_echo", "-14%", "+0Hz", "bass@2"), ("kt:emre", "-10%", "-23Hz", "bass@2")),
    "hen": (("k:af_jessica", "+4%", "+15Hz", ""), ("kt:elif=1.25,emre=-0.25", "+2%", "+8Hz", "")),
    "fox": (("k:am_adam", "-4%", "+0Hz", ""), ("kt:elif=-0.25,emre=1.25", "-4%", "+22Hz", "")),
    "tiny": (("k:bf_isabella", "+8%", "+53Hz", ""), ("kt:elif=1.25,emre=-0.25", "+8%", "+22Hz", "")),
    "lion": (("k:am_echo", "-12%", "-23Hz", "room@0.10,0.8"), ("kt:elif=-0.25,emre=1.25", "-12%", "-23Hz", "room@0.10,0.8")),
}


# The same Turkish types made the other way (BIBI_XPLANT=1): a Turkish character speaks the Turkish the way elif (women) or emre (men) does, with the TIMBRE of a voice of
# Kokoro-82M ("kt:elif:p=1,af_river:t=1", see _tr_style), so that the characters of a tale differ in WHO they sound like and not only in how high they sit.  The entries come
# from a search over the voice grid of the speech lab (tools/speech_lab.py --only grid: ECAPA voice prints of every Kokoro voice at several pitches) and are checked on the
# lines of the gallery (tools/speech_lab.py --only gallery, the "-xplant" pass).  Off by default: the daily videos keep KTYPES until the gallery says (and a listener agrees)
# that these are better.  A type that is not in this table keeps its entry of KTYPES.
XPLANT_TR = {
    "girl": (("kt:elif:p=1,bf_emma:t=1", "-2%", "+0Hz", ""), ("kt:elif:p=1,af_heart:t=1", "-2%", "+30Hz", "")),
    "boy": (("kt:emre:p=1,emre:t=0.5,am_adam:t=0.5", "+4%", "+30Hz", ""), ("kt:emre:p=1,emre:t=0.5,am_adam:t=0.5", "+4%", "+30Hz", "")),
    "baby": ("kt:elif:p=1,af_heart:t=1", "+0%", "+30Hz", ""),
    "woman": ("kt:elif:p=1,af_river:t=1", "-8%", "-8Hz", ""),
    "granny": (("kt:elif:p=1,elif:t=0.5,bf_isabella:t=0.5", "-14%", "-23Hz", "lp@7000"), None, ("kt:elif:p=1,af_river:t=1", "-14%", "-23Hz", "lp@7000")),
    "fakegranny": ("kt:emre:p=1,am_echo:t=1", "-8%", "+30Hz", ""),
    "man": ("kt:emre:p=1,am_adam:t=1", "-6%", "-23Hz", ""),
    "grandpa": ("kt:emre:p=1,emre:t=0.5,am_michael:t=0.5", "-12%", "-23Hz", "lp@7000"),
    "prince": ("kt:emre:p=1,emre:t=0.5,am_michael:t=0.5", "-2%", "+15Hz", ""),
    "king": ("kt:emre:p=1,emre:t=0.5,am_echo:t=0.5", "-14%", "-23Hz", "room@0.07,0.5"),
    "lord": ("kt:emre:p=1,emre:t=0.5,bm_fable:t=0.5", "-10%", "+0Hz", ""),
    "queen": ("kt:elif:p=1,af_river:t=1", "-12%", "-8Hz", "room@0.06,0.5"),
    "stepmother": ("kt:elif:p=1,bf_isabella:t=1", "-10%", "-23Hz", ""),
    "stepsister": (("kt:elif=0.8,emre=0.2", "+6%", "-15Hz", ""), ("kt:elif:p=1,af_river:t=1", "+6%", "-23Hz", "")),
    "witch": ("kt:elif:p=1,elif:t=0.5,af_bella:t=0.5", "-14%", "-23Hz", "lp@7000"),
    "fairy": ("kt:elif:p=1,af_alloy:t=1", "-14%", "-8Hz", "room@0.14,0.9"),
    "mirror": ("kt:emre:p=1,emre:t=0.5,am_fenrir:t=0.5", "-16%", "-23Hz", "room@0.16,0.9"),
    "dwarf": ("kt:emre:p=1,emre:t=0.5,am_fenrir:t=0.5", "+8%", "+30Hz", ""),
    "elf": ("kt:emre:p=1,emre:t=0.5,am_santa:t=0.5", "+10%", "+45Hz", ""),
    "elfgirl": ("kt:elif:p=1,af_heart:t=1", "+10%", "+30Hz", ""),
    "pig": (("kt:emre:p=1,emre:t=0.5,am_santa:t=0.5", "+4%", "+0Hz", ""), ("kt:elif=0.2,emre=0.8", "+4%", "+8Hz", ""), ("kt:emre:p=1,am_adam:t=1", "+4%", "+30Hz", "")),
    "wolf": ("kt:emre:p=1,emre:t=0.5,bm_fable:t=0.5", "-10%", "-23Hz", "bass@2"),
    "hare": ("kt:emre:p=1,emre:t=0.5,am_michael:t=0.5", "+8%", "+45Hz", ""),
    "tortoise": ("kt:emre:p=1,emre:t=0.5,am_michael:t=0.5", "-20%", "-23Hz", "lp@7000"),
    "bear": ("kt:emre:p=1,bm_fable:t=1", "-12%", "-8Hz", ""),
    "mamabear": ("kt:elif:p=1,elif:t=0.5,af_bella:t=0.5", "-10%", "-23Hz", ""),
    "goat_little": ("kt:emre:p=1,emre:t=0.5,am_echo:t=0.5", "+4%", "+45Hz", ""),
    "goat_big": ("kt:emre:p=1,emre:t=0.5,bm_fable:t=0.5", "-10%", "-8Hz", "bass@2"),
    "hen": ("kt:elif:p=1,elif:t=0.5,af_heart:t=0.5", "+2%", "+30Hz", ""),
    "fox": ("kt:emre:p=1,emre:t=0.5,am_liam:t=0.5", "-4%", "+15Hz", ""),
    "tiny": ("kt:elif:p=1,elif:t=0.5,af_heart:t=0.5", "+8%", "+30Hz", ""),
    "nar": ("kt:elif:p=1,elif:t=0.5,af_heart:t=0.5", "-5%", "+0Hz", ""),
}


def xplant_on():
    return os.environ.get("BIBI_XPLANT", "").strip().lower() in ("1", "yes", "on", "true")


KID_TYPES = ("girl", "boy", "baby", "tiny", "elfgirl", "goat_little")        # (children and small animals: the Edge casting has real child voices for them in English, Ana and Maisie)
KIDS_DEFAULT = "kokoro"                       # who speaks the English children: "kokoro" (a Kokoro voice moved up) or "edge" (the child voices of Edge); BIBI_KIDS says otherwise


def _pick(entry, off):
    """The entry of a type is one (voice spec, rate, pitch, effect), or a tuple of up to three of them: (the voice of the type, the voice of a second character of the
    same type in a tale [a positive offset in tales.CASTING], the voice of a third one [a negative offset]).  Characters of one type that speak in one tale (three pigs,
    two grannies) are then different VOICES, not one voice a little higher or lower - that is what makes two people sound like two people.
    -> (the entry, the pitch offset in Hz that is still to be added)."""
    if isinstance(entry[0], str):
        return entry, off
    if off > 0 and len(entry) > 1 and entry[1]:
        return entry[1], 0
    if off < 0 and len(entry) > 2 and entry[2]:
        return entry[2], 0
    return entry[0], off


def cast(typ, lang, edge, off=0):
    """(voice spec with its Edge stand-in, rate, pitch, effect) of a character type in a language, or None when Kokoro has no voice for it (an Edge voice speaks then).
    `edge` is the (voice, rate, pitch, effect) the Edge casting (tales.TYPES) gives the same character, `off` tells two characters of one type apart: a variant voice of
    the type when KTYPES has one (see _pick), else a pitch offset in Hz."""
    if typ not in KTYPES:
        return None
    if lang == "en" and typ in KID_TYPES and os.environ.get("BIBI_KIDS", KIDS_DEFAULT).strip().lower() == "edge":
        return None                                                          # (the child voices of Edge speak them, tales.TYPES)
    entry = KTYPES[typ][0 if lang == "en" else 1]
    if lang == "tr" and typ in XPLANT_TR and xplant_on():
        entry = XPLANT_TR[typ]
    (v, r, p, fx), off = _pick(entry, off)
    if off:
        p = "%+dHz" % (int(p[:-2]) + off)
    return ("%s|%s|%s|%s" % (v, edge[0], edge[1], edge[2]), r, p, fx)


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
