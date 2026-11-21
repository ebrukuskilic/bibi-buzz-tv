"""Makes text-to-speech words SING: every syllable of a spoken word is moved onto its note (see psola.py).

  ch  = Chunk(y, sr, n_syllables)      # a spoken word (or two) and where its syllables are
  out = sing_line([ch, ...], notes)    # the words of one sung line, one note per syllable
"""
import numpy as np

from . import psola as P

LEAD_MAX = 0.20          # the longest a consonant before a vowel may last (seconds, natural speed)
CODA_MAX = 0.16
GAP = 0.035              # silence between the end of a syllable and the next one when notes touch
LEVEL = 0.16             # the loudest 30 ms of every syllable gets this level before the line is mixed


def _env_db(an):
    return 20 * np.log10(an["rms"] + 1e-5)


def active_range(an):
    """First and last frame of the clip that are louder than 30 dB below its loudest frame."""
    db = _env_db(an)
    idx = np.where(db > db.max() - 30.0)[0]
    if not len(idx):
        return 0, len(db) - 1
    return int(idx[0]), int(idx[-1])


def split_syllables(an, a, b, n, min_gap=0.075):
    """Cuts the frames a..b into `n` syllables at the deepest dips of the loudness: [(frame_a, frame_b), ...].
    Where the voice has fewer dips than syllables, the longest syllable is cut in the middle of its voiced part."""
    if n <= 1 or b - a < 4:
        return [(a, b)]
    db = _env_db(an)
    sm = np.convolve(db, np.ones(5) / 5.0, mode="same")
    vox = an["voiced"]
    mind = max(2, int(min_gap / P.HOP))
    cands = []
    for k in range(a + mind, b - mind):
        if sm[k] <= sm[k - 1] and sm[k] < sm[k + 1]:
            lp = sm[max(a, k - 3 * mind):k].max()
            rp = sm[k + 1:min(b, k + 3 * mind) + 1].max()
            depth = min(lp, rp) - sm[k]
            if depth > 1.5:
                cands.append((depth, k))
    cands.sort(reverse=True)
    cuts = []
    for depth, k in cands:
        if all(abs(k - c) >= mind for c in cuts):
            cuts.append(k)
        if len(cuts) == n - 1:
            break
    cuts.sort()
    while len(cuts) < n - 1:                                            # not enough dips: halve the longest piece
        edges = [a] + cuts + [b]
        j = max(range(len(edges) - 1), key=lambda i: edges[i + 1] - edges[i])
        lo, hi = edges[j], edges[j + 1]
        vv = [k for k in range(lo, hi) if vox[k]]
        mid = int(np.median(vv)) if len(vv) > 4 else (lo + hi) // 2
        mid = min(max(mid, lo + 1), hi - 1)
        cuts.append(mid)
        cuts.sort()
    edges = [a] + cuts + [b]
    return [(edges[i], edges[i + 1]) for i in range(n)]


def nucleus(an, fa, fb):
    """(first, last) frame of the held part of a syllable: its loud voiced frames; None when nothing is voiced."""
    vox, rms = an["voiced"], an["rms"]
    seg = np.arange(fa, fb + 1)
    seg = seg[(seg >= 0) & (seg < len(rms))]
    if not len(seg):
        return None
    mx = rms[seg].max()
    good = [int(k) for k in seg if vox[k] and rms[k] >= 0.30 * mx]
    if not good:
        return None
    runs, start, last = [], good[0], good[0]
    for k in good[1:]:
        if k - last > 6:                                                # holes up to 30 ms are bridged
            runs.append((start, last))
            start = k
        last = k
    runs.append((start, last))
    return max(runs, key=lambda r: (r[1] - r[0]))


class Chunk:
    """A spoken word (or a short phrase) with `n` syllables: its analysis, pitch marks and the frames of every syllable."""

    def __init__(self, y, sr, n):
        self.y, self.sr, self.n = y, sr, n
        self.an = P.analyse(y, sr)
        self.marks = P.pitch_marks(y, sr, self.an)
        a, b = active_range(self.an)
        self.frames = split_syllables(self.an, a, b, n)

    def onset_len(self, i):
        """Samples of the consonants before the vowel of syllable i (natural length, at most LEAD_MAX)."""
        fa, fb = self.frames[i]
        nu = nucleus(self.an, fa, fb)
        sa = int(fa * P.HOP * self.sr)
        va = int(nu[0] * P.HOP * self.sr) if nu else sa + (int(fb * P.HOP * self.sr) - sa) // 5
        return min(va - sa, int(LEAD_MAX * self.sr))


def sing_syllable(ch, i, start, end, pitch, limit_end=None):
    """Syllable i of chunk `ch` sung from sample `start` to `end` (the clock of `pitch`).  The consonants before the vowel come BEFORE
    `start`, so the vowel is on the beat.  Returns (first_output_sample, signal)."""
    y, sr, an, marks = ch.y, ch.sr, ch.an, ch.marks
    H = P.HOP
    fa, fb = ch.frames[i]
    sa, sb = int(fa * H * sr), int(fb * H * sr)
    nu = nucleus(an, fa, fb)
    if nu is None:                                                     # nothing to hold (a whispered or very short sound)
        va, vb = sa + (sb - sa) // 5, sb - (sb - sa) // 5
    else:
        va, vb = int(nu[0] * H * sr), int((nu[1] + 1) * H * sr)
    vb = max(vb, va + int(0.04 * sr))
    onset_in = max(1, va - sa)
    coda_in = max(0, sb - vb)
    Lo = min(onset_in, int(LEAD_MAX * sr))
    Lc = min(coda_in, int(CODA_MAX * sr))
    gap = int(GAP * sr)
    limit = end - gap
    if limit_end is not None:
        limit = min(limit, limit_end)
    Dn = max(int(0.06 * sr), limit - start - Lc)
    tmap = [(0, sa), (Lo, va)]
    L = vb - va
    head = min(int(0.03 * sr), int(0.15 * L))
    tail = min(int(0.20 * sr), int(0.40 * L))
    if Dn > head + tail + int(0.03 * sr) and L > head + tail + 8:
        tmap.append((Lo + head, va + head))                            # the steady middle of the vowel is stretched, its start and its end keep their speed
        tmap.append((Lo + Dn - tail, vb - tail))
    tmap.append((Lo + Dn, vb))
    tmap.append((Lo + Dn + Lc, vb + Lc if coda_in else vb + 1))
    fixed = [tmap[0]]
    for t_out, t_in in tmap[1:]:
        fixed.append((max(t_out, fixed[-1][0] + 1), max(t_in, fixed[-1][1] + 1)))
    origin = start - Lo
    plan = P.Plan(fixed, lambda t, origin=origin: pitch(t + origin))
    return origin, P.synth(y, sr, an, marks, plan, seed=1 + i)


def sing_line(chunks, notes, accents=None, sr=44100):
    """chunks: [Chunk]; notes: [(start_s, end_s, midi)] one per syllable of all the chunks in order, on the line's own clock (seconds).
    Returns (signal, t0): `signal` starts at t0 seconds of that clock (a little before the first note: its consonants)."""
    curve = P.note_curve([(int(s * sr), int(e * sr), m) for s, e, m in notes], sr)
    flat = [(c, i) for c in chunks for i in range(c.n)]
    assert len(flat) == len(notes), "%d syllables but %d notes" % (len(flat), len(notes))
    parts = []
    for k, ((ch, i), (s, e, m)) in enumerate(zip(flat, notes)):
        limit_end = None
        if k + 1 < len(flat):
            nch, ni = flat[k + 1]
            limit_end = int(notes[k + 1][0] * sr) - nch.onset_len(ni) - int(0.01 * sr)
        o, sig = sing_syllable(ch, i, int(s * sr), int(e * sr), curve, limit_end)
        w = int(0.03 * sr)
        if len(sig) > w:                                               # the same level for every syllable
            cs = np.concatenate([[0.0], np.cumsum(sig ** 2)])
            mxr = float(np.sqrt(np.max((cs[w:] - cs[:-w]) / w)))
            if mxr > 1e-6:
                sig = sig * (LEVEL / mxr)
        f = int(0.006 * sr)
        if len(sig) > 4 * f:
            sig[:f] *= np.linspace(0, 1, f)
            sig[-3 * f:] *= np.linspace(1, 0, 3 * f)
        parts.append((o, sig * (1.0 if not accents else accents[k])))
    t_first = min(o for o, _ in parts)
    t_last = max(o + len(s) for o, s in parts)
    out = np.zeros(t_last - t_first + 1)
    for o, s in parts:
        out[o - t_first:o - t_first + len(s)] += s
    return out, t_first / sr
