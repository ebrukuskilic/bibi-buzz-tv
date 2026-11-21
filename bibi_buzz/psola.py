"""Pitch tracking, pitch marks and TD-PSOLA: turns spoken words into sung notes (numpy only).

The voice of a text-to-speech clip is analysed once (pitch track, pitch marks, voiced / unvoiced), then every syllable is
re-synthesised on its note: the vowel is held for the length of the note (a time map that stretches only the steady
part of the vowel), the pitch is a flat note with a short glide to the next one and a little vibrato on long notes,
and the consonants keep their natural length.  Formants stay where they are (PSOLA copies whole pitch periods), so the
voice stays the same voice.
"""
import bisect
import math

import numpy as np

HOP = 0.005                                  # seconds between two analysis frames


# ================================================================================================ analysis
def _down(y, sr, target=11025):
    f = max(1, int(round(sr / target)))
    n = len(y) // f * f
    return y[:n].reshape(-1, f).mean(axis=1), sr / f


def analyse(y, sr, fmin=70.0, fmax=620.0):
    """-> dict(t, f0, voiced, rms, hop): one row per 5 ms.  f0 in Hz (0 where unvoiced), rms of a 30 ms window."""
    yd, sd = _down(y, sr)
    fl = int(0.04 * sd)
    hop = int(round(HOP * sd))
    lo, hi = int(sd / fmax), int(sd / fmin)
    pad = np.concatenate([np.zeros(fl // 2), yd, np.zeros(fl)])
    nfr = max(1, (len(yd)) // hop)
    idx = np.arange(nfr) * hop
    fr = np.stack([pad[i:i + fl] for i in idx])
    fr = (fr - fr.mean(axis=1, keepdims=True)) * np.hanning(fl)
    e = np.sqrt((fr ** 2).mean(axis=1))
    nfft = 1 << (2 * fl - 1).bit_length()
    sp = np.fft.rfft(fr, n=nfft, axis=1)
    ac = np.fft.irfft(sp * np.conj(sp), axis=1)[:, :hi + 2]
    ac = ac / (ac[:, :1] + 1e-12)
    ref = float(np.percentile(e, 95)) + 1e-9
    f0 = np.zeros(nfr)
    conf = np.zeros(nfr)
    for k in range(nfr):
        if e[k] < 0.06 * ref:
            continue
        seg = ac[k, lo:hi + 1]
        # all local peaks; prefer the shortest lag whose peak is close to the best one (avoids octave-down errors)
        pk = [j for j in range(1, len(seg) - 1) if seg[j] >= seg[j - 1] and seg[j] > seg[j + 1] and seg[j] > 0.3]
        if not pk:
            continue
        best = max(seg[j] for j in pk)
        j = next(j for j in pk if seg[j] >= 0.88 * best)
        a, b, c = seg[j - 1], seg[j], seg[j + 1]
        d = a - 2 * b + c
        lag = lo + j + (0.5 * (a - c) / d if abs(d) > 1e-12 else 0.0)
        f0[k] = sd / lag
        conf[k] = seg[j]
    voiced = (conf > 0.5) & (f0 > 0)
    f0 = np.where(voiced, f0, 0.0)
    # remove isolated octave jumps / single-frame islands
    med = f0.copy()
    for k in range(2, nfr - 2):
        w = f0[k - 2:k + 3]
        w = w[w > 0]
        if f0[k] > 0 and len(w) >= 3:
            m = float(np.median(w))
            if f0[k] > 1.35 * m or f0[k] < m / 1.35:
                med[k] = m
    f0 = med
    v = f0 > 0
    for k in range(1, nfr - 1):                                       # a one-frame hole or island is not a voicing change
        if not v[k] and v[k - 1] and v[k + 1]:
            f0[k] = 0.5 * (f0[k - 1] + f0[k + 1])
    v = f0 > 0
    for k in range(1, nfr - 1):
        if v[k] and not v[k - 1] and not v[k + 1]:
            f0[k] = 0.0
    # 30 ms rms on the full signal
    w = int(0.03 * sr)
    cs = np.concatenate([[0.0], np.cumsum(y.astype(np.float64) ** 2)])
    centers = (np.arange(nfr) * HOP * sr).astype(int)
    a = np.clip(centers - w // 2, 0, len(y))
    b = np.clip(centers + w // 2, 0, len(y))
    rms = np.sqrt((cs[b] - cs[a]) / np.maximum(b - a, 1))
    return dict(t=np.arange(nfr) * HOP, f0=f0, voiced=f0 > 0, rms=rms, hop=HOP)


def pitch_marks(y, sr, an):
    """Epochs (sample indices of the strongest peak of every pitch period) of all voiced stretches, ascending."""
    f0, voiced = an["f0"], an["voiced"]
    n = len(f0)
    marks = []
    k = 0
    while k < n:
        if not voiced[k]:
            k += 1
            continue
        k0 = k
        while k < n and voiced[k]:
            k += 1
        k1 = k                                                          # voiced frames k0 .. k1-1
        a, b = int(k0 * HOP * sr), min(len(y) - 1, int(k1 * HOP * sr))
        if b - a < 3 * sr / 600:
            continue
        seg = y[a:b + 1]
        sign = 1.0 if seg.max() >= -seg.min() else -1.0
        ys = sign * y

        def period(pos):
            i = min(n - 1, max(0, int(pos / sr / HOP)))
            f = f0[i] if f0[i] > 0 else f0[k0:k1][f0[k0:k1] > 0].mean()
            return sr / f

        # seed at the strongest peak of the stretch, then walk both ways
        j0 = a + int(np.argmax(ys[a:b + 1]))
        fw = [j0]
        while True:
            T = period(fw[-1])
            c = fw[-1] + T
            if c >= b - 0.3 * T:
                break
            lo, hi = int(c - 0.28 * T), int(c + 0.28 * T) + 1
            nxt = lo + int(np.argmax(ys[lo:hi]))
            if nxt <= fw[-1] + 0.5 * T:
                nxt = int(c)
            fw.append(nxt)
        bw = []
        cur = j0
        while True:
            T = period(cur)
            c = cur - T
            if c <= a + 0.3 * T:
                break
            lo, hi = int(c - 0.28 * T), int(c + 0.28 * T) + 1
            nxt = lo + int(np.argmax(ys[max(lo, 0):hi])) if lo >= 0 else int(c)
            if nxt >= cur - 0.5 * T:
                nxt = int(c)
            bw.append(nxt)
            cur = nxt
        marks += sorted(bw) + fw
    return np.array(sorted(set(marks)), dtype=np.int64)


# ================================================================================================ synthesis
class Plan:
    """Where every piece of the output comes from: `tmap` is a list of (out_sample, in_sample) control points (piecewise linear,
    both ascending) and `pitch(out_sample)` the wanted f0 in Hz for the voiced parts."""

    def __init__(self, tmap, pitch):
        self.out = np.array([p[0] for p in tmap], dtype=np.float64)
        self.inp = np.array([p[1] for p in tmap], dtype=np.float64)
        self.pitch = pitch

    def t_in(self, t_out):
        return float(np.interp(t_out, self.out, self.inp))

    @property
    def length(self):
        return int(self.out[-1])


def synth(y, sr, an, marks, plan, unvoiced_hop=0.006, jitter=0.004, seed=1, shimmer=0.0):
    """TD-PSOLA of `y` according to `plan`; returns the output signal (float64).  A voiced grain is interpolated between the two
    pitch periods that surround the input position (a held vowel changes smoothly instead of stepping from period to period), and
    the output periods get a tiny random jitter like a real voice (no buzzing comb of identical periods), and with `shimmer` a tiny random
    change of loudness from period to period."""
    rng = np.random.default_rng(seed)
    n_out = plan.length
    out = np.zeros(n_out + 4 * sr // 100)
    vox = an["voiced"]
    ml = np.asarray(marks).tolist()

    def is_voiced(pos):
        i = int(pos / sr / HOP)
        return 0 <= i < len(vox) and bool(vox[i])

    def period_at(k):
        if len(ml) < 2:
            return sr / 150.0
        a = ml[k] - ml[k - 1] if k > 0 else ml[k + 1] - ml[k]
        b = ml[k + 1] - ml[k] if k + 1 < len(ml) else a
        return min(max(0.5 * (a + b), sr / 700.0), sr / 60.0)

    def grain(c, half):
        a, b = c - half, c + half + 1
        seg = np.zeros(b - a)
        sa, sb = max(a, 0), min(b, len(y))
        if sb > sa:
            seg[sa - a:sb - a] = y[sa:sb]
        return seg

    t = 0.0
    uh = unvoiced_hop * sr
    while t < n_out:
        ti = plan.t_in(t)
        if is_voiced(ti) and len(ml):
            k1 = bisect.bisect_left(ml, ti)
            k0 = k1 - 1
            if k1 >= len(ml):
                k1 = k0 = len(ml) - 1
            elif k0 < 0:
                k0 = k1
            T0, T1 = period_at(k0), period_at(k1)
            if k1 != k0 and 0 < ml[k1] - ml[k0] < 1.8 * max(T0, T1):
                al = (ti - ml[k0]) / (ml[k1] - ml[k0])
            else:
                al = 0.0 if abs(ti - ml[k0]) <= abs(ti - ml[k1]) else 1.0
                k0 = k1 = (k0 if al == 0.0 else k1)
                al = 0.0
            Ta = (1 - al) * T0 + al * T1
            half = int(round(max(T0, T1)))
            seg = grain(ml[k0], half)
            if al > 0:
                seg = (1 - al) * seg + al * grain(ml[k1], half)
            f = float(plan.pitch(t))
            if f <= 0:
                f = sr / Ta
            Pn = sr / f * (1.0 + jitter * (rng.random() * 2 - 1))
            seg = seg * np.hanning(len(seg)) * (Pn / Ta) * (1.0 + shimmer * (rng.random() * 2 - 1))
            o = int(round(t)) - half
            i0, i1 = max(o, 0), min(o + len(seg), len(out))
            if i1 > i0:
                out[i0:i1] += seg[i0 - o:i1 - o]
            t += Pn
        else:
            half = int(uh)
            seg = grain(int(round(ti)), half)[:2 * half] * np.hanning(2 * half)
            o = int(round(t)) - half
            i0, i1 = max(o, 0), min(o + len(seg), len(out))
            if i1 > i0:
                out[i0:i1] += seg[i0 - o:i1 - o]
            t += uh
    return out[:n_out]


# ================================================================================================ pitch curves
def midi_hz(m):
    return 440.0 * 2.0 ** ((m - 69.0) / 12.0)


def note_curve(notes, sr, glide=0.06, vib_rate=5.4, vib_cents=14.0, vib_delay=0.28):
    """notes: [(start_out_sample, end_out_sample, midi)] ascending, may leave holes -> callable(out_sample) -> Hz.
    A short glide leads into every note (it starts `glide` before the note and ends at it) and a note that lasts longer than
    `vib_delay` gets a light vibrato after that."""
    ns = sorted(notes)
    starts = [s for s, _, _ in ns]

    def f(t):
        i = bisect.bisect_right(starts, t) - 1
        if i < 0:
            i = 0
        s, e, m = ns[i]
        cents = 0.0
        g = glide * sr
        if i > 0 and t - s < g * 0.5 and ns[i - 1][2] != m and s - ns[i - 1][1] < 0.12 * sr:
            u = 0.5 + (t - s) / g                                       # 0 .. 1 over the glide that straddles the note start
            u = min(1.0, max(0.0, u))
            u = u * u * (3 - 2 * u)
            cents += (1.0 - u) * 100.0 * (ns[i - 1][2] - m)
        elif i + 1 < len(ns) and e - t < g * 0.5 and ns[i + 1][2] != m and ns[i + 1][0] - e < 0.12 * sr:
            u = 0.5 - (e - t) / g
            u = min(1.0, max(0.0, u))
            u = u * u * (3 - 2 * u)
            cents += u * 100.0 * (ns[i + 1][2] - m)
        td = (t - s) / sr
        if td > vib_delay:
            amp = vib_cents * min(1.0, (td - vib_delay) / 0.25)
            cents += amp * math.sin(2 * math.pi * vib_rate * (td - vib_delay))
        return midi_hz(m + cents / 100.0)

    return f


def _smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def human_params(seed=1, vib=1.0, spread=1.0):
    """How alive one singer is.  Everything that is random comes from the seed (a render can be repeated, and two singers of a choir are never
    quite the same).  vib scales the vibrato, spread the small mistakes (a note a little flat or sharp, a slow drift, a scoop into a phrase)."""
    return dict(rng=np.random.default_rng(seed), vib_cents=22.0 * vib, vib_rate=5.5, note_cents=5.0 * spread, drift_cents=7.0 * spread,
                scoop=1.0 * spread, sag=1.0 * spread, jitter=0.008, shimmer=0.03, glide=0.07, tremolo=0.05 * vib)


def note_curve_h(notes, sr, hp):
    """Like note_curve, but a person sings it: notes: [(start_out_sample, end_out_sample, midi)] -> callable(out_sample) -> Hz, with
      - a note that is never quite in tune (a few cents flat or sharp), and a slow drift of the whole line,
      - a scoop from below into the first note of a phrase and a small dip on a repeated note (the second 'twinkle' is a new breath),
      - a glide into the next note that is a little longer for a leap,
      - vibrato on the longer notes (late, slow to grow, with its own speed and depth for every note), nothing on the short ones,
      - a note that ends a phrase sags a little at its end.
    The callable has .info (one dict per note, in order of the notes: rate, depth, delay, phase) for the tremolo that goes with the vibrato."""
    rng = hp["rng"]
    ns = sorted(notes)
    starts = [s for s, _, _ in ns]
    info = []
    for i, (s, e, m) in enumerate(ns):
        d = (e - s) / sr
        gap_b = (s - ns[i - 1][1]) / sr if i > 0 else 9.0
        gap_a = (ns[i + 1][0] - e) / sr if i + 1 < len(ns) else 9.0
        prev_m = ns[i - 1][2] if i > 0 else None
        scoop = 0.0
        if gap_b > 0.14:
            scoop = float(rng.uniform(35.0, 70.0)) * hp["scoop"]
        elif prev_m == m and gap_b < 0.12:
            scoop = float(rng.uniform(6.0, 14.0)) * hp["scoop"]
        info.append(dict(
            off=float(np.clip(rng.normal(0.0, hp["note_cents"]), -2.2 * hp["note_cents"], 2.2 * hp["note_cents"])),
            depth=hp["vib_cents"] * float(np.clip((d - 0.34) / 0.55, 0.0, 1.0)) * float(rng.uniform(0.8, 1.2)),
            rate=hp["vib_rate"] * float(1.0 + 0.07 * rng.standard_normal()),
            delay=float(rng.uniform(0.17, 0.30)), phase=float(rng.uniform(0.0, 2.0 * math.pi)),
            scoop=scoop, sag=(float(rng.uniform(8.0, 22.0)) * hp["sag"] if (gap_a > 0.2 and d >= 0.6) else 0.0), dur=d))
    t0 = ns[0][0] / sr
    span = (max(e for _, e, _ in ns) - ns[0][0]) / sr + 2.0
    k = int(span * 20) + 24
    z = rng.standard_normal(k)
    w = 16                                                              # 0.8 s of the 20 Hz noise
    sm = np.convolve(np.pad(z, (w, w), mode="edge"), np.ones(w) / w, mode="valid")[:k]
    sm = (sm - sm.mean()) / (sm.std() + 1e-9) * hp["drift_cents"]
    grid = np.arange(k) / 20.0

    def f(t):
        i = max(0, bisect.bisect_right(starts, t) - 1)
        s, e, m = ns[i]
        nf = info[i]
        cents = nf["off"] + float(np.interp(t / sr - t0, grid, sm))
        td = (t - s) / sr
        if i > 0 and ns[i - 1][2] != m and (s - ns[i - 1][1]) < 0.12 * sr and td < 0.5 * hp["glide"] * (1.0 + 0.12 * min(abs(m - ns[i - 1][2]), 8)):
            g = hp["glide"] * (1.0 + 0.12 * min(abs(m - ns[i - 1][2]), 8))
            u = _smooth01(0.5 + td / g)                                 # 0 .. 1 over the glide that straddles the note start
            cents += (1.0 - u) * 100.0 * (ns[i - 1][2] - m)
        elif i + 1 < len(ns) and ns[i + 1][2] != m and (ns[i + 1][0] - e) < 0.12 * sr:
            g = hp["glide"] * (1.0 + 0.12 * min(abs(m - ns[i + 1][2]), 8))
            if (e - t) / sr < 0.5 * g:
                u = _smooth01(0.5 - (e - t) / sr / g)
                cents += u * 100.0 * (ns[i + 1][2] - m)
        if nf["scoop"] and td < 0.14:
            cents -= nf["scoop"] * (1.0 - _smooth01((td + 0.03) / 0.17))
        if nf["sag"]:
            cents -= nf["sag"] * _smooth01(((e - t) / sr - 0.25) / -0.25)
        if nf["depth"] > 0.0 and td > nf["delay"]:
            amp = nf["depth"] * min(1.0, (td - nf["delay"]) / 0.35)
            cents += amp * math.sin(2.0 * math.pi * nf["rate"] * (td - nf["delay"]) + nf["phase"] + 0.35 * math.sin(2.0 * math.pi * 0.8 * td))
        return midi_hz(m + cents / 100.0)

    f.info = info
    return f
