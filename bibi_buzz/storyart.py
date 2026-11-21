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


def pose_for(name, t, phase=0.0, moving=False, amp=None, face=1, seed=0.0, speed=1.0, gesture=False):
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
        if gesture and not moving and name in ("idle", "talk"):      # alive even when standing still: breathing arms, a shift of weight, and while the voice is on the free arm talks with it
            P.arm_l = 14 + 2.4 * s(t * 1.7 + seed * 2.0)
            P.arm_r = 14 + 2.4 * s(t * 1.7 + seed * 2.0 + 1.3)
            P.lean = 1.0 * s(t * 0.8 + seed)
            if amp is not None:
                g = 0.5 + 0.5 * s(t * 3.3 + seed * 3.0)
                P.arm_r = 14 + 40 * amp * g
                P.arm_l = 14 + 16 * amp * (1.0 - g)
                P.lean += 2.0 * amp
                P.bob += 2.6 * amp * abs(s(t * 5.6 + seed))
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
    elif name == "dance":                                   # a waltz: sways from side to side with the arms out (partners use the same time, so they sway together)
        w = s(t * 2.2)
        P.dx, P.lean = w * 12, w * 5
        P.bob = abs(s(t * 2.2 + 0.8)) * 6
        P.arm_l, P.arm_r = 58 + w * 12, 58 - w * 12
        P.eyes, P.mouth = "happy", "smile"
    elif name == "sweep":                                   # sweeping the floor with a broom, eyes on the floor
        w = s(t * 3.0)
        P.dx, P.lean = w * 9, face * (3.0 + 2.0 * w)
        P.arm_l, P.arm_r = 34 + w * 5, 40 + w * 5
        P.look = (face * 2.0, 5.0)
        P.mouth = "smile"
    elif name == "angry":                                   # stamping with fury: a scowl, clenched arms, a quick stamp-stamp
        P.eyes, P.mouth, P.mouth_amt = "angry", "open", 0.45
        P.arm_l = P.arm_r = 18
        P.bob = abs(s(t * 8 + seed)) * 7
        P.dx = s(t * 21) * 2.4
    elif name == "stitch":                                  # sewing: the arm goes up and down with the needle, eyes on the work
        P.arm_r = 95 + s(t * 7 + seed) * 38
        P.look = (3, 4)
        P.mouth = "smile"
        P.bob = 1.6 * s(t * 2.4 + seed) + abs(s(t * 3.5 + seed)) * 2
    elif name == "curtsy":                                  # a little curtsy: dips down and up again, the skirt widens a bit
        w = 0.5 - 0.5 * math.cos(t * 3.0)
        P.sq = 1.0 - 0.09 * w
        P.arm_l = P.arm_r = 46 + 10 * w
        P.eyes, P.mouth = "happy", "smile"
        P.bob = 0.0
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


def star_pts(cx, cy, ro, ri=None, n=5):
    """The corners of an n-pointed star (one point up) around (cx, cy)."""
    ri = ri if ri is not None else ro * 0.45
    pts = []
    for i in range(n * 2):
        ang = math.radians(-90.0 + 180.0 * i / n)
        rr = ro if i % 2 == 0 else ri
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    return pts


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
    elif kind == "crook":                                                                # a shepherd's staff: a long wooden stick with a curled top
        r.line([(hx, hy + 52), (hx, hy - 132)], INK, 9)
        r.line([(hx, hy + 52), (hx, hy - 132)], "#A8703A", 5.6)
        r.arc(hx + 15, hy - 132, 15, 15, 180, 420, INK, 9)
        r.arc(hx + 15, hy - 132, 15, 15, 180, 420, "#A8703A", 5.6)
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
    elif kind == "stone":                                                                # a smooth, round stone
        r.ell(hx, hy - 8, 19, 14, "#9EA7B3", INK, 2.6, ang=-8)
        r.ell(hx - 6, hy - 13, 7, 3.6, "#CDD3DB", None, ang=-20)
    elif kind == "pot":                                                                  # the little magic pot (black, with a golden star)
        for sx in (-1, 1):
            r.arc(hx + sx * 33, hy - 33, 10, 11, -90 if sx > 0 else 90, 90 if sx > 0 else 270, INK, 5)
        r.ell(hx, hy - 26, 32, 27, "#34344A", INK, 3.0)
        r.rrect(hx - 30, hy - 53, hx + 30, hy - 41, 4, "#24243A", INK, 2.6)
        r.ell(hx, hy - 53, 26, 5, "#FFF0C2", INK, 1.8)
        r.poly(star_pts(hx, hy - 26, 14, 6), "#FFD21F", INK, 2.0)
        r.ell(hx - 18, hy - 35, 5, 9, "#6A6A86", None, ang=20)
    elif kind == "bowl":                                                                 # a bowl of porridge with a spoon in it
        r.line([(hx + 8, hy - 44), (hx + 31, hy - 80)], "#C98A52", 5.2)
        r.ell(hx + 33, hy - 85, 6.5, 9, "#D9A066", INK, 2.0, ang=-30)
        r.poly([(hx + 32 * math.cos(math.radians(a)), hy - 30 + 26 * math.sin(math.radians(a))) for a in range(0, 181, 15)], "#6CB7FF", INK, 2.8)
        r.line([(hx - 25, hy - 18), (hx + 25, hy - 18)], "#FFFFFF", 2.6)
        r.ell(hx, hy - 30, 32, 9, "#EAF4FF", INK, 2.6)
        r.poly([(hx - 26, hy - 31), (hx - 19, hy - 43), (hx - 6, hy - 50), (hx + 6, hy - 50), (hx + 19, hy - 43), (hx + 26, hy - 31)], "#FFF8E1", INK, 2.4)
        r.ell(hx - 8, hy - 42, 7.5, 3, "#FFFFFF", None, ang=-15)
    elif kind == "club":                                                                 # the troll's big, knobbly stick
        r.line([(hx, hy + 16), (hx + 12, hy - 92)], INK, 22)
        r.line([(hx, hy + 16), (hx + 12, hy - 92)], "#8B5A2B", 15)
        r.ell(hx + 15, hy - 112, 25, 36, "#8B5A2B", INK, 3, ang=8)
        r.ell(hx + 8, hy - 122, 8, 13, "#B07B45", None, ang=8)
        for dx, dy in ((-12, -104), (30, -100), (4, -134)):
            r.dot(hx + 15 + dx, hy + dy, 3.6, "#C9A36A")
    elif kind == "wand":                                                                 # a fairy wand with a golden star on top
        r.line([(hx - 4, hy + 8), (hx + 26, hy - 60)], INK, 8.5)
        r.line([(hx - 4, hy + 8), (hx + 26, hy - 60)], "#F4EBFF", 5)
        r.poly(star_pts(hx + 29, hy - 76, 21, 9), "#FFD21F", INK, 2.6)
        r.poly(star_pts(hx + 28, hy - 77, 10, 4.5), "#FFF6BF", None)
    elif kind == "broom":                                                                # a straw broom that reaches the floor
        r.line([(hx + 12, hy - 96), (hx - 10, hy + 88)], INK, 9)
        r.line([(hx + 12, hy - 96), (hx - 10, hy + 88)], "#9A6A3A", 5.4)
        r.poly([(hx - 28, hy + 62), (hx + 6, hy + 66), (hx + 22, hy + 100), (hx - 44, hy + 94)], "#E3B857", INK, 2.6)
        r.rrect(hx - 30, hy + 60, hx + 8, hy + 72, 3, "#C9482F", INK, 2.2)
        for i in range(4):
            r.line([(hx - 30 + i * 9, hy + 76), (hx - 38 + i * 12, hy + 96)], "#C79A3F", 2)
    elif kind == "scroll":                                                               # a rolled invitation with a red ribbon
        r.rrect(hx - 34, hy - 26, hx + 34, hy - 4, 9, "#FFF4D6", INK, 2.6)
        r.ell(hx - 34, hy - 15, 6, 11, "#F2DFAE", INK, 2.2)
        r.ell(hx + 34, hy - 15, 6, 11, "#F2DFAE", INK, 2.2)
        r.rrect(hx - 7, hy - 28, hx + 7, hy - 2, 2, "#E2574C", INK, 2)
    elif kind == "apple":                                                                # one big, shiny red apple with a stalk and a leaf
        r.ell(hx - 7, hy - 21, 17, 19, "#E2362F", INK, 2.8)
        r.ell(hx + 8, hy - 21, 17, 19, "#E2362F", INK, 2.8)
        r.ell(hx, hy - 20, 22, 18, "#E2362F", None)
        r.ell(hx - 11, hy - 28, 5.5, 9, "#FF9C94", None, ang=24)
        r.line([(hx, hy - 38), (hx + 3, hy - 50)], "#6B4423", 4.2)
        r.ell(hx + 14, hy - 50, 11, 5.2, "#3DB54A", INK, 2, ang=-24)
    elif kind == "apples":                                                               # a basket piled high with red apples
        r.arc(hx, hy - 10, 25, 34, 180, 360, "#9B5C2E", 4.5)
        for ax, ay in ((-15, -26), (14, -27), (-1, -35), (-26, -17), (26, -16)):
            r.dot(hx + ax, hy + ay, 12.5, "#E2362F")
            r.dot(hx + ax - 4, hy + ay - 4, 3.6, "#FF9C94")
        r.rrect(hx - 29, hy - 12, hx + 29, hy + 22, 8, "#D9A066", INK, 2.4)
        r.line([(hx - 29, hy + 4), (hx + 29, hy + 4)], "#B8733A", 2)
        for i in range(3):
            r.line([(hx - 16 + i * 16, hy - 10), (hx - 16 + i * 16, hy + 20)], "#B8733A", 1.8)
    elif kind == "pickaxe":                                                              # a miner's pickaxe: a wooden handle and a curved iron head
        r.line([(hx - 6, hy + 16), (hx + 16, hy - 86)], INK, 12)
        r.line([(hx - 6, hy + 16), (hx + 16, hy - 86)], "#A5703A", 7)
        r.poly([(hx - 34, hy - 70), (hx - 8, hy - 91), (hx + 16, hy - 95), (hx + 42, hy - 91), (hx + 66, hy - 70), (hx + 44, hy - 79), (hx + 16, hy - 80), (hx - 12, hy - 79)], "#B7C0CE", INK, 2.8)
        r.poly([(hx - 8, hy - 91), (hx + 16, hy - 95), (hx + 42, hy - 91), (hx + 16, hy - 87)], "#E4EAF2", None)
    elif kind == "box":                                                                  # a shoe box tied with a red ribbon
        r.rrect(hx - 36, hy - 40, hx + 36, hy + 2, 5, "#F2D9A6", INK, 2.6)
        r.rrect(hx - 40, hy - 52, hx + 40, hy - 38, 4, "#E8C07A", INK, 2.4)
        r.rrect(hx - 7, hy - 52, hx + 7, hy + 2, 2, "#E2362F", None)
        r.ell(hx - 12, hy - 58, 11, 7, "#E2362F", INK, 2.0, ang=-20)
        r.ell(hx + 12, hy - 58, 11, 7, "#E2362F", INK, 2.0, ang=20)
        r.dot(hx, hy - 55, 3.6, "#B01E18")
    elif kind == "hammer":                                                               # a little cobbler's hammer: a wooden handle and an iron head
        r.line([(hx - 2, hy + 10), (hx + 14, hy - 46)], INK, 9.5)
        r.line([(hx - 2, hy + 10), (hx + 14, hy - 46)], "#B8733A", 5.6)
        r.rrect(hx - 8, hy - 66, hx + 42, hy - 42, 5, "#8F9CB0", INK, 2.8)
        r.rrect(hx - 4, hy - 62, hx + 36, hy - 54, 3, "#D6DEEA", None)
    elif kind == "needle":                                                               # a big shiny needle with a loop of red thread
        r.arc(hx + 34, hy - 38, 20, 28, -30, 150, "#E2362F", 3.4)
        r.line([(hx - 8, hy + 10), (hx + 22, hy - 74)], INK, 6.5)
        r.line([(hx - 8, hy + 10), (hx + 22, hy - 74)], "#E4EAF2", 3.2)
        r.ell(hx + 21, hy - 69, 3, 6.4, "#FFFFFF", INK, 1.8, ang=-20)
    elif kind == "sack":                                                                 # a sack of wheat / flour with a red string round its neck
        r.ell(hx, hy - 30, 32, 38, "#E7D7AE", INK, 2.8)
        r.poly([(hx - 15, hy - 64), (hx + 15, hy - 64), (hx + 22, hy - 82), (hx + 6, hy - 74), (hx - 6, hy - 85), (hx - 21, hy - 76)], "#E7D7AE", INK, 2.4)
        r.line([(hx - 15, hy - 64), (hx + 15, hy - 64)], "#C9482F", 4.2)
        r.ell(hx - 9, hy - 36, 11, 7, "#FFFFFF", None, ang=-25)
    elif kind == "sheaf":                                                                # a tied sheaf of golden wheat
        for i in range(8):
            lean = (i - 3.5) * 3.2
            r.line([(hx + (i - 3.5) * 2.2, hy + 6), (hx + lean * 1.8, hy - 96)], INK, 6.6)
            r.line([(hx + (i - 3.5) * 2.2, hy + 6), (hx + lean * 1.8, hy - 96)], "#E9B93F", 3.8)
        for i in range(8):
            lean = (i - 3.5) * 3.2
            r.ell(hx + lean * 1.8, hy - 112, 7.4, 19, "#F0BE44", INK, 2, ang=lean * 1.5)
        r.rrect(hx - 24, hy - 46, hx + 24, hy - 34, 4, "#E2362F", INK, 2.4)
    elif kind == "sickle":                                                               # a little curved blade on a wooden handle
        r.line([(hx - 2, hy + 8), (hx + 8, hy - 42)], INK, 11)
        r.line([(hx - 2, hy + 8), (hx + 8, hy - 42)], "#B8733A", 6.4)
        r.poly([(hx + 4, hy - 44), (hx + 34, hy - 70), (hx + 62, hy - 60), (hx + 70, hy - 40), (hx + 52, hy - 54), (hx + 32, hy - 56), (hx + 14, hy - 38)], "#C9D2DE", INK, 2.6)
    elif kind == "loaf":                                                                 # a hot loaf of bread on a white plate, with a little steam
        r.ell(hx, hy - 8, 58, 11, "#FFFFFF", INK, 2.6)
        r.ell(hx, hy - 30, 44, 26, "#C97A2E", INK, 2.8)
        r.ell(hx, hy - 35, 38, 19, "#E8A24A", None)
        for i in range(3):
            r.line([(hx - 19 + i * 19, hy - 48), (hx - 8 + i * 19, hy - 31)], "#A85E1E", 2.8)
        for i in range(2):
            r.line([(hx - 12 + i * 24 + 5 * math.sin(j * 1.6 + i), hy - 58 - j * 11) for j in range(4)], "#FFFFFF", 3.4)
    elif kind == "dough":                                                                # a pink mixing bowl with a soft ball of dough and a wooden spoon
        r.line([(hx + 10, hy - 36), (hx + 34, hy - 76)], "#C98A52", 5.4)
        r.ell(hx + 36, hy - 81, 7, 10, "#D9A066", INK, 2, ang=-30)
        r.poly([(hx + 34 * math.cos(math.radians(a)), hy - 30 + 26 * math.sin(math.radians(a))) for a in range(0, 181, 15)], "#FF6B8B", INK, 2.8)
        r.ell(hx, hy - 30, 34, 9, darker("#FF6B8B", 0.1), INK, 2.4)
        r.ell(hx, hy - 40, 26, 17, "#FFF4DA", INK, 2.4)
        r.ell(hx - 8, hy - 46, 8, 4, "#FFFFFF", None, ang=-15)
    elif kind in ("slipper", "cushion"):                                                 # a glass slipper (on a red velvet cushion with tassels)
        if kind == "cushion":
            r.rrect(hx - 44, hy - 24, hx + 44, hy - 4, 10, "#D93A52", INK, 2.8)
            r.rrect(hx - 36, hy - 21, hx + 30, hy - 16, 3, "#EF6D82", None)
            for sx in (-1, 1):
                r.dot(hx + sx * 44, hy - 4, 5.2, "#FFD21F")
        base = hy - 24 if kind == "cushion" else hy - 4
        sh_pts = [(-30, 0), (-31, -26), (-24, -37), (-11, -35), (-5, -23), (9, -17), (25, -14), (36, -8), (38, 0)]      # a high-heeled shoe, seen from the side
        r.rrect(hx - 36, base - 2, hx - 24, base + 9, 3, "#BFE6FF", INK, 2.4)                    # the heel
        r.poly([(hx + 1.25 * px + 4, base - 2 + 1.25 * py) for px, py in sh_pts], "#BFE6FF", INK, 2.8)
        r.poly([(hx + 1.25 * px + 4, base - 2 + 1.25 * py) for px, py in ((-28, -4), (-29, -24), (-23, -33), (-14, -30), (-17, -12))], "#E6F6FF", None)
        r.dot(hx + 30, base - 14, 4, "#FF8FB8")                                                  # a little pink gem on the toe
        r.poly(star_pts(hx + 20, base - 40, 10, 4, 4), "#FFFFFF", None)


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
    elif kind == "pointy":                                                               # a tall, floppy pointed cap (a dwarf's) with a pompom at the bent tip
        col = color or "#E2574C"
        r.poly([(-46, y + 10), (46, y + 10), (32, y - 34), (16, y - 70), (-8, y - 94), (-38, y - 100), (-52, y - 86), (-30, y - 74), (-22, y - 44), (-36, y - 16)], col, INK, 3)
        r.poly([(-46, y + 10), (46, y + 10), (43, y - 6), (-43, y - 6)], darker(col, 0.14), INK, 2.6)
        r.dot(-52, y - 88, 9.5, "#FFFFFF")
        r.ell(14, y - 36, 6, 18, mix(col, "#FFFFFF", 0.35), None, ang=-18)


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
def wolf(c, x, y, k=1.0, t=0.0, P=None, fur="#8E9AB0", scarf=None, cap=None, glasses=False, hold=None, **_):
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
    hands = f_arms(r, P, 46, -142, 52, 20, fur, hand=dark)
    held(r, hold, hands[1])
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
def girl(c, x, y, k=1.0, t=0.0, P=None, dress="#6CB7FF", hair="#FFC83D", hold=None, hood=None, granny=None, gramps=None,
         gown=None, prince=None, wings=None, hat_kind=None, hat_color=None, shoe=None, beard=None, boy=None, **_):
    """A person. dress/hair = colours; hood = red riding hood; granny = a shawl and a bun; gramps = a grandpa's cardigan; gown = a sparkly ball gown
    with glass slippers; prince = a prince's coat, white tights and short hair; wings = fairy wings; hat_kind / hat_color = a hat() on top of the head;
    shoe = the colour of the shoes (a gown wears glass slippers unless the shoes are given); beard = the colour of a long, bushy beard (a dwarf's);
    boy = a village boy: a simple tunic in that colour with a belt, brown trousers, boots and short hair."""
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k + P.lower * k, k, P.face, P.lean, P.sq)
    skin = "#FFDDBF"
    if wings:                                                                            # fairy wings behind everything
        for s in (-1, 1):
            r.ell(s * 62, -158, 30, 66, wings, INK, 3, ang=s * 24)
            r.ell(s * 54, -112, 20, 42, mix(wings, "#FFFFFF", 0.35), INK, 2.6, ang=s * 56)
            r.ell(s * 66, -170, 9, 36, "#FFFFFF", None, ang=s * 24)
    for s in (-1, 1):                                                                    # legs, socks, shoes
        sw, lift = P.leg(s)
        hip, foot = (s * 17, -58), (s * 18 + sw, -14 - lift)
        if P.sit:
            foot = (s * 30, -30)
        if gramps:                                                                       # brown trousers and sturdy shoes
            r.limb(hip, foot, 20, "#7A5A3A", INK, 2.6)
            r.ell(foot[0] + s * 2, foot[1] + 22, 19, 10, "#3B2A1E", INK, 2.6)
            continue
        if boy:                                                                          # brown trousers and boots
            r.limb(hip, foot, 17, "#8A6238", INK, 2.6)
            r.ell(foot[0] + s * 2, foot[1] + 22, 19, 10, "#4A3020", INK, 2.6)
            continue
        if prince:                                                                       # white tights and dark boots
            r.limb(hip, foot, 17, "#F2F2F8", INK, 2.6)
            r.ell(foot[0] + s * 2, foot[1] + 22, 19, 10, "#3B2A1E", INK, 2.6)
            continue
        r.limb(hip, foot, 14, skin)
        r.limb((foot[0], foot[1] + 6), (foot[0], foot[1] + 18), 15, "#FFFFFF", INK, 2.4)
        r.ell(foot[0] + s * 2, foot[1] + 22, 17, 9, shoe or ("#BFE6FF" if gown else "#E2574C"), INK, 2.6)     # (glass slippers with a ball gown)
        if gown and not shoe:
            r.ell(foot[0] + s * 2 - 5, foot[1] + 19, 6, 2.4, "#FFFFFF", None)
    if not hood and not granny and not gramps and not prince and not boy:
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
    elif gown:                                                                           # a ball gown: a snug top, a wide bell skirt, a golden sash
        dress = gown
        r.poly([(-26, -140), (26, -140), (106, -50), (-106, -50)], dress, INK, 3.2)
        r.poly([(-26, -140), (26, -140), (30, -112), (-30, -112)], mix(dress, "#FFFFFF", 0.22), None)
        r.ell(0, -50, 106, 11, darker(dress, 0.1), INK, 2.6)
        for sx, sy, sr in ((-74, -64, 7), (-38, -82, 5), (8, -66, 7), (46, -90, 5), (76, -62, 6), (-10, -98, 5), (-58, -60, 5), (30, -70, 4)):
            r.poly(star_pts(sx, sy, sr, sr * 0.4, 4), "#FFFFFF", None)                    # glitter on the skirt
        r.rrect(-29, -118, 29, -106, 5, "#FFD21F", INK, 2.4)
        r.dot(0, -112, 5.5, "#FFF1A0")
    elif prince:                                                                         # a coat with golden buttons, a frilly collar and golden shoulders
        dress = prince
        r.poly([(-30, -142), (30, -142), (44, -58), (-44, -58)], dress, INK, 3.2)
        r.poly([(-13, -142), (13, -142), (0, -100)], "#FFFFFF", INK, 2.4)
        r.line([(0, -100), (0, -60)], darker(dress, 0.25), 2.6)
        for yy in (-94, -80, -66):
            r.dot(0, yy, 4.2, "#FFD21F")
        r.rrect(-42, -86, 42, -76, 3, "#FFD21F", INK, 2.2)
        r.ell(0, -58, 44, 8, darker(dress, 0.1), INK, 2.6)
    elif boy:                                                                            # a simple tunic with a belt and a little buckle
        dress = boy
        r.poly([(-28, -142), (28, -142), (44, -62), (-44, -62)], dress, INK, 3.2)
        r.poly([(-13, -142), (13, -142), (0, -118)], mix(dress, "#FFFFFF", 0.55), INK, 2.2)
        r.rrect(-44, -96, 44, -83, 3, "#8B5A2B", INK, 2.4)
        r.rrect(-7, -97, 7, -82, 2, "#FFD21F", INK, 2)
        r.ell(0, -62, 44, 8, darker(dress, 0.1), INK, 2.6)
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
    elif prince or boy:                                                                  # short, neat hair with a little quiff
        for a in range(195, 346, 25):
            r.ell(50 * math.cos(math.radians(a)) * 0.92, -176 + 46 * math.sin(math.radians(a)), 14, 13, hair, INK, 2.6)
        r.ell(14, -220, 26, 13, hair, INK, 2.8, ang=-10)
        for s in (-1, 1):
            r.ell(s * 45, -178, 10, 17, hair, INK, 2.6)
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
    if beard:                                                                            # a long, bushy beard that hides the chin, with a few wavy strands
        r.poly([(-43, -164), (43, -164), (50, -138), (41, -112), (17, -88), (0, -83), (-17, -88), (-41, -112), (-50, -138)], beard, INK, 3.2)
        for bx, by in ((-27, -126), (-6, -110), (15, -112), (28, -128)):
            r.line([(bx, by), (bx + 3, by + 17)], darker(beard, 0.16), 2.2)
        r.ell(-26, -134, 8, 14, mix(beard, "#FFFFFF", 0.65), None, ang=14)
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
    if hat_kind:
        hat(r, hat_kind, -216, hat_color)
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


# ------------------------------------------------------------------------------------------------ the magic mirror
def mirror(c, x, y, k=1.0, t=0.0, P=None, frame="#FFD21F", glass="#BFD9FF", mist="#EEF6FF", **_):
    """The magic mirror: a tall oval in a golden frame set with jewels, standing on two curly feet, with a kind misty face that talks in the shiny glass."""
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k, k, P.face, P.lean, P.sq)
    for s in (-1, 1):                                                                    # two curly feet and the stand
        r.ell(s * 50, -9, 32, 10, frame, INK, 3)
        r.ell(s * 76, -19, 10, 9, frame, INK, 2.6)
    r.rrect(-28, -62, 28, -16, 7, darker(frame, 0.1), INK, 3)
    r.ell(0, -216, 114, 170, darker(frame, 0.1), INK, 3.6)                               # the golden frame, a thick oval ...
    r.ell(0, -216, 106, 162, frame, None)
    for i in range(12):                                                                  # ... with round jewels all the way round
        a = math.radians(i * 30 + 15)
        r.dot(110 * math.cos(a), -216 + 166 * math.sin(a), 8, ("#FF5C8A", "#5FD8C2", "#FFFFFF")[i % 3])
    r.poly(star_pts(0, -404, 31, 13), "#FFE98A", INK, 3)                                 # a star on top
    r.ell(0, -216, 88, 142, glass, INK, 3)                                               # the glass, with two shiny arcs
    r.arc(0, -216, 76, 128, 198, 252, "#FFFFFF", 6)
    r.arc(0, -216, 76, 128, 262, 280, "#FFFFFF", 4)
    for i, (sx, sy, sr) in enumerate(((-52, -300, 8), (58, -150, 6), (50, -296, 5), (-58, -140, 7))):         # twinkling stars in the glass
        tw = 0.7 + 0.3 * math.sin(t * 3.1 + i * 1.7)
        r.poly(star_pts(sx, sy, sr * tw, sr * tw * 0.4, 4), "#FFFFFF", None)
    r.ell(0, -214, 56, 76, mist, None)                                                   # a misty face
    sh = P.face * 3
    f_eyes(r, sh, -236, 24, 11, 14, P, pupil="#3E6FD4")
    f_cheeks(r, sh, -208, 36, "#FFB3C7", 9, 0)
    f_mouth(r, sh, -188, P, 15)
    return r


# ------------------------------------------------------------------------------------------------ hen
def hen(c, x, y, k=1.0, t=0.0, P=None, feathers="#E4573D", comb="#E2362F", apron=None, hold=None, **_):
    """A hen on two legs: a round, fluffy body with a fan of tail feathers, two wings that act as arms, a big head with a red comb and wattle,
    and a pointy orange beak that opens when she speaks. `apron` = the colour of a little apron."""
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k + min(P.lower, 0.0) * k, k, P.face, P.lean, P.sq)   # "@70" lifts her onto a stool; "sit" does not sink her through the floor
    dark, light, beak, leg = darker(feathers, 0.22), mix(feathers, "#FFE9C8", 0.55), "#FFA11F", "#F29A2E"
    sh = 5
    for s in (-1, 1):                                                                    # thin orange legs and three-toed feet
        sw, lift = P.leg(s)
        hip, foot = (s * 17, -44), (s * 19 + sw, -9 - lift)
        r.limb(hip, foot, 8, leg)
        for tx in (-15, 0, 15):
            r.line([(foot[0], foot[1] + 1), (foot[0] + tx, foot[1] + 8)], INK, 8.4)
        for tx in (-15, 0, 15):
            r.line([(foot[0], foot[1] + 1), (foot[0] + tx, foot[1] + 8)], leg, 4.2)
    for i, a in enumerate((58, 34, 10)):                                                 # a fan of three tail feathers
        sway = 3 * math.sin(t * 2.4 + i)
        r.ell(-48 - 11 * math.sin(math.radians(a)) * 2.2, -108 - 30 * math.cos(math.radians(a)), 13, 36, (dark, feathers, light)[i], INK, 3, ang=-(a + sway))
    r.ell(0, -88, 54, 50, feathers, INK, 3.2)                                            # the round body
    r.ell(7, -80, 34, 34, light, None)
    for i in range(3):                                                                   # little feather scallops on the belly
        r.arc(-6 + i * 14, -84 + (i % 2) * 8, 8, 6, 20, 160, mix(light, dark, 0.35), 2.2)
    if apron:
        r.poly([(-27, -122), (27, -122), (40, -54), (-40, -54)], apron, INK, 3)
        r.rrect(-14, -88, 14, -68, 4, darker(apron, 0.1), INK, 2)
        r.dot(0, -108, 6, "#FF7AA8")
    hands = []
    for s, ang in ((-1, P.arm_l), (1, P.arm_r)):                                         # the wings are the arms
        a = math.radians(ang)
        sx, sy, L = s * 44, -108, 46
        ex, ey = sx + s * math.sin(a) * L, sy + math.cos(a) * L
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        r.ell(mx, my, 17, 31, dark, INK, 3, ang=-s * ang)
        r.ell(mx - s * 2, my - 3, 9, 20, mix(dark, "#FFFFFF", 0.22), None, ang=-s * ang)
        hands.append((ex, ey))
    held(r, hold, hands[1])
    for dx, dy, rr in ((-16, -200, 11), (7, -210, 14.5), (29, -199, 11)):               # the red comb on top
        r.ell(dx, dy, rr, rr * 1.15, comb, INK, 3)
    r.ell(5, -160, 45, 41, feathers, INK, 3.2)                                           # the head
    r.ell(sh, -150, 30, 22, light, None)
    op = 0.0
    if P.mouth in ("open", "wow", "grin"):
        op = 3 + 10 * (P.mouth_amt if P.mouth_amt is not None else 0.4)
    r.ell(sh, -126 + op * 0.8, 8, 11, comb, INK, 2.2)                                    # the wattle
    if op > 0.5:                                                                          # the mouth is open: dark inside, the lower beak drops
        r.poly([(sh - 11, -149), (sh + 11, -149), (sh + 8, -140 + op), (sh - 8, -140 + op)], "#7A1F2E", INK, 2)
    r.poly([(sh - 10, -148 + op), (sh + 10, -148 + op), (sh + 6, -138 + op), (sh, -134 + op), (sh - 6, -138 + op)], darker(beak, 0.08), INK, 2.4)
    r.poly([(sh - 15, -160), (sh + 15, -160), (sh + 10, -148), (sh, -143), (sh - 10, -148)], beak, INK, 2.6)
    r.line([(sh - 9, -148), (sh + 9, -148)], darker(beak, 0.3), 1.8)
    f_eyes(r, sh * 1.4, -170, 21, 10.5, 13, P)
    f_cheeks(r, sh, -148, 38, "#FF8A6B", 8, P.puff)
    return r


# ------------------------------------------------------------------------------------------------ chick
def chick(c, x, y, k=1.0, t=0.0, P=None, fur="#FFD84A", **_):
    """A fluffy little chick: one big round yellow ball with a tuft on top, tiny wings, orange legs and a small beak that peeps."""
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k + min(P.lower, 0.0) * k, k, P.face, P.lean, P.sq)
    belly, beak, leg = mix(fur, "#FFFFFF", 0.5), "#FF9A1F", "#F29A2E"
    sh = 4
    for s in (-1, 1):
        sw, lift = P.leg(s)
        foot = (s * 15 + sw * 0.6, -6 - lift * 0.6)
        r.limb((s * 14, -24), foot, 6, leg)
        r.ell(foot[0] + s * 3, foot[1] + 1, 13, 5.5, leg, INK, 2.2)
    r.ell(0, -54, 47, 45, fur, INK, 3.2)
    r.ell(0, -40, 29, 25, belly, None)
    for s, ang in ((-1, P.arm_l), (1, P.arm_r)):                                         # tiny wings
        a = math.radians(ang)
        sx, sy, L = s * 43, -50, 20
        ex, ey = sx + s * math.sin(a) * L, sy + math.cos(a) * L
        r.ell((sx + ex) / 2, (sy + ey) / 2, 9.5, 17, darker(fur, 0.1), INK, 2.6, ang=-s * ang)
    for i, (dx, rot) in enumerate(((-7, -22), (0, 0), (7, 22))):                         # a tuft of three feathers
        r.ell(dx, -101 - (4 if i == 1 else 0), 4.6, 12, fur, INK, 2.2, ang=rot)
    f_eyes(r, sh * 1.2, -62, 16, 8.5, 10.5, P)
    f_cheeks(r, sh, -46, 30, "#FF9A8A", 6.5, P.puff)
    op = 0.0
    if P.mouth in ("open", "wow", "grin"):
        op = 2 + 6 * (P.mouth_amt if P.mouth_amt is not None else 0.4)
    if op > 0.5:
        r.ell(sh, -41 + op * 0.4, 7, 3 + op * 0.55, "#7A1F2E", INK, 1.8)
    r.poly([(sh - 10, -52), (sh + 10, -52), (sh + 6, -43), (sh, -38), (sh - 6, -43)], beak, INK, 2.2)
    return r


# ------------------------------------------------------------------------------------------------ critters: cat, dog, mouse, lion, fox, sheep, cow
CRITTERS = {"cat": ("#F5A04A", "#FFF1DC"), "dog": ("#C98A52", "#FFF1DC"), "mouse": ("#B8B8C8", "#F6F0F6"), "lion": ("#EBA83F", "#FFEBBE"),
            "fox": ("#E2762E", "#FFF4E8"), "sheep": ("#3F3636", "#FFFFFF"), "cow": ("#FFFFFF", "#FFC4CF")}


def _band_of(v, v0, v1, n):
    return min(n - 1, max(0, int((v - v0) / (v1 - v0) * n)))


def _ell_stripes(r, cx, cy, rx, ry, colors, across="y"):
    """An ellipse (local units) filled with stripes of the given colours and no outline: across="y" = bands from top to bottom, "x" = from left to right."""
    n = len(colors)
    for i, col in enumerate(colors):
        pa, pb = [], []
        for j in range(7):
            u = j / 6.0
            if across == "y":
                y = cy - ry + 2 * ry * (i + u * (1.0 + (0.04 if i < n - 1 else 0.0))) / n
                w = rx * math.sqrt(max(0.0, 1 - ((y - cy) / ry) ** 2))
                pa.append((cx - w, y))
                pb.append((cx + w, y))
            else:
                x = cx - rx + 2 * rx * (i + u * (1.0 + (0.04 if i < n - 1 else 0.0))) / n
                h = ry * math.sqrt(max(0.0, 1 - ((x - cx) / rx) ** 2))
                pa.append((x, cy - h))
                pb.append((x, cy + h))
        r.poly(pa + pb[::-1], col, None)


def critter(c, x, y, k=1.0, t=0.0, P=None, species="cat", fur=None, belly=None, accent=None, stripes=False, patch=None, apron=None, bow=None, hold=None, wool=None, **_):
    """One kit for seven furry friends on two legs (species = cat, dog, mouse, lion, fox, sheep or cow): the same round body, arms and face, with
    their own ears, muzzle, tail and extras. fur / belly = colours; accent = the colour of a lion's mane or of a cow's spots; stripes = tabby stripes;
    patch = a dog's eye patch; apron = a little apron; bow = a bow on the head."""
    P = P or Pose()
    r = Rig(c, x + P.dx * k, y - P.bob * k + min(P.lower, 0.0) * k, k, P.face, P.lean, P.sq)
    f0, b0 = CRITTERS[species]
    fur, belly = fur or f0, belly or b0
    wools = [wool] if isinstance(wool, str) else list(wool or ["#FFFFFF"])             # a sheep's wool: one colour, or a list of colours (a rainbow)
    dark = darker(fur, 0.28)
    sh = 3
    sway = math.sin(t * 2.4)
    legc = fur if species != "cow" else "#FFFFFF"
    if species == "cat":                                                                 # --- the tail, behind everything
        r.line([(-34, -66), (-70, -70), (-88, -100), (-82 + 5 * sway, -140)], INK, 18)
        r.line([(-34, -66), (-70, -70), (-88, -100), (-82 + 5 * sway, -140)], fur, 12)
    elif species == "dog":
        r.limb((-36, -72), (-62 + 9 * math.sin(t * 8.0), -100), 13, fur)
    elif species == "mouse":
        r.line([(-34, -60), (-72, -46), (-100, -66), (-114 + 4 * sway, -104)], INK, 9)
        r.line([(-34, -60), (-72, -46), (-100, -66), (-114 + 4 * sway, -104)], "#F2A5B5", 4.6)
    elif species == "lion":
        r.line([(-34, -66), (-72, -60), (-94, -88)], INK, 13)
        r.line([(-34, -66), (-72, -60), (-94, -88)], fur, 7.4)
        r.ell(-98, -94, 15, 19, accent or "#B5651D", INK, 2.8, ang=30)
    elif species == "fox":
        r.ell(-64, -90, 42, 25, fur, INK, 3.2, ang=-38)
        r.ell(-90, -108, 18, 15, "#FFFFFF", INK, 2.6, ang=-38)
    elif species == "sheep":
        r.ell(-42, -80, 15, 15, wools[-1], INK, 2.8)
    elif species == "cow":
        r.line([(-36, -72), (-62, -62), (-66, -30)], INK, 8)
        r.line([(-36, -72), (-62, -62), (-66, -30)], "#FFFFFF", 4)
        r.ell(-66, -24, 8, 13, "#3A3030", INK, 2.2)
    for s in (-1, 1):                                                                    # legs and feet
        sw, lift = P.leg(s)
        hip, foot = (s * 19, -54), (s * 23 + sw, -12 - lift)
        r.limb(hip, foot, 16, legc)
        r.ell(foot[0] + s * 4, foot[1] + 5, 20, 9, "#3A3030" if species == "cow" else legc, INK, 2.8)
    if species == "sheep":                                                               # a body of fluffy wool
        nw = len(wools)
        for i in range(10):
            a = 2 * math.pi * i / 10
            py = -92 + 50 * math.sin(a)
            r.ell(46 * math.cos(a), py, 24, 24, wools[_band_of(py, -142, -42, nw)], INK, 3)
        if nw > 1:
            _ell_stripes(r, 0, -92, 46, 50, wools, "y")
        else:
            r.ell(0, -92, 46, 50, wools[0], None)
            if wools[0].upper() != "#FFFFFF":                                            # (coloured wool needs a few lighter tufts to look fluffy)
                hl = mix(wools[0], "#FFFFFF", 0.42)
                r.ell(-17, -122, 18, 10, hl, None, ang=-28)
                r.ell(22, -60, 13, 7, hl, None, ang=-18)
    else:
        r.ell(0, -92, 44, 48, fur, INK, 3.2)
        r.ell(0, -84, 27, 32, belly, None)
        if species == "cow":
            for (px, py, rx, ry) in ((-24, -112, 17, 21), (26, -70, 15, 17), (24, -118, 10, 12)):
                r.ell(px, py, rx, ry, accent or "#3A3030", None)
        if stripes:
            for i in range(3):
                r.line([(-44 + 6 * i, -108 + 16 * i), (-30, -104 + 16 * i)], dark, 4.2)
                r.line([(44 - 6 * i, -108 + 16 * i), (30, -104 + 16 * i)], dark, 4.2)
    if apron:
        r.poly([(-26, -118), (26, -118), (38, -52), (-38, -52)], apron, INK, 3)
        r.rrect(-13, -86, 13, -66, 4, darker(apron, 0.1), INK, 2)
    hands = f_arms(r, P, 40, -118, 38, 16, fur if species != "cow" else "#FFFFFF", hand=belly if species in ("cat", "dog", "mouse", "lion", "fox") else None)
    held(r, hold, hands[1])
    for s in (-1, 1):                                                                    # --- ears and mane, behind the head
        if species == "dog":
            r.ell(s * 51, -150, 17, 36, dark, INK, 3, ang=s * 14)
        elif species == "sheep":
            r.ell(s * 56, -164, 21, 10, fur, INK, 3, ang=-s * 16)
        elif species == "cow":
            r.ell(s * 58, -168, 21, 10, fur if fur != "#FFFFFF" else "#3A3030", INK, 3, ang=-s * 16)
            r.poly([(s * 24, -194), (s * 30, -218), (s * 40, -216), (s * 36, -192)], "#F4EAD0", INK, 2.6)
    if species == "lion":
        for i in range(14):
            a = 2 * math.pi * i / 14
            r.ell(60 * math.cos(a), -158 + 56 * math.sin(a), 26, 26, accent or "#B5651D", INK, 3)
        r.ell(0, -158, 60, 54, accent or "#B5651D", None)
    for s in (-1, 1):
        tw = 3 * math.sin(t * 3.1 + s)
        if species == "cat":
            r.poly([(s * 12, -190), (s * 52, -172), (s * (38 + tw * 0.3), -230)], fur, INK, 3.2)
            r.poly([(s * 22, -192), (s * 45, -180), (s * (37 + tw * 0.3), -216)], "#FFB3C7", None)
        elif species == "mouse":
            r.ell(s * 40, -196, 27, 29, fur, INK, 3.2)
            r.ell(s * 40, -196, 17, 19, "#F7B6C6", None)
        elif species == "lion":
            r.ell(s * 36, -198, 15, 15, fur, INK, 3)
            r.ell(s * 36, -198, 8, 8, "#E8A9A0", None)
        elif species == "fox":
            r.poly([(s * 10, -188), (s * 54, -170), (s * (42 + tw * 0.3), -240)], fur, INK, 3.2)
            r.poly([(s * 22, -190), (s * 47, -178), (s * (41 + tw * 0.3), -222)], "#FFF4E8", None)
            r.poly([(s * 36, -224), (s * (42 + tw * 0.3), -240), (s * 46, -216)], "#3A2A22", None)
    if species == "sheep":                                                               # the head: a dark face inside a fluffy wool cap
        r.ell(0, -158, 46, 42, fur, INK, 3.2)
        for i in range(7):
            r.ell(-36 + 12 * i, -196 + 4 * abs(i - 3), 15, 14, wools[i % len(wools)], INK, 2.8)
        if len(wools) > 1:
            _ell_stripes(r, 0, -190, 36, 12, wools, "x")
        else:
            r.ell(0, -190, 36, 12, wools[0], None)
            if wools[0].upper() != "#FFFFFF":
                r.ell(-12, -199, 11, 5, mix(wools[0], "#FFFFFF", 0.42), None, ang=-10)
    else:
        r.ell(0, -158, 48, 43, fur if species != "cow" else "#FFFFFF", INK, 3.2)
    if species in ("cat", "mouse", "lion", "fox", "dog"):                                # muzzle and nose
        wid = {"cat": 22, "mouse": 20, "lion": 25, "fox": 24, "dog": 28}[species]
        r.ell(sh, -146, wid, 16 if species != "dog" else 21, belly, None)
        if species == "fox":
            for s in (-1, 1):
                r.poly([(s * 30, -156), (s * 54, -148), (s * 36, -126)], "#FFFFFF", None)
        if species == "patch" or patch:
            r.ell(-19, -166, 17, 16, patch, None)
    if species == "cat":
        r.poly([(sh - 6, -152), (sh + 6, -152), (sh, -145)], "#FF7A9A", INK, 2)
    elif species == "dog":
        r.ell(sh, -152, 11, 8, "#2B2B2B", INK, 2)
        r.dot(sh + 3, -155, 2.4, "#FFFFFF")
    elif species == "mouse":
        r.dot(sh, -150, 5.5, "#F58BA7")
    elif species == "lion":
        r.poly([(sh - 9, -154), (sh + 9, -154), (sh, -143)], "#8A4B2A", INK, 2)
    elif species == "fox":
        r.ell(sh, -152, 8, 6, "#2B2B2B", INK, 2)
    elif species == "sheep":
        r.ell(sh, -150, 20, 15, "#5A4A4A", None)
        r.dot(sh, -152, 5, "#F58BA7")
    elif species == "cow":
        r.ell(sh, -142, 33, 21, "#FFB3C1", INK, 2.6)
        r.dot(sh - 11, -142, 3.8, "#C77A8A")
        r.dot(sh + 11, -142, 3.8, "#C77A8A")
    f_eyes(r, sh * 1.5, -168, 20, 10.5, 13, P)
    f_cheeks(r, sh, -146, 37, "#FF9DAB", 8, P.puff)
    if species in ("cat", "dog", "mouse", "lion", "fox", "sheep"):
        f_mouth(r, sh, -135 if species != "cow" else -126, P, 11)
        if P.mouth in ("open", "grin") and species == "dog":                              # a long pink tongue
            r.ell(sh, -122, 7, 11, "#FF7A9A", INK, 2)
    else:
        f_mouth(r, sh, -128, P, 9)
    if species in ("cat", "mouse"):                                                      # whiskers
        for s in (-1, 1):
            for dy in (-7, 0, 7):
                r.line([(s * 30, -148 + dy * 0.5), (s * 68, -152 + dy * 1.5)], "#5A4A4A", 2.2)
    if stripes and species == "cat":                                                     # tabby stripes on the forehead
        for i in (-1, 0, 1):
            r.line([(i * 11, -199 + abs(i) * 4), (i * 11, -184 + abs(i) * 3)], dark, 4.4)
    if bow:
        r.poly([(sh * 0 + 16, -196), (sh * 0 + 46, -208), (sh * 0 + 46, -184)], bow, INK, 2.4)
        r.poly([(sh * 0 + 16, -196), (sh * 0 - 14, -208), (sh * 0 - 14, -184)], bow, INK, 2.4)
        r.dot(16, -196, 7, darker(bow, 0.15))
    return r


# ------------------------------------------------------------------------------------------------ small helpers for Bibi's friends
def friend(c, which, x, y, k, t, mood="smile"):
    f = {"bibi": D.bibi, "pip": D.pip, "mo": D.mo, "lila": D.lila}[which]
    f(c, x, y, k, t=t, mood=mood, look=(4, -2))


CHARACTERS = {"pig": pig, "wolf": wolf, "bear": bear, "hare": hare, "tortoise": tortoise, "girl": girl, "ginger": ginger, "goat": goat, "troll": troll,
              "mirror": mirror, "hen": hen, "chick": chick}
for _sp in CRITTERS:                                                                     # every critter species is an actor kind of its own
    CHARACTERS[_sp] = (lambda sp: (lambda c, x, y, k=1.0, t=0.0, P=None, **kw: critter(c, x, y, k, t, P, species=sp, **kw)))(_sp)
