"""Sound for the story videos: mood music and sound effects (numpy only, no sample files), ducking and the mix."""
import random
from functools import lru_cache

import numpy as np

from .audio import SR, add, ding, hz, pop_sfx, sparkle, tone, woodblock
from .music import ducking, write_wav  # noqa: F401  (write_wav is re-exported for story.py)


# ================================================================================================ sound effects
def _noise(n, seed=1):
    return np.random.default_rng(seed).standard_normal(n)


def band_noise(dur, lo, hi, seed=1):
    n = int(dur * SR)
    spec = np.fft.rfft(_noise(n, seed))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    mask = np.clip(np.minimum((f - lo) / max(lo * 0.4, 1.0), (hi - f) / max(hi * 0.3, 1.0)), 0, 1)
    y = np.fft.irfft(spec * mask, n)
    return y / (np.max(np.abs(y)) + 1e-9)


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def sfx_knock():
    out = np.zeros(int(1.0 * SR))
    for i in range(3):
        n = int(0.14 * SR)
        t = np.arange(n) / SR
        hit = np.sin(2 * np.pi * (170 - 40 * t / 0.14) * t) * np.exp(-t * 34) + 0.5 * _noise(n, 3 + i) * np.exp(-t * 120)
        add(out, 0.04 + i * 0.22, hit, 0.9)
    return out


def sfx_wind(dur=2.4):
    t = _t(dur)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.4
    lo = band_noise(dur, 200, 900, 7)
    hi = band_noise(dur, 800, 3200, 8)
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * 2.3 * t)
    return (0.8 * lo + 0.35 * hi) * env * trem * 0.8


def sfx_collapse():
    dur = 1.8
    t = _t(dur)
    y = band_noise(dur, 150, 3500, 11) * np.exp(-t * 2.6) * 0.8
    y += np.sin(2 * np.pi * 62 * t) * np.exp(-t * 5.5) * 0.9
    rng = random.Random(5)
    for i in range(14):
        add(y, 0.05 + i * 0.07 + rng.random() * 0.05, tone(rng.choice((260, 330, 420, 520, 660)), 0.1, harm=(1, 0.5), decay=34), 0.25)
    return y


def sfx_boing():
    dur = 0.5
    t = _t(dur)
    f = 300 + 380 * np.sin(np.pi * np.clip(t / 0.22, 0, 1)) - 120 * np.clip((t - 0.22) / 0.28, 0, 1)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) * (1 + 0.15 * np.sin(2 * np.pi * 28 * t)) * 0.8


def sfx_splash():
    dur = 1.2
    t = _t(dur)
    y = band_noise(dur, 700, 6000, 13) * np.exp(-t * 4.2) * 0.8
    for i, f in enumerate((520, 660, 820, 470, 710)):
        add(y, 0.1 + i * 0.09, tone(f, 0.18, harm=(1,), decay=18), 0.18)
    return y


def sfx_sparkle():
    tmp = np.zeros(int(1.6 * SR))
    sparkle(tmp, 0.0)
    return tmp


def sfx_ding():
    return ding(84)


def sfx_pop():
    return pop_sfx() * 0.8


def sfx_thud():
    t = _t(0.35)
    return np.sin(2 * np.pi * 72 * t) * np.exp(-t * 14) * 0.9


def sfx_hoof():
    """One light hoof on a wooden plank (trip ...)."""
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (430 - 130 * t / 0.16) * t) * np.exp(-t * 36) * 0.8 + _noise(n, 7) * np.exp(-t * 160) * 0.3


def sfx_hoof2():
    """... and the other hoof, a little lower (trap)."""
    n = int(0.17 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (340 - 100 * t / 0.17) * t) * np.exp(-t * 34) * 0.85 + _noise(n, 9) * np.exp(-t * 150) * 0.3


def sfx_boom():
    dur = 0.9
    t = _t(dur)
    return (np.sin(2 * np.pi * (90 - 40 * t) * t) * np.exp(-t * 5) * 0.9 + band_noise(dur, 100, 2500, 17) * np.exp(-t * 7) * 0.7)


def sfx_cheer():
    dur = 2.6
    t = _t(dur)
    env = np.minimum(1, t / 0.25) * np.exp(-np.maximum(0, t - 0.9) * 1.2)
    crowd = band_noise(dur, 500, 3200, 19) * env * (0.7 + 0.3 * np.sin(2 * np.pi * 5.5 * t))
    y = crowd * 0.55
    for i, m in enumerate((72, 76, 79, 84)):
        add(y, 0.05 + i * 0.08, tone(hz(m), 0.9, harm=(1, 0.5, 0.25), decay=3.2), 0.18)
    add(y, 0.0, sfx_sparkle(), 0.6)
    return y


def sfx_creak():
    dur = 0.95
    t = _t(dur)
    f = 190 + 90 * np.sin(np.pi * t / dur) + 12 * np.sin(2 * np.pi * 17 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = sum(np.sin(k * ph) / k for k in (1, 2, 3, 4, 5))
    env = np.minimum(1, t / 0.08) * np.minimum(1, (dur - t) / 0.2)
    return y * env * 0.22


def sfx_snore():
    dur = 2.2
    t = _t(dur)
    breath = np.clip(np.sin(2 * np.pi * t / 1.1), 0, 1) ** 1.3
    f = 96 + 8 * np.sin(2 * np.pi * 9 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) + 0.6 * np.sin(2 * ph) + 0.35 * np.sin(3 * ph)) * breath * 0.45
    return y + band_noise(dur, 150, 700, 23) * breath * 0.12


def sfx_dizzy():
    dur = 1.0
    t = _t(dur)
    f = 560 + 220 * np.sin(2 * np.pi * 3.2 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, (dur - t) / 0.3) * 0.28


def sfx_whoosh():
    dur = 0.7
    t = _t(dur)
    return band_noise(dur, 400, 3600, 29) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5 * 0.55


def sfx_beep3():
    out = np.zeros(int(2.0 * SR))
    for i, f in enumerate((523, 523, 784)):
        add(out, i * 0.55, tone(f, 0.35 if i < 2 else 0.9, harm=(1, 0.3), decay=2.2), 0.5)
    return out


def sfx_fanfare():
    out = np.zeros(int(3.0 * SR))
    for i, (m, d) in enumerate(((60, 0.22), (64, 0.22), (67, 0.22), (72, 1.3))):
        t0 = i * 0.24
        for dm in (0, 4, 7) if i == 3 else (0,):
            add(out, t0, tone(hz(m + dm), d + 0.2, harm=(1, 0.7, 0.5, 0.35), decay=2.4), 0.2)
    return out


def sfx_munch():
    out = np.zeros(int(1.1 * SR))
    for i in range(3):
        add(out, 0.05 + i * 0.28, band_noise(0.13, 200, 1600, 31 + i) * np.exp(-_t(0.13) * 22), 0.6)
    return out


def sfx_gulp():
    t = _t(0.35)
    f = 260 - 140 * t / 0.35
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 0.6


def sfx_yawn():
    dur = 1.5
    t = _t(dur)
    f = 300 + 180 * np.sin(np.pi * t / dur) - 120 * (t / dur)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.8
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 + band_noise(dur, 300, 1200, 37) * 0.1) * env


def sfx_rumble():
    """A hungry tummy: a low growl that wobbles."""
    dur = 1.1
    t = _t(dur)
    f = 74 - 20 * t / dur + 8 * np.sin(2 * np.pi * 11 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    am = 0.55 + 0.45 * np.sin(2 * np.pi * 8 * t)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
    y = (np.sin(ph) + 0.7 * np.sin(2 * ph) + 0.5 * np.sin(3 * ph) + 0.3 * np.sin(4 * ph)) * am * env * 0.4
    return y + band_noise(dur, 80, 320, 41) * env * 0.22


def sfx_tada():
    out = np.zeros(int(2.2 * SR))
    for i, m in enumerate((67, 72, 76, 79, 84)):
        add(out, i * 0.09, tone(hz(m), 1.2, harm=(1, 0.5, 0.25), decay=3.0), 0.2)
    return out


SFX = {"knock": sfx_knock, "wind": sfx_wind, "collapse": sfx_collapse, "boing": sfx_boing, "splash": sfx_splash,
       "sparkle": sfx_sparkle, "ding": sfx_ding, "pop": sfx_pop, "thud": sfx_thud, "hoof": sfx_hoof, "hoof2": sfx_hoof2, "boom": sfx_boom, "cheer": sfx_cheer,
       "creak": sfx_creak, "snore": sfx_snore, "dizzy": sfx_dizzy, "whoosh": sfx_whoosh, "beep3": sfx_beep3,
       "fanfare": sfx_fanfare, "munch": sfx_munch, "gulp": sfx_gulp, "yawn": sfx_yawn, "tada": sfx_tada, "rumble": sfx_rumble}
SFX_GAIN = {"wind": 0.45, "collapse": 0.55, "boom": 0.5, "cheer": 0.5, "knock": 0.55, "creak": 0.5, "snore": 0.35,
            "fanfare": 0.4, "tada": 0.4, "beep3": 0.35, "boing": 0.4, "pop": 0.35, "sparkle": 0.45}


@lru_cache(maxsize=None)
def _sfx(name):
    return SFX[name]().astype(np.float32)


# ================================================================================================ music
MOODS = {
    "happy":   dict(bpm=104, key=0, minor=False, pat="strum", mel=0.80, oct=0, bass=True, shake=True, vol=1.0),
    "title":   dict(bpm=112, key=0, minor=False, pat="strum", mel=0.95, oct=0, bass=True, shake=True, vol=1.0),
    "calm":    dict(bpm=78, key=5, minor=False, pat="arp", mel=0.40, oct=0, bass=False, shake=False, vol=0.9),
    "tense":   dict(bpm=90, key=9, minor=True, pat="drone", mel=0.22, oct=-12, bass=True, shake=False, vol=0.95),
    "chase":   dict(bpm=144, key=2, minor=False, pat="arp16", mel=0.85, oct=0, bass=True, shake=True, vol=1.0),
    "sad":     dict(bpm=66, key=9, minor=True, pat="arp", mel=0.30, oct=0, bass=False, shake=False, vol=0.85),
    "triumph": dict(bpm=118, key=0, minor=False, pat="strum", mel=1.0, oct=0, bass=True, shake=True, vol=1.0),
    "night":   dict(bpm=60, key=7, minor=False, pat="arp", mel=0.55, oct=12, bass=False, shake=False, vol=0.8),
    "sneaky":  dict(bpm=96, key=3, minor=True, pat="drone", mel=0.30, oct=0, bass=True, shake=False, vol=0.9),
}
PROG_MAJ = ((0, "M"), (7, "M"), (9, "m"), (5, "M"))
PROG_MIN = ((0, "m"), (8, "M"), (3, "M"), (10, "M"))
PENT_MAJ = (0, 2, 4, 7, 9)
PENT_MIN = (0, 3, 5, 7, 10)


@lru_cache(maxsize=None)
def _inst(kind, m, dur):
    if kind == "uke":
        return tone(hz(m), dur, harm=(1, 0.5, 0.3, 0.15), decay=3.6).astype(np.float32)
    if kind == "xylo":
        return tone(hz(m), dur, harm=(1, 0, 0.18, 0, 0.08), decay=6.0).astype(np.float32)
    if kind == "bass":
        return tone(hz(m), dur, harm=(1, 0.3), decay=4.5).astype(np.float32)
    if kind == "bell":
        return tone(hz(m), dur, harm=(1, 0.35, 0.12), decay=2.6).astype(np.float32)
    if kind == "pad":
        n = int(dur * SR)
        t = np.arange(n) / SR
        y = (np.sin(2 * np.pi * hz(m) * t) + 0.35 * np.sin(2 * np.pi * hz(m) * 2.003 * t)) * np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.8)
        return y.astype(np.float32)
    raise KeyError(kind)


@lru_cache(maxsize=None)
def _shake(seed):
    n = int(0.07 * SR)
    return (np.random.default_rng(seed % 7).standard_normal(n) * np.exp(-np.arange(n) / SR * 55)).astype(np.float32)


def scene_music(mood, dur, seed):
    """Music for one scene: `dur` seconds plus a tail for the crossfade."""
    P = MOODS.get(mood, MOODS["happy"])
    rng = random.Random(seed * 31 + 7)
    n = int((dur + 1.2) * SR)
    buf = np.zeros(n + SR * 4, dtype=np.float32)
    beat = 60.0 / P["bpm"]
    bar = beat * 4
    prog = PROG_MIN if P["minor"] else PROG_MAJ
    pent = PENT_MIN if P["minor"] else PENT_MAJ
    key = P["key"]
    mi = rng.randrange(len(pent))
    nbars = int((dur + 1.2) / bar) + 1
    for b in range(nbars):
        t0 = b * bar
        root, q = prog[b % 4]
        third = 3 if q == "m" else 4
        tones = (key + root + 48 + P["oct"], key + root + 48 + third + P["oct"], key + root + 48 + 7 + P["oct"])
        pat = P["pat"]
        if pat == "strum":
            for bt in range(4):
                g = 0.17 if bt in (0, 2) else 0.11
                for j, m in enumerate(tones):
                    add(buf, t0 + bt * beat + j * 0.013, _inst("uke", m + 12, 0.9), g * (1.0 if bt != 1 and bt != 3 else 0.85))
        elif pat in ("arp", "arp16"):
            step = beat / (2 if pat == "arp" else 4)
            seq = (0, 1, 2, 1) if pat == "arp16" else (0, 1, 2, 1, 0, 2, 1, 2)
            for i in range(int(4 * beat / step)):
                m = tones[seq[i % len(seq)]] + 12
                add(buf, t0 + i * step, _inst("uke" if pat == "arp16" else "xylo", m, 0.7), 0.14)
        elif pat == "drone":
            for m in (tones[0] - 12, tones[2] - 12):
                add(buf, t0, _inst("pad", m, bar + 0.6), 0.10)
            for bt in (1, 3):
                add(buf, t0 + bt * beat, woodblock(), 0.05)
            add(buf, t0 + 2.5 * beat, _inst("bass", tones[0] - 12, 0.5), 0.14)
        if P["bass"] and pat in ("strum", "arp16", "drone"):
            add(buf, t0, _inst("bass", tones[0] - 12, 0.6), 0.22)
            add(buf, t0 + 2 * beat, _inst("bass", tones[2] - 12 if pat != "drone" else tones[0] - 12, 0.5), 0.17)
        if P["shake"]:
            for i in range(8):
                if i % 2 == 1:
                    add(buf, t0 + i * beat / 2, _shake(i + b), 0.05)
        for i in range(8):                                                            # melody on 8th notes
            if rng.random() < P["mel"] * (0.55 if i % 2 else 0.95):
                mi = int(np.clip(mi + rng.choice((-2, -1, -1, 0, 1, 1, 2)), 0, len(pent) * 2 - 1))
                m = key + 72 + P["oct"] + pent[mi % len(pent)] + 12 * (mi // len(pent)) - 12
                add(buf, t0 + i * beat / 2, _inst("xylo" if mood not in ("night", "calm") else "bell", m, 0.8), 0.20)
    out = buf[:n].copy()
    fi, fo = int(0.5 * SR), int(1.0 * SR)
    out[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)
    out[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)
    return out * P["vol"]


def mix(tale, clips, voices=True):
    """Final mono float32 mix (voices + mood music + sound effects) of exactly tale.duration seconds."""
    n = int(round(tale.duration * SR))
    music = np.zeros(n + SR * 4, dtype=np.float32)
    for (t0, t1, mood, si) in tale.mood_spans:
        sm = scene_music(mood, t1 - t0, si + 1)
        add(music, t0, sm, 1.0)
    music = music[:n]
    voice = np.zeros(n + SR * 6, dtype=np.float32)
    ivs = []
    for (t, key) in tale.voice_events:
        if voices:
            add(voice, t, clips[key], 1.0)
        ivs.append((t, t + len(clips[key]) / SR))
    voice = voice[:n]
    duck = ducking(ivs, n, depth=0.62)
    sfx = np.zeros(n + SR * 4, dtype=np.float32)
    for (t, name, g) in tale.sfx_events:
        add(sfx, t, _sfx(name), g * SFX_GAIN.get(name, 0.5))
    sfx = sfx[:n]
    out = music * duck * 0.55 + sfx * 0.9 + voice * 1.0
    fade = int(1.2 * SR)
    out[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    peak = float(np.max(np.abs(out))) or 1.0
    if peak > 0.95:
        out *= 0.95 / peak
    return out
