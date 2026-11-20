"""Draws one frame of a Lesson at time t.

Layouts: 'long' = 1280x720 (16:9), 'short' = 720x1280 (9:16, scaled to 1080x1920 when encoding).
Everything that moves is driven by the lesson's beat grid and the real voice clips:
  * pictures pop in exactly at their cue start (cues sit on beats),
  * Bibi bounces on the beat and opens his mouth with the real loudness of the voice,
  * captions highlight the words while they are being spoken.
"""
import math
import random

import numpy as np
from PIL import Image

from . import draw as D
from . import emoji as E
from . import schedule as SCH
from . import vocab as V
from .draw import Canvas, SS, INK, clamp, lerp, pop, darker, mix

FPS = 24
CAPTION_TAGS = {"intro", "say", "fact", "sound", "answer", "phrase", "outro", "think", "item"}
RINGS = ["#FF6FAE", "#3E8EDE", "#FFB400", "#3DB54A", "#9B59D0", "#FF8A1F", "#00B8D4", "#E8383D"]
GREEN = "#2DB84D"


# ------------------------------------------------------------------------------ layouts
class Layout:
    def __init__(self, fmt):
        self.fmt = fmt
        self.v = fmt == "short"
        if self.v:
            self.w, self.h = 720, 1280
            self.sx0, self.sy0, self.sx1, self.sy1 = 50, 190, 650, 850
            self.bibi = (112, 1062, 0.56)
            self.cap_bottom, self.cap_w, self.cap_size = 988, 600, 38
            self.chip = (360, 92)
            self.ground = 1110
            self.sun = (612, 128)
        else:
            self.w, self.h = 1280, 720
            self.sx0, self.sy0, self.sx1, self.sy1 = 270, 85, 1240, 585
            self.bibi = (140, 535, 0.9)
            self.cap_bottom, self.cap_w, self.cap_size = 708, 1120, 40
            self.chip = (150, 46)
            self.ground = 612
            self.sun = (1130, 105)
        self.scx, self.scy = (self.sx0 + self.sx1) / 2, (self.sy0 + self.sy1) / 2
        self.sw, self.sh = self.sx1 - self.sx0, self.sy1 - self.sy0


_layouts = {}


def layout(fmt):
    if fmt not in _layouts:
        _layouts[fmt] = Layout(fmt)
    return _layouts[fmt]


# ----------------------------------------------------------------------------- backgrounds
THEMES = {
    "park": dict(top="#78CDFF", bot="#E2F7FF", hills=("#A9E98C", "#97E17D", "#82D667"), ground="#6CC653", deco="clouds",
                 dots=("#FFFFFF", "#FFE066", "#FF9BD2", "#B58CF2")),
    "sunset": dict(top="#FF9F80", bot="#FFEBB5", hills=("#FFCB78", "#FFB963", "#F7A455"), ground="#EE9440", deco="clouds",
                   dots=("#FFFFFF", "#FFF3B0", "#FF7A7A", "#C27AF0")),
    "ocean": dict(top="#3CC1F2", bot="#C8F3FF", hills=("#46B8E8", "#2FA4D8", "#2490C8"), ground="#1C7FB8", deco="bubbles",
                  dots=("#FFFFFF", "#CFF4FF", "#FFE066", "#FF9BD2")),
    "night": dict(top="#1B1F4F", bot="#5A4AA0", hills=("#4A4AA8", "#40409A", "#35358A"), ground="#2E2E7A", deco="stars",
                  dots=("#FFF3A0", "#C9B8FF", "#9FD8FF", "#FFFFFF")),
    "candy": dict(top="#FFB0E4", bot="#FFF0FA", hills=("#DDB6FF", "#CFA3FF", "#C190FA"), ground="#AE7CEC", deco="clouds",
                  dots=("#FFFFFF", "#FFE066", "#7AD8FF", "#FF7AB6")),
}
_bg = {}


def background(L, theme):
    key = (L.fmt, theme)
    if key in _bg:
        return _bg[key]
    th = THEMES[theme]
    w, h = L.w, L.h
    top = np.array(D.hex2rgb(th["top"]), dtype=np.float32)
    bot = np.array(D.hex2rgb(th["bot"]), dtype=np.float32)
    n = h * SS
    u = np.clip(np.arange(n, dtype=np.float32) / (0.66 * n), 0, 1)[:, None]
    col = (top[None, :] + (bot - top)[None, :] * u).astype(np.uint8)
    img = Image.fromarray(np.ascontiguousarray(np.repeat(col[:, None, :], w * SS, axis=1)))
    c = Canvas(img, w=w, h=h)
    g = L.ground
    h1, h2, h3 = th["hills"]
    c.ellipse(0.20 * w, g + 40, 0.42 * w, 200, fill=h1)
    c.ellipse(0.80 * w, g + 50, 0.46 * w, 180, fill=h2)
    c.ellipse(0.50 * w, g + 180, 0.75 * w, 220, fill=h3)
    c.rect(0, g, w, h, th["ground"])
    rng = random.Random(7)
    for _ in range(int(70 * w / 1280)):
        c.ellipse(rng.uniform(0, w), rng.uniform(g - 30, h - 8), 5, 5, fill=rng.choice(th["dots"]))
    _bg[key] = c.img
    return c.img


def decor(c, L, theme, t):
    kind = THEMES[theme]["deco"]
    w = L.w
    if kind == "clouds":
        D.sun(c, t, *L.sun)
        for x0, y0, sp, sc in ((100, 140, 14, 1.0), (520, 90, 9, 1.3), (860, 220, 11, 0.8)):
            if L.v:
                y0 = y0 * 0.8 + 40
            D.cloud(c, (x0 + t * sp) % (w + 400) - 200, y0, sc)
    elif kind == "stars":
        rng = random.Random(3)
        for i in range(26):
            x, y = rng.uniform(0, w), rng.uniform(0, L.ground - 60)
            r = 7 + 5 * math.sin(t * 2.2 + i)
            D.star(c, x, y, r, "#FFF3A0", ang=t * 20 + i * 15)
        mx, my = L.sun
        c.ellipse(mx, my, 54, 54, fill="#FFF3C0")
        c.ellipse(mx + 24, my - 12, 46, 46, fill="#33378A")
    elif kind == "bubbles":
        rng = random.Random(5)
        for i in range(16):
            x = rng.uniform(0, w)
            sp = rng.uniform(25, 60)
            y = L.ground - ((t * sp + rng.uniform(0, 900)) % (L.ground + 60)) + 40
            r = rng.uniform(8, 24)
            c.ellipse(x + math.sin(t * 1.5 + i) * 8, y, r, r, outline="#FFFFFF", width=3)


# --------------------------------------------------------------------------------- helpers
def label(c, text, cx, cy, size, color, p, max_w):
    """Big sticker-style text that pops in."""
    if p <= 0.02 or not text:
        return
    s = size * min(p, 1.12)
    while s > 16 and c.text_width(text, s) > max_w:
        s *= 0.94
    c.text(cx, cy, text, s, "#FFFFFF", stroke=max(8, s * 0.14), stroke_fill="#FFFFFF")
    c.text(cx, cy, text, s, color, stroke=max(3, s * 0.05), stroke_fill=darker(color, 0.55))


def plate(c, cx, cy, d, ring, fill="#FFFFFF"):
    c.ellipse(cx, cy, d / 2, d / 2, fill=fill, outline=ring, width=max(3, d * 0.035))


def draw_shape(c, name, cx, cy, size, color):
    r = size / 2
    ol, lw = darker(color, 0.35), max(3, size * 0.03)
    if name == "circle":
        c.ellipse(cx, cy, r, r, fill=color, outline=ol, width=lw)
    elif name == "oval":
        c.ellipse(cx, cy, r, r * 0.64, fill=color, outline=ol, width=lw)
    elif name == "square":
        c.rrect(cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86, r * 0.12, fill=color, outline=ol, width=lw)
    elif name == "rectangle":
        c.rrect(cx - r, cy - r * 0.6, cx + r, cy + r * 0.6, r * 0.1, fill=color, outline=ol, width=lw)
    elif name == "triangle":
        c.poly([(cx, cy - r * 0.92), (cx + r, cy + r * 0.78), (cx - r, cy + r * 0.78)], fill=color, outline=ol, width=lw)
    elif name == "diamond":
        c.poly([(cx, cy - r), (cx + r * 0.72, cy), (cx, cy + r), (cx - r * 0.72, cy)], fill=color, outline=ol, width=lw)
    elif name == "star":
        D.star(c, cx, cy + r * 0.05, r, color)
    elif name == "heart":
        D.heart(c, cx, cy - r * 0.08, r * 0.92, color)


def icon(c, ref, cx, cy, size, ring="#FFB400", plate_on=True, p=1.0, angle=0.0, tint=None):
    """Draws an emoji / colour dot / number / letter / shape inside an optional sticker plate."""
    if p <= 0.02:
        return
    s = size * min(p, 1.15)
    if plate_on:
        plate(c, cx, cy, s, ring)
    inner = s * (0.76 if plate_on else 0.95)
    if ref.startswith("#"):
        c.ellipse(cx, cy, s * 0.36, s * 0.36, fill=ref, outline=darker(ref, 0.3), width=max(2, s * 0.025))
    elif ref.startswith("n:"):
        c.text(cx, cy + s * 0.02, ref[2:], inner * 0.78, ring, stroke=max(2, s * 0.02), stroke_fill=darker(ring, 0.5))
    elif ref.startswith("L:"):
        c.text(cx, cy + s * 0.02, ref[2:], inner * 0.78, ring, stroke=max(2, s * 0.02), stroke_fill=darker(ring, 0.5))
    elif ref.startswith("S:"):
        draw_shape(c, ref[2:], cx, cy, inner * 0.92, ring)
    else:
        c.sprite(E.scaled(ref, inner), cx, cy, angle)


def burst(c, cx, cy, t, t0, n=8, r0=120, r1=260, size=18, dur=0.9):
    u = (t - t0) / dur
    if u <= 0 or u >= 1:
        return
    cols = ["#FFD23F", "#FF6FAE", "#3E8EDE", "#3DB54A", "#FF8A1F", "#9B59D0"]
    for k in range(n):
        a = 2 * math.pi * k / n + 0.4
        rr = lerp(r0, r1, 1 - (1 - u) ** 2)
        D.star(c, cx + math.cos(a) * rr, cy + math.sin(a) * rr, size * (1 - u) + 3, cols[k % len(cols)], ang=u * 200 + k * 20)


def bubble(c, text, cx, cy, size, color, p, xmin, xmax):
    if p <= 0.02 or not text:
        return
    s = size * min(p, 1.1)
    w, h = c.text_width(text, s) + 64, s * 1.55
    cx = clamp(cx, xmin + w / 2, xmax - w / 2)
    c.rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, h / 2, fill="#FFFFFF", outline=color, width=5)
    tail = [(cx - w * 0.20, cy + h / 2 - 4), (cx - w * 0.34, cy + h / 2 + h * 0.5), (cx - w * 0.06, cy + h / 2 - 4)]
    c.poly(tail, fill="#FFFFFF")
    c.line(tail[:2], color, 5)
    c.line(tail[1:], color, 5)
    c.text(cx, cy, text, s, color)


def grid_pos(n, region, max_cols=5):
    x0, y0, x1, y1 = region
    cols = min(n, max_cols)
    rows = int(math.ceil(n / cols))
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    out = []
    for i in range(n):
        r, k = divmod(i, cols)
        in_row = cols if r < rows - 1 else n - cols * (rows - 1)
        out.append((x0 + (x1 - x0) / 2 + (k - (in_row - 1) / 2) * cw, y0 + (r + 0.5) * ch))
    return out, min(cw, ch)


def cap(s):
    return s[:1].upper() + s[1:]


# ------------------------------------------------------------------------------- context
class Ctx:
    def __init__(self, lesson, L, t):
        self.lesson, self.L, self.t = lesson, L, t
        self.beat = lesson.beat
        self.ph = ((t - lesson.grid0) / lesson.beat) % 1.0
        self.pulse = 1.0 + 0.05 * math.exp(-self.ph * 7.0)
        self.bob = -9.0 * abs(math.sin(math.pi * self.ph))
        self.amp = self._amp()

    def _amp(self):
        for cu in self.lesson.all_cues:
            if cu.text and cu.t <= self.t < cu.t + cu.dur:
                env = self.lesson.env.get(cu.text)
                if env is None or len(env) == 0:
                    return 0.6
                return float(env[min(int((self.t - cu.t) * 30), len(env) - 1)])
        return None

    def cue_p(self, seg, k, dur=0.5):
        return pop(self.t, seg.cues[k].t, dur) if 0 <= k < len(seg.cues) else 0.0

    def started(self, seg, k):
        return 0 <= k < len(seg.cues) and self.t >= seg.cues[k].t

    def n_started(self, seg, tag=None):
        return sum(1 for cu in seg.cues if self.t >= cu.t and (tag is None or cu.tag == tag))

    def active(self, seg):
        """Last started cue of the segment (index, cue) or (-1, None)."""
        idx = -1
        for k, cu in enumerate(seg.cues):
            if self.t >= cu.t:
                idx = k
        return (idx, seg.cues[idx]) if idx >= 0 else (-1, None)


def bibi_at(X, c, x, y, k):
    D.bibi(c, x, y, k, t=X.t, mood="open" if X.amp is not None else "smile", look=(5, -2), bob=X.bob,
           mouth_amt=X.amp)


# ------------------------------------------------------------------------------ renderers
def r_title(X, c, seg):
    L, d, t = X.L, seg.data, X.t
    label(c, d["title"], L.scx, L.scy - 135, 118, "#FF6FAE", pop(t, 0.15, 0.6), L.sw - 40)
    label(c, d["sub"], L.scx, L.scy - 52, 56, "#3E8EDE", pop(t, 0.5, 0.6), L.sw - 100)
    codes = d["codes"]
    n = len(codes)
    gap = min(175, (L.sw - 100) / max(n, 1))
    x0 = L.scx - gap * (n - 1) / 2
    for k, code in enumerate(codes):
        t0 = X.lesson.grid0 + k * X.beat
        dy = -16 * max(0.0, math.sin(clamp((t - t0) / 0.5) * math.pi))
        icon(c, code, x0 + k * gap, L.scy + 70 + dy, 140, RINGS[k % len(RINGS)], p=pop(t, t0, 0.45))
    bibi_at(X, c, 150, 465, 1.25)


def r_card(X, c, seg):
    L, d, t = X.L, seg.data, X.t
    size = 470 if L.v else 380
    cy = L.sy0 + 290 if L.v else L.scy - 30
    ring = d["ring"]
    p = X.cue_p(seg, 0, 0.55)
    snd_i = next((k for k, cu in enumerate(seg.cues) if cu.tag == "sound"), -1)
    ang = 0.0
    if snd_i >= 0 and seg.cues[snd_i].t <= t < seg.cues[snd_i].t + seg.cues[snd_i].slot:
        ang = 7 * math.sin((t - seg.cues[snd_i].t) * 13)
    icon(c, d["code"], L.scx, cy, size * X.pulse, ring, p=p, angle=ang)
    burst(c, L.scx, cy, t, seg.cues[0].t, n=8, r0=size * 0.55, r1=size * 0.85)
    label(c, cap(d["word"]), L.scx, cy + size / 2 + (62 if not L.v else 70), 100 if not L.v else 118, ring, p, L.sw - 60)
    if snd_i >= 0 and d.get("sound"):
        bubble(c, cap(d["sound"]) + "!", L.scx + size * 0.30, cy - size * 0.58, 58 if not L.v else 52, ring,
               X.cue_p(seg, snd_i, 0.4), L.sx0, L.sx1)


def r_count(X, c, seg):
    L, d, t = X.L, seg.data, X.t
    n = d["n"]
    counts = [cu for cu in seg.cues if cu.tag == "count"]
    total = seg.cues[-1]
    k = sum(1 for cu in counts if t >= cu.t)
    if L.v:
        region, badge = (L.sx0, L.sy0 + 250, L.sx1, L.sy1 - 60), (L.scx, L.sy0 + 105, 100)
    else:
        region, badge = (L.sx0 + 270, L.sy0 + 5, L.sx1, L.sy1 - 75), (L.sx0 + 125, L.scy - 30, 110)
    pos, cell = grid_pos(n, region, 5)
    size = min(cell * 0.94, 165)
    for i in range(min(k, n)):
        x, y = pos[i]
        dy = 0.0
        if t >= total.t and t - total.t < 1.6:
            dy = -abs(math.sin((t - total.t) * 6 + i * 0.5)) * 14
        icon(c, d["code"], x, y + dy, size, plate_on=False, p=pop(t, counts[i].t, 0.4))
    if k > 0:
        j = min(k, n) - 1
        bx, by, br = badge
        pk = pop(t, counts[j].t, 0.35)
        s = br * min(pk, 1.12) * (1.0 + 0.04 * (t >= total.t))
        c.ellipse(bx, by, s, s, fill="#FF6FAE", outline="#FFFFFF", width=8)
        c.text(bx, by + 4, str(j + 1), s * (1.5 if j + 1 < 10 else 1.15), "#FFFFFF", stroke=5, stroke_fill=darker("#FF6FAE", 0.4))
    if t >= total.t:
        label(c, total.text.rstrip("!").strip() + "!", L.scx + (0 if L.v else 130), L.sy1 - 30, 66 if not L.v else 60,
              "#3E8EDE", pop(t, total.t, 0.5), L.sw - 60)
        burst(c, L.scx + (0 if L.v else 130), L.scy, t, total.t, n=10, r0=150, r1=330, size=20, dur=1.1)


def r_number(X, c, seg):
    L, d, t = X.L, seg.data, X.t
    n = d["n"]
    t0 = seg.cues[0].t
    p = pop(t, t0, 0.5)
    col = RINGS[n % len(RINGS)]
    if L.v:
        cx, cy, cw, ch = L.scx, L.sy0 + 150, 420, 270
        region = (L.sx0, L.sy0 + 330, L.sx1, L.sy1 - 20)
    else:
        cx, cy, cw, ch = L.sx0 + 190, L.scy - 30, 300, 360
        region = (L.sx0 + 390, L.sy0 + 5, L.sx1, L.sy1 - 20)
    s = min(p, 1.1)
    if p > 0.02:
        c.rrect(cx - cw / 2 * s, cy - ch / 2 * s, cx + cw / 2 * s, cy + ch / 2 * s, 46, fill=col, outline="#FFFFFF", width=10)
        c.text(cx, cy + 6, str(n), ch * 0.78 * s * (1.0 if n < 10 else 0.72), "#FFFFFF", stroke=8, stroke_fill=darker(col, 0.45))
    label(c, cap(V.NUMBER_WORDS[n]), cx, cy + ch / 2 + 62, 84, col, pop(t, t0 + 0.1, 0.5), cw + 120)
    pos, cell = grid_pos(n, region, 5)
    size = min(cell * 0.94, 160)
    for i, (x, y) in enumerate(pos):
        icon(c, d["code"], x, y, size, plate_on=False, p=pop(t, t0 + 0.15 + i * 0.07, 0.4))


def splash(c, cx, cy, r, color):
    for i in range(8):
        a = 2 * math.pi * i / 8 + 0.3
        rr = r * (0.27 + 0.06 * math.sin(i * 2.1))
        c.ellipse(cx + math.cos(a) * r * 0.92, cy + math.sin(a) * r * 0.92, rr, rr, fill=color)
    c.ellipse(cx, cy, r * 0.96, r * 0.96, fill=color, outline=darker(color, 0.25), width=max(3, r * 0.03))
    c.ellipse(cx - r * 0.34, cy - r * 0.44, r * 0.2, r * 0.12, fill=mix(color, "#FFFFFF", 0.55))


def r_color(X, c, seg):
    L, d, t = X.L, seg.data, X.t
    hexc = d["hex"]
    p = X.cue_p(seg, 0, 0.55)
    if L.v:
        bx, by, br = L.scx, L.sy0 + 160, 150
        slots = [(L.scx - 140, L.sy0 + 460), (L.scx + 140, L.sy0 + 460), (L.scx - 140, L.sy0 + 620), (L.scx + 140, L.sy0 + 620)]
        isz = 150
    else:
        bx, by, br = L.sx0 + 255, L.scy - 10, 205
        slots = [(L.sx0 + 640, L.scy - 140), (L.sx0 + 860, L.scy - 140), (L.sx0 + 640, L.scy + 120), (L.sx0 + 860, L.scy + 120)]
        isz = 185
    if p > 0.02:
        splash(c, bx, by, br * min(p, 1.1) * X.pulse, hexc)
        c.text(bx, by, cap(d["name"]), br * 0.62 * min(p, 1.1), "#FFFFFF", stroke=max(5, br * 0.05), stroke_fill=darker(hexc, 0.5))
    burst(c, bx, by, t, seg.cues[0].t, n=8, r0=br * 1.0, r1=br * 1.45)
    for k, (w, code) in enumerate(d["items"][:4]):
        pk = X.cue_p(seg, 1 + k, 0.45)
        sx, sy = slots[k]
        icon(c, code, sx, sy, isz, hexc, p=pk)
        if pk > 0.5:
            label(c, cap(w), sx, sy + isz / 2 + 24, 38, darker(hexc, 0.1), 1.0, isz * 1.4)


def r_letter(X, c, seg):
    L, d, t = X.L, seg.data, X.t
    col = RINGS[(ord(d["L"]) - 65) % len(RINGS)]
    if L.v:
        cx, cy, cw, ch = L.scx, L.sy0 + 170, 440, 320
        ex, ey, esz = L.scx, L.sy0 + 485, 290
    else:
        cx, cy, cw, ch = L.sx0 + 245, L.scy - 10, 430, 440
        ex, ey, esz = L.sx0 + 725, L.scy - 40, 310
    p = X.cue_p(seg, 0, 0.55)
    if p > 0.02:
        s = min(p, 1.1) * X.pulse
        c.rrect(cx - cw / 2 * s, cy - ch / 2 * s, cx + cw / 2 * s, cy + ch / 2 * s, 56, fill=col, outline="#FFFFFF", width=10)
        c.text(cx, cy + 8, d["L"] + d["L"].lower(), ch * 0.62 * min(p, 1.1), "#FFFFFF", stroke=8, stroke_fill=darker(col, 0.45))
    p1 = X.cue_p(seg, 1, 0.5)
    icon(c, d["code"], ex, ey, esz, col, p=p1)
    burst(c, ex, ey, t, seg.cues[1].t, n=8, r0=esz * 0.6, r1=esz * 0.95)
    label(c, cap(d["word"]), ex, ey + esz / 2 + 52, 88, col, p1, L.sw * 0.5 if not L.v else L.sw - 60)


def r_shape(X, c, seg):
    L, d, t = X.L, seg.data, X.t
    hexc = d["hex"]
    p = X.cue_p(seg, 0, 0.55)
    if L.v:
        sx, sy, ssz = L.scx, L.sy0 + 170, 330
        lx, ly = L.scx, L.sy0 + 405
        slots = [(L.scx - 200, L.sy0 + 560), (L.scx, L.sy0 + 560), (L.scx + 200, L.sy0 + 560)]
        isz, vert = 170, False
    else:
        sx, sy, ssz = L.sx0 + 255, L.scy - 40, 340
        lx, ly = L.sx0 + 255, L.scy + 195
        slots = [(L.sx0 + 700, L.sy0 + 90), (L.sx0 + 700, L.sy0 + 255), (L.sx0 + 700, L.sy0 + 420)]
        isz, vert = 150, True
    if p > 0.02:
        draw_shape(c, d["name"], sx, sy, ssz * min(p, 1.1) * X.pulse, hexc)
    burst(c, sx, sy, t, seg.cues[0].t, n=8, r0=ssz * 0.6, r1=ssz * 0.95)
    label(c, cap(d["name"]), lx, ly, 92, hexc, p, L.sw * 0.5 if not L.v else L.sw - 60)
    for k, (w, code) in enumerate(d["items"][:3]):
        pk = X.cue_p(seg, 3 + k, 0.45)
        x, y = slots[k]
        icon(c, code, x, y, isz, hexc, p=pk)
        if pk > 0.5:
            if vert:
                c.text(x + isz / 2 + 25, y, cap(w), 46, INK, anchor="lm")
            else:
                label(c, cap(w), x, y + isz / 2 + 26, 36, darker(hexc, 0.1), 1.0, 200)


def r_pair(X, c, seg):
    L, d, t = X.L, seg.data, X.t
    big, small = (330, 150) if d["size"] else (270, 270)
    if L.v:
        big, small = (330, 170) if d["size"] else (250, 250)
        pa, pb = (L.scx, L.sy0 + 125), (L.scx, L.sy0 + 470)
        la, lb = L.sy0 + 300, L.sy0 + 635
        if d["size"]:
            pb = (L.scx, L.sy0 + 450)
            lb = L.sy0 + 595
    else:
        pa, pb = (L.scx - 245, L.scy - 30), (L.scx + 245, L.scy - 30 + (60 if d["size"] else 0))
        la, lb = L.scy + 190, L.scy + 190
    for k, (word, code, sz, pos, ly) in enumerate(((d["a"], d["ca"], big, pa, la), (d["b"], d["cb"], small, pb, lb))):
        p = X.cue_p(seg, k, 0.5)
        col = RINGS[(k * 3 + 1) % len(RINGS)]
        icon(c, code, pos[0], pos[1], sz * (X.pulse if p > 0.9 else 1.0), col, p=p)
        label(c, cap(word), pos[0], ly, 90, col, p, L.sw * 0.45 if not L.v else L.sw - 60)
        burst(c, pos[0], pos[1], t, seg.cues[k].t, n=8, r0=sz * 0.6, r1=sz * 0.9)


def r_phrase(X, c, seg):
    L, d, t = X.L, seg.data, X.t
    pc = X.cue_p(seg, 0, 0.5)
    if L.v:
        ex, ey, esz = L.scx, L.sy0 + 155, 290
        bx, by, bw, bh = L.scx, L.sy0 + 470, 620, 250
        ty = L.sy0 + 625
    else:
        ex, ey, esz = L.sx0 + 118, L.scy - 40, 220
        bx, by, bw, bh = L.sx0 + 615, L.scy - 40, 690, 270
        ty = L.scy + 150
    icon(c, d["code"], ex, ey, esz, "#FFB400", p=pc)
    p1 = X.cue_p(seg, 1, 0.45)
    spoken = [cu for cu in seg.cues if cu.tag == "phrase"]
    flash = any(0 <= t - cu.t < 0.5 for cu in spoken)
    if p1 > 0.02:
        s = min(p1, 1.08) * (1.03 if flash else 1.0)
        col = "#FF6FAE" if not flash else "#FF3D8B"
        c.rrect(bx - bw / 2 * s, by - bh / 2 * s, bx + bw / 2 * s, by + bh / 2 * s, 60, fill="#FFFFFF", outline=col, width=8)
        tail = [(bx - bw * 0.30, by + bh / 2 * s - 4), (bx - bw * 0.42, by + bh / 2 * s + 60), (bx - bw * 0.16, by + bh / 2 * s - 4)]
        c.poly(tail, fill="#FFFFFF")
        c.line(tail[:2], col, 8)
        c.line(tail[1:], col, 8)
        c.text_fit(bx, by, d["text"], 96 * s, "#3B2A1A", bw - 70)
    k_think = next((k for k, cu in enumerate(seg.cues) if cu.tag == "think"), -1)
    if k_think >= 0 and X.started(seg, k_think):
        cu = seg.cues[k_think]
        if t < cu.t + cu.slot:
            label(c, "Your turn!", L.scx + (0 if L.v else 110), ty, 74, "#3DB54A", pop(t, cu.t, 0.4) * X.pulse, L.sw - 40)


def r_review(X, c, seg):
    L, d, t = X.L, seg.data, X.t
    items = d["items"]
    n = len(items)
    cols = 3 if L.v else (4 if n <= 8 else 5)
    region = (L.sx0, L.sy0 + 10, L.sx1, L.sy1 - 95)
    pos, cell = grid_pos(n, region, cols)
    size = min(cell * 0.86, 210)
    cur = X.n_started(seg, "item") - 1
    for i, ((lab, ref), (x, y)) in enumerate(zip(items, pos)):
        p = pop(t, seg.v0 + 0.05 + i * 0.07, 0.4)
        on = i == cur
        s = size * (1.18 if on else 1.0) * (X.pulse if on else 1.0)
        dy = -10 * abs(math.sin(math.pi * X.ph)) if on else 0
        icon(c, ref, x, y + dy, s, GREEN if on else RINGS[i % len(RINGS)], p=p)
    if cur >= 0:
        lab = items[cur][0]
        label(c, lab, L.scx, L.sy1 - 36, 84, "#FF6FAE", pop(t, seg.cues[1 + cur].t, 0.35), L.sw - 40)


def r_quiz(X, c, seg):
    L, d, t = X.L, seg.data, X.t
    opts, ans, show = d["options"], d["answer"], d.get("show")
    q = seg.cues[0]
    label(c, q.text, L.scx, L.sy0 + (50 if L.v else 38), 52 if not L.v else 50, "#3E8EDE", pop(t, seg.v0 + 0.05, 0.5), L.sw - 30)
    if show:
        region = (L.sx0, L.sy0 + 95, L.sx1, L.sy0 + (260 if not L.v else 330))
        pos, cell = grid_pos(show["n"], region, 5)
        sz = min(cell * 0.94, 100 if not L.v else 118)
        for i, (x, y) in enumerate(pos):
            icon(c, show["code"], x, y, sz, plate_on=False, p=pop(t, q.t + 0.1 + i * 0.05, 0.35))
    oy = L.scy + (110 if show else 30) if not L.v else L.sy0 + (500 if show else 330)
    osz = (190 if show else 230) if not L.v else 190
    gap = 300 if not L.v else 215
    answered = X.started(seg, 2)
    for i, (lab, ref) in enumerate(opts):
        x = L.scx + (i - (len(opts) - 1) / 2) * gap
        p = pop(t, q.t + 0.15 + 0.12 * i, 0.45)
        s = osz
        ring = RINGS[i % len(RINGS)]
        if answered:
            if i == ans:
                s = osz * 1.2 * (X.pulse if t - seg.cues[2].t < 1.6 else 1.0)
                ring = GREEN
            else:
                s = osz * 0.78
        icon(c, ref, x, oy, s, ring, p=p)
        if answered and i == ans:
            c.arc(x, oy, s / 2 + 10, s / 2 + 10, 0, 360, GREEN, 8)
            if ref[:2] not in ("n:", "L:", "S:") and not ref.startswith("#"):
                label(c, cap(lab), x, oy + s / 2 + 34, 44, GREEN, 1.0, 280)
            burst(c, x, oy, t, seg.cues[2].t, n=10, r0=s * 0.6, r1=s * 1.0, size=18, dur=1.0)
    k_think = 1
    cu = seg.cues[k_think]
    if cu.t <= t < cu.t + cu.slot:
        k = int((t - cu.t) / X.beat)
        num = max(1, 3 - k)
        loc = (t - cu.t) / X.beat - k
        r = 52 * (1.0 + 0.12 * math.exp(-loc * 6))
        cx, cy = L.scx, L.sy1 - (45 if not L.v else 60)
        c.ellipse(cx, cy, r, r, fill="#FFB400", outline="#FFFFFF", width=6)
        c.text(cx, cy + 3, str(num), r * 1.3, "#FFFFFF", stroke=4, stroke_fill="#B26A00")


def r_outro(X, c, seg):
    L, t = X.L, X.t
    label(c, "See you next time!", L.scx if L.v else L.w / 2, L.sy0 + (90 if L.v else 70), 92 if not L.v else 80, "#FF6FAE",
          X.cue_p(seg, 0, 0.6), L.w - 60)
    cx = L.w / 2
    sc = L.w / 1280.0
    y = L.sy0 + (330 if L.v else 330)
    if L.v:
        D.pip(c, 150, y + 250, 0.95, t, "open" if X.amp is not None else "smile", (4, -2))
        D.mo(c, 570, y + 250, 0.85, t, "open" if X.amp is not None else "smile", (-4, -2))
        D.lila(c, 360, y + 520, 0.9, t, "open" if X.amp is not None else "smile", (0, -2))
        bibi_at(X, c, 360, y - 30, 1.7)
    else:
        D.pip(c, 330, y + 90, 1.05, t, "smile", (4, -2))
        D.mo(c, 960, y + 110, 0.95, t, "smile", (-4, -2))
        D.lila(c, 1130, y + 80, 0.95, t, "smile", (-4, -2))
        bibi_at(X, c, 640, y + 20, 1.6)
    for k in range(6):
        u = ((t - seg.t0) * 0.35 + k / 6.0) % 1.0
        D.heart(c, cx + math.sin(k * 2.3 + t * 1.3) * L.w * 0.38, L.sy1 - u * 520, 16 + 6 * math.sin(k), "#FF5C8A")


def r_cta(X, c, seg):
    """The Like / Subscribe card right before the goodbye (YouTube has no comments, end screens or subscribe watermark on kids videos)."""
    L, t = X.L, X.t - seg.t0
    t_like, t_sub = SCH.cta_times(X.lesson)
    D.cta(c, L.w / 2, L.sy0 + (150 if L.v else 130), t, min(1.0, (L.w - 70) / 820.0), t_like, t_sub)
    mood = "open" if X.amp is not None else "smile"
    y = L.sy0 + 330
    if L.v:
        D.pip(c, 150, y + 250, 0.95, X.t, mood, (4, -2))
        D.mo(c, 570, y + 250, 0.85, X.t, mood, (-4, -2))
        D.lila(c, 360, y + 255, 0.85, X.t, mood, (0, -2))
        bibi_at(X, c, 360, y + 20, 1.5)
    else:
        D.pip(c, 330, y + 100, 1.05, X.t, "smile", (4, -2))
        D.mo(c, 960, y + 120, 0.95, X.t, "smile", (-4, -2))
        D.lila(c, 1130, y + 90, 0.95, X.t, "smile", (-4, -2))
        bibi_at(X, c, 640, y + 70, 1.5)
    for k in range(6):
        u = ((X.t - seg.t0) * 0.35 + k / 6.0) % 1.0
        D.heart(c, L.w / 2 + math.sin(k * 2.3 + X.t * 1.3) * L.w * 0.38, L.sy1 - u * 520, 16 + 6 * math.sin(k), "#FF5C8A")


RENDERERS = {"title": r_title, "card": r_card, "count": r_count, "number": r_number, "color": r_color,
             "letter": r_letter, "shape": r_shape, "pair": r_pair, "phrase": r_phrase, "review": r_review,
             "quiz": r_quiz, "cta": r_cta, "outro": r_outro}
OWN_BIBI = {"title", "cta", "outro"}


# --------------------------------------------------------------------------------- caption
def caption(c, L, text, progress):
    words = text.split()
    if not words:
        return
    size = L.cap_size if len(text) < 70 else L.cap_size - 4
    f = D.font(size)
    lines, cur = [], []
    for wd in words:
        if cur and f.getlength(" ".join(cur + [wd])) / SS > L.cap_w:
            lines.append(cur)
            cur = [wd]
        else:
            cur.append(wd)
    lines.append(cur)
    lh = size * 1.32
    widths = [[f.getlength(w + " ") / SS for w in ln] for ln in lines]
    line_w = [sum(ws) - f.getlength(" ") / SS for ws in widths]
    pad = 34
    bh = lh * len(lines) + 22
    bw = max(line_w) + 2 * pad
    cx = L.w / 2
    y1 = L.cap_bottom
    y0 = y1 - bh
    c.rrect(cx - bw / 2, y0, cx + bw / 2, y1, min(40, bh / 2), fill="#FFFFFF", outline="#FF9BC0", width=4)
    idx = int(clamp(progress) * len(words) * 0.98)
    k = 0
    for li, (ln, ws) in enumerate(zip(lines, widths)):
        x = cx - line_w[li] / 2
        y = y0 + 11 + lh * (li + 0.5)
        for w, wd in zip(ln, ws):
            c.text(x, y, w, size, "#FF4F86" if k <= idx else "#2B3A55", anchor="lm")
            x += wd
            k += 1


def chip(c, L):
    x, y = L.chip
    c.rrect(x - 118, y - 25, x + 118, y + 25, 25, fill="#FFF6C2", outline="#FFB400", width=3)
    c.text(x, y + 1, "Bibi Buzz TV", 29, "#9A5A00")


# ----------------------------------------------------------------------------------- frame
def find_seg(lesson, t):
    segs = lesson.segs
    if t < segs[0].t0:
        return segs[0]
    for s in segs:
        if s.t0 <= t < s.t1:
            return s
    return segs[-1]


def render_frame(lesson, t):
    L = layout(lesson.fmt)
    seg = find_seg(lesson, t)
    img = background(L, lesson.theme).copy()
    c = Canvas(img, w=L.w, h=L.h)
    decor(c, L, lesson.theme, t)
    chip(c, L)
    X = Ctx(lesson, L, t)
    RENDERERS[seg.kind](X, c, seg)
    if seg.kind not in OWN_BIBI:
        bx, by, bk = L.bibi
        bibi_at(X, c, bx, by, bk)
    # caption of the active cue
    for cu in seg.cues:
        if cu.tag in CAPTION_TAGS and cu.shown and cu.t <= t < cu.t + cu.slot:
            caption(c, L, cu.shown, (t - cu.t) / max(0.2, cu.dur))
            break
    out = c.final()
    if t < 0.4:
        out = Image.blend(out, Image.new("RGB", out.size, "white"), 1 - t / 0.4)
    tail = lesson.duration - t
    if tail < 1.0:
        out = Image.blend(out, Image.new("RGB", out.size, "black"), clamp(1 - tail / 1.0))
    return out


def sample_times(lesson):
    """One representative moment per segment (everything of the segment visible)."""
    out = []
    for s in lesson.segs:
        out.append(min(s.t1 - 0.15, s.cues[-1].t + min(1.0, max(0.3, s.cues[-1].dur * 0.8))))
    return out
