"""Extra life for the lesson videos: things that fly, swim, sway and twinkle behind the pictures (birds, butterflies, balloons,
fish, jellyfish, fireflies, shooting stars, swaying grass and seaweed, floating candy), light rays and orbiting stars around the
big pictures, and a shower of confetti.

Everything is drawn with the Canvas of draw.py and is a pure function of the time t, so frames can still be drawn in parallel.
A fixed pseudo random number per object (_rnd) replaces a random generator, so the same time always gives the same frame.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from . import draw as D
from .draw import INK, clamp, lerp, mix, darker, ellipse_pts, bez

CONFETTI = ["#FF6FAE", "#FFD23F", "#3E8EDE", "#3DB54A", "#FF8A1F", "#9B59D0", "#00B8D4", "#E8383D"]


def _frac(x):
    return x - math.floor(x)


def _rnd(i, k=0):
    """A fixed pseudo random number in 0..1 for the pair (i, k)."""
    return _frac(math.sin(i * 12.9898 + k * 78.233 + 1.7) * 43758.5453)


# ------------------------------------------------------------------------------------------------ little things
def sparkle(c, x, y, r, color, ang=0.0):
    """A four-pointed twinkle."""
    pts = []
    for i in range(8):
        rr = r if i % 2 == 0 else r * 0.26
        a = math.radians(ang + i * 45)
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    c.poly(pts, fill=color)


def bird(c, x, y, s, t, ph, body, face=1):
    """A chubby little bird in profile with flapping wings (face = +1 flies to the right)."""
    fl = math.sin(t * 9.0 + ph)                                        # +1 wing up .. -1 wing down
    y += math.sin(t * 4.5 + ph) * 1.6 * s
    ink = darker(body, 0.55)
    c.poly([(x - face * 10 * s, y + 1 * s), (x - face * 25 * s, y - 6 * s), (x - face * 24 * s, y + 6 * s)], fill=darker(body, 0.18), outline=ink, width=1.4 * s)
    wing = [(x - face * 1 * s, y - 4 * s), (x - face * (14 + 5 * fl) * s, y - (4 + 19 * fl) * s), (x - face * 13 * s, y + 2 * s)]
    c.poly(wing, fill=darker(body, 0.12), outline=ink, width=1.4 * s)
    c.ellipse(x, y, 14 * s, 10 * s, fill=body, outline=ink, width=1.6 * s)
    c.ellipse(x + face * 3 * s, y + 4 * s, 8 * s, 5 * s, fill=mix(body, "#FFFFFF", 0.6))
    c.ellipse(x + face * 11 * s, y - 7 * s, 7.5 * s, 7 * s, fill=body, outline=ink, width=1.6 * s)
    c.poly([(x + face * 17 * s, y - 9 * s), (x + face * 26 * s, y - 5 * s), (x + face * 17 * s, y - 3 * s)], fill="#FF9F1C", outline=ink, width=1.2 * s)
    c.ellipse(x + face * 12 * s, y - 8 * s, 2.6 * s, 2.8 * s, fill="#FFFFFF")
    c.ellipse(x + face * 12.8 * s, y - 8 * s, 1.4 * s, 1.6 * s, fill=INK)
    c.poly([(x - face * 2 * s, y - 4 * s), (x - face * (12 + 4 * fl) * s, y - (3 + 14 * fl) * s), (x - face * 12 * s, y + 1 * s)], fill=body, outline=ink, width=1.2 * s)


def butterfly(c, x, y, s, t, ph, c1, c2):
    flap = 0.30 + 0.70 * abs(math.sin(t * 8.5 + ph))
    for sd in (-1, 1):
        c.poly(ellipse_pts(x + sd * 10 * s * flap, y - 7 * s, 12 * s * flap, 9 * s, ang=-sd * 32, n=24), fill=c1, outline=darker(c1, 0.35), width=1.3 * s)
        c.poly(ellipse_pts(x + sd * 8 * s * flap, y + 7 * s, 9 * s * flap, 7 * s, ang=sd * 32, n=24), fill=c2, outline=darker(c2, 0.35), width=1.3 * s)
        c.ellipse(x + sd * 12 * s * flap, y - 9 * s, 3 * s * flap, 2.6 * s, fill="#FFFFFF")
    c.ellipse(x, y, 2.2 * s, 10 * s, fill=INK)
    for sd in (-1, 1):
        c.line([(x, y - 9 * s), (x + sd * 6 * s, y - 17 * s)], INK, 1.3 * s)


def balloon(c, x, y, s, t, cols=("#FF6FAE", "#FFD23F", "#3E8EDE", "#3DB54A")):
    """A hot air balloon with a basket, swaying a little."""
    rx, ry = 40 * s, 48 * s
    sw = math.sin(t * 1.3) * 4 * s
    bx, by = x + sw, y + ry + 40 * s
    for dx in (-17, 17):
        c.line([(x + dx * s, y + ry * 0.8), (bx + dx * 0.5 * s, by - 8 * s)], INK, 1.6 * s)
    c.rrect(bx - 15 * s, by - 8 * s, bx + 15 * s, by + 10 * s, 4 * s, fill="#C98A4B", outline=INK, width=2 * s)
    c.ellipse(x, y, rx, ry, fill=cols[0])
    with c.clip_ellipse(x, y, rx, ry) as cc:
        n = 6
        for i in range(n):
            cc.rect(x - rx + i * (2 * rx / n), y - ry - 3, x - rx + (i + 1) * (2 * rx / n), y + ry + 3, cols[i % len(cols)])
        cc.ellipse(x - rx * 0.38, y - ry * 0.42, rx * 0.2, ry * 0.1, fill="#FFFFFF")
    c.ellipse(x, y, rx, ry, outline=INK, width=2.4 * s)
    c.poly([(x - 9 * s, y + ry - 2 * s), (x + 9 * s, y + ry - 2 * s), (x + 6 * s, y + ry + 8 * s), (x - 6 * s, y + ry + 8 * s)], fill=darker(cols[0], 0.2), outline=INK, width=1.6 * s)


def fish(c, x, y, s, t, ph, col, face=1):
    wag = math.sin(t * 6.5 + ph)
    ink = darker(col, 0.5)
    c.poly([(x - face * 18 * s, y), (x - face * 36 * s, y - (13 - 3 * wag) * s + wag * 5 * s), (x - face * 36 * s, y + (13 + 3 * wag) * s + wag * 5 * s)], fill=darker(col, 0.12), outline=ink, width=1.8 * s)
    c.poly([(x - face * 4 * s, y - 12 * s), (x + face * 8 * s, y - 20 * s), (x + face * 12 * s, y - 11 * s)], fill=darker(col, 0.12), outline=ink, width=1.6 * s)
    c.ellipse(x, y, 25 * s, 15 * s, fill=col, outline=ink, width=2 * s)
    c.ellipse(x + face * 2 * s, y + 6 * s, 16 * s, 6 * s, fill=mix(col, "#FFFFFF", 0.55))
    c.arc(x - face * 7 * s, y, 9 * s, 12 * s, 90 if face > 0 else 270, 270 if face > 0 else 450, ink, 1.6 * s)
    c.ellipse(x + face * 13 * s, y - 3 * s, 4.4 * s, 4.6 * s, fill="#FFFFFF", outline=ink, width=1.2 * s)
    c.ellipse(x + face * 14.5 * s, y - 3 * s, 2.2 * s, 2.4 * s, fill=INK)
    c.arc(x + face * 20 * s, y + 5 * s, 4 * s, 3 * s, 20, 160, ink, 1.4 * s)


def jelly(c, x, y, s, t, ph, col="#FF9BD2"):
    pulse = 1.0 + 0.08 * math.sin(t * 2.4 + ph)
    for i in range(5):
        tx = x + (i - 2) * 9 * s
        pts = [(tx + math.sin(t * 3.0 + ph + i * 0.9 + j * 0.8) * 3.6 * s * (0.3 + j / 5.0), y + 8 * s + j * 9 * s * pulse) for j in range(6)]
        c.line(pts, mix(col, "#FFFFFF", 0.25), 3.2 * s)
    dome = [(x + math.cos(math.pi * k / 20) * 26 * s, y + 8 * s - math.sin(math.pi * k / 20) * 24 * s * pulse) for k in range(21)]
    c.poly(dome, fill=col, outline=darker(col, 0.35), width=2 * s)
    for i in range(5):
        c.ellipse(x + (i - 2) * 10.4 * s, y + 8 * s, 5.4 * s, 4.2 * s, fill=col, outline=darker(col, 0.35), width=1.6 * s)
    c.ellipse(x - 9 * s, y - 6 * s * pulse, 3.4 * s, 3.8 * s, fill=INK)
    c.ellipse(x + 9 * s, y - 6 * s * pulse, 3.4 * s, 3.8 * s, fill=INK)
    c.ellipse(x - 14 * s, y - 0.5 * s * pulse, 4 * s, 2.8 * s, fill="#FF6F9A")
    c.ellipse(x + 14 * s, y - 0.5 * s * pulse, 4 * s, 2.8 * s, fill="#FF6F9A")
    c.arc(x, y - 1 * s * pulse, 5 * s, 4 * s, 20, 160, INK, 1.8 * s)
    c.ellipse(x - 9 * s, y - 15 * s * pulse, 6 * s, 3 * s, fill=mix(col, "#FFFFFF", 0.6))


def seaweed(c, x, ground, h, t, ph, col="#2FA84F"):
    n = 9
    pts = [(x + math.sin(t * 1.7 + ph + j * 0.55) * (j / n) * 16, ground - h * j / n) for j in range(n + 1)]
    c.line(pts, darker(col, 0.4), 14)
    c.line(pts, col, 9)
    c.line([(px + 1.5, py) for px, py in pts[2:]], mix(col, "#FFFFFF", 0.35), 2)


def lollipop(c, x, y, s, t, ph, col):
    a = math.sin(t * 1.6 + ph) * 0.18
    c.line([(x, y + 4 * s), (x - math.sin(a) * 40 * s, y + 44 * s)], "#FFFFFF", 5 * s)
    c.line([(x, y + 4 * s), (x - math.sin(a) * 40 * s, y + 44 * s)], "#E4D2F0", 2 * s)
    c.ellipse(x, y, 20 * s, 20 * s, fill=col, outline=darker(col, 0.35), width=2 * s)
    for k in range(3):
        c.arc(x, y, (6 + 5 * k) * s, (6 + 5 * k) * s, 200 + 120 * k + t * 40, 330 + 120 * k + t * 40, "#FFFFFF", 2.4 * s)


def wrapped_candy(c, x, y, s, t, ph, col):
    a = math.sin(t * 1.9 + ph) * 12
    for sd in (-1, 1):
        c.poly([(x + sd * 12 * s, y), (x + sd * 26 * s, y - 11 * s), (x + sd * 26 * s, y + 11 * s)], fill=mix(col, "#FFFFFF", 0.35), outline=darker(col, 0.35), width=1.6 * s)
    c.poly(ellipse_pts(x, y, 15 * s, 11 * s, ang=a, n=26), fill=col, outline=darker(col, 0.35), width=2 * s)
    c.arc(x, y, 8 * s, 6 * s, 200, 320, "#FFFFFF", 2 * s)


def cloud_tint(c, cx, cy, s, color):
    for dx, dy, r in ((-46, 8, 30), (-14, -10, 38), (24, -4, 34), (54, 10, 26), (4, 14, 34)):
        c.ellipse(cx + dx * s, cy + dy * s, r * s, r * s, fill=color)


def shooting_star(c, w, h, t, period=8.0, dur=1.05, seed=0, top=0.05, bottom=0.30):
    k = int(t // period)
    u = (t - k * period) / dur
    if u < 0 or u > 1:
        return
    r = _rnd(k, seed)
    sgn = -1 if r > 0.5 else 1
    x0 = lerp(0.2, 0.8, _rnd(k, seed + 1)) * w
    y0 = lerp(top, bottom, _rnd(k, seed + 2)) * h
    dx, dy = sgn * 0.34 * w, 0.20 * w
    hx, hy = x0 + dx * u, y0 + dy * u
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    L = 0.26 * w * (1 - 0.4 * u)
    c.poly([(hx - uy * 7, hy + ux * 7), (hx - ux * L, hy - uy * L), (hx + uy * 7, hy - ux * 7)], fill="#FFF6C8")
    c.poly([(hx - uy * 3.5, hy + ux * 3.5), (hx - ux * L * 0.6, hy - uy * L * 0.6), (hx + uy * 3.5, hy - ux * 3.5)], fill="#FFFFFF")
    D.star(c, hx, hy, 11, "#FFE066", ang=u * 300)


def firefly(c, x, y, t, ph, glow_bg="#4A4AA8"):
    g = 0.5 + 0.5 * math.sin(t * 2.2 + ph)
    c.ellipse(x, y, 13 + 6 * g, 13 + 6 * g, fill=mix(glow_bg, "#C8E64C", 0.16 + 0.12 * g))
    c.ellipse(x, y, 8 + 3 * g, 8 + 3 * g, fill=mix(glow_bg, "#E8F26A", 0.45 + 0.2 * g))
    c.ellipse(x, y, 4.6, 4.6, fill=mix("#FFF3A0", "#FFFFFF", g * 0.7))


# ------------------------------------------------------------------------------------------------ light rays and stars
def rays(c, cx, cy, r0, r1, t, color, n=12, spin=14.0, width=0.20):
    """Slowly turning rays behind a big picture (the picture's own plate hides their bases)."""
    for i in range(n):
        a = math.radians(t * spin + i * 360.0 / n)
        da = math.radians(360.0 / n * width)
        c.poly([(cx + math.cos(a - da) * r0, cy + math.sin(a - da) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1),
                (cx + math.cos(a + da) * r0, cy + math.sin(a + da) * r0)], fill=color)


def orbit(c, cx, cy, r, t, n=5, size=13, colors=("#FFD23F", "#FF6FAE", "#FFFFFF"), speed=38.0):
    for i in range(n):
        a = math.radians(t * speed + i * 360.0 / n)
        rr = r * (1.0 + 0.05 * math.sin(t * 2.0 + i * 1.7))
        sparkle(c, cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.92, size * (0.75 + 0.25 * math.sin(t * 5 + i * 2)), colors[i % len(colors)], ang=t * 60 + i * 20)


def confetti(c, w, h, t, t0, dur=3.4, n=64, seed=1):
    """Paper confetti that falls from the top of the screen from t0 on."""
    u = t - t0
    if u < 0 or u > dur:
        return
    for i in range(n):
        uu = u - _rnd(i, seed + 2) * 0.55
        if uu < 0:
            continue
        y = -30 + uu * (230 + 230 * _rnd(i, seed + 1))
        if y > h + 30:
            continue
        x = _rnd(i, seed) * w + math.sin(uu * 3.0 + i) * 26
        a = math.radians(uu * (160 + 320 * _rnd(i, seed + 3)) + i * 41)
        pw, ph = 5 + 4 * _rnd(i, seed + 4), 9 + 6 * _rnd(i, seed + 5)
        ca, sa = math.cos(a), math.sin(a)
        sq = abs(math.cos(uu * 4 + i))                                   # the paper turns over
        pts = [(x + ca * px * sq - sa * py, y + sa * px * sq + ca * py) for px, py in ((-pw, -ph), (pw, -ph), (pw, ph), (-pw, ph))]
        c.poly(pts, fill=CONFETTI[i % len(CONFETTI)])


# ------------------------------------------------------------------------------------------------ whole backgrounds
BIRD_COLORS = ("#4A8FE7", "#FF7A59", "#F5B82E", "#E85D9A")
BUTTERFLIES = (("#FF9F1C", "#FFD166"), ("#FF6FAE", "#FFC2E2"), ("#4FC3F7", "#B3E5FC"))


def grass(c, w, g, t, color, flower_cols=("#FFFFFF", "#FFE066", "#FF9BD2", "#B58CF2"), flowers=True):
    n = int(w / 38)
    for i in range(n):
        x = (i + 0.5 + (_rnd(i, 3) - 0.5) * 0.7) * w / n
        h = 15 + 15 * _rnd(i, 4)
        sway = math.sin(t * 2.0 + i * 0.7) * 4.5
        base = g + 10 + 16 * _rnd(i, 5)
        for dx, hh in ((-6, 0.65), (0, 1.0), (6, 0.8)):
            c.poly([(x + dx - 3, base), (x + dx + sway * hh, base - h * hh), (x + dx + 3, base)], fill=darker(color, 0.12) if dx else color)
    if flowers:
        for i in range(max(4, int(w / 150))):
            x = (i + 0.3 + 0.5 * _rnd(i, 8)) * w / max(4, int(w / 150))
            hh = 44 + 26 * _rnd(i, 9)
            base = g + 14 + 12 * _rnd(i, 10)
            sway = math.sin(t * 1.8 + i * 1.3) * 5
            top = (x + sway, base - hh)
            c.line(bez((x, base), (x + sway * 0.2, base - hh * 0.6), top, 10), "#3DA84A", 3.4)
            D.mini_flower(c, top[0], top[1], 15 + 4 * _rnd(i, 11), flower_cols[i % len(flower_cols)], t + i)


def day_ambient(c, L, th, t):
    """Birds, butterflies and a balloon in the sky, swaying grass and flowers on the ground (park, sunset and candy backdrops)."""
    w, h, g = L.w, L.h, L.ground
    cycle = 24.0
    k = int((t + 4.0) // cycle)
    u = ((t + 4.0) - k * cycle) / cycle
    face = 1 if k % 2 == 0 else -1
    x0 = -90 + u * (w + 180) if face > 0 else w + 90 - u * (w + 180)
    yb = (0.16 if not L.v else 0.20) * h
    for i, (dx, dy) in enumerate(((0, 0), (-1.0, -30), (-1.0, 30))):
        bx = x0 + dx * 70 * face * (1 if dx else 0)
        bird(c, bx, yb + dy + 14 * math.sin(u * 14 + i), 1.4, t, i * 0.9, BIRD_COLORS[(k + i) % len(BIRD_COLORS)], face)
    if th != "candy":
        cyc2 = 70.0
        u2 = ((t + 20.0) % cyc2) / cyc2
        balloon(c, w + 90 - u2 * (w + 200), (0.30 if not L.v else 0.26) * h + 12 * math.sin(t * 0.7), 1.05 if not L.v else 0.85, t)
    else:
        for i in range(5):
            x = w * (0.08 + 0.2 * i) + math.sin(t * 0.5 + i) * 18
            y = h * 0.78 - ((t * 22 + i * 190) % (h * 0.8)) + h * 0.05
            (lollipop if i % 2 == 0 else wrapped_candy)(c, x, y, 1.15, t, i, CONFETTI[(i * 3) % len(CONFETTI)])
    for i, (c1, c2) in enumerate(BUTTERFLIES):
        cx = w * (0.14 + 0.36 * i) + math.sin(t * 0.31 + i * 2.0) * w * 0.07
        cy = h * (0.58 if not L.v else 0.72) + math.sin(t * 0.47 + i * 1.3) * h * 0.06
        bx = cx + math.sin(t * 0.9 + i) * 70
        by = cy + math.sin(t * 1.7 + i * 2.3) * 36
        butterfly(c, bx, by, 1.6, t, i * 1.7, c1, c2)
    gcol = {"park": "#4FB73E", "sunset": "#DA7A24", "candy": "#9561DC"}.get(th, "#4FB73E")
    grass(c, w, g, t, gcol, flowers=th != "candy")


SEA_FISH = (("#FF8A1F", 1.15), ("#FFD23F", 0.85), ("#FF6FAE", 1.0), ("#9B59D0", 0.8), ("#3DD6A5", 0.95), ("#FFFFFF", 0.7))


def sea_ambient(c, L, t):
    w, h, g = L.w, L.h, L.ground
    for i in range(8):
        seaweed(c, w * (0.04 + 0.125 * i) + 24 * _rnd(i, 1), g + 26, 54 + 56 * _rnd(i, 2), t, i * 1.3, ("#2FA84F", "#45C46A", "#1F9A6B")[i % 3])
    for i, (col, sz) in enumerate(SEA_FISH):
        face = 1 if i % 2 == 0 else -1
        sp = 28 + 20 * _rnd(i, 3)
        span = w + 200
        px = (t * sp + _rnd(i, 4) * span) % span
        x = -100 + px if face > 0 else w + 100 - px
        y = h * (0.26 + 0.50 * _rnd(i, 5)) + math.sin(t * 1.3 + i) * 8
        fish(c, x, y, sz * (1.45 if not L.v else 1.3), t, i * 1.1, col, face)
    for i in range(2):
        jelly(c, w * (0.30 + 0.42 * i) + math.sin(t * 0.4 + i * 3) * 40, h * (0.34 + 0.12 * i) + math.sin(t * 0.9 + i) * 22, 1.5, t, i * 2.0, ("#FF9BD2", "#C9A3FF")[i])


def night_ambient(c, L, t):
    w, h, g = L.w, L.h, L.ground
    for i, (x0, y0, sp) in enumerate(((0.10, 0.20, 7), (0.55, 0.32, 5), (0.85, 0.12, 9))):
        cloud_tint(c, (w * x0 + t * sp) % (w + 400) - 200, h * y0, 1.1 - 0.15 * i, "#4B4799")
    shooting_star(c, w, h, t)
    for i in range(12):
        fx = w * _rnd(i, 1) + math.sin(t * 0.42 + i * 1.7) * 34
        fy = g * (0.55 + 0.42 * _rnd(i, 2)) + math.cos(t * 0.53 + i * 1.3) * 24
        firefly(c, fx, fy, t, i * 1.9)


def twinkles(c, L, t, color="#FFFFFF"):
    """A few little twinkles near the edges of the picture."""
    w, h = L.w, L.h
    for i in range(7):
        ph = t * 1.6 + i * 2.1
        r = 13.0 * max(0.0, math.sin(ph)) ** 2
        if r > 1.0:
            x = w * (0.06 + 0.88 * _rnd(i, 21))
            y = h * (0.10 + 0.42 * _rnd(i, 22))
            sparkle(c, x, y, r, color, ang=15 * i)


def ambient(c, L, theme, t):
    """The living background of a lesson frame (drawn after the sun / clouds / stars and before the pictures)."""
    if theme in ("park", "sunset", "candy"):
        day_ambient(c, L, theme, t)
        twinkles(c, L, t, "#FFFFFF")
    elif theme == "ocean":
        sea_ambient(c, L, t)
        twinkles(c, L, t, "#FFFFFF")
    elif theme == "night":
        night_ambient(c, L, t)


# ------------------------------------------------------------------------------------------------ scene change
def _wipe_shape(kind):
    """Outline points of the wipe's hole, scaled to a circumradius of 1."""
    if kind == "star":
        pts = [(math.cos(math.radians(-90 + i * 36)) * (1.0 if i % 2 == 0 else 0.56),
                math.sin(math.radians(-90 + i * 36)) * (1.0 if i % 2 == 0 else 0.56)) for i in range(10)]
    elif kind == "heart":
        pts = []
        for i in range(60):
            a = 2 * math.pi * i / 60
            pts.append((16 * math.sin(a) ** 3, -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)) + 2.5))
    else:
        pts = [(math.cos(2 * math.pi * i / 48), math.sin(2 * math.pi * i / 48)) for i in range(48)]
    big = max(math.hypot(x, y) for x, y in pts)
    return [(x / big, y / big) for x, y in pts]


_shapes = {}


def wipe(new, old, u, kind="circle", cx=None, cy=None, edge=9.0):
    """Reveals the picture `new` on top of `old` (RGB images of the same size) through a hole that grows from (cx, cy) as u goes 0..1.
    The hole is a circle, a star or a heart (with a white rim); at the end a circle takes over so that the whole screen is uncovered."""
    w, h = new.size
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    if kind not in _shapes:
        _shapes[kind] = _wipe_shape(kind)
    pts = _shapes[kind]
    far = math.hypot(max(cx, w - cx), max(cy, h - cy)) + edge + 8
    u = clamp(u)
    e = 1.0 - (1.0 - u) ** 2.0
    r_poly = far * (0.60 if kind != "circle" else 1.0) * e
    r_circ = far * clamp((u - 0.45) / 0.55) ** 1.4 if kind != "circle" else 0.0
    spin = math.radians((1.0 - u) * 110.0) if kind == "star" else 0.0
    ca, sa = math.cos(spin), math.sin(spin)
    ss = 2
    out = old
    for grow, src in ((edge, Image.new("RGB", (w, h), "#FFFFFF")), (0.0, new)):
        m = Image.new("L", (w * ss, h * ss), 0)
        dm = ImageDraw.Draw(m)
        rr = r_poly + grow if r_poly > 1.0 else 0.0
        if rr > 1.0:
            dm.polygon([((cx + (x * ca - y * sa) * rr) * ss, (cy + (x * sa + y * ca) * rr) * ss) for x, y in pts], fill=255)
        rc = r_circ + grow if r_circ > 1.0 else 0.0
        if rc > 1.0:
            dm.ellipse([(cx - rc) * ss, (cy - rc) * ss, (cx + rc) * ss, (cy + rc) * ss], fill=255)
        if rr > 1.0 or rc > 1.0:
            out = Image.composite(src, out, m.resize((w, h), Image.BOX))
    return out


# ------------------------------------------------------------------------------------------------ fairy tales (the 1280x720 screen)
_glows = {}


def glow(c, x, y, r, color, alpha=0.8):
    """A soft round glow of radius r (layout px): Canvas.sprite pastes the RGBA picture with its own transparency."""
    key = (int(r), color, int(round(alpha * 8)))
    if key not in _glows:
        n = max(4, int(2 * r * D.SS))
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        d = np.hypot(xx - n / 2.0, yy - n / 2.0) / (n / 2.0)
        arr = np.zeros((n, n, 4), np.uint8)
        arr[..., 0], arr[..., 1], arr[..., 2] = D.hex2rgb(color)
        arr[..., 3] = (np.clip(1.0 - d, 0.0, 1.0) ** 2 * (key[2] / 8.0) * 255).astype(np.uint8)
        _glows[key] = Image.fromarray(arr, "RGBA")
    c.sprite(_glows[key], x, y)


def leaf(c, x, y, s, ang, col):
    pts = ellipse_pts(x, y, 11 * s, 5.5 * s, ang=ang, n=18)
    c.poly(pts, fill=col, outline=darker(col, 0.4), width=1.2 * s)
    a = math.radians(ang)
    c.line([(x - math.cos(a) * 9 * s, y - math.sin(a) * 9 * s), (x + math.cos(a) * 9 * s, y + math.sin(a) * 9 * s)], darker(col, 0.3), 1.1 * s)


def petal(c, x, y, s, ang, col):
    c.poly(ellipse_pts(x, y, 6 * s, 3.2 * s, ang=ang, n=14), fill=col)


LEAVES = ("#7CC24A", "#F2B134", "#E8743B", "#B7D84B", "#D9A441")


def falling(c, ts, w, h, n, draw, period=11.0, seed=0, sway=46.0, top=-30.0, bottom=None):
    """n things that drift from the top of the screen to the bottom (every one has its own start, speed and swing)."""
    bottom = h + 30.0 if bottom is None else bottom
    for i in range(n):
        per = period * (0.8 + 0.5 * _rnd(i, seed + 1))
        u = ((ts + _rnd(i, seed + 2) * per) % per) / per
        x = _rnd(i, seed + 3) * w + math.sin(u * 9.0 + i) * sway
        y = lerp(top, bottom, u)
        draw(x, y, i, u)


def tale_day(c, ts, w, h, dusk=False, birds=True):
    if birds:
        cyc = 28.0
        for fl in range(2):
            tt = ts + 6.0 + fl * 15.0
            k = int(tt // cyc)
            u = (tt - k * cyc) / 14.0
            if 0.0 <= u <= 1.0:
                face = 1 if (k + fl) % 2 == 0 else -1
                x0 = -140 + u * (w + 280) if face > 0 else w + 140 - u * (w + 280)
                yb = h * (0.10 + 0.07 * fl) + 10 * math.sin(u * 11 + fl)
                for i in range(2):
                    bird(c, x0 - face * i * 64, yb + i * 26, 1.2, ts, i * 0.9 + fl, BIRD_COLORS[(k + i + fl) % 4], face)
    for i, (c1, c2) in enumerate(BUTTERFLIES[:2]):
        cx = w * (0.20 + 0.50 * i) + math.sin(ts * 0.27 + i * 2.0) * w * 0.10
        cy = h * (0.62 if i == 0 else 0.55) + math.sin(ts * 0.43 + i * 1.3) * h * 0.05
        butterfly(c, cx + math.sin(ts * 0.9 + i) * 64, cy + math.sin(ts * 1.7 + i * 2.3) * 30, 1.5, ts, i * 1.7, c1, c2)
    cols = ("#FFFFFF", "#FFC2E2", "#FFE680")
    falling(c, ts, w, h, 6, lambda x, y, i, u: petal(c, x, y, 1.0, ts * 90 + i * 50, cols[i % 3]), period=15.0, seed=11, sway=60.0)
    if dusk:
        tale_fireflies(c, ts, w, h, 9, seed=5)


def tale_forest(c, ts, w, h, dusk=False):
    falling(c, ts, w, h, 9, lambda x, y, i, u: leaf(c, x, y, 1.0 + 0.2 * (i % 3), ts * 70 + i * 63 + math.sin(ts * 2 + i) * 40, LEAVES[i % len(LEAVES)]), period=12.0, seed=21)
    c0, c1 = BUTTERFLIES[1]
    butterfly(c, w * 0.30 + math.sin(ts * 0.5) * 90, h * 0.58 + math.sin(ts * 1.5) * 28, 1.4, ts, 1.0, c0, c1)
    if dusk:
        tale_fireflies(c, ts, w, h, 14, seed=7)
    else:
        for i in range(8):
            x = w * (0.1 + 0.8 * _rnd(i, 31)) + math.sin(ts * 0.3 + i) * 30
            y = h * (0.15 + 0.5 * _rnd(i, 32)) + math.cos(ts * 0.37 + i) * 24
            glow(c, x, y, 7, "#FFF6C0", 0.35 + 0.25 * math.sin(ts * 1.5 + i))


def tale_fireflies(c, ts, w, h, n=12, seed=3):
    for i in range(n):
        x = w * (0.05 + 0.9 * _rnd(i, seed)) + math.sin(ts * 0.42 + i * 1.7) * 38
        y = h * (0.40 + 0.45 * _rnd(i, seed + 1)) + math.cos(ts * 0.53 + i * 1.3) * 26
        g = 0.5 + 0.5 * math.sin(ts * 2.1 + i * 1.9)
        glow(c, x, y, 16 + 6 * g, "#E8F26A", 0.30 + 0.35 * g)
        c.ellipse(x, y, 2.4, 2.4, fill=mix("#FFF3A0", "#FFFFFF", g * 0.8))


def tale_night(c, ts, w, h, shooting=True):
    for i in range(7):
        ph = ts * 1.5 + i * 2.3
        r = 12.0 * max(0.0, math.sin(ph)) ** 2
        if r > 1.0:
            sparkle(c, w * (0.05 + 0.9 * _rnd(i, 41)), h * (0.04 + 0.34 * _rnd(i, 42)), r, "#FFF6C8", ang=20 * i)
    if shooting:
        shooting_star(c, w, h, ts, period=13.0, dur=1.0, seed=3, top=0.04, bottom=0.26)
    tale_fireflies(c, ts, w, h, 10, seed=9)


def tale_hall(c, ts, w, h):
    for i in range(5):
        x = w * (0.1 + 0.8 * _rnd(i, 51)) + math.sin(ts * 0.3 + i * 2) * 40
        y = h * 0.8 - ((ts * 14 + i * 160) % (h * 0.75))
        glow(c, x, y, 38 + 20 * _rnd(i, 52), ("#FFE9A8", "#FFD1EC", "#CFE8FF")[i % 3], 0.20)
    for i in range(16):
        x = w * (0.04 + 0.92 * _rnd(i, 53)) + math.sin(ts * 0.5 + i) * 24
        y = h * 0.95 - ((ts * (18 + 14 * _rnd(i, 54)) + i * 97) % (h * 0.95))
        r = 4.5 + 5.0 * max(0.0, math.sin(ts * 3.0 + i * 1.9)) ** 2
        sparkle(c, x, y, r, ("#FFF2B0", "#FFFFFF", "#FFD7EE")[i % 3], ang=ts * 40 + i * 30)


def tale_room(c, ts, w, h, night=False):
    for i in range(14):
        x = w * (0.04 + 0.92 * _rnd(i, 61)) + math.sin(ts * 0.25 + i * 1.7) * 26
        y = h * (0.12 + 0.62 * _rnd(i, 62)) + math.cos(ts * 0.31 + i * 1.1) * 20
        glow(c, x, y, 5.5, "#FFF3C4" if not night else "#C9D4FF", 0.30 + 0.22 * math.sin(ts * 1.3 + i))


STORY_AMBIENT = {
    "meadow": ("day", False), "meadow_open": ("day", False), "meadow_dawn": ("day", False), "river": ("day", False),
    "meadow_gorge": ("day", False), "race": ("day", False), "meadow_dusk": ("day", True), "meadow_gorge_dusk": ("day", True),
    "sunset": ("day", True), "forest": ("forest", False), "forest_dusk": ("forest", True),
    "garden_night": ("night", True), "castle_night": ("night", True),
    "ballroom": ("hall", False), "ballroom_day": ("hall", False), "room": ("room", False), "room_night": ("room", True),
}


def story_ambient(c, bg, ts, w=1280, h=720):
    """The living layer of a tale scene (behind the actors): birds, butterflies, petals, falling leaves, fireflies, glitter, dust."""
    kind = STORY_AMBIENT.get(bg)
    if not kind:
        return
    k, flag = kind
    if k == "day":
        tale_day(c, ts, w, h, dusk=flag, birds=not flag)
    elif k == "forest":
        tale_forest(c, ts, w, h, dusk=flag)
    elif k == "night":
        tale_night(c, ts, w, h)
    elif k == "hall":
        tale_hall(c, ts, w, h)
    elif k == "room":
        tale_room(c, ts, w, h, night=flag)


FG_GRASS = {"meadow": "#3FA33A", "meadow_open": "#3FA33A", "meadow_dawn": "#4CA84A", "river": "#3FA33A", "meadow_gorge": "#3FA33A",
            "race": "#3FA33A", "meadow_dusk": "#C98A2E", "meadow_gorge_dusk": "#C98A2E", "sunset": "#B8782A", "forest": "#2F8A3A",
            "forest_dusk": "#2A6E55", "garden_night": "#2F4A8A"}


def story_foreground(c, bg, ts, cx, z, world, w=1280, h=720):
    """Tufts of swaying grass along the bottom edge, in FRONT of everybody (they slide a little faster than the backdrop when the camera moves)."""
    col = FG_GRASS.get(bg)
    if not col:
        return
    f = 1.25
    step = 78.0
    first = int((cx - 640.0 / z - 120.0) // step)
    last = int((cx + 640.0 / z + 120.0) // step) + 1
    for j in range(first, last + 1):
        wx = j * step + 28.0 * (_rnd(j, 71) - 0.5)
        sx = w / 2.0 + (wx - cx) * z * f
        if sx < -60 or sx > w + 60:
            continue
        hh = (26.0 + 22.0 * _rnd(j, 72)) * (0.9 + 0.1 * z)
        sway = math.sin(ts * 2.1 + j * 0.8) * 5.0
        base = h + 6.0
        for dx, k in ((-9, 0.7), (0, 1.0), (9, 0.82)):
            c.poly([(sx + dx - 4, base), (sx + dx + sway * k, base - hh * k), (sx + dx + 4, base)], fill=darker(col, 0.14) if dx else col)
