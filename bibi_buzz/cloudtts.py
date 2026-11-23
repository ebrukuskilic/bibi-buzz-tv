"""Google Cloud Text-to-Speech (the Chirp 3 HD voices) for the narrator and the characters of the lessons and the fairy tales.

Why: the open voices that run on the render machine (ktts.py) were judged "bad" by the channel's owner.  Google's Chirp 3 HD voices are neural voices made for
dubbing and audiobooks, and the SAME thirty voices (14 women, 16 men) speak English and Turkish, so the narrator and every character of a tale can be a different,
real-sounding person in both languages (a mother is not her daughter, three pigs are three people), and a character keeps its voice in the Turkish version.

What it needs (once): a Google Cloud project with billing and the "Cloud Text-to-Speech API" switched on, and an API key that is restricted to that API; the key is the
secret GOOGLE_TTS_KEY of the repository.  The first million characters of Chirp 3 HD voices of a month are free; a day of videos is about 10 to 15 thousand characters.
    BIBI_GOOGLE="en,tr" (or "all")   asks for these voices for these languages; "no" or nothing: they are not asked for (everything stays as it is)
    GOOGLE_TTS_KEY                   the API key; without it BIBI_GOOGLE does nothing.  It travels in a request header and is never printed or logged
    GOOGLE_TTS_ENDPOINT              another address of the service (the offline tests use a little fake server of their own)
    BIBI_GOOGLE_MAX_CHARS            the most characters one run may send (default 60000: a runaway loop can never cost real money; the lab raises it)
    BIBI_GOOGLE_RPM                  requests per minute (default 150; the quota of the voices is 200)
Like the Kokoro voices (ktts.py) the Google voices are asked for first, and whatever they cannot make (the key is refused, the quota is spent, a line fails) is made by the
Kokoro voice of the same character when that is installed and asked for (link / alt_of below), else by the Edge voice named in the spec: a video is never lost because of them.

A voice spec is the `voice` of an item of voice.py, in the form of the Kokoro specs:
    "g:tr:Leda|tr-TR-EmelNeural|-6%|+0Hz"      Google voice Leda, speaking Turkish ("g:en:Leda": American English, "g:en-GB:Leda": British English)
and, after the bars, the Edge voice (with its rate and pitch) that takes over when nothing else can run.  The rate "-6%" is a speaking rate of 0.94 and the pitch "+20Hz" a
pitch factor of 1 + 20 / 150 (ktts.py): a smaller or a bigger person, made by ktts.shift_voice (the service speaks that many times slower, the clip is played that many times
faster, so the pitch and the formants move together - Chirp 3 HD has no pitch setting of its own).
"""
import base64
import concurrent.futures
import io
import json
import os
import random
import re
import threading
import time
import urllib.error
import urllib.request
import wave

import numpy as np

from . import ktts as KT

KSR = KT.KSR                                                  # 24 kHz: the clips are the very files of Kokoro (voice._convert2 reads both)
ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"
VOICES_URL = "https://texttospeech.googleapis.com/v1/voices"
WOMEN = ("Achernar", "Aoede", "Autonoe", "Callirrhoe", "Despina", "Erinome", "Gacrux", "Kore", "Laomedeia", "Leda", "Pulcherrima", "Sulafat", "Vindemiatrix", "Zephyr")
MEN = ("Achird", "Algenib", "Algieba", "Alnilam", "Charon", "Enceladus", "Fenrir", "Iapetus", "Orus", "Puck", "Rasalgethi", "Sadachbia", "Sadaltager", "Schedar",
       "Umbriel", "Zubenelgenubi")
VOICES = WOMEN + MEN
LOCALES = {"en": "en-US", "tr": "tr-TR"}
_sleep = time.sleep                                           # (the tests put a quick one here)
_S = {"dead": None, "chars": 0, "calls": 0, "seconds": 0.0, "streak": 0}   # the state of this process: why the service is given up, what was sent, how many requests in a row failed
_LOCK = threading.RLock()
_NEXT = [0.0]                                                 # the earliest time of the next request (the rate limit of all threads together)


class GoogleError(RuntimeError):
    """code = the HTTP status (0 = no answer); fatal = the key, the billing or the service is the problem (no other request would work either);
    retry = a second try may work (quota of a minute, a server in trouble, a lost connection)."""

    def __init__(self, msg, code=0, fatal=False, retry=False):
        super().__init__(msg)
        self.code, self.fatal, self.retry = code, fatal, retry


# ------------------------------------------------------------------------------------------------------------------------ settings
def _key():
    return (os.environ.get("GOOGLE_TTS_KEY") or "").strip()


def _scrub(s):
    """A text for the log: the key is never in it."""
    k = _key()
    s = str(s)
    return s.replace(k, "***") if len(k) > 8 else s


def _endpoint():
    return (os.environ.get("GOOGLE_TTS_ENDPOINT") or ENDPOINT).strip()


def dead():
    """Why this process gave up on the service ('' when it did not)."""
    return _S["dead"] or ""


def _kill(why):
    with _LOCK:
        if not _S["dead"]:
            _S["dead"] = _scrub(why)[:300]


def reset():
    """Forgets what went wrong and what was sent (the tests)."""
    with _LOCK:
        _S.update(dead=None, chars=0, calls=0, seconds=0.0, streak=0)
        _NEXT[0] = 0.0


def enabled(lang):
    """True when the Google voices are asked for this language (BIBI_GOOGLE="en,tr" or "all"), the key is there and the service has not been given up in this run."""
    want = {x.strip() for x in os.environ.get("BIBI_GOOGLE", "").lower().replace(";", ",").split(",") if x.strip()}
    if not ({lang, "all"} & want):
        return False
    return bool(_key()) and not _S["dead"]


def is_spec(voice):
    return isinstance(voice, str) and voice.startswith("g:")


def parse_body(body):
    """'tr:Leda' -> ('tr-TR', 'tr-TR-Chirp3-HD-Leda'); 'en-GB:Leda' -> ('en-GB', 'en-GB-Chirp3-HD-Leda')"""
    tok, _, voice = body.partition(":")
    tok, voice = tok.strip(), voice.strip()
    if voice not in VOICES:
        raise ValueError("not a Chirp 3 HD voice: %r" % (body,))
    locale = LOCALES.get(tok.lower())
    if locale is None:
        m = re.fullmatch(r"([a-z]{2})-([A-Za-z]{2})", tok)
        if not m:
            raise ValueError("not a language: %r" % (body,))
        locale = "%s-%s" % (m.group(1).lower(), m.group(2).upper())
    return locale, "%s-Chirp3-HD-%s" % (locale, voice)


def language(voice):
    """'tr' or 'en' of a Google voice spec."""
    return "tr" if voice.startswith("g:tr") else "en"


# ------------------------------------------------------------------------------------------------------------------------ the service
def _throttle():
    """Keeps all threads together under the requests-per-minute limit of the service."""
    gap = 60.0 / max(10.0, float(os.environ.get("BIBI_GOOGLE_RPM") or 150))
    with _LOCK:
        now = time.time()
        wait = _NEXT[0] - now
        _NEXT[0] = max(now, _NEXT[0]) + gap
    if wait > 0:
        _sleep(wait)


def _error_of(code, raw):
    """-> (status, reason, message) of an error answer of the service (Google's error object); '' for what is not there."""
    try:
        e = json.loads(raw).get("error", {})
        reason = ""
        for d in e.get("details", []) or []:
            if isinstance(d, dict) and d.get("reason"):
                reason = str(d["reason"])
                break
        return str(e.get("status", "")), reason, str(e.get("message", ""))[:240]
    except Exception:
        return "", "", (raw or "")[:160]


def _post(url, body, key, timeout=60):
    """One request.  Returns the answer (a dict) or raises GoogleError."""
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8", "X-Goog-Api-Key": key, "User-Agent": "bibi-buzz-tv/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", "replace")
        except Exception:
            raw = ""
        status, reason, msg = _error_of(e.code, raw)
        text = "HTTP %d %s %s: %s" % (e.code, status, reason, msg)
        if e.code in (401, 403):
            raise GoogleError(text, e.code, fatal=True)
        if e.code == 429 or e.code >= 500:
            raise GoogleError(text, e.code, retry=True)
        raise GoogleError(text, e.code)                                          # (400, 404: this request is wrong, again it would be the same)
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        raise GoogleError("no answer: %r" % (e,), 0, retry=True)
    except ValueError as e:
        raise GoogleError("answer is not json: %r" % (e,), 0, retry=True)


def _resample(y, sr, to):
    n = int(round(len(y) * to / float(sr)))
    return np.interp(np.linspace(0.0, len(y) - 1, n), np.arange(len(y)), y) if n > 1 and len(y) > 1 else y


def _samples(b64):
    """The answer's audioContent (LINEAR16 with a WAV header) -> float array at 24 kHz."""
    b = base64.b64decode(b64)
    try:
        with wave.open(io.BytesIO(b), "rb") as w:
            sr, ch, sw, pcm = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.readframes(w.getnframes())
    except Exception:                                                              # (a header whose length is not right: the samples start after the 44 bytes of it)
        sr, ch, sw, pcm = KSR, 1, 2, (b[44:] if b[:4] == b"RIFF" else b)
    if sw != 2:
        raise GoogleError("the sample size of the answer is %d bytes" % sw, 0)
    y = np.frombuffer(pcm[:len(pcm) // 2 * 2], dtype="<i2").astype(np.float64) / 32768.0
    if ch == 2:
        y = y.reshape(-1, 2).mean(axis=1)
    return _resample(y, sr, KSR) if sr != KSR else y


def _charge(n):
    cap = int(os.environ.get("BIBI_GOOGLE_MAX_CHARS") or 60000)
    with _LOCK:
        if _S["chars"] + n > cap:
            why = "the budget of this run (%d characters) is spent" % cap
            _kill(why)                                                              # (nothing more is sent in this run: the other voices take the rest)
            raise GoogleError(why, 0, fatal=True)
        _S["chars"] += n
        _S["calls"] += 1


def _piece(text, locale, name, speed, key):
    """One request: a piece of text (at most 5000 bytes) -> its clip."""
    body = {"input": {"text": text}, "voice": {"languageCode": locale, "name": name},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": KSR, "speakingRate": round(float(speed), 3)}}
    last = None
    for attempt in range(5):
        if _S["dead"]:
            raise GoogleError("given up: " + _S["dead"], 0, fatal=True)
        _charge(len(text))
        _throttle()
        try:
            ans = _post(_endpoint(), body, key)
            if not ans.get("audioContent"):
                raise GoogleError("the answer has no audio", 0, retry=True)
            y = _samples(ans["audioContent"])
            _S["streak"] = 0
            return y
        except GoogleError as e:
            if e.fatal:
                _kill(str(e))
                raise
            if not e.retry:
                raise
            last = e
        except Exception as e:                                                     # (a broken answer: another try)
            last = GoogleError("broken answer: %r" % (e,), 0, retry=True)
        _sleep(min(30.0, 1.5 * (2 ** attempt)) + random.random())
    with _LOCK:
        _S["streak"] += 1
        if _S["streak"] >= 6:                                                     # (an outage: no minutes of tries for every line of the video)
            _kill("the service does not answer (6 requests in a row failed after all their tries): %s" % (last,))
    raise GoogleError("given up after 5 tries: %s" % (last,), 0)


def _pieces(text, limit=1400):
    """The text in pieces of at most `limit` characters (a request holds 5000 bytes, and every ç ğ ı ö ş ü is two of them), cut between sentences."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return [text]
    out, cur = [], ""
    for s in KT.sentences(text, 600):
        if cur and len(cur) + 1 + len(s) > limit:
            out.append(cur)
            cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        out.append(cur)
    return out


def speak(text, voice, rate, pitch, ffmpeg="ffmpeg"):
    """The clip (float array, 24 kHz) of a text in a Google voice spec; raises when it cannot be made or does not look like speech.
    A pitch other than +0Hz makes a smaller or a bigger person (ktts.shift_voice): the service speaks `factor` times slower, the clip is then played `factor` times faster."""
    eng, body, _fb = KT.split_spec(voice)
    if eng != "g":
        raise ValueError("not a Google voice: %r" % (voice,))
    locale, name = parse_body(body)
    key = _key()
    if not key:
        raise GoogleError("GOOGLE_TTS_KEY is not set", 0, fatal=True)
    f = KT.pitch_factor(pitch)
    if abs(f - 1.0) < 0.01:
        f = 1.0
    speed = min(2.0, max(0.25, KT.speed_of(rate) / f))
    parts = []
    for p in _pieces(text):
        parts += [_piece(p, locale, name, speed, key), np.zeros(int(0.12 * KSR))]
    y = np.concatenate(parts[:-1])
    if not np.all(np.isfinite(y)) or len(y) < 0.2 * KSR or float(np.max(np.abs(y))) < 1e-3:
        raise RuntimeError("the clip is empty or broken")
    y = KT.shift_voice(y, f)
    secs, n = len(y) / float(KSR), len(text.strip())
    if not (0.03 * n <= secs <= max(0.30 * n, 2.5)):                               # people say 6 to 25 characters a second; a clip far outside is a failure of the service
        raise RuntimeError("the clip has the wrong length: %.1f s for %d characters" % (secs, n))
    return y


def make(items, path_of, ffmpeg="ffmpeg", log=print):
    """Writes the 24 kHz clip of every item (text, voice spec, rate, pitch, ...) to path_of(item) (a file name like that of Kokoro's: voice._convert2 reads it).  Returns the
    items that could NOT be made: the caller takes the Kokoro or the Edge voice for those.  The first clip is made alone: when the key or the billing is wrong the whole
    batch is given up at once (no minutes of retries); the others are made by a few threads at the pace the service allows."""
    items = list(items)
    rows = {}
    for it in items:
        rows.setdefault(path_of(it), (it[0], it[1], it[2], it[3], path_of(it)))
    todo = [r for r in rows.values() if not KT._made(r[4])]
    t0 = time.time()
    done = {"n": 0, "secs": 0.0}
    budget = float(os.environ.get("BIBI_GOOGLE_BUDGET") or 3000)                    # seconds for one batch

    def one(row):
        text, voice, rate, pitch, path = row
        if _S["dead"]:
            return
        if time.time() - t0 > budget:
            _kill("the time of this batch (%d s) is spent" % budget)
            return
        try:
            y = speak(text, voice, rate, pitch, ffmpeg)
            KT.write_wav(path + ".part", y, KSR)
            os.replace(path + ".part", path)
            with _LOCK:
                done["n"] += 1
                done["secs"] += len(y) / float(KSR)
        except Exception as e:
            log("[gtts] %s failed for %r: %s" % (voice.split("|")[0], text[:50], _scrub(repr(e))[:260]))

    if todo and _S["dead"]:
        log("[gtts] the service is given up in this run (%s); the other voices are used" % _S["dead"])
    elif todo:
        one(todo[0])
        if not _S["dead"] and len(todo) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get("BIBI_GOOGLE_WORKERS") or 4)) as ex:
                list(ex.map(one, todo[1:]))
        if _S["dead"]:
            log("[gtts] the service was given up: %s" % _S["dead"])
    failed = [it for it in items if not KT._made(path_of(it))]
    made = len(rows) - len({path_of(it) for it in failed})
    _S["seconds"] += done["secs"]
    log("[gtts] %d of %d clips made (%.0f s of speech, %d characters sent so far in this run) in %.0f s; %d item(s) go to the other voices" %
        (made, len(rows), done["secs"], _S["chars"], time.time() - t0, len(failed)))
    return failed


def _voices_url():
    ep = _endpoint()
    return ep[:-len("text:synthesize")] + "voices" if ep.endswith("text:synthesize") else VOICES_URL


def list_voices(locale):
    """The Chirp 3 HD voices the service offers for a language (a list of names), for the lab's log."""
    key = _key()
    if not key:
        return []
    req = urllib.request.Request(_voices_url() + "?languageCode=" + locale, headers={"X-Goog-Api-Key": key, "User-Agent": "bibi-buzz-tv/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        vs = json.loads(r.read().decode("utf-8")).get("voices", [])
    return sorted(v["name"] for v in vs if "Chirp3-HD" in v.get("name", ""))


# ------------------------------------------------------------------------------------------------------------------------ the characters
# The same TYPES as tales.TYPES, here with the Chirp 3 HD voices: type -> (voice, rate, pitch, effect[, 'en-GB' = British English in the English tales]).  The entry may be a tuple
# of up to three such entries (see ktts._pick): the voice of the type, of a second and of a third character of that type in one tale (the three pigs are three different people).
# The same voice speaks the character in English and in Turkish.  A "+X Hz" is a factor of 1 + X / 150 (shift_voice: a smaller or a bigger person); an effect is voice.py's
# (room = a hall, lp = a veiled voice, bass = a heavier one).
# The first casting is made from what Google says of the voices (Leda youthful, Gacrux mature, Algenib gravelly ...) and is checked by the speech lab (tools/speech_lab.py,
# the "google" job): the pitch (F0), the naturalness (UTMOS), the words a listener would miss (Whisper) and the voice prints (ECAPA) of every voice and every character, and
# that no two characters of one tale are the same voice or sound alike.
GTYPES = {
    "nar": ("Sulafat", "-6%", "+0Hz", ""),
    "girl": (("Leda", "-2%", "+22Hz", ""), ("Zephyr", "-2%", "+22Hz", "")),
    "teen": ("Autonoe", "-2%", "+0Hz", ""),
    "boy": (("Puck", "+4%", "+30Hz", ""), ("Sadachbia", "+4%", "+30Hz", "")),
    "baby": ("Laomedeia", "+0%", "+40Hz", ""),
    "woman": ("Erinome", "-4%", "+0Hz", ""),
    "granny": (("Gacrux", "-14%", "-8Hz", ""), None, ("Vindemiatrix", "-14%", "-8Hz", "")),
    "fakegranny": ("Algenib", "-8%", "+30Hz", ""),
    "man": ("Orus", "-6%", "+0Hz", ""),
    "grandpa": ("Umbriel", "-14%", "-8Hz", "lp@7000"),
    "prince": ("Achird", "+0%", "+0Hz", "", "en-GB"),
    "king": ("Alnilam", "-14%", "+0Hz", "room@0.07,0.5", "en-GB"),
    "lord": ("Rasalgethi", "-8%", "+0Hz", "", "en-GB"),
    "queen": ("Pulcherrima", "-10%", "+0Hz", "room@0.06,0.5", "en-GB"),
    "stepmother": ("Kore", "-12%", "-8Hz", ""),
    "stepsister": (("Callirrhoe", "+6%", "+15Hz", ""), ("Despina", "+6%", "+0Hz", "")),
    "witch": ("Gacrux", "-14%", "-15Hz", "lp@7000"),
    "fairy": ("Aoede", "-8%", "+15Hz", "room@0.12,0.8"),
    "mirror": ("Charon", "-18%", "+0Hz", "room@0.16,0.9"),
    "dwarf": ("Sadaltager", "+6%", "+15Hz", ""),
    "elf": ("Puck", "+10%", "+45Hz", ""),
    "elfgirl": ("Leda", "+10%", "+30Hz", ""),
    "troll": ("Algenib", "-16%", "-15Hz", "bass@2"),
    "giant": ("Enceladus", "-16%", "-30Hz", "room@0.10,0.7"),
    "pig": (("Fenrir", "+2%", "+30Hz", ""), ("Zubenelgenubi", "+2%", "+15Hz", ""), ("Schedar", "+2%", "+30Hz", "")),
    "wolf": ("Algieba", "-10%", "-15Hz", "bass@2"),
    "hare": ("Achird", "+8%", "+30Hz", ""),
    "tortoise": ("Umbriel", "-20%", "-8Hz", "lp@7000"),
    "bear": ("Charon", "-12%", "-8Hz", ""),
    "mamabear": ("Kore", "-8%", "+0Hz", ""),
    "goat_little": ("Sadachbia", "+4%", "+45Hz", ""),
    "goat_mid": ("Iapetus", "+0%", "+0Hz", ""),
    "goat_big": ("Alnilam", "-14%", "-15Hz", "bass@2"),
    "hen": ("Callirrhoe", "+4%", "+15Hz", ""),
    "fox": ("Zubenelgenubi", "-4%", "+0Hz", ""),
    "tiny": ("Zephyr", "+8%", "+45Hz", ""),
    "lion": ("Orus", "-12%", "-15Hz", "room@0.10,0.8"),
}
NARRATOR = {"en": ("Sulafat", "-6%", "+0Hz"), "tr": ("Sulafat", "-6%", "+0Hz")}       # the narrator of the lessons (English); the tales take GTYPES["nar"]
ALT = {}                                                                              # (voice spec, rate, pitch) of a Google character -> its Kokoro casting (spec, rate, pitch, effect)


def cast(typ, lang, edge, off=0):
    """(voice spec with its Edge stand-in, rate, pitch, effect) of a character type in a language, or None when there is no Google voice for it.  `edge` is the
    (voice, rate, pitch, effect) of the Edge casting (tales.TYPES), `off` tells two characters of one type apart (ktts._pick: a variant voice, else a pitch offset in Hz)."""
    if typ not in GTYPES or lang not in LOCALES:
        return None
    entry, off = KT._pick(GTYPES[typ], off)
    v, r, p, fx = entry[:4]
    loc = entry[4] if len(entry) > 4 and lang == "en" else lang
    if off:
        p = "%+dHz" % (int(p[:-2]) + off)
    return ("g:%s:%s|%s|%s|%s" % (loc, v, edge[0], edge[1], edge[2]), r, p, fx)


def link(google, kokoro):
    """Tells which Kokoro casting (a tuple (spec, rate, pitch, effect) of ktts.cast) takes over a line of the Google casting `google` when the service cannot make it."""
    ALT[(google[0], google[1], google[2])] = tuple(kokoro)


def alt_of(item):
    """The item (text, voice, rate, pitch, effect) of the Kokoro casting of the character that has the Google item `item`, or None."""
    k = ALT.get((item[1], item[2], item[3]))
    return (item[0],) + k if k else None


def lesson_voice():
    """(voice spec, rate, pitch) of the narrator of the English lessons: the Edge voice that stands in for it is added by voice.py."""
    v, r, p = NARRATOR["en"]
    return "g:en:%s" % v, r, p
