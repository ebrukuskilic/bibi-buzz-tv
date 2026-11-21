"""Story engine for the Bibi fairy-tale videos.

A Tale is a list of Scenes; a Scene is a backdrop plus actors / props and a list of Beats. A beat is one narrated
sentence (or one character's line, or a silent pause) plus "acts" (walk, pose, camera, effects ...) that happen while it
plays. The voice decides how long a beat lasts, so picture and sound always stay in sync (nothing is sped up).
After compile() every actor has a timeline and frame(t) is a pure function of time -> frames can be drawn in parallel.
"""
import bisect
import math
import os
import subprocess
import time
from multiprocessing import Pool

import numpy as np
from PIL import Image

from . import draw as D
from . import storyart as A
from . import storyart2 as B
from . import storyaudio as SA
from . import storyprops as PR
from . import vibe as VB
from . import voice as VO
from .draw import clamp, lerp, ease_out_back
from .storyview import View

FPS = 24
SR = VO.SR
XFADE = 0.55
HEAD = {"pig": 236, "wolf": 292, "bear": 254, "hare": 294, "tortoise": 118, "girl": 238, "ginger": 232, "goat": 290, "troll": 300,
        "bibi": 150, "pip": 120, "mo": 130, "lila": 130, "mirror": 400, "hen": 228, "chick": 118}
HEADW = {"pig": 62, "wolf": 66, "bear": 72, "hare": 56, "tortoise": 112, "girl": 60, "ginger": 58, "goat": 64, "troll": 80,
         "bibi": 70, "pip": 60, "mo": 60, "lila": 60, "mirror": 114, "hen": 52, "chick": 50}
FAMILY = ("bibi", "pip", "mo", "lila")


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def dscale(y):
    return 0.80 + 0.30 * clamp((y - 480.0) / 200.0)


# ================================================================================================ definitions
class ActorDef:
    def __init__(self, id, kind, x, y, k, face, show, style):
        self.zy = style.pop("zy", None)            # fixed depth-sorting value (e.g. 900 = always in front)
        self.flat = style.pop("flat", False)       # no depth scaling (e.g. standing on a roof)
        self.id, self.kind, self.x, self.y, self.k, self.face, self.show, self.style = id, kind, x, y, k, face, show, style
        self.seed = (sum(ord(ch) for ch in id) % 10) / 3.0


class ActorTL:
    def __init__(self, d):
        self.d = d
        self.segs = []                      # (t0, t1, x0, y0, x1, y1, pose, kind, cum0)
        self.poses = [(-1.0, "idle")]
        self.faces = [(-1.0, d.face)]
        self.vis = [(-1.0, 1 if d.show else 0)]
        self.scales = []                    # (t0, t1, k0, k1)
        self.tilts = []                     # (t0, t1, d0, d1): extra lean in degrees (head to the right, like Pose.lean): falling over
        self.hops = []
        self.holds = [(-1.0, d.style.get("hold"))]
        self.free_at = 0.0

    def end_pos(self):
        if self.segs:
            s = self.segs[-1]
            return s[4], s[5]
        return self.d.x, self.d.y

    def end_cum(self):
        if self.segs:
            s = self.segs[-1]
            return s[8] + math.hypot(s[4] - s[2], s[5] - s[3])
        return 0.0

    def state(self, t):
        x, y, cum = self.d.x, self.d.y, 0.0
        moving, pose, speed = False, None, 0.0
        for (t0, t1, x0, y0, x1, y1, pz, kind, c0) in self.segs:
            if t < t0:
                break
            if t >= t1:
                x, y, cum = x1, y1, c0 + math.hypot(x1 - x0, y1 - y0)
                continue
            u = (t - t0) / (t1 - t0)
            e = ease(u) if kind == "move" else (u if kind == "walk" else u)
            if kind == "walk":
                e = u * 0.86 + 0.14 * ease(u)
            x, y = lerp(x0, x1, e), lerp(y0, y1, e)
            cum = c0 + math.hypot(x - x0, y - y0)
            if kind == "walk":
                moving, pose = True, pz
                speed = math.hypot(x1 - x0, y1 - y0) / (t1 - t0)
            break
        return x, y, moving, pose, speed, cum

    def pose_name(self, t):
        i = bisect.bisect_right([p[0] for p in self.poses], t) - 1
        return self.poses[max(i, 0)][1]

    def prev_pose(self, t):
        """(name of the pose before the current one, time the current one began) - for smooth sit / stand changes."""
        i = bisect.bisect_right([p[0] for p in self.poses], t) - 1
        if i <= 0:
            return None, -1.0
        return self.poses[i - 1][1], self.poses[i][0]

    def walk_end(self, t):
        return max([sg[1] for sg in self.segs if sg[1] <= t and sg[7] == "walk"] or [-1.0])

    def face_at(self, t):
        i = bisect.bisect_right([p[0] for p in self.faces], t) - 1
        return self.faces[max(i, 0)][1]

    def vis_at(self, t):
        """Returns (visible, pop 0..1) with a short pop animation after each show / before each hide."""
        i = bisect.bisect_right([p[0] for p in self.vis], t) - 1
        t0, v = self.vis[max(i, 0)]
        if v:
            return True, (ease_out_back(clamp((t - t0) / 0.32)) if t0 >= 0 else 1.0)
        if t0 >= 0 and t - t0 < 0.2:
            return True, 1 - ease(clamp((t - t0) / 0.2))
        return False, 0.0

    def scale_at(self, t):
        k = 1.0
        for (t0, t1, k0, k1) in self.scales:
            if t < t0:
                break
            k = k1 if t >= t1 else lerp(k0, k1, ease((t - t0) / (t1 - t0)))
            if t < t1:
                break
        return k

    def tilt_at(self, t):
        d = 0.0
        for (t0, t1, d0, d1) in self.tilts:
            if t < t0:
                break
            d = d1 if t >= t1 else lerp(d0, d1, ease((t - t0) / (t1 - t0)))
            if t < t1:
                break
        return d

    def hold_at(self, t):
        i = bisect.bisect_right([p[0] for p in self.holds], t) - 1
        return self.holds[max(i, 0)][1]

    def hop_at(self, t):
        for h in self.hops:
            if h <= t < h + 0.5:
                return math.sin((t - h) / 0.5 * math.pi) * 46
        return 0.0


class PropDef:
    def __init__(self, id, kind, x, y, k, show, st):
        self.id, self.kind, self.x, self.y, self.k, self.show, self.st = id, kind, x, y, k, show, st


class PropTL:
    def __init__(self, d):
        self.d = d
        self.vars = {}                      # name -> [(t0, t1, v0, v1)]
        self.vis = [(-1.0, 1 if d.show else 0)]

    def value(self, name, t):
        v = self.d.st.get(name, 0.0)
        for (t0, t1, v0, v1) in self.vars.get(name, ()):
            if t < t0:
                break
            v = v1 if t >= t1 else lerp(v0, v1, ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0)
            if t < t1:
                break
        return v

    def now(self, name, t):
        return self.value(name, t)

    def vis_at(self, t):
        i = bisect.bisect_right([p[0] for p in self.vis], t) - 1
        t0, v = self.vis[max(i, 0)]
        if v:
            return True, (ease_out_back(clamp((t - t0) / 0.35)) if t0 >= 0 else 1.0)
        return False, 0.0


class Beat:
    def __init__(self, kind, who, text, acts, lead, tail, dur, voice=None):
        self.kind, self.who, self.text, self.acts = kind, who, text, acts
        self.lead, self.tail, self.dur = lead, tail, dur
        self.voice = voice                  # an entry of Tale.voices other than the speaker's own (a wolf talking like Grandma)
        self.t0 = self.t1 = self.v0 = self.v1 = 0.0
        self.key = None


def _split(act):
    act = tuple(act)
    if act and isinstance(act[-1], dict):
        return act[0], act[1:-1], act[-1]
    return act[0], act[1:], {}


AUTO_SFX = {"wind": "wind", "burst": "boom", "splash": "splash", "confetti": "cheer", "sparkle": "sparkle",
            "hearts": "ding", "dust": "thud", "mark": "pop", "dizzy": "dizzy", "zzz": "snore"}


class Scene:
    def __init__(self, tale, name, bg, world=1280, mood="happy", title=None, drift=0.03, clouds=True):
        self.tale, self.name, self.bg, self.world, self.mood = tale, name, bg, world, mood
        self.title = tale.T(title) if title else title                   # the chapter name, in the tale's language
        self.drift, self.clouds = drift, clouds
        self.actors, self.props, self.beats = {}, {}, []
        self.cams = []
        self.follows = []
        self.fxs = []
        self.sfx = []
        self.speech = []
        self.dur = 0.0
        self.t_start = 0.0

    # ---- authoring
    def actor(self, id, atype, x, y=590, k=1.0, face=1, show=True, **style):
        self.actors[id] = ActorDef(id, atype, x, y, k, face, show, style)
        return self

    def prop(self, id, ptype, x, y=600, k=1.0, show=True, **st):
        self.props[id] = PropDef(id, ptype, x, y, k, show, st)
        return self

    def nar(self, text, *acts, lead=0.25, tail=0.45, dur=0.0):
        self.beats.append(Beat("nar", None, self.tale.T(text), acts, lead, tail, dur))
        return self

    def say(self, who, text, *acts, lead=0.2, tail=0.4, dur=0.0, voice=None):
        self.beats.append(Beat("say", who, self.tale.T(text), acts, lead, tail, dur, voice))
        return self

    def wait(self, dur, *acts):
        self.beats.append(Beat("wait", None, "", acts, 0.0, 0.0, dur))
        return self

    # ---- compile
    def compile(self, t_start, clips):
        self.t_start = t_start
        atl = {i: ActorTL(d) for i, d in self.actors.items()}
        ptl = {i: PropTL(d) for i, d in self.props.items()}
        self.atl, self.ptl = atl, ptl
        self.cams, self.fxs, self.sfx, self.speech, self.follows = [], [], [], [], []
        cursor = 0.0
        for b in self.beats:
            b.t0 = cursor
            if b.text:
                clip = clips[b.key]
                vd = len(clip) / SR
                b.v0, b.v1 = b.t0 + b.lead, b.t0 + b.lead + vd
                base_end = b.v1 + b.tail
                self.speech.append((b.v0, b.v1, b.who, b.key, b.text))
            else:
                b.v0 = b.v1 = b.t0
                base_end = b.t0 + b.dur
            end = base_end
            for act in b.acts:
                e = self._act(act, b, base_end)
                if e:
                    end = max(end, e + 0.12)
            b.t1 = end
            cursor = end
        for tl in list(atl.values()) + list(ptl.values()):                 # acts may be authored out of time order
            for attr in ("poses", "faces", "vis", "holds"):
                if hasattr(tl, attr):
                    getattr(tl, attr).sort(key=lambda it: it[0])
        self.dur = cursor + 0.05
        return self.dur

    def _act(self, act, b, base_end):
        verb, a, o = _split(act)
        at = o.get("at", 0.0)
        if isinstance(at, str):                                        # "60%" = 60 % of the way through the voice line ("60%+0.3" = and 0.3 s later)
            base0, base1 = (b.v0, b.v1) if b.text else (b.t0, base_end)
            pct, _, plus = at.partition("%")
            ta = base0 + float(pct) / 100.0 * (base1 - base0) + (float(plus) if plus else 0.0)
        else:
            ta = b.t0 + at if at >= 0 else base_end + at
        if verb in ("walk", "move"):
            tl = self.atl[a[0]]
            px, py = tl.end_pos()
            tx = a[1]
            ty = a[2] if len(a) > 2 else py
            dist = math.hypot(tx - px, ty - py)
            speed = o.get("speed", 150.0)
            start = max(ta, tl.free_at)
            if o.get("fit"):                                            # take exactly as long as the beat (speed follows)
                dur = max(0.3, base_end - start)
                speed = dist / dur
            else:
                dur = o.get("dur", max(0.2, dist / speed))
            pose = o.get("pose", "run" if speed >= 300 else "walk")
            tl.segs.append((start, start + dur, px, py, tx, ty, pose, verb, tl.end_cum()))
            tl.free_at = start + dur
            if abs(tx - px) > 2 and not o.get("keepface"):
                tl.faces.append((start, 1 if tx > px else -1))
            return start + dur
        if verb == "pose":
            self.atl[a[0]].poses.append((ta, a[1]))
        elif verb == "face":
            self.atl[a[0]].faces.append((ta, a[1]))
        elif verb == "hold":
            self.atl[a[0]].holds.append((ta, a[1]))
        elif verb == "show":
            tgt = self.atl.get(a[0]) or self.ptl[a[0]]
            tgt.vis.append((ta, 1))
            self.sfx.append((ta, "pop", 0.5))
        elif verb == "hide":
            tgt = self.atl.get(a[0]) or self.ptl[a[0]]
            tgt.vis.append((ta, 0))
        elif verb == "scale":
            tl = self.atl[a[0]]
            k0 = tl.scale_at(ta)
            dur = o.get("dur", a[2] if len(a) > 2 else 0.6)
            tl.scales.append((ta, ta + dur, k0, a[1]))
            return ta + dur
        elif verb == "tilt":                                            # ("tilt", who, degrees, {"at", "dur"}): fall over (+ = head to the right)
            tl = self.atl[a[0]]
            d0 = tl.tilt_at(ta)
            dur = o.get("dur", a[2] if len(a) > 2 else 0.5)
            tl.tilts.append((ta, ta + dur, d0, a[1]))
            return ta + dur
        elif verb == "hop":
            self.atl[a[0]].hops.append(ta)
            self.sfx.append((ta, "boing", 0.5))
        elif verb == "set":
            pid, name, val = a[0], a[1], a[2]
            dur = o.get("dur", a[3] if len(a) > 3 else 0.8)
            tl = self.ptl[pid]
            v0 = tl.value(name, ta)
            tl.vars.setdefault(name, []).append((ta, ta + dur, v0, val))
            if name == "collapse" and val > v0:
                self.sfx.append((ta, "collapse", 0.9))
            if name == "door" and val > v0:
                self.sfx.append((ta, "creak", 0.6))
            return ta + dur
        elif verb == "cam":
            dur = o.get("dur", a[3] if len(a) > 3 else 1.2)
            self.cams.append((ta, ta + dur, a[0], a[1], a[2]))
        elif verb == "follow":                                          # camera tracks an actor: ("follow", who, offset_x, zoom, {dur})
            dur = o.get("dur", 3600.0)
            self.follows.append((ta, ta + dur, a[0], a[1] if len(a) > 1 else 0.0, a[2] if len(a) > 2 else 1.0, o.get("cy", 360.0)))
        elif verb == "fx":
            kind, x, y = a[0], a[1], a[2]
            dur = o.get("dur", a[3] if len(a) > 3 and not isinstance(a[3], dict) else 2.0)
            kw = self.tale.fx_args(kind, {k: v for k, v in o.items() if k not in ("at", "dur")})
            self.fxs.append(dict(t0=ta, t1=ta + dur, kind=kind, x=x, y=y, kw=kw))
            sfx = o.get("sfx", AUTO_SFX.get(kind))
            if sfx and o.get("sfx", True) is not False:
                self.sfx.append((ta, sfx, 0.8))
        elif verb == "sfx":
            self.sfx.append((ta, a[0], o.get("gain", 0.8)))
        else:
            raise ValueError("unknown act %r" % (verb,))
        return None

    # ---- state at time
    def cam_at(self, ts):
        cx, cy, z = 640.0, 360.0, 1.0
        for (t0, t1, tx, ty, tz) in self.cams:
            if ts < t0:
                break
            if ts >= t1:
                cx, cy, z = tx, ty, tz
                continue
            e = ease((ts - t0) / (t1 - t0))
            cx, cy, z = lerp(cx, tx, e), lerp(cy, ty, e), lerp(z, tz, e)
            break
        for (t0, t1, who, ox, fz, fcy) in self.follows:
            if ts < t0:
                break
            ax = self.atl[who].state(min(ts, t1))[0]
            w = ease((ts - t0) / 0.6)
            cx, cy, z = lerp(cx, ax + ox, w), lerp(cy, fcy, w), lerp(z, fz, w)
        z = max(1.0, z + self.drift * ease(ts / max(self.dur, 1.0)))
        cx = clamp(cx, 640.0 / z, self.world - 640.0 / z)
        cy = clamp(cy, 360.0 / z, 720.0 - 360.0 / z)
        return cx, cy, z


# ================================================================================================ tale
class Tale:
    kind = "tale"
    fmt = "long"
    bpm = 0
    grid0 = 0.0
    beat = 1.0
    segs = ()
    items = ()

    def __init__(self, id, title, blurb, tags, voices, cover=None, lang="en"):
        self.id, self.title, self.blurb, self.tags, self.voices = id, title, blurb, list(tags), voices
        self.cover = cover
        self.lang = lang                    # "en" or "tr": the scripts are written in English, tales_tr.py has the Turkish lines
        self.scenes = []
        self.duration = 0.0

    # ---- language
    def T(self, text):
        """`text` (an English line of a script) in this tale's language. A line without a Turkish translation is an error,
        so a half translated video can never be rendered."""
        if self.lang == "en" or not text:
            return text
        from . import tales_tr
        return tales_tr.lookup(text)

    def fx_args(self, kind, kw):
        """Translates the words that a screen effect writes (title card, caption, 'The End' card, burst, mark)."""
        if self.lang == "en":
            return kw
        kw = dict(kw)
        if kind == "title":
            kw["lines"] = tuple(self.T(l) for l in kw.get("lines", ("THE STORY",)))
            kw["sub"] = self.T(kw.get("sub", "Story Time with Bibi Buzz TV"))
        elif kind == "the_end":
            kw["text"] = self.T(kw.get("text", "The End"))
            if kw.get("sub"):
                kw["sub"] = self.T(kw["sub"])
        elif kind in ("caption", "burst", "mark") and kw.get("text"):
            kw["text"] = self.T(kw["text"])
        return kw

    def scene(self, name, bg, **kw):
        sc = Scene(self, name, bg, **kw)
        self.scenes.append(sc)
        return sc

    # ---- voices
    def voice_of(self, who):
        return self.voices[who or "nar"]

    def voice_items(self):
        out = []
        for sc in self.scenes:
            for b in sc.beats:
                if b.text:
                    v, r, p = self.voice_of(b.voice or b.who)
                    b.key = (b.text, v, r, p)
                    out.append(b.key)
        return out

    def texts(self):
        return [b.text for sc in self.scenes for b in sc.beats if b.text]

    def codes(self):
        return []

    def cues(self):
        return []

    # ---- compile
    def compile(self, clips):
        t = 0.0
        for sc in self.scenes:
            t += sc.compile(t, clips)
        self.duration = t
        self.starts = [sc.t_start for sc in self.scenes]
        self.sfx_events, self.voice_events, self.mood_spans, self.chapters_list = [], [], [], []
        for si, sc in enumerate(self.scenes):
            for (ts, name, g) in sc.sfx:
                self.sfx_events.append((sc.t_start + ts, name, g))
            for (v0, v1, who, key, text) in sc.speech:
                self.voice_events.append((sc.t_start + v0, key))
            self.mood_spans.append((sc.t_start, sc.t_start + sc.dur, sc.mood, si))
            if sc.title:
                self.chapters_list.append((sc.t_start, sc.title))
        self.sfx_events.sort()
        return t


def chapters(tale, min_len=10.5):
    """[(start_seconds, label)]. YouTube only shows chapters when every one lasts >= 10 s, so a short scene is folded into its neighbour."""
    ch = list(tale.chapters_list)
    if not ch or ch[0][0] > 0.01:
        ch.insert(0, (0.0, tale.T("Intro")))
    out = []
    for i, (t, label) in enumerate(ch):
        end = ch[i + 1][0] if i + 1 < len(ch) else tale.duration
        if out and end - t < min_len:
            continue                                                  # its time now belongs to the chapter before
        out.append((t, label))
    while len(out) > 1 and out[1][0] - out[0][0] < min_len:           # a short first chapter swallows the next label instead
        del out[1]
    return out


def envelope(y, hz=30):
    hop = SR // hz
    n = max(1, len(y) // hop)
    e = np.sqrt(np.mean(y[: n * hop].reshape(n, hop) ** 2, axis=1)) if len(y) >= hop else np.array([0.5])
    ref = float(np.percentile(e, 90)) or 1e-6
    return np.clip(e / ref, 0, 1) ** 0.8


# ================================================================================================ drawing
def _bubble(s, text, ax, ay, tint="#FFFFFF", avoid=()):
    """Speech bubble on the screen canvas; (ax, ay) is the speaker's head.
    `avoid` = screen rects (x0, y0, x1, y1) of the other characters' faces: the bubble slides sideways, or wraps narrower, rather than cover one;
    when that is not enough (a small speaker next to a tall friend) it rises above them and its tail gets longer."""
    size = 40
    lh = size * 1.22
    pref = 0.30 if ax < 640 else 0.70
    best = None
    for lift in (0, 44, 88, 132):
        if best is not None and best[0] <= 1e-6:
            break
        seen = set()
        for maxw in (620, 500, 390):
            words, lines, cur = text.split(), [], ""
            for w in words:
                trial = (cur + " " + w).strip()
                if s.text_width(trial, size) > maxw and cur:
                    lines.append(cur)
                    cur = w
                else:
                    cur = trial
            lines.append(cur)
            if tuple(lines) in seen:
                continue
            seen.add(tuple(lines))
            tw = max(s.text_width(l, size) for l in lines)
            bw, bh = tw + 56, lh * len(lines) + 34
            by1 = ay - 26 - lift
            by0 = by1 - bh
            if by0 < 14:
                by0 = 14
                by1 = by0 + bh
            for fr in (pref, 1.0 - pref, 0.5, 0.12, 0.88):
                x0 = clamp(ax - bw * fr, 18, 1280 - 18 - bw)
                ov = sum(max(0.0, min(x0 + bw, r[2]) - max(x0, r[0])) * max(0.0, min(by1, r[3]) - max(by0, r[1])) for r in avoid)
                if best is None or ov < best[0] - 1e-6:
                    best = (ov, x0, bw, bh, by0, by1, lines)
                if ov <= 1e-6:
                    break
            if best[0] <= 1e-6:
                break
    _, bx0, bw, bh, by0, by1, lines = best
    s.rrect(bx0 + 4, by0 + 6, bx0 + bw + 4, by1 + 6, 30, fill="#00000026")
    tipx = clamp(ax, bx0 + 40, bx0 + bw - 40)
    rise = max(0.0, (ay - 26) - by1)                                       # how far the bubble was lifted: the tail stretches down to the speaker
    s.poly([(tipx - 22, by1 - 6), (tipx + 22, by1 - 6), (clamp(ax, tipx - 50, tipx + 50), min(ay - 6, by1 + 54 + rise))], fill=tint, outline=D.INK, width=3.5)
    s.rrect(bx0, by0, bx0 + bw, by1, 30, fill=tint, outline=D.INK, width=3.5)
    s.rect(tipx - 20, by1 - 8, tipx + 20, by1 - 1, tint)
    for i, l in enumerate(lines):
        s.text(bx0 + bw / 2, by0 + 17 + lh * (i + 0.5), l, size, D.INK)


def _shadow_color(near, far, x, y):
    ss = D.SS
    try:
        px = near.getpixel((int(clamp(x * ss, 0, near.width - 1)), int(clamp(y * ss, 0, near.height - 1))))
        if px[3] < 200:
            px = far.getpixel((int(clamp(x * ss, 0, far.width - 1)), int(clamp(y * ss, 0, far.height - 1))))
    except Exception:
        px = (120, 150, 100)
    return D.rgb2hex(tuple(int(v * 0.72) for v in px[:3]))


def _lower_at(tl, ts):
    """How far the body is lowered (+) or lifted (-) by a sitting pose, easing in over 0.3 s so that sitting down / getting up does not pop."""
    moving = tl.state(ts)[2]
    if moving:
        return 0.0
    lower = A.pose_for(tl.pose_name(ts), ts).lower
    pn, pt0 = tl.prev_pose(ts)
    we = tl.walk_end(ts)
    t_set = max(pt0, we)
    if ts - t_set < 0.3 and t_set >= 0.0:
        prev_lower = A.pose_for(pn, ts).lower if (pn and pt0 >= we) else 0.0
        lower = lerp(prev_lower, lower, ease(clamp((ts - t_set) / 0.3)))
    return lower


def _draw_actor(view, scene, tl, ts, near, far, tale, amp_of):
    d = tl.d
    vis, pop = tl.vis_at(ts)
    if not vis or pop <= 0.01:
        return
    x, y, moving, wpose, speed, cum = tl.state(ts)
    kk = d.k * (1.0 if d.flat else dscale(y)) * tl.scale_at(ts) * pop
    hop = tl.hop_at(ts)
    face = tl.face_at(ts)
    name = wpose if (moving and wpose) else tl.pose_name(ts)
    phase = cum / (46.0 * max(0.6, kk) + 0.05 * speed) * math.pi
    amp = amp_of.get(d.id)
    if d.kind in FAMILY:                                    # the Bibi friends are drawn straight on the screen canvas
        f = {"bibi": D.bibi, "pip": D.pip, "mo": D.mo, "lila": D.lila}[d.kind]
        mood = "open" if amp is not None else ("wow" if name in ("scared", "surprised") else "smile")
        kw = dict(t=ts, mood=mood, look=(3, -2))
        if d.kind == "bibi":
            kw["mouth_amt"] = amp
        f(view.c, view.X(x), view.Y(y - hop) - HEAD[d.kind] * 0.4 * kk * view.z, kk * view.z * 0.9, **kw)
        return
    P = A.pose_for(name, ts, phase=phase, moving=moving, amp=amp, face=face, seed=d.seed, speed=speed / 150.0,
                   gesture=not tl.hold_at(ts))
    P.lean += tl.tilt_at(ts)
    style = d.style
    if d.kind in ("girl", "bear", "troll", "wolf", "hen"):
        style = dict(style)
        style["hold"] = tl.hold_at(ts)
    P.look = (face * 3.0, -1.0) if P.look == (0.0, 0.0) and name in ("idle", "talk", "walk", "wave") else P.look
    P.lower = _lower_at(tl, ts)
    sh = _shadow_color(near, far, x, y)
    rx = {"pig": 70, "wolf": 66, "bear": 82, "hare": 62, "tortoise": 110, "girl": 66, "ginger": 56, "goat": 62, "troll": 90, "hen": 62, "chick": 44}.get(d.kind, 70) * kk
    view.ellipse(x, y + 3, rx * (1 - 0.18 * min(1.0, hop / 46.0)), rx * 0.16, fill=sh)
    A.CHARACTERS[d.kind](view, x, y - hop, kk, ts, P, **style)


def _fx_pos(scene, f, ts):
    x, y = f["x"], f["y"]
    if isinstance(x, str):
        tl = scene.atl[x]
        ax, ay, *_ = tl.state(ts)
        kk = tl.d.k * (1.0 if tl.d.flat else dscale(ay)) * tl.scale_at(ts)
        return ax, ay - HEAD[tl.d.kind] * kk * 0.78 + (y or 0) + _lower_at(tl, ts) * kk
    return x, y


def draw_scene(tale, si, ts, scale_out=1.0):
    D.set_language(getattr(tale, "lang", "en"))                 # the font of the tale's language (also in every worker process)
    scene = tale.scenes[si]
    ss = D.SS
    far, near, wf = B.backdrop(scene.bg, scene.world)
    cx, cy, z = scene.cam_at(ts)
    vw, vh = 1280.0 / z, 720.0 / z
    x0, y0 = cx - vw / 2, cy - vh / 2
    if scene.world > 1280:
        cxf = 640.0 + (cx - 640.0) * (wf - 1280.0) / (scene.world - 1280.0)
    else:
        cxf = cx
    fx0 = cxf - vw / 2
    OW, OH = 1280 * ss, 720 * ss
    f = far.resize((OW, OH), Image.BILINEAR, box=(fx0 * ss, y0 * ss, (fx0 + vw) * ss, (y0 + vh) * ss))
    n = near.resize((OW, OH), Image.BILINEAR, box=(x0 * ss, y0 * ss, (x0 + vw) * ss, (y0 + vh) * ss))
    f.paste(n, (0, 0), n)
    canvas = D.Canvas(f)
    view = View(canvas, cx, cy, z)
    if scene.clouds and scene.bg.startswith(("meadow", "race")):
        for i in range(3):
            px = (i * 520 + ts * (9 + 4 * i) + 100) % (scene.world + 600) - 300
            B.cloud_shape(view, px, 70 + 46 * i, 0.9 + 0.2 * i)
    VB.story_ambient(canvas, scene.bg, ts)                      # birds, butterflies, leaves, fireflies, glitter: behind the actors
    amp_of = {}
    for (v0, v1, who, key, text) in scene.speech:
        if who and v0 - 0.02 <= ts <= v1:
            env = tale.env[key]
            i = int((ts - v0) * 30)
            amp_of[who] = float(env[min(i, len(env) - 1)])
    items = []
    for pid, ptl in scene.ptl.items():
        vis, pop = ptl.vis_at(ts)
        if vis:
            items.append((ptl.d.y, 0, "prop", ptl, pop))
    for aid, atl in scene.atl.items():
        items.append((atl.d.zy if atl.d.zy is not None else atl.state(ts)[1], 1, "actor", atl, 1.0))
    items.sort(key=lambda it: (it[0], it[1]))
    for _, _, kind, tl, pop in items:
        if kind == "prop":
            d = tl.d
            st = {name: tl.value(name, ts) for name in set(d.st) | set(tl.vars)}
            st.update({k: v for k, v in d.st.items() if k not in st})
            for name in tl.vars:
                st[name] = tl.value(name, ts)
            PR.PROPS[d.kind](view, d.x, d.y, d.k * pop, ts, st)
        else:
            _draw_actor(view, scene, tl, ts, near, far, tale, amp_of)
    VB.story_foreground(canvas, scene.bg, ts, cx, z, scene.world)     # swaying grass along the bottom edge, in front of everybody
    for f_ in scene.fxs:
        if f_["t0"] <= ts <= f_["t1"]:
            x, y = _fx_pos(scene, f_, ts)
            PR.FX[f_["kind"]](view, canvas, x, y, ts - f_["t0"], **f_["kw"])
    heads = {}
    for aid, atl_ in scene.atl.items():
        vis_, _p = atl_.vis_at(ts)
        if not vis_:
            continue
        hx_, hy_, *_r = atl_.state(ts)
        kk_ = atl_.d.k * (1.0 if atl_.d.flat else dscale(hy_)) * atl_.scale_at(ts)
        sx_, sy_ = view.P(hx_, hy_ + _lower_at(atl_, ts) * kk_)
        hw_ = HEADW.get(atl_.d.kind, 60) * kk_ * view.z
        top_ = sy_ - HEAD[atl_.d.kind] * kk_ * view.z
        heads[aid] = (sx_ - hw_, top_, sx_ + hw_, top_ + HEAD[atl_.d.kind] * kk_ * view.z * 0.5)
    for (v0, v1, who, key, text) in scene.speech:
        if who and v0 - 0.08 <= ts <= v1 + 0.45 and who in scene.atl:
            tl = scene.atl[who]                              # (a hidden actor speaks from where he went out of sight)
            ax, ay, *_ = tl.state(ts)
            kk = tl.d.k * (1.0 if tl.d.flat else dscale(ay)) * tl.scale_at(ts)
            vis, _pop = tl.vis_at(ts)
            sx, sy = view.P(ax, ay - HEAD[tl.d.kind] * kk * (0.96 if vis else 0.55) + (_lower_at(tl, ts) * kk if vis else 0.0))
            _bubble(canvas, text, sx, sy, tint=tale.bubble_tint.get(who, "#FFFFFF"), avoid=[r for aid, r in heads.items() if aid != who])
    return canvas.final()


def render_frame(tale, t):
    t = clamp(t, 0.0, tale.duration - 1e-3)
    si = max(0, bisect.bisect_right(tale.starts, t) - 1)
    sc = tale.scenes[si]
    ts = t - sc.t_start
    img = draw_scene(tale, si, ts)
    if si + 1 < len(tale.scenes) and ts > sc.dur - XFADE:
        a = ease((ts - (sc.dur - XFADE)) / XFADE)
        img = Image.blend(img, draw_scene(tale, si + 1, 0.0), a)
    if t < 0.4:
        img = Image.blend(Image.new("RGB", img.size, "white"), img, ease(t / 0.4))
    elif t > tale.duration - 0.8:
        img = Image.blend(img, Image.new("RGB", img.size, "white"), ease((t - (tale.duration - 0.8)) / 0.8))
    return img


# ================================================================================================ preparing / rendering
Tale.bubble_tint = {}


def prepare(tale, ffmpeg, cache_dir):
    items = tale.voice_items()
    clips = VO.synth_items(items, ffmpeg, cache_dir)
    tale.compile(clips)
    tale.env = {k: envelope(y) for k, y in clips.items()}
    return clips


def sample_times(tale, per_scene=3):
    out = []
    for sc in tale.scenes:
        for i in range(per_scene):
            out.append(sc.t_start + sc.dur * (0.12 + 0.76 * i / max(1, per_scene - 1)))
    return out


def contact_sheet(tale, path, cols=4, thumb=320, times=None):
    times = times or sample_times(tale)
    frames = [render_frame(tale, t) for t in times]
    fw = thumb
    fh = int(fw * 9 / 16)
    rows = int(math.ceil(len(frames) / cols))
    sheet = Image.new("RGB", (cols * fw, rows * fh), "white")
    for i, fr in enumerate(frames):
        sheet.paste(fr.resize((fw, fh), Image.LANCZOS), ((i % cols) * fw, (i // cols) * fh))
    sheet.save(path)
    return path


_TALE = None


def _init(tale):
    global _TALE
    _TALE = tale


def _work(rng):
    a, b = rng
    return b"".join(render_frame(_TALE, i / FPS).tobytes() for i in range(a, b))


def render(tale, out_path, ffmpeg, cache_dir, workers=None, quiet=False, t_range=None, with_audio=True, with_voice=True):
    t_start = time.time()
    clips = prepare(tale, ffmpeg, cache_dir)
    total = tale.duration
    t0, t1 = (0.0, total) if t_range is None else (max(0.0, t_range[0]), min(total, t_range[1]))
    mix = SA.mix(tale, clips, voices=with_voice)
    a0, a1 = int(t0 * SR), int(t1 * SR)
    wav = out_path + ".wav"
    SA.write_wav(wav, mix[a0:a1] if with_audio else mix[a0:a1] * 0)
    f0, f1 = int(t0 * FPS), int(math.ceil(t1 * FPS))
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720",
           "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-vf", "format=yuv420p",
           "-c:v", "libx264", "-preset", "veryfast", "-tune", "animation", "-crf", "23", "-g", str(FPS * 2),
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "160k",
           "-t", f"{t1 - t0:.3f}", "-movflags", "+faststart", "-f", "mp4", out_path + ".part.mp4"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    workers = workers or os.cpu_count() or 2
    step = 6
    chunks = [(i, min(i + step, f1)) for i in range(f0, f1, step)]
    done = 0
    try:
        with Pool(workers, initializer=_init, initargs=(tale,)) as pool:
            for data in pool.imap(_work, chunks):
                proc.stdin.write(data)
                done += 1
                if not quiet and done % max(1, len(chunks) // 10) == 0:
                    print(f"  [{tale.id}] {100 * done // len(chunks)}%", flush=True)
        proc.stdin.close()
    except BrokenPipeError:
        pass
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError("ffmpeg failed (%s) for %s" % (rc, tale.id))
    os.replace(out_path + ".part.mp4", out_path)
    os.remove(wav)
    ch = chapters(tale)
    text = "\n".join(f"{fmt_time(t)} {label}" for t, label in ch)
    voiced = sum(len(clips[b.key]) / SR for sc in tale.scenes for b in sc.beats if b.text)
    return dict(file=os.path.basename(out_path), duration=total, frames=f1 - f0, cues=len(tale.voice_events), voice_seconds=voiced,
                bpm=0, seconds_to_render=round(time.time() - t_start, 1), chapters=[(round(t, 2), l) for t, l in ch], chapters_text=text)


def fmt_time(t):
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def sync_report(tale):
    problems = []
    spans = sorted((v0 + sc.t_start, v1 + sc.t_start, text) for sc in tale.scenes for (v0, v1, who, key, text) in sc.speech)
    for a, b in zip(spans, spans[1:]):
        if a[1] > b[0] + 0.01:
            problems.append(f"voice lines overlap: {a[2]!r} / {b[2]!r}")
    voiced = sum(v1 - v0 for v0, v1, _ in spans)
    return problems, dict(duration=tale.duration, cues=len(spans), voice_seconds=voiced, bpm=0)


# ================================================================================================ cover (thumbnail)
def make_cover(tale, path):
    """Designed thumbnail of a tale (1280x720 JPEG): the story's backdrop, its stars drawn big, and the poster title.
    `tale.cover` = dict(bg, title=(line1, line2), actors=[(id, kind, x, y, k, face, pose, style)], props=[(id, kind, x, y, k, state)])."""
    sp = tale.cover
    ct = Tale(tale.id + "-cover", tale.title, "", [], {"nar": ("", "", "")}, lang=getattr(tale, "lang", "en"))
    sc = ct.scene("cover", sp["bg"], mood="happy", drift=0.0, clouds=True)
    for (pid, ptype, x, y, k, st) in sp.get("props", ()):
        sc.prop(pid, ptype, x, y, k, **st)
    acts = []
    for (aid, kind, x, y, k, face, pose, style) in sp["actors"]:
        sc.actor(aid, kind, x, y, k, face=face, flat=True, **style)
        acts.append(("pose", aid, pose))
    lines = sp["title"]
    acts.append(("fx", "title", 0, 0, {"at": 0.0, "dur": 30.0, "lines": lines, "still": True, "top": 46, "size": sp.get("size", 118),
                                          "gap": sp.get("gap", 118), "pill": 30, "sfx": False}))
    sc.wait(3.0, *acts)
    ct.compile({})
    ct.env = {}
    t = 1.5
    for cand in [1.0 + 0.05 * i for i in range(40)]:                  # a moment when nobody is blinking
        if all(not A.pose_for(pz, cand, seed=sc.actors[aid].seed).blink for (aid, _k, _x, _y, _kk, _f, pz, _st) in sp["actors"]):
            t = cand
            break
    img = draw_scene(ct, 0, t)
    img.convert("RGB").save(path, quality=92)
    return path
