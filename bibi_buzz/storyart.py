"""Artwork for the Bibi story videos: a small puppet rig, the characters, props, backdrops and effects.

Everything is drawn with Pillow (no image files). Characters are drawn in LOCAL units with the feet at (0, 0)
and "up" being negative y; Rig maps them to the canvas (scale k, mirror, lean, squash).
"""
import math
import re
import random

from . import draw as D
from .draw import INK, SS, clamp, lerp, smooth, darker, mix, blinking

W, H = D.W, D.H


# ------------------------------------------------------------------------------------------------ rig
class Rig:
    def __init__(self, c, x, y, k=1.0, face=1, lean=0.0, sq=1.0):
        self.c, self.x0, self.y0, self.k, self.face, self.sq = c, x, y, k, face, sq
        a = math.radians(lean)
        self.ca, self.sa = math.cos(a), math.sin(a)
        self.wx = 1.0 + (1.0 - sq) * 0.7

    def P(self, lx, ly):
        lx = lx * self.face * self.wx
        ly = ly * self.sq
        return (self.x0 + (lx * self.ca - ly * self.sa) * self.k, self.y0 + (lx * self.sa + ly * self.ca) * self.k)

    def ell(self, lx, ly, rx, ry, fill=None, line=INK, ow=3.0, ang=0.0, n=36):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        pts = []
        for i in range(n):
            th = 2 * math.pi * i / n
            ex, ey = rx * math.cos(th), ry * math.sin(th)
            pts.append(self.P(lx + ex * ca - ey * sa, ly + ex * sa + ey * ca))
        self.c.poly(pts, fill=fill, outline=line, width=ow * self.k if line else 0)

    def dot(self, lx, ly, rr, fill):
        self.ell(lx, ly, rr, rr, fill, None, n=18)

    def poly(self, pts, fill=None, line=INK, ow=3.0):
        self.c.poly([self.P(*p) for p in pts], fill=fill, outline=line, width=ow * self.k if line else 0)

    def line(self, pts, color=INK, w=3.0):
        self.c.line([self.P(*p) for p in pts], color, max(1.0, w * self.k))

    def limb(self, p0, p1, w, fill, line=INK, ow=3.0):
        a, b = self.P(*p0), self.P(*p1)
        if line:
            self.c.line([a, b], line, (w + 2 * ow) * self.k)
        self.c.line([a, b], fill, w * self.k)

    def arc(self, lx, ly, rx, ry, a0, a1, color=INK, w=3.0, n=14):
        pts = []
        for i in range(n + 1):
            th = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((lx + rx * math.cos(th), ly + ry * math.sin(th)))
        self.line(pts, color, w)

    def rrect(self, x0, y0, x1, y1, rad, fill=None, line=INK, ow=3.0):
        pts = []
        for (cx, cy, a0) in ((x1 - rad, y0 + rad, -90), (x1 - rad, y1 - rad, 0), (x0 + rad, y1 - rad, 90), (x0 + rad, y0 + rad, 180)):
            for i in range(7):
                th = math.radians(a0 + 90 * i / 6)
                pts.append((cx + rad * math.cos(th), cy + rad * math.sin(th)))
        self.poly(pts, fill, line, ow)

    def blob(self, pts, fill=None, line=INK, ow=3.0, closed=True):
        self.poly(pts, fill, line, ow)


# ------------------------------------------------------------------------------------------------ pose
class Pose:
    """Everything that changes while a character moves or acts."""

    def __init__(self):
        self.face, self.lean, self.sq, self.bob = 1, 0.0, 1.0, 0.0
        self.arm_l, self.arm_r = 14.0, 14.0
        self.phase, self.moving = 0.0, False
        self.eyes, self.mouth, self.mouth_amt = "open", "smile", None
        self.look = (0.0, 0.0)
        self.blink = False
        self.puff = 0.0
        self.dx = 0.0
        self.hold = None
        self.sit = False
        self.lower = 0.0                    # body offset in local px (+ = down); sitting = 30, minus any lift

    def leg(self, s):
        if not self.moving:
            return 0.0, 0.0
        ph = self.phase + (0.0 if s > 0 else math.pi)
        return math.sin(ph) * 11, max(0.0, math.sin(ph)) * 11


def pose_for(name, t, phase=0.0, moving=False, amp=None, face=1, seed=0.0, speed=1.0):
    """Maps a pose name + time to rig parameters. `amp` is the voice loudness (0..1) while the character talks.
    Modifiers: "sit@84" lifts the body 84 px (feet dangle, e.g. on a tall chair); "sit+sad" keeps the pose but takes the face of "sad"."""
    lift, expr = 0.0, None
    if "@" in name or "+" in name:
        toks = re.split(r"([@+])", name)
        name = toks[0]
        for sep, val in zip(toks[1::2], toks[2::2]):
            if sep == "@":
                lift = float(val)
            else:
                expr = val
    P = Pose()
    P.face, P.phase, P.moving = face, phase, moving
    s = math.sin
    P.bob = abs(s(phase)) * 5 * min(speed, 1.6) if moving else 1.6 * s(t * 2.4 + seed)
    P.blink = blinking(t, 3.3 + (seed % 1.0), seed)
    if moving:
        P.arm_l = 14 + s(phase) * 28
        P.arm_r = 14 - s(phase) * 28
        P.lean = s(phase) * 2.2 + (7 * min(speed, 2.0) - 7 if name == "run" else 0)
        if name == "run":
            P.arm_l, P.arm_r = 60 + s(phase) * 40, 60 - s(phase) * 40
            P.lean = 9
    if name in ("idle", "walk", "run", "talk"):
        pass
    elif name == "wave":
        P.arm_r = 150 + s(t * 9) * 22
        P.mouth = "grin"
    elif name == "cheer":
        P.arm_l, P.arm_r = 160 + s(t * 8) * 12, 160 - s(t * 8) * 12
        P.bob = abs(s(t * 6 + seed)) * 14
        P.mouth, P.eyes = "grin", "happy"
    elif name == "happy":
        P.eyes, P.mouth = "happy", "grin"
        P.bob = abs(s(t * 4 + seed)) * 6
        P.arm_l = P.arm_r = 30 + s(t * 4) * 8
    elif name == "scared":
        P.eyes, P.mouth = "wide", "wow"
        P.arm_l = P.arm_r = 130
        P.dx = s(t * 55) * 2.2
        P.lean = s(t * 40) * 1.2
    elif name == "sad":
        P.eyes, P.mouth = "sad", "sad"
        P.lean = -5
        P.arm_l = P.arm_r = 6
        P.look = (0, 4)
    elif name == "sleep":
        P.eyes, P.mouth = "closed", "smile"
        P.blink = False
        P.bob = 3 * s(t * 1.3 + seed)
        P.lean = 0
        P.arm_l = P.arm_r = 8
    elif name == "nap":
        P.eyes, P.mouth = "closed", "smile"
        P.blink = False
        P.lean = -11
        P.arm_l = P.arm_r = 30
        P.bob = 2.5 * s(t * 1.4 + seed)
    elif name == "sit":
        P.sit = True
        P.arm_l = P.arm_r = 20
    elif name == "blow":
        P.mouth, P.puff = "puff", 1.0
        P.lean = -6 + 12 * max(0.0, s(t * 5))
        P.arm_l = P.arm_r = 20
        P.eyes = "angry"
    elif name == "dizzy":
        P.eyes, P.mouth = "swirl", "wow"
        P.lean = s(t * 3.2) * 9
        P.dx = s(t * 3.2) * 6
        P.arm_l = P.arm_r = 60 + s(t * 3.2) * 20
    elif name == "eat":
        P.arm_r = 120 + s(t * 5) * 20
        P.mouth = "open" if s(t * 5) > 0.2 else "smile"
        P.eyes = "happy"
    elif name == "think":
        P.arm_r = 140
        P.look = (3, -4)
        P.mouth = "flat"
    elif name == "knock":
        P.arm_r = 100 + s(t * 14) * 18
    elif name == "shrug":
        P.arm_l = P.arm_r = 70
        P.mouth = "flat"
    elif name == "laugh":
        P.eyes, P.mouth, P.mouth_amt = "happy", "open", 0.8 + 0.2 * s(t * 14)
        P.bob = abs(s(t * 7)) * 5
    elif name == "jump":
        P.bob = abs(s(t * 5 + seed)) * 26
        P.sq = 1.0 + 0.06 * s(t * 10)
        P.arm_l = P.arm_r = 130
        P.eyes, P.mouth = "happy", "grin"
    elif name == "sly":
        P.eyes, P.mouth = "sly", "grin"
        P.arm_l, P.arm_r = 20, 20
    elif name == "proud":
        P.eyes, P.mouth = "sly", "grin"
        P.arm_l = P.arm_r = 40
        P.lean = -3
    elif name == "tired":
        P.eyes, P.mouth = "closed", "flat"
        P.lean = 4 + s(t * 2) * 1.5
        P.arm_l = P.arm_r = 5
        P.bob = 0.0
    elif name == "surprised":
        P.eyes, P.mouth = "wide", "wow"
        P.arm_l = P.arm_r = 80
        P.bob = 4
    elif name in ("pull", "strain", "grip"):
        # a tug of war (everybody faces the thing they pull, so "backwards" = away from the facing side = -face): hands out in front,
        # leaning back. pull = heave-ho, strain = the biggest heave (eyes shut, shaking), grip = holding on, getting ready.
        # (every puller uses the same time, so a whole line of them heaves together)
        w = s(t * 6.3)
        if name == "pull":
            P.eyes, P.mouth, P.puff = "angry", "puff", 1.0
            P.lean = -face * (11.0 + 3.5 * w)
            P.arm_r, P.arm_l = 100 + 5 * w, -48 + 5 * w
            P.bob = 1.6 * abs(w)
        elif name == "strain":
            P.eyes, P.mouth, P.puff = "closed", "puff", 1.0
            P.blink = False
            P.lean = -face * (19.0 + 4.5 * w)
            P.arm_r, P.arm_l = 108 + 6 * w, -40 + 6 * w
            P.dx = s(t * 31.0) * 1.6
            P.bob = 2.4 * abs(w)
        else:
            P.eyes, P.mouth = "open", "flat"
            P.lean = -face * 6.0
            P.arm_r, P.arm_l = 96, -52
            P.look = (face * 3.0, 0.0)
    elif name == "plant":                                   # bending over the garden bed to plant a seed (the bed is on the facing side)
        P.lean = face * 11.0
        P.arm_r = 56 + s(t * 3.0) * 24
        P.arm_l = 20
        P.mouth = "smile"
        P.look = (face * 3.0, 3.0)
    if expr:
        E = pose_for(expr, t, phase, False, None, face, seed, speed)
        P.eyes, P.mouth, P.mouth_amt, P.look = E.eyes, E.mouth, E.mouth_amt, E.look
        name = expr if expr in ("blow", "dizzy", "scared", "laugh") else name
    P.lower = (30.0 if P.sit else 0.0) - lift
    if amp is not None and name not in ("blow", "dizzy", "scared", "laugh"):
        P.mouth, P.mouth_amt = "open", amp
        if P.eyes == "closed":
            P.eyes = "open"
    return P


# ------------------------------------------------------------------------------------------------ faces
def f_eyes(r, x, y, spread, rx, ry, P, pupil=INK, white="#FFFFFF"):
    st = P.eyes
    blink = P.blink and st in ("open", "sly", "angry", "sad")
    look = P.look
    for s in (-1, 1):
        ex = x + s * spread
        inner, outer = ex - s * rx * 0.9, ex + s * rx * 1.0            # inner = toward the nose
        if st == "closed" or blink:
            r.arc(ex, y - ry * 0.25, rx * 0.95, ry * 0.6, 22, 158, INK, 3.4)
            continue
        if st == "happy":
            r.arc(ex, y + ry * 0.35, rx * 1.0, ry * 0.8, 205, 335, INK, 3.8)
            continue
        wide = st == "wide"
        wr, hr = rx * (1.22 if wide else 1.0), ry * (1.22 if wide else 1.0)
        cy, hh = y, hr
        if st == "sly":
            cy, hh = y + hr * 0.2, hr * 0.62
        r.ell(ex, cy, wr, hh, white, INK, 2.6)
        if st == "swirl":
            for i in range(3):
                r.arc(ex, y, wr * (0.25 + 0.22 * i), hr * (0.25 + 0.22 * i), i * 90, 250 + i * 90, INK, 2.2)
            continue
        pr = 0.40 if wide else (0.78 if st == "sly" else 0.64)
        px, py = ex + look[0] * 0.55, cy + look[1] * 0.55
        r.ell(px, py, wr * pr, hh * pr * 1.08, pupil, None)
        r.dot(px + wr * 0.2, py - hh * 0.26, wr * 0.2, "#FFFFFF")
        if st == "sly":                                                 # heavy lid
            r.line([(ex - wr * 1.05, cy - hh * 0.62 + s * 1.5), (ex + wr * 1.05, cy - hh * 0.62 - s * 1.5)], INK, 4.4)
        elif st == "angry":
            r.line([(outer, y - hr * 1.65), (inner, y - hr * 1.0)], INK, 4.4)
        elif st == "sad":
            r.line([(outer, y - hr * 1.15), (inner, y - hr * 1.6)], INK, 3.6)


def f_cheeks(r, x, y, spread, color="#FF9DB0", rr=9, puff=0.0):
    for s in (-1, 1):
        r.ell(x + s * spread * (1 + 0.12 * puff), y, rr * (1 + 0.55 * puff), rr * 0.74 * (1 + 0.55 * puff), color, None)


def f_mouth(r, x, y, P, w=15.0, color=INK, teeth=False):
    m, amp = P.mouth, P.mouth_amt
    if m == "smile":
        r.arc(x, y - 4, w, w * 0.72, 18, 162, color, 3.4)
    elif m == "grin":
        pts = [(x + w * 1.15 * math.cos(math.radians(a)), y - 6 + w * 0.95 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
        r.poly(pts, "#B8283C", color, 2.8)
        if teeth:
            r.poly([(x - w * 0.9, y - 6), (x + w * 0.9, y - 6), (x + w * 0.8, y + 2), (x - w * 0.8, y + 2)], "#FFFFFF", None)
        else:
            r.ell(x, y + w * 0.55, w * 0.5, w * 0.28, "#FF8FA3", None)
    elif m == "open":
        a = 0.35 if amp is None else clamp(amp)
        ry = (3 + 12 * a)
        r.ell(x, y + ry * 0.55, w * 0.85, ry, "#B8283C", color, 2.6)
        r.ell(x, y + ry * 1.15, w * 0.5, ry * 0.42, "#FF8FA3", None)
    elif m == "wow":
        r.ell(x, y + 5, w * 0.5, w * 0.7, "#B8283C", color, 2.6)
    elif m == "sad":
        r.arc(x, y + 8, w * 0.8, w * 0.6, 200, 340, color, 3.4)
    elif m == "flat":
        r.line([(x - w * 0.6, y), (x + w * 0.6, y)], color, 3.4)
    elif m == "puff":
        r.ell(x, y + 2, w * 0.38, w * 0.38, "#7A2A3A", color, 2.4)


def f_arms(r, P, shoulder_x, shoulder_y, length, w, skin, hand=None, sleeve=None):
    """Both arms; angle 0 = hanging down, 90 = out to the side, 180 = straight up."""
    out = []
    for s, ang in ((-1, P.arm_l), (1, P.arm_r)):
        a = math.radians(ang)
        sx, sy = s * shoulder_x, shoulder_y
        ex, ey = sx + s * math.sin(a) * length, sy + math.cos(a) * length
        r.limb((sx, sy), (ex, ey), w, skin)
        if sleeve:
            mx, my = sx + (ex - sx) * 0.45, sy + (ey - sy) * 0.45
            r.limb((sx, sy), (mx, my), w + 2, sleeve, None, 0)
        r.dot(ex, ey, w * 0.62, hand or skin)
        out.append((ex, ey))
    return out


def held(r, kind, hand):
    """A small item in the hand at local position `hand`."""
    if not kind:
        return
    hx, hy = hand
    if kind == "basket":
        r.arc(hx, hy - 4, 20, 22, 180, 360, "#9B5C2E", 4.5)
        r.rrect(hx - 22, hy - 6, hx + 22, hy + 22, 7, "#D9A066", INK, 2.4)
        r.line([(hx - 22, hy + 8), (hx + 22, hy + 8)], "#B8733A", 2)
        for i, col in enumerate(("#FF6B8B", "#FFD23F", "#B58CFF")):
            r.dot(hx - 12 + i * 12, hy - 8 - (i % 2) * 4, 6.5, col)
    elif kind == "flag":
        r.line([(hx, hy + 10), (hx, hy - 120)], "#8B5A2B", 5)
        r.poly([(hx, hy - 120), (hx + 62, hy - 100), (hx, hy - 80)], "#E2574C", INK, 2.6)
    elif kind == "flowers":
        for i, col in enumerate(("#FF6B8B", "#FFD23F", "#B58CFF", "#FFFFFF")):
            r.line([(hx, hy + 8), (hx - 14 + i * 9, hy - 34)], "#3E9B3A", 2.6)
            r.dot(hx - 14 + i * 9, hy - 38, 8, col)
            r.dot(hx - 14 + i * 9, hy - 38, 3, "#FFE98A")
    elif kind == "spoon":
        r.line([(hx, hy + 6), (hx + 14, hy - 30)], "#B8B8C4", 4.4)
        r.ell(hx + 17, hy - 37, 7.5, 9.5, "#D0D0DA", INK, 1.8, ang=-20)
    elif kind == "medal":
        r.line([(hx - 10, hy - 26), (hx, hy), (hx + 10, hy - 26)], "#E2574C", 4)
        r.dot(hx, hy + 6, 11, "#FFD21F")
        r.dot(hx, hy + 6, 6, "#FFE98A")
    elif kind == "club":                                                                 # the troll's big, knobbly stick
        r.line([(hx, hy + 16), (hx + 12, hy - 92)], INK, 22)
        r.line([(hx, hy + 16), (hx + 12, hy - 92)], "#8B5A2B", 15)
        r.ell(hx + 15, hy - 112, 25, 36, "#8B5A2B", INK, 3, ang=8)
        r.ell(hx + 8, hy - 122, 8, 13, "#B07B45", None, ang=8)
        for dx, dy in ((-12, -104), (30, -100), (4, -134)):
            r.dot(hx + 15 + dx, hy + dy, 3.6, "#C9A36A")


def shadow(c, x, y, rx, color="#00000030"):
    """Soft contact shadow (drawn as a darker ellipse; colour comes from the backdrop)."""
    c.ellipse(x, y + 2, rx, rx * 0.16, fill=color)


# ------------------------------------------------------------------------------------------------ hats
def hat(r, kind, y, color=None):
    """y = top of the head; the hat sits on it with a small overlap."""
    if kind == "straw":
        r.ell(0, y + 4, 72, 13, "#F0C860", INK, 3)
        r.rrect(-32, y - 38, 32, y + 4, 16, "#F7D878", INK, 3)
        r.rrect(-33, y - 8, 33, y + 4, 3, color or "#E2574C", INK, 2.4)
    elif kind == "cap":
        r.ell(0, y - 4, 50, 28, color or "#3DB54A", INK, 3, n=30)
        r.ell(28, y + 12, 44, 8, darker(color or "#3DB54A", 0.12), INK, 2.6)
        r.dot(0, y - 30, 6, "#FFFFFF")
    elif kind == "helmet":
        r.ell(0, y - 6, 54, 34, "#FFD21F", INK, 3, n=30)
        r.rrect(-62, y + 6, 62, y + 19, 7, "#F2B800", INK, 3)
        r.rrect(-8, y - 38, 8, y, 4, "#F2B800", None)
    elif kind == "bonnet":
        r.ell(0, y - 8, 56, 32, "#FFF4D6", INK, 3, n=30)
        r.rrect(-54, y + 4, 54, y + 17, 6, "#FF7AA8", INK, 2.6)
        r.dot(-36, y + 14, 8, "#FF7AA8")
    elif kind == "tophat":
        r.rrect(-46, y - 6, 46, y + 8, 6, "#2B2B3B", INK, 3)
        r.rrect(-30, y - 58, 30, y - 2, 5, "#3A3A4E", INK, 3)
        r.rrect(-30, y - 16, 30, y - 6, 2, "#E2574C", None)
    elif kind == "bow":
        for s in (-1, 1):
            r.poly([(0, y), (s * 28, y - 16), (s * 28, y + 16)], color or "#FF5C8A", INK, 2.6)
        r.dot(0, y, 8, darker(color or "#FF5C8A", 0.12))
    elif kind == "crown":
        r.poly([(-30, y + 10), (-34, y - 24), (-16, y - 6), (0, y - 32), (16, y - 6), (34, y - 24), (30, y + 10)], "#FFD21F", INK, 3)


# ------------------------------------------------------------------------------------------------ pig
def pig(c, x, y, k=1.0, t=0.0, P=None, skin="#FFB3C7", outfit="#3E8EDE", hat_kind=None, hat_color=None, apron=False, **_):
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k, k, P.face, P.lean, P.sq)
    snout, belly = darker(skin, 0.1), mix(skin, "#FFFFFF", 0.45)
    ear_in = "#FF8FB0"
    legs_up = 8 if P.sit else 0
    for s in (-1, 1):                                        # legs
        sw, lift = P.leg(s)
        hip, foot = (s * 21, -46), (s * 22 + sw, -10 - lift + (0 if not P.sit else -4))
        r.limb(hip, foot, 21, skin)
        r.ell(foot[0] + s * 1, foot[1] + 3, 15, 8.5, "#E8749A", INK, 2.6)
    tail = [(-44 + 0, -70)] + [(-58 + (13 - a / 70.0) * math.cos(math.radians(a)), -88 + (13 - a / 70.0) * math.sin(math.radians(a))) for a in range(150, 660, 40)]
    r.line(tail, INK, 6.4)                                                              # curly tail
    r.line(tail, snout, 3.2)
    r.ell(0, -88, 52, 48, skin, INK, 3.2)                                              # body
    r.ell(0, -80, 31, 29, belly, None)
    pants = [(52 * math.cos(math.radians(a)), -88 + 48 * math.sin(math.radians(a))) for a in range(0, 181, 12)]
    r.poly(pants, outfit, INK, 3)
    r.rrect(-22, -122, 22, -82, 6, outfit, INK, 3)                                     # bib
    for s in (-1, 1):
        r.limb((s * 16, -120), (s * 24, -138), 9, outfit, INK, 2.6)                     # straps
        r.dot(s * 17, -118, 4.5, "#FFD21F")
    r.rrect(-12, -108, 12, -92, 4, darker(outfit, 0.12), INK, 2)
    if apron:
        r.poly([(-30, -122), (30, -122), (44, -50), (-44, -50)], "#FFFFFF", INK, 3)
        r.dot(0, -96, 7, "#FF7AA8")
    f_arms(r, P, 44, -112, 40, 19, skin, hand=skin)
    r.ell(0, -166, 57, 51, skin, INK, 3.2)                                             # head
    for s in (-1, 1):                                                                   # ears
        r.ell(s * 40, -206, 17, 25, skin, INK, 3, ang=s * 32)
        r.ell(s * 40, -204, 9, 15, ear_in, None, ang=s * 32)
    sh = P.face * 4
    r.ell(sh, -154, 25, 18, snout, INK, 3)                                              # snout
    r.ell(sh - 9, -154, 3.6, 5.4, "#C94B73", None)
    r.ell(sh + 9, -154, 3.6, 5.4, "#C94B73", None)
    f_eyes(r, sh * 1.5, -172, 24, 11, 13.5, P)
    f_cheeks(r, sh, -152, 43, "#FF8FB0", 9, P.puff)
    f_mouth(r, sh, -134, P, 14)
    if hat_kind:
        hat(r, hat_kind, -216, hat_color)
    return r


# ------------------------------------------------------------------------------------------------ wolf
def wolf(c, x, y, k=1.0, t=0.0, P=None, fur="#8E9AB0", scarf=None, cap=None, glasses=False, **_):
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k, k, P.face, P.lean, P.sq)
    dark, light = darker(fur, 0.28), "#E8ECF4"
    for s in (-1, 1):                                                                    # long legs
        sw, lift = P.leg(s)
        hip, foot = (s * 22, -66), (s * 26 + sw, -10 - lift)
        r.limb(hip, foot, 23, dark)
        r.ell(foot[0] + s * 3, foot[1] + 3, 18, 9, "#4A5368", INK, 2.6)
    sway = 8 * math.sin(t * 3.0)
    r.ell(-82, -76, 22, 44, fur, INK, 3.2, ang=38 + sway)                               # bushy tail
    r.ell(-98, -46, 13, 17, light, None, ang=38 + sway)
    r.ell(0, -112, 50, 66, fur, INK, 3.2)                                                # body
    r.ell(0, -100, 29, 44, light, None)
    f_arms(r, P, 46, -142, 52, 20, fur, hand=dark)
    if scarf:
        r.rrect(-42, -168, 42, -150, 9, scarf, INK, 3)
        r.poly([(20, -156), (46, -156), (50, -112), (30, -112)], scarf, INK, 3)
    r.ell(0, -200, 57, 47, fur, INK, 3.2)                                                # head
    for s in (-1, 1):                                                                    # cheek fur
        r.poly([(s * 54, -212), (s * 74, -198), (s * 56, -192), (s * 70, -178), (s * 52, -176), (s * 58, -160), (s * 40, -170)], fur, INK, 3)
    if cap:                                                                              # Grandma's nightcap (the ears stick out in front of it)
        r.poly([(-52, -232), (52, -232), (50, -262), (30, -300), (4, -322), (-22, -312), (-44, -276)], cap, INK, 3.2)
        r.ell(-26, -324, 11, 11, "#FF7AA8", INK, 2.6)
    for s in (-1, 1):                                                                    # pointed ears
        r.poly([(s * 24, -234), (s * 34, -280), (s * 62, -226)], fur, INK, 3.2)
        r.poly([(s * 33, -236), (s * 37, -266), (s * 53, -232)], "#FFB3C7", None)
    if cap:
        r.rrect(-56, -240, 56, -222, 8, mix(cap, "#FF8FB0", 0.55), INK, 3)               # the frilly brim
    sh = P.face * 5
    r.ell(sh, -186, 33, 25, light, INK, 3)                                               # muzzle
    r.ell(sh, -198, 13, 9, "#2B2B3B", INK, 2.4)                                          # nose
    r.dot(sh - 4, -201, 3, "#FFFFFF")
    f_eyes(r, sh * 1.4, -212, 25, 11.5, 13, P, white="#FFFBE0")
    f_mouth(r, sh, -176, P, 17, teeth=True)
    if P.puff:
        f_cheeks(r, sh, -184, 47, "#FF9DB0", 10, P.puff)
    if glasses:
        for s in (-1, 1):
            r.ell(sh * 1.4 + s * 25, -212, 18, 18, None, "#7A5A3A", 3)
        r.line([(sh * 1.4 - 8, -212), (sh * 1.4 + 8, -212)], "#7A5A3A", 3)
    return r


# ------------------------------------------------------------------------------------------------ bears
def bear(c, x, y, k=1.0, t=0.0, P=None, fur="#9A6232", outfit=None, extra=None, hat_kind=None, hat_color=None, hold=None, **_):
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k, k, P.face, P.lean, P.sq)
    dark, muzzle = darker(fur, 0.2), mix(fur, "#FFF0D2", 0.65)
    for s in (-1, 1):
        sw, lift = P.leg(s)
        hip, foot = (s * 26, -48), (s * 28 + sw, -12 - lift)
        r.limb(hip, foot, 29, fur)
        r.ell(foot[0], foot[1] + 4, 20, 10, dark, INK, 2.8)
    r.ell(0, -98, 60, 58, fur, INK, 3.3)
    r.ell(0, -90, 36, 36, muzzle, None)
    if outfit:
        r.poly([(-44, -118), (44, -118), (54, -66), (-54, -66)], outfit, INK, 3) if extra == "apron" else None
        if extra == "tie":
            r.poly([(0, -138), (-10, -150), (10, -150)], outfit, INK, 2.4)
            r.poly([(0, -138), (-9, -112), (0, -100), (9, -112)], outfit, INK, 2.6)
        elif extra == "bib":
            r.rrect(-26, -124, 26, -84, 12, outfit, INK, 3)
            r.dot(0, -104, 6, "#FFFFFF")
    hands = f_arms(r, P, 54, -128, 46, 24, fur, hand=fur)
    held(r, hold, hands[1])
    r.ell(0, -188, 62, 54, fur, INK, 3.3)
    for s in (-1, 1):
        r.ell(s * 46, -228, 21, 21, fur, INK, 3)
        r.ell(s * 46, -226, 11, 11, muzzle, None)
    sh = P.face * 4
    r.ell(sh, -174, 31, 23, muzzle, INK, 3)
    r.ell(sh, -184, 11, 8, "#3A2A22", INK, 2.2)
    r.dot(sh - 3, -186, 2.8, "#FFFFFF")
    f_eyes(r, sh * 1.5, -200, 26, 11.5, 14, P)
    f_cheeks(r, sh, -172, 48, "#FF9A8A", 9, P.puff)
    f_mouth(r, sh, -158, P, 14)
    hk = hat_kind or (extra if extra in ("bonnet", "cap", "bow") else None)
    if hk:
        hat(r, hk, -240 if hk == "bow" else -236, hat_color or (outfit if hk == "cap" else None))
    return r


# ------------------------------------------------------------------------------------------------ hare
def hare(c, x, y, k=1.0, t=0.0, P=None, fur="#D9BE98", **_):
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k, k, P.face, P.lean, P.sq)
    belly, inner = "#FFF4E2", "#FFB3C7"
    for s in (-1, 1):                                                                    # long hind legs + sneakers
        sw, lift = P.leg(s)
        hip, foot = (s * 20, -56), (s * 24 + sw, -14 - lift)
        r.limb(hip, foot, 19, fur)
        r.ell(foot[0] + s * 4, foot[1] + 5, 22, 10, "#E2574C", INK, 2.8)
        r.rrect(foot[0] - 14, foot[1] + 1, foot[0] + 14, foot[1] + 5, 2, "#FFFFFF", None)
    r.ell(0, -92, 44, 50, fur, INK, 3.2)
    r.ell(0, -84, 27, 33, belly, None)
    r.rrect(-40, -118, 40, -104, 6, "#3E8EDE", INK, 2.8)                                  # sporty sash
    r.rrect(-14, -126, 14, -100, 3, "#FFFFFF", INK, 2.4)
    f_arms(r, P, 40, -122, 40, 17, fur, hand=belly)
    for s in (-1, 1):                                                                    # tall ears
        lean_e = s * (16 + 4 * math.sin(t * 2.2 + s))
        r.ell(s * 18, -232, 14, 52, fur, INK, 3, ang=lean_e)
        r.ell(s * 18, -230, 7, 40, inner, None, ang=lean_e)
    r.ell(0, -158, 47, 43, fur, INK, 3.2)
    r.ell(0, -146, 25, 19, belly, None)
    r.dot(P.face * 3, -152, 5.5, "#FF8FA3")
    sh = P.face * 3
    f_eyes(r, sh * 1.5, -166, 20, 10.5, 13, P)
    f_cheeks(r, sh, -144, 36, "#FFB0A0", 8, P.puff)
    f_mouth(r, sh, -138, P, 11)
    if P.mouth in ("smile", "grin", "flat"):                                              # buck teeth
        r.rrect(sh - 7, -140, sh + 7, -127, 2, "#FFFFFF", INK, 2)
        r.line([(sh, -140), (sh, -127)], INK, 1.6)
    def hw(yy):
        return 47 * math.sqrt(max(0.0, 1 - ((yy + 158) / 43.0) ** 2)) + 1.5
    r.poly([(-hw(-195), -195), (hw(-195), -195), (hw(-184), -184), (-hw(-184), -184)], "#E2574C", INK, 2.6)  # headband
    return r


# ------------------------------------------------------------------------------------------------ tortoise (side view)
def tortoise(c, x, y, k=1.0, t=0.0, P=None, shell="#4FB05A", hold=None, **_):
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k, k, P.face, P.lean, P.sq)
    skin = "#9BD86B"
    for i, (lx, s) in enumerate(((-52, 1), (54, 1), (-30, -1), (34, -1))):             # four stubby legs
        sw = math.sin(P.phase + i * 1.6) * 5 if P.moving else 0
        lift = max(0.0, math.sin(P.phase + i * 1.6)) * 5 if P.moving else 0
        r.ell(lx + sw, -12 - lift, 17, 13, skin if s == 1 else darker(skin, 0.1), INK, 2.8)
    r.ell(-2, -36, 88, 18, "#E8E49A", INK, 3)                                          # belly rim
    r.ell(-90, -44, 12, 9, skin, INK, 2.6, ang=-20)                                       # tail
    dome = [(88 * math.cos(math.radians(a)), -40 + 66 * math.sin(math.radians(a))) for a in range(180, 361, 10)]
    r.poly(dome, shell, INK, 3.4)
    for (px, py, pr) in ((0, -78, 24), (-44, -64, 19), (44, -64, 19), (-24, -38, 14), (24, -38, 14)):
        pts = [(px + pr * math.cos(math.radians(a)), py + pr * 0.82 * math.sin(math.radians(a))) for a in range(0, 360, 60)]
        r.poly(pts, mix(shell, "#B6F08C", 0.55), darker(shell, 0.4), 2.4)
    hx = 96
    r.limb((70, -46), (hx, -56 + math.sin(t * 2) * 1.5), 24, skin)                      # neck
    if hold == "medal":                                                                  # winner's medal on a ribbon
        r.line([(62, -68), (80, -34), (112, -60)], "#E2574C", 6)
        r.ell(80, -25, 12.5, 12.5, "#FFD21F", INK, 2.4)
        r.ell(80, -25, 7, 7, "#FFF0A0", None)
    r.ell(hx + 14, -62, 29, 25, skin, INK, 3)                                            # head
    P.look = (0.0, 0.0)
    ex = hx + 20
    if P.eyes in ("closed", "sleep") or P.blink:
        r.arc(ex, -68, 6, 4, 20, 160, INK, 3)
    elif P.eyes == "happy":
        r.arc(ex, -66, 7, 5, 205, 335, INK, 3.4)
    else:
        r.ell(ex, -68, 8.5, 10, "#FFFFFF", INK, 2.4)
        r.ell(ex + 2, -67, 4.8, 6, INK, None)
        r.dot(ex + 3.5, -70, 1.8, "#FFFFFF")
    r.dot(hx + 27, -52, 3, "#FF9DB0")
    if P.mouth in ("open", "wow", "grin"):
        r.ell(hx + 29, -53, 7, 4 + (6 * (P.mouth_amt or 0.4)), "#B8283C", INK, 2)
    else:
        r.arc(hx + 24, -56, 11, 8, 20, 150, INK, 3)
    r.dot(hx + 6, -54, 6, "#FF9DB0")
    r.ell(hx + 10, -86, 20, 7, "#2E7DE0", INK, 2.6, ang=-6)                               # little cap
    r.ell(hx + 2, -92, 14, 11, "#3E8EDE", INK, 2.6)
    return r


# ------------------------------------------------------------------------------------------------ girl
def girl(c, x, y, k=1.0, t=0.0, P=None, dress="#6CB7FF", hair="#FFC83D", hold=None, hood=None, granny=None, gramps=None, **_):
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k + P.lower * k, k, P.face, P.lean, P.sq)
    skin = "#FFDDBF"
    for s in (-1, 1):                                                                    # legs, socks, shoes
        sw, lift = P.leg(s)
        hip, foot = (s * 17, -58), (s * 18 + sw, -14 - lift)
        if P.sit:
            foot = (s * 30, -30)
        if gramps:                                                                       # brown trousers and sturdy shoes
            r.limb(hip, foot, 20, "#7A5A3A", INK, 2.6)
            r.ell(foot[0] + s * 2, foot[1] + 22, 19, 10, "#3B2A1E", INK, 2.6)
            continue
        r.limb(hip, foot, 14, skin)
        r.limb((foot[0], foot[1] + 6), (foot[0], foot[1] + 18), 15, "#FFFFFF", INK, 2.4)
        r.ell(foot[0] + s * 2, foot[1] + 22, 17, 9, "#E2574C", INK, 2.6)
    if not hood and not granny and not gramps:
        for s in (-1, 1):                                                                # long hair behind
            r.ell(s * 50, -148, 21, 38, hair, INK, 3)
    if hood:                                                                             # a red hooded cloak instead of the dress
        r.poly([(-30, -142), (30, -142), (72, -50), (-72, -50)], hood, INK, 3.2)
        r.ell(0, -50, 72, 9, darker(hood, 0.12), INK, 2.6)
        r.line([(0, -136), (0, -56)], darker(hood, 0.22), 2.6)
        dress = hood
    elif gramps:                                                                         # a cardigan over a white shirt
        dress = gramps
        r.poly([(-30, -142), (30, -142), (40, -62), (-40, -62)], dress, INK, 3.2)
        r.poly([(-13, -142), (13, -142), (0, -102)], "#FFFFFF", INK, 2.4)
        r.line([(0, -102), (0, -62)], darker(dress, 0.25), 2.6)
        for yy in (-92, -78):
            r.dot(0, yy, 4.2, "#FFD21F")
        r.ell(0, -62, 40, 8, darker(dress, 0.1), INK, 2.6)
    else:
        r.poly([(-28, -140), (28, -140), (60, -52), (-60, -52)], dress, INK, 3.2)       # dress
        r.ell(0, -52, 60, 9, darker(dress, 0.1), INK, 2.6)
        r.poly([(-22, -138), (22, -138), (36, -66), (-36, -66)], "#FFFFFF", INK, 2.6)   # apron
        r.rrect(-12, -108, 12, -90, 4, "#FFE3EC", INK, 2)
    hands = f_arms(r, P, 30, -134, 40, 14, skin, hand=skin, sleeve=dress)
    held(r, hold, hands[1])
    for s in (-1, 1):
        r.ell(s * 34, -140, 14, 11, dress, INK, 2.6)                                      # puffed sleeves
    if granny:                                                                           # a shawl over the shoulders
        r.poly([(-46, -148), (46, -148), (54, -112), (0, -84), (-54, -112)], granny, INK, 3)
        r.line([(-30, -112), (0, -92), (30, -112)], darker(granny, 0.2), 2.4)
    if hood:                                                                             # the hood behind the head, the clasp at the neck
        r.ell(0, -179, 61, 57, hood, INK, 3.2)
        r.ell(0, -142, 46, 17, hood, INK, 3)
        r.dot(0, -138, 6.5, "#FFD21F")
    r.ell(0, -176, 45, 42, skin, INK, 3.2)                                               # head
    if hood:                                                                             # a little fringe under the hood
        for i, a in enumerate(range(-28, 29, 14)):
            r.ell(a * 0.9, -196 + abs(a) * 0.12, 12, 11, hair, INK, 2.6)
        r.arc(0, -176, 51, 49, 168, 372, INK, 20)                                        # the hood's rim around the face
        r.arc(0, -176, 51, 49, 168, 372, hood, 14.5)
    elif gramps:                                                                         # white tufts above the ears, bald on top
        for s in (-1, 1):
            r.ell(s * 44, -186, 14, 16, hair, INK, 2.6)
            r.ell(s * 47, -164, 11, 15, hair, INK, 2.6)
    elif granny:
        r.ell(0, -224, 20, 17, hair, INK, 3)                                             # the bun
        for i, a in enumerate(range(200, 341, 18)):
            r.ell(50 * math.cos(math.radians(a)) * 0.92, -176 + 46 * math.sin(math.radians(a)), 13, 12, hair, INK, 2.6)
        for s in (-1, 1):
            r.ell(s * 46, -168, 12, 16, hair, INK, 2.6)
    else:
        for i, a in enumerate(range(200, 341, 22)):                                      # curly fringe + top
            r.ell(52 * math.cos(math.radians(a)) * 0.92, -176 + 47 * math.sin(math.radians(a)), 14, 13, hair, INK, 2.8)
        for s in (-1, 1):
            r.ell(s * 49, -172, 14, 14, hair, INK, 2.8)
            r.ell(s * 53, -150, 13, 13, hair, INK, 2.8)
            r.ell(s * 49, -128, 13, 13, hair, INK, 2.8)
        r.poly([(-40, -190), (-10, -204), (30, -200), (42, -184), (28, -178), (10, -190), (-12, -184), (-34, -178)], hair, None)
        for a in range(0, 5):
            r.ell(-32 + a * 16, -192 + (a % 2) * 3, 10, 9, hair, None)
    sh = P.face * 3
    f_eyes(r, sh, -172, 17, 9.5, 12, P, pupil="#2A6FD4")
    f_cheeks(r, sh, -156, 29, "#FF9DB0", 8, 0)
    if gramps:                                                                           # bushy brows and a big white moustache
        for s in (-1, 1):
            r.ell(sh + s * 17, -192, 12, 5.5, hair, INK, 2.2)
            r.ell(sh + s * 10, -152, 14, 8, hair, INK, 2.4)
    f_mouth(r, sh, -145, P, 11)
    if granny:                                                                           # round glasses
        for s in (-1, 1):
            r.ell(sh + s * 17, -172, 14.5, 15, None, "#7A5A3A", 2.8)
        r.line([(sh - 3, -172), (sh + 3, -172)], "#7A5A3A", 2.6)
    return r


# ------------------------------------------------------------------------------------------------ gingerbread man
def ginger(c, x, y, k=1.0, t=0.0, P=None, dough="#C98A4B", icing="#FFF8EC", **_):
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k, k, P.face, P.lean, P.sq)
    light = mix(dough, "#FFFFFF", 0.2)
    for s in (-1, 1):                                                                    # stubby legs with white icing cuffs
        sw, lift = P.leg(s)
        hip, foot = (s * 20, -62), (s * 25 + sw, -16 - lift - (4 if P.sit else 0))
        r.limb(hip, foot, 25, dough)
        r.limb((hip[0] + (foot[0] - hip[0]) * 0.58, hip[1] + (foot[1] - hip[1]) * 0.58),
               (hip[0] + (foot[0] - hip[0]) * 0.8, hip[1] + (foot[1] - hip[1]) * 0.8), 27, icing, None, 0)
        r.ell(foot[0] + s * 4, foot[1] + 4, 19, 11, dough, INK, 2.8)
    r.rrect(-44, -148, 44, -50, 36, dough, INK, 3.2)                                     # the round, puffy body
    r.rrect(-34, -140, 28, -96, 24, light, None)
    for yy, col in ((-120, "#E2574C"), (-98, "#3DB54A"), (-76, "#3E8EDE")):             # three gumdrop buttons
        r.ell(0, yy, 8.2, 8.2, col, INK, 2)
        r.dot(-2.6, yy - 3, 2.4, "#FFFFFF")
    for s, ang in ((-1, P.arm_l), (1, P.arm_r)):                                         # arms with icing cuffs
        a = math.radians(ang)
        sx, sy = s * 42, -126
        ex, ey = sx + s * math.sin(a) * 44, sy + math.cos(a) * 44
        r.limb((sx, sy), (ex, ey), 23, dough)
        r.limb((sx + (ex - sx) * 0.58, sy + (ey - sy) * 0.58), (sx + (ex - sx) * 0.8, sy + (ey - sy) * 0.8), 25, icing, None, 0)
        r.ell(ex, ey, 14, 14, dough, INK, 2.8)
    for i in range(5):                                                                   # scalloped icing collar
        r.ell(-24 + i * 12, -142, 7.6, 6.6, icing, INK, 2)
    r.ell(0, -178, 57, 49, dough, INK, 3.2)                                              # head
    r.ell(-8, -187, 40, 30, light, None)
    sh = P.face * 4
    for dx in (-22, 0, 22):                                                              # icing dots on the forehead
        r.dot(sh + dx, -213 + abs(dx) * 0.14, 3.8, icing)
    f_eyes(r, sh * 1.5, -183, 22, 11, 13.5, P)
    f_cheeks(r, sh, -165, 39, "#FF9DB0", 9, P.puff)
    f_mouth(r, sh, -149, P, 14)
    return r


# ------------------------------------------------------------------------------------------------ billy goat
def goat(c, x, y, k=1.0, t=0.0, P=None, fur="#F5EFE0", scarf="#FF6B8B", horn="#E8D8A6", horns=1.0, **_):
    """A billy goat on two legs: curly horns (`horns` = their size), floppy ears, a pointy beard and a scarf with a little bell."""
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k, k, P.face, P.lean, P.sq)
    belly, hoof = mix(fur, "#FFFFFF", 0.55), "#5B4A44"
    beard = mix(fur, "#FFFFFF", 0.3) if sum(D.hex2rgb(fur)) < 480 else darker(fur, 0.12)
    for s in (-1, 1):                                                                    # legs with split hooves
        sw, lift = P.leg(s)
        hip, foot = (s * 21, -52), (s * 23 + sw, -13 - lift)
        r.limb(hip, foot, 21, fur)
        r.rrect(foot[0] - 13, foot[1] + 1, foot[0] + 13, foot[1] + 15, 6, hoof, INK, 2.6)
        r.line([(foot[0], foot[1] + 4), (foot[0], foot[1] + 14)], INK, 1.8)
    r.ell(-50, -88, 10, 17, fur, INK, 2.8, ang=-32)                                      # a little upturned tail
    r.ell(0, -98, 52, 54, fur, INK, 3.2)                                                 # body
    r.ell(0, -90, 32, 35, belly, None)
    f_arms(r, P, 46, -122, 40, 18, fur, hand=hoof)
    r.rrect(-40, -148, 40, -130, 9, scarf, INK, 3)                                       # the scarf and its bell
    r.poly([(14, -136), (40, -134), (47, -94), (27, -97)], scarf, INK, 3)
    r.dot(-24, -123, 8, "#FFD21F")
    r.dot(-26.5, -126, 3, "#FFF3B0")
    for s in (-1, 1):                                                                    # horns that sweep up and curl outward, behind the head
        pts = [(s * (24 + d * horns), -212 - u * horns) for d, u in ((0, 0), (5, 22), (15, 42), (30, 56), (48, 61), (63, 54))]
        wd = [19, 17, 15, 12.5, 10, 7.5]
        for i in range(len(pts) - 1):
            r.line([pts[i], pts[i + 1]], INK, wd[i] * (0.6 + 0.4 * horns ** 0.5) + 5)
        r.line([pts[-2], pts[-1]], INK, wd[-1] * (0.6 + 0.4 * horns ** 0.5) + 5)
        for i in range(len(pts) - 1):
            r.line([pts[i], pts[i + 1]], horn, wd[i] * (0.6 + 0.4 * horns ** 0.5))
        for i in (1, 2, 3):
            px, py = pts[i]
            r.line([(px - 5 * s, py + 4), (px + 5 * s, py - 4)], darker(horn, 0.3), 2)
    for s in (-1, 1):                                                                    # floppy ears
        r.ell(s * 60, -190, 25, 11.5, fur, INK, 3, ang=s * 20)
        r.ell(s * 61, -189, 15, 6, "#FFB3C7", None, ang=s * 20)
    sh = P.face * 4
    r.poly([(sh - 11, -142), (sh + 11, -142), (sh + 4, -108), (sh, -100), (sh - 4, -108)], beard, INK, 2.6)   # pointy beard
    r.ell(0, -182, 50, 49, fur, INK, 3.2)                                                # head
    r.ell(sh, -160, 29, 23, belly, INK, 2.8)                                             # muzzle
    r.ell(sh - 9, -168, 3.4, 5, hoof, None)
    r.ell(sh + 9, -168, 3.4, 5, hoof, None)
    f_eyes(r, sh * 1.5, -192, 22, 10.5, 12.5, P)
    f_cheeks(r, sh, -172, 41, "#FF9DB0", 8, P.puff)
    f_mouth(r, sh, -150, P, 11)
    return r


# ------------------------------------------------------------------------------------------------ troll
def troll(c, x, y, k=1.0, t=0.0, P=None, skin="#8CC063", tunic="#8A6A4A", hair="#4F7A3A", hold=None, **_):
    """A grumpy, lumpy troll: big flat feet, a round tummy in a patched tunic, pointy ears, wild hair, one bushy eyebrow and two tusks."""
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k, k, P.face, P.lean, P.sq)
    dark, nose = darker(skin, 0.2), mix(skin, "#F4F2A0", 0.4)
    for s in (-1, 1):                                                                    # thick legs, big flat feet
        sw, lift = P.leg(s)
        hip, foot = (s * 31, -66), (s * 35 + sw, -15 - lift)
        r.limb(hip, foot, 38, dark)
        r.ell(foot[0] + s * 5, foot[1] + 6, 31, 14, skin, INK, 2.8)
        for i in (-1, 0, 1):
            r.dot(foot[0] + s * 5 + i * 13, foot[1] + 13, 4.8, mix(skin, "#FFF6C8", 0.6))
    r.ell(0, -120, 77, 74, tunic, INK, 3.3)                                              # the tunic
    r.rrect(-48, -94, -22, -68, 3, "#B58A55", INK, 2.2)                                  # a patch, with stitches
    for i in range(3):
        r.line([(-46 + i * 11, -91), (-46 + i * 11, -86)], INK, 1.6)
    r.rrect(-74, -112, 74, -98, 5, "#C9A36A", INK, 2.6)                                  # a rope belt with a knot
    r.ell(10, -105, 11, 11, "#B58A55", INK, 2.4)
    hands = f_arms(r, P, 76, -150, 58, 32, skin, hand=dark)
    held(r, hold, hands[1])
    r.poly([(-46, -262), (-40, -300), (-24, -270), (-14, -312), (2, -272), (16, -308), (26, -268), (42, -298), (46, -258)], hair, INK, 3)   # wild hair
    for s in (-1, 1):                                                                    # big pointy ears
        r.poly([(s * 60, -228), (s * 102, -258), (s * 90, -206)], skin, INK, 3)
        r.poly([(s * 68, -228), (s * 92, -244), (s * 85, -215)], "#FFB3C7", None)
    r.ell(0, -214, 70, 58, skin, INK, 3.3)                                               # head
    for dx, dy, rr in ((-40, -240, 4.5), (47, -232, 3.8), (-54, -206, 3.4)):             # a few warts
        r.dot(dx, dy, rr, dark)
    sh = P.face * 5
    r.ell(sh * 1.3, -250, 46, 9, hair, INK, 2.6)                                          # one big bushy eyebrow
    f_eyes(r, sh * 1.4, -228, 27, 13, 15, P, white="#FFF9D0")
    r.ell(sh, -198, 26, 19, nose, INK, 3)                                                 # a big lumpy nose
    r.ell(sh - 8, -194, 4.2, 5.4, dark, None)
    r.ell(sh + 8, -194, 4.2, 5.4, dark, None)
    f_mouth(r, sh, -172, P, 22, teeth=True)
    for s in (-1, 1):                                                                    # two tusks
        r.poly([(sh + s * 20, -164), (sh + s * 13, -186), (sh + s * 8, -164)], "#FFFFFF", INK, 2.2)
    return r


# ------------------------------------------------------------------------------------------------ small helpers for Bibi's friends
def friend(c, which, x, y, k, t, mood="smile"):
    f = {"bibi": D.bibi, "pip": D.pip, "mo": D.mo, "lila": D.lila}[which]
    f(c, x, y, k, t=t, mood=mood, look=(4, -2))


CHARACTERS = {"pig": pig, "wolf": wolf, "bear": bear, "hare": hare, "tortoise": tortoise, "girl": girl, "ginger": ginger, "goat": goat, "troll": troll}
