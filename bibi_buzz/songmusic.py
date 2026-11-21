"""The little band of the song videos (numpy only): a lead instrument that plays the tune, chords and a bass, a few drums, a bit of reverb.

Notes are written like "C4 C4 G4:2 r:1 Bb3:0.5": a note name with its octave, then ":beats" (one beat when left out); r is a rest.
Chords are written like "C:4 F:2 G7:2": the chord name and how many beats it lasts.
"""
import numpy as np

from .audio import SR, add, hz, tone

NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_midi(tok):
    """'C4' -> 60, 'F#3' -> 54, 'Bb3' -> 58, 'r' -> None"""
    if tok[0] in "rR":
        return None
    m = NAMES[tok[0]]
    i = 1
    while i < len(tok) and tok[i] in "#b":
        m += 1 if tok[i] == "#" else -1
        i += 1
    return 12 * (int(tok[i:]) + 1) + m


def parse_notes(spec):
    """'C4 C4:2 r:1' -> [(midi or None, beats)]"""
    out = []
    for tok in spec.split():
        name, _, d = tok.partition(":")
        out.append((note_midi(name), float(d) if d else 1.0))
    return out


def parse_chords(spec):
    """'C:4 F:2 G7:2' -> [(symbol, beats)]"""
    out = []
    for tok in spec.split():
        name, _, d = tok.partition(":")
        out.append((name, float(d) if d else 4.0))
    return out


def chord_pcs(sym):
    """('C' | 'Am' | 'G7' | 'Bb' | 'F#m' ...) -> (root pitch class, [pitch classes]) """
    root = NAMES[sym[0]]
    i = 1
    while i < len(sym) and sym[i] in "#b":
        root += 1 if sym[i] == "#" else -1
        i += 1
    q = sym[i:]
    third = 3 if q.startswith("m") and not q.startswith("maj") else 4
    pcs = [root % 12, (root + third) % 12, (root + 7) % 12]
    if q.endswith("7"):
        pcs.append((root + 10) % 12)
    return root % 12, pcs


def voicing(pcs, lo=57):
    """The chord tones as notes between `lo` and lo+12 (ascending)."""
    return sorted(lo + ((pc - lo) % 12) for pc in pcs)


# ================================================================================================ instruments
def _t(dur):
    return np.arange(int(dur * SR)) / SR


def xylophone(m, dur=0.7):
    return tone(hz(m), dur, harm=(1, 0, 0.18, 0, 0.08), decay=6.0)


def glockenspiel(m, dur=1.3):
    f, t = hz(m), _t(dur)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * 3.2) + 0.32 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6.5) \
        + 0.12 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 11)
    return y * np.minimum(1.0, t / 0.003)


def music_box(m, dur=1.5):
    f, t = hz(m), _t(dur)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * 2.6) + 0.25 * np.sin(2 * np.pi * f * 3.0 * t) * np.exp(-t * 5.0) \
        + 0.10 * np.sin(2 * np.pi * f * 5.0 * t) * np.exp(-t * 8.0)
    return y * np.minimum(1.0, t / 0.004)


def flute(m, dur=0.8):
    f, t = hz(m), _t(dur)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1.0, t / 0.3)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    y = np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    y = y + 0.025 * np.random.default_rng(int(f)).standard_normal(len(t))
    env = np.minimum(1.0, t / 0.05) * np.minimum(1.0, (dur - t) / 0.12)
    return y * env * 0.7


def ukulele(m, dur=0.9):
    f, t = hz(m), _t(dur)
    y = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (3.4 + 1.6 * k)) for k, a in ((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.12)))
    return y * np.minimum(1.0, t / 0.003)


def pluck_bass(m, dur=0.6):
    f, t = hz(m), _t(dur)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * 4.0) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 7.0)
    return y * np.minimum(1.0, t / 0.004)


def kick():
    t = _t(0.28)
    f = 55 + 120 * np.exp(-t * 26)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11) * 0.9


def clap(seed=3):
    rng = np.random.default_rng(seed)
    out = np.zeros(int(0.22 * SR))
    for i, d in enumerate((0.0, 0.012, 0.026)):
        n = int(0.09 * SR)
        t = np.arange(n) / SR
        nz = np.diff(rng.standard_normal(n + 1))
        add(out, d, nz * np.exp(-t * (70 if i < 2 else 28)), 0.5)
    return out


def shaker_hit(dur=0.07, seed=1):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.diff(np.random.default_rng(seed).standard_normal(n + 1)) * np.exp(-t * 60)


def wood(m=79):
    return tone(hz(m), 0.08, harm=(1, 0.5), decay=40)


def tambourine(seed=5):
    rng = np.random.default_rng(seed)
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    nz = np.diff(rng.standard_normal(n + 1))
    return nz * np.exp(-t * 28) * 0.7 + 0.2 * np.sin(2 * np.pi * 7300 * t) * np.exp(-t * 40)


LEADS = {"xylo": xylophone, "glock": glockenspiel, "box": music_box, "flute": flute}


# ================================================================================================ the sequencer
def play_lead(buf, notes, inst="xylo", gain=0.3):
    """notes: [(t_seconds, midi, dur_seconds)] -> into buf"""
    f = LEADS[inst]
    for t, m, d in notes:
        add(buf, t, f(m, min(1.6, max(0.35, d * 1.1))) if inst == "flute" else f(m), gain)


def play_chords(buf, segs, bpm, beats, style="strum", gain=1.0, bass_gain=0.7, shift=0, origin=0.0):
    """segs: [(chord_symbol, first_beat, n_beats)] with the beats counted from the start of the song (`origin` = the beat where the bars
    of this stretch begin, so that 'beat 1 of the bar' is right); `shift` transposes by semitones.
    style: strum | oompah | waltz | lull | pad | none"""
    if style == "none":
        return
    beat = 60.0 / bpm
    o = int(round(origin))
    for sym, b0, nb in segs:
        root, pcs = chord_pcs(sym)
        root = (root + shift) % 12
        tri = voicing([(p + shift) % 12 for p in pcs])
        low = 36 + (root - 36) % 12
        n = int(round(nb))
        for j in range(n):
            b = b0 + j
            t = b * beat
            pos = (int(round(b)) - o) % beats
            if style == "strum":                                    # two eighth notes of a rolling arpeggio on every beat, the bass on 1 and 3
                a, b2 = ((0, 1), (2, 1))[pos % 2]
                add(buf, t, ukulele(tri[a % len(tri)]), 0.16 * gain)
                add(buf, t + beat / 2, ukulele(tri[b2 % len(tri)]), 0.12 * gain)
                if pos % 2 == 0:
                    add(buf, t, pluck_bass(low if pos == 0 else low + 7), 0.30 * bass_gain * gain)
            elif style == "oompah":
                if pos % 2 == 0:
                    add(buf, t, pluck_bass(low if pos == 0 else low + 7), 0.34 * bass_gain * gain)
                else:
                    for m in tri:
                        add(buf, t, ukulele(m, 0.5), 0.10 * gain)
            elif style == "waltz":
                if pos == 0:
                    add(buf, t, pluck_bass(low), 0.34 * bass_gain * gain)
                else:
                    for m in tri:
                        add(buf, t, ukulele(m, 0.6), 0.09 * gain)
            elif style == "lull":
                for e, k in enumerate((0, 1, 2, 1)):
                    add(buf, t + e * beat / 4, music_box(tri[k % len(tri)] + 12, 1.2), 0.10 * gain)
                if pos == 0:
                    add(buf, t, pluck_bass(low), 0.22 * bass_gain * gain)
            elif style == "pad":
                if j == 0:
                    for m in tri:
                        add(buf, t, tone(hz(m), nb * beat, harm=(1, 0.4), decay=0.6), 0.05 * gain)


def play_drums(buf, b0, b1, bpm, beats, style="light", gain=1.0, origin=0.0):
    """beats b0 .. b1 (counted from the start of the song; `origin` = the beat where the bars begin). styles: none | light | clap | party"""
    if style == "none":
        return
    beat = 60.0 / bpm
    o = int(round(origin))
    b = int(np.ceil(b0 - 1e-9))
    while b < b1 - 1e-9:
        t = b * beat
        pos = (b - o) % beats
        if style in ("light", "clap", "party"):
            add(buf, t + beat / 2, shaker_hit(), 0.09 * gain)
            if style == "light":
                if pos % 2 == 1:
                    add(buf, t, wood(), 0.06 * gain)
            else:
                if pos % 2 == 1:
                    add(buf, t, clap(), 0.20 * gain)
                if pos % 2 == 0:
                    add(buf, t, kick(), 0.26 * gain if style == "party" else 0.16 * gain)
                if style == "party":
                    add(buf, t + beat / 2, tambourine(), 0.08 * gain)
                    add(buf, t, shaker_hit(seed=2), 0.06 * gain)
        b += 1


def reverb(y, wet=0.13, rt=0.85, seed=7):
    """A small room: the signal convolved with a decaying noise tail (FFT), mixed in at `wet`."""
    n = int(rt * 1.3 * SR)
    t = np.arange(n) / SR
    ir = np.random.default_rng(seed).standard_normal(n) * np.exp(-t * 6.9 / rt)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(y) + n
    nfft = 1 << (L - 1).bit_length()
    w = np.fft.irfft(np.fft.rfft(y, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(y)]
    return y + wet * w * (np.max(np.abs(y)) / (np.max(np.abs(w)) + 1e-9))
