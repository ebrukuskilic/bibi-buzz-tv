"""Low-level drawing helpers + all characters (Bibi, Pip, Mo, Lila), flowers, sun, clouds.

Everything is drawn procedurally with Pillow at 2x supersampling, so no external
image assets are needed. Coordinates are always in 1280x720 space.
"""
import math
import os
import random
from contextlib import contextmanager
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, SS = 1280, 720, 2
INK = "#3B2A1A"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ----------------------------------------------------------------- math utils
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_back(x):
    x = clamp(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def pop(t, t0, dur=0.5):
    """0 before t0, then a bouncy 0->1 (slight overshoot)."""
    return ease_out_back((t - t0) / dur) if t >= t0 else 0.0


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(c):
    return "#%02x%02x%02x" % tuple(int(max(0, min(255, v))) for v in c)


def mix(c1, c2, t):
    a, b = hex2rgb(c1), hex2rgb(c2)
    return rgb2hex([lerp(a[i], b[i], t) for i in range(3)])


def darker(c, amt=0.35):
    return mix(c, "#000000", amt)


def ellipse_pts(cx, cy, rx, ry, ang=0, n=44):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        x, y = rx * math.cos(th), ry * math.sin(th)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


def bez(p0, p1, p2, n=16):
    pts = []
    for i in range(n + 1):
        u = i / n
        x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0]
        y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]
        pts.append((x, y))
    return pts


# ---------------------------------------------------------------------- fonts
FONT_CANDIDATES = [
    "assets/Fredoka-Variable.ttf",
    "assets/FredokaOne-Regular.ttf",
    "assets/Fredoka-Bold.ttf",
    "assets/font.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Rounded Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def font(size):
    """Font of `size` layout pixels. Sizes are quantised to 1 layout px so animated (growing) text does not
    create thousands of font objects."""
    return _font(max(8, int(size * SS) // SS * SS))


@lru_cache(None)
def _font(px):
    for p in FONT_CANDIDATES:
        full = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if os.path.exists(full):
            f = ImageFont.truetype(full, px)
            try:  # variable fonts (Fredoka): pick the bold weight
                axes = f.get_variation_axes()
                f.set_variation_by_axes([700 if "eight" in str(a.get("name")) else a.get("default", 100) for a in axes])
            except Exception:
                pass
            return f
    return ImageFont.load_default(px)


# --------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, img=None, ox=0, oy=0, w=None, h=None):
        self.w, self.h = w or W, h or H
        self.img = img if img is not None else Image.new("RGB", (self.w * SS, self.h * SS), "white")
        self.d = ImageDraw.Draw(self.img)
        self.ox, self.oy = ox, oy

    def _p(self, x, y):
        return ((x - self.ox) * SS, (y - self.oy) * SS)

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, width=0):
        x0, y0 = self._p(cx - rx, cy - ry)
        x1, y1 = self._p(cx + rx, cy + ry)
        self.d.ellipse([x0, y0, x1, y1], fill=fill, outline=outline,
                       width=max(1, int(width * SS)) if outline else 0)

    def poly(self, pts, fill=None, outline=None, width=0):
        pp = [self._p(x, y) for x, y in pts]
        self.d.polygon(pp, fill=fill)
        if outline:
            self.d.line(pp + [pp[0]], fill=outline, width=max(1, int(width * SS)), joint="curve")

    def rect(self, x0, y0, x1, y1, fill):
        a, b = self._p(x0, y0), self._p(x1, y1)
        self.d.rectangle([a[0], a[1], b[0], b[1]], fill=fill)

    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, width=0):
        a, b = self._p(x0, y0), self._p(x1, y1)
        self.d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=r * SS, fill=fill,
                                 outline=outline, width=max(1, int(width * SS)) if outline else 0)

    def line(self, pts, fill, width):
        pp = [self._p(x, y) for x, y in pts]
        w = max(1, int(width * SS))
        self.d.line(pp, fill=fill, width=w, joint="curve")
        r = w / 2
        for (x, y) in (pp[0], pp[-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def arc(self, cx, cy, rx, ry, a0, a1, fill, width):
        x0, y0 = self._p(cx - rx, cy - ry)
        x1, y1 = self._p(cx + rx, cy + ry)
        self.d.arc([x0, y0, x1, y1], a0, a1, fill=fill, width=max(1, int(width * SS)))

    def text(self, x, y, s, size, fill, anchor="mm", stroke=0, stroke_fill=None):
        px, py = self._p(x, y)
        self.d.text((px, py), s, font=font(size), fill=fill, anchor=anchor,
                    stroke_width=int(stroke * SS), stroke_fill=stroke_fill)

    @contextmanager
    def clip_ellipse(self, cx, cy, rx, ry):
        """Draw inside an ellipse only (used for stripes / dots on bodies)."""
        x0, y0 = int(cx - rx - 3), int(cy - ry - 3)
        x1, y1 = int(cx + rx + 4), int(cy + ry + 4)
        box = (int((x0 - self.ox) * SS), int((y0 - self.oy) * SS),
               int((x1 - self.ox) * SS), int((y1 - self.oy) * SS))
        layer = self.img.crop(box)
        yield Canvas(layer, x0, y0)
        mask = Image.new("L", layer.size, 0)
        ImageDraw.Draw(mask).ellipse(
            [(cx - rx - x0) * SS, (cy - ry - y0) * SS, (cx + rx - x0) * SS, (cy + ry - y0) * SS], fill=255)
        self.img.paste(layer, box[:2], mask)

    def final(self):
        return self.img.resize((self.w, self.h), Image.BOX)

    # ---- helpers used by the lesson engine
    def text_width(self, s, size):
        return font(size).getlength(s) / SS

    def text_fit(self, x, y, s, size, fill, max_w, anchor="mm", stroke=0, stroke_fill=None):
        """Like text() but shrinks the font until the string fits max_w (layout pixels)."""
        while size > 12 and self.text_width(s, size) + 2 * stroke > max_w:
            size *= 0.94
        self.text(x, y, s, size, fill, anchor=anchor, stroke=stroke, stroke_fill=stroke_fill)
        return size

    def sprite(self, spr, cx, cy, angle=0.0):
        """Paste an RGBA image (already scaled to layout pixels * SS) centred on (cx, cy)."""
        if angle:
            spr = spr.rotate(angle, resample=Image.BICUBIC, expand=True)
        px = int(round((cx - self.ox) * SS - spr.width / 2))
        py = int(round((cy - self.oy) * SS - spr.height / 2))
        self.img.paste(spr, (px, py), spr)


# ------------------------------------------------------------ face primitives
def blinking(t, period=3.4, offset=0.0):
    return ((t + offset) % period) < 0.14


def eyes(c, x, y, k, spread, rx, ry, look=(0, 0), blink=False, lashes=False):
    for s in (-1, 1):
        ex = x + s * spread * k
        if blink:
            c.arc(ex, y - ry * 0.3 * k, rx * k, ry * 0.55 * k, 20, 160, INK, 3.2 * k)
            continue
        c.ellipse(ex, y, rx * k, ry * k, fill="white", outline=INK, width=2.5 * k)
        px, py = ex + look[0] * k, y + look[1] * k
        c.ellipse(px, py, rx * 0.64 * k, ry * 0.66 * k, fill=INK)
        c.ellipse(px + rx * 0.22 * k, py - ry * 0.25 * k, rx * 0.24 * k, rx * 0.24 * k, fill="white")
        if lashes:
            for a in (-1, 0, 1):
                bx, by = ex + s * rx * 0.85 * k, y - ry * 0.55 * k
                c.line([(bx, by), (bx + s * (6 + a * 2) * k, by - (7 - a * 2) * k)], INK, 2.2 * k)


def cheeks(c, x, y, k, spread, color="#FF9DB0"):
    for s in (-1, 1):
        c.ellipse(x + s * spread * k, y, 10 * k, 7 * k, fill=color)


def mouth(c, x, y, k, kind="smile", t=0.0, color=INK, amt=None):
    if kind == "smile":
        c.arc(x, y, 15 * k, 11 * k, 15, 165, color, 3.5 * k)
    elif kind == "open":
        ry = (6 + 5 * abs(math.sin(t * 9))) * k if amt is None else (3 + 10 * clamp(amt)) * k
        c.ellipse(x, y + 8 * k, 13 * k, ry, fill="#B8283C", outline=INK, width=2.5 * k)
        c.ellipse(x, y + 8 * k + ry * 0.45, 7 * k, ry * 0.4, fill="#FF8FA3")
    elif kind == "wow":
        c.ellipse(x, y + 7 * k, 8 * k, 11 * k, fill="#B8283C", outline=INK, width=2.5 * k)


# -------------------------------------------------------------------- flowers
def mini_flower(c, x, y, r, color, t=0.0, center="#FFD23F", petals=8):
    if r <= 0.5:
        return
    for i in range(petals):
        th = 2 * math.pi * i / petals + t * 0.4
        px, py = x + math.cos(th) * r * 0.72, y + math.sin(th) * r * 0.72
        c.ellipse(px, py, r * 0.46, r * 0.46, fill=color, outline=darker(color), width=max(1.5, r * 0.05))
    c.ellipse(x, y, r * 0.58, r * 0.58, fill=center, outline=darker(center), width=max(1.5, r * 0.05))


def flower(c, x, ground, height, color, grow=1.0, t=0.0, phase=0.0, face=True, dx=0.0):
    if grow <= 0.01:
        return
    h = height * grow
    sway = math.sin(t * 2 + phase) * 5 * grow
    top = (x + dx * grow + sway, ground - h)
    pts = bez((x, ground), (x + (dx * grow + sway) * 0.1, ground - h * 0.55), top, 18)
    c.line(pts, "#2E8B3E", 10 * min(grow, 1.1) + 2)
    c.line(pts, "#4FBF5A", 6 * min(grow, 1.1) + 1)
    mid = pts[8]
    c.poly(ellipse_pts(mid[0] - 28 * grow, mid[1] - 4 * grow, 28 * grow, 11 * grow, ang=-28),
           fill="#5BC15A", outline="#2E7D3A", width=2)
    c.poly(ellipse_pts(mid[0] + 26 * grow, mid[1] + 14 * grow, 25 * grow, 10 * grow, ang=28),
           fill="#5BC15A", outline="#2E7D3A", width=2)
    r = 60 * grow * min(1.0, height / 330.0)
    r = max(r, 14 * grow)
    mini_flower(c, top[0], top[1], r, color, t)
    if face and r > 24:
        for s in (-1, 1):
            c.ellipse(top[0] + s * r * 0.2, top[1] - r * 0.1, r * 0.08, r * 0.1, fill=INK)
        c.arc(top[0], top[1] + r * 0.02, r * 0.2, r * 0.15, 20, 160, INK, max(2, r * 0.05))


# ------------------------------------------------------------------ characters
def bibi(c, x, y, k=1.0, t=0.0, mood="smile", look=(0, 0), flower_color=None, flower_pop=1.0, bob=None, mouth_amt=None):
    """Bibi the baby bee - the star of Bibi Buzz TV."""
    y = y + (math.sin(t * 3.2) * 6 * k if bob is None else bob * k)
    flap = 0.8 + 0.25 * math.sin(t * 16)
    for s in (-1, 1):
        c.poly(ellipse_pts(x + s * 42 * k, y - 62 * k, 30 * k, 50 * k * flap, ang=s * 28),
               fill="#DDF4FF", outline="#8CCBEA", width=3 * k)
    for s in (-1, 1):
        pts = bez((x + s * 16 * k, y - 56 * k), (x + s * 24 * k, y - 98 * k), (x + s * 42 * k, y - 94 * k), 12)
        c.line(pts, INK, 4 * k)
        c.ellipse(pts[-1][0], pts[-1][1], 7 * k, 7 * k, fill=INK)
    c.ellipse(x, y, 72 * k, 64 * k, fill="#FFD23F")
    with c.clip_ellipse(x, y, 72 * k, 64 * k) as cc:
        for a, b in ((24, 36), (56, 72)):
            cc.rect(x - 100 * k, y + a * k, x + 100 * k, y + b * k, INK)
        cc.rect(x - 100 * k, y + 40 * k, x + 100 * k, y + 52 * k, "#3E8EDE")
    c.ellipse(x, y, 72 * k, 64 * k, outline=INK, width=3.5 * k)
    c.poly([(x + 30 * k, y + 46 * k), (x + 54 * k, y + 50 * k), (x + 48 * k, y + 82 * k), (x + 30 * k, y + 72 * k)],
           fill="#3E8EDE", outline=INK, width=2.5 * k)
    eyes(c, x, y - 10 * k, k, 25, 15, 18, look, blinking(t, 3.4, 0.4))
    cheeks(c, x, y + 12 * k, k, 44)
    mouth(c, x, y + 4 * k, k, mood, t, amt=mouth_amt)
    if flower_color:
        mini_flower(c, x + 40 * k, y - 66 * k, 26 * k * flower_pop, flower_color, t)


def pip(c, x, y, k=1.0, t=0.0, mood="smile", look=(0, 0)):
    """Pip the cheerful ladybug."""
    for s in (-1, 1):
        c.ellipse(x + s * 36 * k, y + 62 * k, 17 * k, 9 * k, fill="#2B2B2B")
    c.ellipse(x, y + 6 * k, 70 * k, 60 * k, fill="#F0383C")
    with c.clip_ellipse(x, y + 6 * k, 70 * k, 60 * k) as cc:
        cc.line([(x, y - 70 * k), (x, y + 80 * k)], INK, 4 * k)
        for dx, dy in ((-36, 18), (36, 18), (-46, 48), (46, 48), (-20, 54), (20, 54)):
            cc.ellipse(x + dx * k, y + dy * k, 10 * k, 10 * k, fill=INK)
    c.ellipse(x, y + 6 * k, 70 * k, 60 * k, outline=INK, width=3.5 * k)
    for s in (-1, 1):
        pts = [(x + s * 14 * k, y - 62 * k), (x + s * 28 * k, y - 92 * k)]
        c.line(pts, INK, 4 * k)
        c.ellipse(pts[-1][0], pts[-1][1], 6 * k, 6 * k, fill=INK)
    c.ellipse(x, y - 34 * k, 48 * k, 36 * k, fill="#2B2B2B", outline=INK, width=3.5 * k)
    eyes(c, x, y - 38 * k, k, 19, 13, 15, look, blinking(t, 3.1, 1.2))
    cheeks(c, x, y - 22 * k, k, 36)
    mouth(c, x, y - 28 * k, k * 0.85, mood, t, color="#FFFFFF")


def mo(c, x, y, k=1.0, t=0.0, mood="smile", look=(0, 0)):
    """Mo the gentle turtle with round glasses."""
    bob = math.sin(t * 2.2) * 3 * k
    c.ellipse(x, y - 14 * k, 92 * k, 66 * k, fill="#B9803D")
    with c.clip_ellipse(x, y - 14 * k, 92 * k, 66 * k) as cc:
        for dx, dy, rx, ry in ((0, -30, 28, 20), (-52, -14, 20, 18), (52, -14, 20, 18),
                               (-32, 22, 22, 14), (32, 22, 22, 14)):
            cc.ellipse(x + dx * k, y + dy * k, rx * k, ry * k, fill="#D9A25A", outline="#8A5A24", width=2.5 * k)
    c.ellipse(x, y - 14 * k, 92 * k, 66 * k, outline=INK, width=3.5 * k)
    for s in (-1, 1):
        c.ellipse(x + s * 58 * k, y + 54 * k, 24 * k, 14 * k, fill="#6FC95F", outline=INK, width=3 * k)
    hy = y + 18 * k + bob
    c.ellipse(x, hy, 52 * k, 44 * k, fill="#7BD36B", outline=INK, width=3.5 * k)
    blink = blinking(t, 4.0, 2.0)
    for s in (-1, 1):
        ex, ey = x + s * 22 * k, hy - 8 * k
        c.ellipse(ex, ey, 18 * k, 18 * k, fill="white")
        if blink:
            c.arc(ex, ey - 4 * k, 12 * k, 8 * k, 20, 160, INK, 3 * k)
        else:
            c.ellipse(ex + look[0] * k, ey + 2 * k + look[1] * k, 8 * k, 9 * k, fill=INK)
            c.ellipse(ex + look[0] * k + 3 * k, ey - 2 * k, 2.8 * k, 2.8 * k, fill="white")
        c.ellipse(ex, ey, 18 * k, 18 * k, outline=INK, width=3.5 * k)
    c.line([(x - 5 * k, hy - 8 * k), (x + 5 * k, hy - 8 * k)], INK, 3 * k)
    cheeks(c, x, hy + 14 * k, k, 40)
    mouth(c, x, hy + 8 * k, k * 0.9, mood, t)


def lila(c, x, y, k=1.0, t=0.0, mood="smile", look=(0, 0)):
    """Lila the sweet butterfly."""
    y = y + math.sin(t * 2.6 + 1) * 7 * k
    flap = 0.62 + 0.38 * abs(math.sin(t * 5))
    for s in (-1, 1):
        c.poly(ellipse_pts(x + s * 64 * k * flap, y - 36 * k, 60 * k * flap, 44 * k, ang=-s * 28),
               fill="#B58CF2", outline="#6A3FB3", width=3 * k)
        c.ellipse(x + s * 74 * k * flap, y - 42 * k, 12 * k * flap, 11 * k, fill="#E6D3FF")
        c.poly(ellipse_pts(x + s * 44 * k * flap, y + 30 * k, 38 * k * flap, 28 * k, ang=s * 28),
               fill="#FF9BD2", outline="#B03C86", width=3 * k)
        c.ellipse(x + s * 50 * k * flap, y + 34 * k, 8 * k * flap, 7 * k, fill="#FFD1EC")
    c.ellipse(x, y + 8 * k, 16 * k, 52 * k, fill="#7A4FB5", outline=INK, width=3 * k)
    for s in (-1, 1):
        pts = bez((x + s * 10 * k, y - 66 * k), (x + s * 14 * k, y - 94 * k), (x + s * 36 * k, y - 100 * k), 12)
        c.line(pts, INK, 3 * k)
        c.ellipse(pts[-1][0], pts[-1][1], 5 * k, 5 * k, fill=INK)
    c.ellipse(x, y - 40 * k, 34 * k, 32 * k, fill="#FFE0CF", outline=INK, width=3 * k)
    eyes(c, x, y - 44 * k, k, 13, 9, 11, look, blinking(t, 3.7, 0.9), lashes=True)
    cheeks(c, x, y - 30 * k, k, 22)
    mouth(c, x, y - 34 * k, k * 0.6, mood, t)
    mini_flower(c, x + 24 * k, y - 66 * k, 16 * k, "#FF6FAE", t, petals=6)


# ------------------------------------------------------------ scenery / props
def star(c, x, y, r, fill, ang=0):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = math.radians(ang - 90 + i * 36)
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    c.poly(pts, fill=fill, outline=darker(fill, 0.25), width=1.5)


def heart(c, x, y, r, fill="#FF5C8A"):
    c.ellipse(x - r * 0.5, y - r * 0.3, r * 0.55, r * 0.55, fill=fill)
    c.ellipse(x + r * 0.5, y - r * 0.3, r * 0.55, r * 0.55, fill=fill)
    c.poly([(x - r * 1.0, y - r * 0.1), (x + r * 1.0, y - r * 0.1), (x, y + r * 1.0)], fill=fill)


def make_background():
    arr = np.zeros((H * SS, W * SS, 3), dtype=np.uint8)
    top, bot = np.array([120, 205, 255]), np.array([226, 247, 255])
    for yy in range(H * SS):
        u = min(1.0, yy / (480.0 * SS))
        arr[yy, :, :] = (top + (bot - top) * u).astype(np.uint8)
    c = Canvas(Image.fromarray(arr))
    c.ellipse(260, 650, 540, 240, fill="#A9E98C")
    c.ellipse(1000, 660, 580, 220, fill="#97E17D")
    c.ellipse(640, 780, 900, 260, fill="#82D667")
    c.rect(0, 610, W, H, "#6CC653")
    rng = random.Random(7)
    for _ in range(70):
        fx, fy = rng.uniform(0, W), rng.uniform(575, H - 8)
        col = rng.choice(["#FFFFFF", "#FFE066", "#FF9BD2", "#B58CF2"])
        c.ellipse(fx, fy, 5, 5, fill=col)
    return c.img


def sun(c, t, x=1130, y=105):
    for i in range(12):
        a = math.radians(i * 30 + t * 12)
        c.line([(x + math.cos(a) * 76, y + math.sin(a) * 76), (x + math.cos(a) * 102, y + math.sin(a) * 102)],
               "#FFC21A", 7)
    c.ellipse(x, y, 62, 62, fill="#FFD84D", outline="#F2A900", width=4)
    for s in (-1, 1):
        c.ellipse(x + s * 21, y - 8, 6, 8, fill=INK)
    c.arc(x, y + 4, 24, 18, 20, 160, INK, 4)
    for s in (-1, 1):
        c.ellipse(x + s * 38, y + 14, 9, 6, fill="#FF9F7A")


def cloud(c, cx, cy, s=1.0):
    for dx, dy, r in ((-46, 8, 30), (-14, -10, 38), (24, -4, 34), (54, 10, 26), (4, 14, 34)):
        c.ellipse(cx + dx * s, cy + dy * s, r * s, r * s, fill="#FFFFFF")


def park(c, t):
    sun(c, t)
    for x0, y0, sp, sc in ((100, 110, 14, 1.0), (520, 70, 9, 1.3), (860, 190, 11, 0.8)):
        cloud(c, (x0 + t * sp) % (W + 400) - 200, y0, sc)


# ------------------------------------------------------------------ text bits
def word_pop_text(c, words, colors, cx, cy, size, t, t0, stagger=0.25, stroke=14):
    f = font(size)
    widths = [f.getlength(w + " ") / SS for w in words]
    total = sum(widths) - f.getlength(" ") / SS
    x = cx - total / 2
    for w, col, wd in zip(words, colors, widths):
        p = pop(t, t0)
        start = t0
        t0 += stagger
        if p > 0.02:
            yy = cy - math.sin(clamp((t - start) / 0.5) * math.pi) * 14
            c.text(x, yy, w, size * min(p, 1.15), "#FFFFFF", anchor="lm", stroke=stroke, stroke_fill="#FFFFFF")
            c.text(x, yy, w, size * min(p, 1.15), col, anchor="lm", stroke=5, stroke_fill=darker(col, 0.5))
        x += wd


def big_label(c, text, cx, cy, size, color, p):
    if p <= 0.02:
        return
    s = size * min(p, 1.12)
    c.text(cx, cy, text, s, "#FFFFFF", stroke=16, stroke_fill="#FFFFFF")
    c.text(cx, cy, text, s, color, stroke=6, stroke_fill=darker(color, 0.55))


def lyric_line(c, text, progress, cy=655, size=40):
    words = text.split()
    f = font(size)
    widths = [f.getlength(w + " ") / SS for w in words]
    total = sum(widths) - f.getlength(" ") / SS
    pad, h = 38, size * 1.7
    c.rrect(W / 2 - total / 2 - pad, cy - h / 2, W / 2 + total / 2 + pad, cy + h / 2, h / 2,
            fill="#FFFFFF", outline="#FF9BC0", width=4)
    idx = int(clamp(progress) * len(words) * 0.98)
    x = W / 2 - total / 2
    for i, (w, wd) in enumerate(zip(words, widths)):
        c.text(x, cy, w, size, "#FF4F86" if i <= idx else "#2B3A55", anchor="lm")
        x += wd
