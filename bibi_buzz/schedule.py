"""Voice-first timeline.

Every spoken line (Cue) is placed on the music's beat grid. Its slot is as long as the real text-to-speech
clip plus a short breath, rounded UP to whole beats - so the voice is never sped up, it always starts exactly
on a beat, and the music (which runs on the same grid) stays perfectly in sync with it.
Segments end on bar lines, so the pictures change with the music.
"""
import math

SR = 44100


class Cue:
    """One spoken line (or a silent pause when text == '')."""

    def __init__(self, text, tag="say", i=0, cap=None, gap=0.30, min_beats=2, pause=0):
        self.text, self.tag, self.i, self.cap = text, tag, i, cap
        self.gap, self.min_beats, self.pause = gap, min_beats, pause
        self.t = self.dur = self.slot = 0.0

    @property
    def shown(self):
        return self.cap if self.cap is not None else self.text


class Seg:
    def __init__(self, kind, data, cues, chapter=None, round_beats=4, codes=None):
        self.kind, self.data, self.cues, self.chapter, self.round_beats = kind, data, cues, chapter, round_beats
        self.codes = list(codes or [])     # emoji sprites this segment needs
        self.t0 = self.t1 = self.v0 = 0.0  # v0: where its pictures start (0 for the first segment)


class Lesson:
    def __init__(self, id, fmt, title, topic, tags, theme, bpm, seed, segs, items=None, blurb=""):
        self.id, self.fmt, self.title, self.topic, self.tags = id, fmt, title, topic, tags
        self.theme, self.bpm, self.seed, self.segs = theme, bpm, seed, segs
        self.items = items or []          # words taught (for the YouTube description)
        self.blurb = blurb
        self.beat = 60.0 / bpm
        self.lead_beats = 4 if fmt == "long" else 1
        self.grid0 = self.lead_beats * self.beat   # bar lines of the music start here
        self.duration = 0.0

    def texts(self):
        return [c.text for s in self.segs for c in s.cues if c.text]

    def cues(self):
        return [c for s in self.segs for c in s.cues]

    def codes(self):
        """Every emoji sprite the lesson needs (so they can be downloaded before rendering)."""
        out = set()
        for s in self.segs:
            out.update(s.codes)
        return sorted(out)


def build(lesson, clips):
    """Fills in Cue.t / dur / slot, Seg.t0 / t1 and Lesson.duration from the real clip lengths."""
    beat = lesson.beat
    t = lesson.lead_beats * beat
    for k, seg in enumerate(lesson.segs):
        seg.t0 = t
        seg.v0 = 0.0 if k == 0 else t
        for cue in seg.cues:
            cue.dur = len(clips[cue.text]) / SR if cue.text else 0.0
            beats = max(cue.min_beats, int(math.ceil((cue.dur + cue.gap) / beat - 1e-9))) + cue.pause
            cue.t, cue.slot = t, beats * beat
            t += cue.slot
        grid = seg.round_beats * beat
        n = max(1, int(math.ceil((t - seg.t0) / grid - 1e-9)))
        t = seg.t0 + n * grid
        seg.t1 = t
    # one closing bar lets the last chord ring out
    lesson.duration = t + (4 * beat if lesson.fmt == "long" else 2 * beat)
    return lesson


def voice_intervals(lesson):
    return [(c.t, c.t + c.dur) for c in lesson.cues() if c.text]


SFX_TAGS = {"reveal": "pop", "count": "count", "item": "pop", "letter": "pop", "answer": "sparkle",
            "celebrate": "sparkle", "total": "sparkle", "result": "sparkle", "a": "pop", "b": "pop", "bubble": "pop"}


def cta_times(lesson):
    """When (seconds after the 'Like and subscribe' card starts) the pointer presses Like and then Subscribe: on beats of the music.
    A Short has a much shorter line ("Like and subscribe for more!"), so its clicks come earlier."""
    if lesson.fmt == "short":
        return 1.0 * lesson.beat, 2.4 * lesson.beat
    return 1.5 * lesson.beat, 3.0 * lesson.beat


def sfx_events(lesson):
    """[(time, kind, arg)] synchronised with the pictures: sounds sit exactly on the cue (= beat) times."""
    ev = []
    for seg in lesson.segs:
        if seg.kind == "logo":
            ev += [(0.0, "sparkle", 0), (lesson.beat * 2, "pop", 0)]
        if seg.kind == "outro":
            ev.append((seg.t0, "sparkle", 0))
        if seg.kind == "cta":
            t_like, t_sub = cta_times(lesson)
            ev += [(seg.t0, "pop", 0), (seg.t0 + 0.25, "pop", 0), (seg.t0 + t_like, "ding", 3), (seg.t0 + t_like, "pop", 0),
                   (seg.t0 + t_sub, "ding", 5), (seg.t0 + t_sub, "pop", 0), (seg.t0 + t_sub + 0.1, "sparkle", 0)]
        for c in seg.cues:
            kind = SFX_TAGS.get(c.tag)
            if kind == "count":
                ev += [(c.t, "pop", 0), (c.t, "ding", c.i)]
            elif kind:
                ev.append((c.t, kind, c.i))
    return sorted(ev)


def chapters(lesson, min_len=10.0):
    """YouTube chapters (every chapter >= 10 s, at least 3, first one at 0:00)."""
    marks = [(0.0, "Welcome to Bibi Buzz TV")]
    for s in lesson.segs:
        if s.chapter:
            marks.append((s.t0, s.chapter))
    out = []
    for t, label in marks:
        if out and t - out[-1][0] < min_len:
            continue
        out.append((t, label))
    if len(out) > 1 and lesson.duration - out[-1][0] < min_len:
        out.pop()
    return out if len(out) >= 3 else []


def fmt_time(t):
    t = int(t)
    return "%d:%02d" % (t // 60, t % 60)
