"""Soundtrack for the lessons: seeded nursery-style music laid on the SAME beat grid as the voice,
music ducking under the voice, sound effects on the cues, and the final mix.

Nothing is ever sped up: voice clips are placed at their cue start (always on a beat), the music runs on
the beat grid, so voice and music stay in sync for the whole video.
"""
import random
import wave

import numpy as np

from . import schedule as SCH
from .audio import SR, add, ding, hz, pop_sfx, shaker, sparkle, tone, uke, woodblock, xylo, bass

SCALE = [0, 2, 4, 7, 9]                     # major pentatonic degrees
PROGS = [[0, 7, 9, 5], [0, 9, 5, 7], [0, 5, 7, 0], [9, 5, 0, 7], [0, 5, 9, 7], [0, 7, 5, 7]]
DING_NOTES = [72, 74, 76, 79, 81, 84, 86, 88, 91, 93]
KEYS = [0, 5, 7, 2, 10, 3]


def scale_note(idx, key):
    octv, deg = divmod(idx, 5)
    return 72 + key + 12 * octv + SCALE[deg]


def chord_pcs(root):
    return (root % 12, (root + (3 if root == 9 else 4)) % 12, (root + 7) % 12)


def voicing(pcs, key):
    return sorted(58 + ((pc + key - 58) % 12) for pc in pcs)


def bell(m, dur=0.9):
    return tone(hz(m), dur, harm=(1, 0.22, 0.1), decay=4.2)


def make_phrase(rng, roots, key):
    """Two bars of melody: list of 8 beats, each None (rest) or a list of one/two scale indices."""
    idx = rng.randint(2, 5)
    beats = []
    for i in range(8):
        pcs = chord_pcs(roots[i // 4])
        if i % 4 == 0:      # downbeat: nearest chord tone
            cands = [j for j in range(0, 8) if (scale_note(j, key) - key) % 12 in pcs]
            idx = min(cands, key=lambda j: abs(j - idx)) if cands else idx
        else:
            idx = max(0, min(7, idx + rng.choice([-2, -1, -1, 0, 1, 1, 2])))
        if i % 4 in (1, 3) and rng.random() < 0.10:
            beats.append(None)
            continue
        if rng.random() < 0.25 and i % 4 != 0:
            j = max(0, min(7, idx + rng.choice([-1, 1])))
            beats.append([idx, j])
        else:
            beats.append([idx])
    return beats


def make_music(lesson, n):
    rng = random.Random(lesson.seed * 7919 + 13)
    beat = lesson.beat
    buf = np.zeros(n + SR * 5, dtype=np.float32)
    key = rng.choice(KEYS)
    prog = rng.choice(PROGS)
    lead = rng.choice([xylo, xylo, bell])
    t_start = lesson.grid0
    t_end = lesson.segs[-1].t1
    bars = max(1, int(round((t_end - t_start) / (4 * beat))))

    # lead-in
    if lesson.lead_beats >= 4:
        for i in range(8):
            add(buf, i * beat / 2, lead(scale_note(i % 5 - 5 + (i // 5) * 5, key)), 0.10 + 0.20 * (i + 1) / 8)
    else:
        add(buf, 0, lead(scale_note(0, key)), 0.22)
        add(buf, beat / 2, lead(scale_note(2, key)), 0.26)

    phrases = [make_phrase(rng, [prog[0], prog[1]], key), make_phrase(rng, [prog[2], prog[3]], key)]
    for bar in range(bars):
        t0 = t_start + bar * 4 * beat
        root = prog[bar % 4]
        pcs = chord_pcs(root)
        tri = voicing(pcs, key)
        r = 36 + key + root
        g = 0.70 if bar == 0 else 1.0
        add(buf, t0, bass(r), 0.38 * g)
        add(buf, t0 + 2 * beat, bass(r + 12), 0.28 * g)
        for e in range(8):                                  # strummed eighth-note arpeggio
            add(buf, t0 + e * beat / 2, uke(tri[(0, 1, 2, 1, 0, 1, 2, 1)[e]]), 0.15 * g)
        phrase = phrases[(bar // 2) % 2]                    # A B A B ...
        for b in range(4):
            step = phrase[(bar % 2) * 4 + b]
            if not step or bar == 0:
                continue
            for k, j in enumerate(step):
                add(buf, t0 + b * beat + k * beat / 2, lead(scale_note(j, key)), 0.27 * g)
        for e in (1, 3, 5, 7):
            add(buf, t0 + e * beat / 2, shaker(), 0.09 * g)
        for b in (1, 3):
            add(buf, t0 + b * beat, woodblock(), 0.06 * g)
    # final chord rings on the closing bar (tonic major)
    ring = 3.0 if lesson.fmt == "long" else 1.6
    for m in (48 + key, 52 + key, 55 + key, 60 + key, 64 + key):
        add(buf, t_end, tone(hz(m), ring, harm=(1, 0.4), decay=1.3), 0.11)
    add(buf, t_end, lead(scale_note(5, key)), 0.25)
    return buf[:n]


def ducking(intervals, n, depth=0.58):
    """Music gain: 1 normally, 1-depth while somebody speaks (smooth ramps, starts slightly early)."""
    m = np.zeros(n, dtype=np.float64)
    for a, b in intervals:
        m[max(0, int(a * SR)):min(n, int(b * SR))] = 1.0
    w = int(0.16 * SR)
    cs = np.concatenate([[0.0], np.cumsum(m)])
    idx = np.arange(n)
    lo, hi = np.clip(idx - w, 0, n), np.clip(idx + w, 0, n)
    avg = (cs[hi] - cs[lo]) / np.maximum(hi - lo, 1)
    return (1.0 - depth * np.clip(avg * 2.2, 0, 1)).astype(np.float32)


def make_sfx(lesson, n):
    sb = np.zeros(n + SR * 3, dtype=np.float32)
    key_hint = 0
    for t, kind, arg in SCH.sfx_events(lesson):
        if kind == "pop":
            add(sb, t, pop_sfx(), 0.20)
        elif kind == "ding":
            add(sb, t, ding(DING_NOTES[(int(arg) - 1) % len(DING_NOTES)] + key_hint), 0.20)
        elif kind == "sparkle":
            tmp = np.zeros(SR * 2)
            sparkle(tmp, 0.0)
            add(sb, t, tmp, 0.9)
    return sb[:n]


def mix(lesson, clips):
    """Returns the final mono float32 mix (music + sfx + voice) of exactly lesson.duration seconds."""
    n = int(round(lesson.duration * SR))
    music = make_music(lesson, n)
    duck = ducking(SCH.voice_intervals(lesson), n)
    sfx = make_sfx(lesson, n)
    voice = np.zeros(n + SR * 4, dtype=np.float32)
    for c in lesson.cues():
        if c.text:
            add(voice, c.t, clips[c.text], 1.0)
    voice = voice[:n]
    out = music * duck * 0.50 + sfx * 0.9 + voice * 1.0
    fade = int(1.0 * SR)
    out[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    peak = float(np.max(np.abs(out))) or 1.0
    if peak > 0.95:
        out *= 0.95 / peak
    return out


def write_wav(path, y):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    return path
