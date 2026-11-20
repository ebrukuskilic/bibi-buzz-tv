"""Backdrops for the Bibi story videos (sky / hills / meadow / forest / rooms / race track).

A backdrop is built once per scene as two big images: FAR (sky, sun, distant hills; moves slowly when the camera pans)
and NEAR (ground and static decoration, transparent above the horizon). The story engine crops them for the camera.
"""
import math
import random

import numpy as np
from PIL import Image

from . import draw as D
from .draw import INK, darker, mix

WH = 720


def layer(w, rgba=False):
    ss = D.SS
    img = Image.new("RGBA" if rgba else "RGB", (int(w * ss), WH * ss), (0, 0, 0, 0) if rgba else (255, 255, 255))
    return D.Canvas(img, w=int(w), h=WH)


def vgrad(c, stops, y0=0, y1=WH):
    """Vertical colour gradient over the full width, rows y0..y1 (layout units)."""
    ss = D.SS
    n = int((y1 - y0) * ss)
    pos = np.array([p for p, _ in stops], dtype=float)
    cols = np.array([D.hex2rgb(col) for _, col in stops], dtype=float)
    u = np.linspace(0, 1, n)
    arr = np.stack([np.interp(u, pos, cols[:, i]) for i in range(3)], axis=1)[:, None, :]
    arr = np.repeat(arr, c.img.width, axis=1).astype(np.uint8)
    im = Image.fromarray(arr, "RGB")
    if c.img.mode == "RGBA":
        im = im.convert("RGBA")
    c.img.paste(im, (0, int(y0 * ss)))


def hills(c, w, base, amp, lam, phase, color, step=20):
    pts = [(x, base - amp * (math.sin(x / lam + phase) + 0.5 * math.sin(x / (lam * 0.43) + phase * 2.1)))
           for x in range(-step, int(w) + 2 * step, step)]
    c.poly(pts + [(w + step, WH + 5), (-step, WH + 5)], fill=color)


def cloud_shape(c, x, y, s=1.0, color="#FFFFFF", shade="#E6F3FF"):
    for dx, dy, rx, ry in ((0, 8, 70, 26), (-44, -2, 36, 30), (6, -16, 44, 38), (50, -2, 34, 28)):
        c.ellipse(x + dx * s, y + dy * s + 5 * s, rx * s, ry * s, fill=shade)
    for dx, dy, rx, ry in ((0, 8, 70, 26), (-44, -2, 36, 30), (6, -16, 44, 38), (50, -2, 34, 28)):
        c.ellipse(x + dx * s, y + dy * s, rx * s, ry * s, fill=color)


def sun_shape(c, x, y, r=62, color="#FFE066", glow="#FFF3B0"):
    for i, a in enumerate((2.3, 1.8, 1.4)):
        c.ellipse(x, y, r * a, r * a, fill=mix("#9ED8FF", glow, 0.25 + 0.2 * i))
    c.ellipse(x, y, r * 1.15, r * 1.15, fill=glow)
    c.ellipse(x, y, r, r, fill=color)


def round_tree(c, x, gy, h, leaf="#3FAE49", trunk="#8B5A2B", edge=None):
    tw = h * 0.07
    c.rrect(x - tw, gy - h * 0.55, x + tw, gy, tw * 0.5, fill=trunk, outline=edge, width=2 if edge else 0)
    sh, hi = darker(leaf, 0.18), mix(leaf, "#FFFFFF", 0.22)
    blobs = ((-0.30, -0.62, 0.27), (0.30, -0.62, 0.27), (0.0, -0.80, 0.31), (-0.14, -0.60, 0.28), (0.18, -0.58, 0.27))
    for dx, dy, rr in blobs:
        c.ellipse(x + dx * h, gy + dy * h, rr * h, rr * h * 0.92, fill=sh, outline=edge, width=2 if edge else 0)
    for dx, dy, rr in blobs:
        c.ellipse(x + dx * h - h * 0.012, gy + dy * h - h * 0.02, rr * h * 0.92, rr * h * 0.84, fill=leaf)
    c.ellipse(x - h * 0.10, gy - h * 0.86, h * 0.12, h * 0.07, fill=hi)


def pine_tree(c, x, gy, h, leaf="#2F9A55", trunk="#7A4A25"):
    tw = h * 0.05
    c.rrect(x - tw, gy - h * 0.2, x + tw, gy, tw * 0.4, fill=trunk)
    for i in range(4):
        by = gy - h * (0.12 + 0.2 * i)
        wd = h * (0.34 - 0.06 * i)
        c.poly([(x - wd, by), (x + wd, by), (x, by - h * 0.34)], fill=mix(leaf, "#FFFFFF", 0.06 * i))


def bush(c, x, gy, s=1.0, leaf="#4CBB55"):
    for dx, dy, rr in ((-34, -18, 30), (0, -26, 36), (34, -18, 30), (-12, -10, 28), (16, -10, 28)):
        c.ellipse(x + dx * s, gy + dy * s, rr * s, rr * s * 0.85, fill=darker(leaf, 0.12))
    for dx, dy, rr in ((-34, -20, 26), (0, -28, 32), (34, -20, 26)):
        c.ellipse(x + dx * s, gy + dy * s, rr * s, rr * s * 0.82, fill=leaf)
    c.ellipse(x - 8 * s, gy - 38 * s, 12 * s, 6 * s, fill=mix(leaf, "#FFFFFF", 0.3))


def flower_dot(c, x, y, s, color, center="#FFD23F"):
    c.line([(x, y), (x, y + 16 * s)], "#3E9B3A", 2.2 * s)
    for i in range(5):
        a = 2 * math.pi * i / 5
        c.ellipse(x + 5.5 * s * math.cos(a), y + 5.5 * s * math.sin(a), 4.6 * s, 4.6 * s, fill=color)
    c.ellipse(x, y, 3.4 * s, 3.4 * s, fill=center)


def tuft(c, x, y, s, color="#4FAE35"):
    for dx, h in ((-6, 14), (0, 20), (6, 12)):
        c.poly([(x + (dx - 3) * s, y), (x + (dx + 3) * s, y), (x + dx * 1.4 * s, y - h * s)], fill=color)


def mushroom(c, x, y, s=1.0, cap="#E2574C"):
    c.rrect(x - 7 * s, y - 20 * s, x + 7 * s, y, 4 * s, fill="#FFF3DC", outline=INK, width=1.8)
    c.ellipse(x, y - 22 * s, 20 * s, 14 * s, fill=cap, outline=INK, width=1.8)
    for dx, dy, rr in ((-8, -26, 3.4), (6, -29, 3), (10, -20, 2.6), (-2, -20, 2.4)):
        c.ellipse(x + dx * s, y + dy * s, rr * s, rr * s, fill="#FFFFFF")


def fence(c, x0, x1, gy, s=1.0, color="#F4E3C1"):
    n = int((x1 - x0) / (34 * s))
    c.rect(x0, gy - 34 * s, x1, gy - 24 * s, color)
    c.rect(x0, gy - 62 * s, x1, gy - 52 * s, color)
    for i in range(n + 1):
        x = x0 + i * 34 * s
        c.poly([(x - 8 * s, gy), (x - 8 * s, gy - 70 * s), (x, gy - 80 * s), (x + 8 * s, gy - 70 * s), (x + 8 * s, gy)], fill=color, outline="#B89B6A", width=1.6)


def windmill(c, x, gy, s=1.0):
    c.poly([(x - 28 * s, gy), (x + 28 * s, gy), (x + 18 * s, gy - 90 * s), (x - 18 * s, gy - 90 * s)], fill="#F6EBD2")
    c.poly([(x - 24 * s, gy - 90 * s), (x + 24 * s, gy - 90 * s), (x, gy - 120 * s)], fill="#D9654F")
    for a in (20, 110, 200, 290):
        r = math.radians(a)
        c.line([(x, gy - 90 * s), (x + math.cos(r) * 52 * s, gy - 90 * s + math.sin(r) * 52 * s)], "#8B6A44", 4 * s)
        c.ellipse(x + math.cos(r) * 40 * s, gy - 90 * s + math.sin(r) * 40 * s, 9 * s, 5 * s, fill="#FFFFFF")


def small_house_far(c, x, gy, s=1.0, wall="#F7E8C8", roof="#D9654F"):
    c.rect(x - 24 * s, gy - 26 * s, x + 24 * s, gy, wall)
    c.poly([(x - 30 * s, gy - 26 * s), (x + 30 * s, gy - 26 * s), (x, gy - 52 * s)], fill=roof)
    c.rect(x - 5 * s, gy - 16 * s, x + 5 * s, gy, "#A8682F")


# ================================================================================================ backdrops
def _sky(c, top="#79C8FF", mid="#B6E7FF", bottom="#F2FBFF", y1=560):
    vgrad(c, [(0, top), (0.55, mid), (1, bottom)], 0, y1)


def far_meadow(c, w, mood="day", seed=1):
    rng = random.Random(seed)
    if mood == "dawn":
        vgrad(c, [(0, "#8FB8FF"), (0.5, "#FFD4B8"), (1, "#FFF1D6")], 0, 580)
    elif mood == "dusk":
        vgrad(c, [(0, "#6F7FD8"), (0.5, "#F4A6B8"), (1, "#FFD9A8")], 0, 580)
    else:
        _sky(c, y1=580)
    sun_shape(c, w * 0.78 if w < 1500 else 1050, 120, 58, "#FFE066" if mood == "day" else "#FFC25A")
    for i in range(int(w // 520) + 3):
        cloud_shape(c, 160 + i * 520 + rng.randint(-60, 60), 90 + rng.randint(0, 90), 0.8 + rng.random() * 0.5)
    hills(c, w, 470, 60, 190, 0.6, "#A6E59A")
    for i in range(int(w // 260) + 2):
        x = 90 + i * 260 + rng.randint(-40, 40)
        if rng.random() < 0.5:
            small_house_far(c, x, 462 + rng.randint(-6, 6), 0.9)
        else:
            round_tree(c, x, 468, 70 + rng.randint(-10, 20), "#7BD37A", "#9A7B55")
    if w > 1500:
        windmill(c, 700, 458, 1.0)
    hills(c, w, 520, 46, 150, 2.2, "#86D673")
    c.rect(0, 540, w, WH, "#79CE5D")


def near_meadow(c, w, seed=2, path=True, flowers=40, trees=True, fence_on=True):
    rng = random.Random(seed)
    vgrad(c, [(0, "#85DA58"), (0.4, "#6BC84A"), (1, "#54B13B")], 520, WH)
    if fence_on:
        fence(c, 0, min(w, 360), 536, 0.9)
    if trees:
        round_tree(c, 70, 560, 250, "#3FAE49")
        round_tree(c, w - 80, 556, 270, "#46B650")
        bush(c, 230, 548, 1.0)
        bush(c, w - 250, 546, 1.1)
    if path:
        c.poly([(w * 0.42, 520), (w * 0.58, 520), (w * 0.80, WH), (w * 0.20, WH)], fill="#EBCB91")
        c.poly([(w * 0.455, 520), (w * 0.545, 520), (w * 0.64, WH), (w * 0.36, WH)], fill="#F3DBAA")
    cols = ["#FF6B8B", "#FFD23F", "#FFFFFF", "#B58CFF", "#FF9A3D"]
    for _ in range(flowers):
        x, y = rng.uniform(0, w), rng.uniform(540, 700)
        if path and w * 0.34 < x < w * 0.66 and y > 560:
            continue
        flower_dot(c, x, y, 0.7 + (y - 520) / 300, rng.choice(cols))
    for _ in range(30):
        tuft(c, rng.uniform(0, w), rng.uniform(530, 710), 0.8 + rng.random() * 0.6, rng.choice(["#4FAE35", "#5BBE3E"]))


def far_forest(c, w, seed=3):
    rng = random.Random(seed)
    vgrad(c, [(0, "#8CD3C7"), (0.6, "#C6EBD4"), (1, "#F0FAE4")], 0, 560)
    for i in range(7):                                                                 # light rays
        x = 100 + i * (w / 7)
        c.poly([(x, 0), (x + 50, 0), (x + 190, 560), (x + 60, 560)], fill=mix("#C6EBD4", "#FFFFFF", 0.45))
    for i in range(int(w // 120) + 2):
        pine_tree(c, 40 + i * 120 + rng.randint(-20, 20), 500 + rng.randint(-8, 8), 190 + rng.randint(-20, 30), "#5BB88B")
    hills(c, w, 520, 30, 120, 1.3, "#6CC27E")
    for i in range(int(w // 150) + 2):
        round_tree(c, 60 + i * 150 + rng.randint(-30, 30), 530, 230 + rng.randint(-20, 40), "#3C9F57", "#7C5230")
    c.rect(0, 545, w, WH, "#5FB864")


def near_forest(c, w, seed=4):
    rng = random.Random(seed)
    vgrad(c, [(0, "#72C45B"), (0.5, "#5BAE49"), (1, "#478F3A")], 530, WH)
    for x in (40, w - 50):
        tw = 62
        c.rrect(x - tw, -20, x + tw, 580, 20, fill="#8A5A30")
        for yy in (80, 200, 330, 450):
            c.arc(x, yy, tw * 0.5, 30, 200, 340, "#6E4524", 5)
        c.ellipse(x, 584, tw + 18, 18, fill="#6E4524")
    for x in (120, w - 140):
        bush(c, x, 560, 1.2, "#3E9E4B")
    for _ in range(14):
        mushroom(c, rng.uniform(80, w - 80), rng.uniform(600, 700), 0.8 + rng.random() * 0.5, rng.choice(["#E2574C", "#FF9A3D"]))
    for _ in range(40):
        tuft(c, rng.uniform(0, w), rng.uniform(540, 710), 0.9 + rng.random() * 0.6, rng.choice(["#3E9B3A", "#52B045"]))
    for _ in range(26):
        x, y = rng.uniform(0, w), rng.uniform(560, 710)
        c.ellipse(x, y, 9, 4, fill=rng.choice(["#E8A33A", "#D9783A", "#C95A3A"]))


def far_room(c, w, wall="#FFE9B8", stripe="#FFDC96", floor="#C98A52", night=False, window=True):
    c.rect(0, 0, w, 560, wall)
    for x in range(0, int(w), 64):
        c.rect(x, 0, x + 26, 560, stripe)
    c.rect(0, 520, w, 548, mix(wall, "#8B5A2B", 0.5))                                 # skirting
    c.rect(0, 540, w, WH, floor)
    for i, y in enumerate(range(556, WH, 28)):
        c.rect(0, y, w, y + 3, darker(floor, 0.16))
    if window:
        wx, wy = w * 0.5, 230
        c.rrect(wx - 130, wy - 120, wx + 130, wy + 120, 16, fill="#8B5A2B")
        c.rrect(wx - 112, wy - 102, wx + 112, wy + 102, 8, fill="#8DD3FF" if not night else "#2A3E8F")
        if night:
            for i in range(9):
                D.star(c, wx - 90 + (i * 53) % 180, wy - 80 + (i * 37) % 160, 5 + i % 3, "#FFF3A8")
        else:
            cloud_shape(c, wx - 40, wy - 40, 0.55)
            c.poly([(wx - 112, wy + 102), (wx - 112, wy + 40), (wx - 40, wy + 20), (wx + 40, wy + 44), (wx + 112, wy + 30), (wx + 112, wy + 102)], fill="#8FDD7A")
        c.rect(wx - 3, wy - 102, wx + 3, wy + 102, "#8B5A2B")
        c.rect(wx - 112, wy - 3, wx + 112, wy + 3, "#8B5A2B")
        for s in (-1, 1):                                                              # curtains
            c.poly([(wx + s * 124, wy - 120), (wx + s * 52, wy - 120), (wx + s * 70, wy + 40), (wx + s * 124, wy + 120)], fill="#FF8FA3", outline=INK, width=2)
        c.rrect(wx - 150, wy - 140, wx + 150, wy - 124, 6, fill="#B5683A", outline=INK, width=2)


def near_room(c, w, floor="#C98A52", rug="#E2574C"):
    c.ellipse(w * 0.5, 650, 380, 56, fill=rug, outline=INK, width=2)
    c.ellipse(w * 0.5, 650, 320, 40, fill=mix(rug, "#FFFFFF", 0.22))
    c.ellipse(w * 0.5, 650, 250, 28, fill=rug)


def far_race(c, w, seed=5):
    rng = random.Random(seed)
    _sky(c, y1=580)
    sun_shape(c, 1050, 110, 56)
    for i in range(int(w // 520) + 3):
        cloud_shape(c, 120 + i * 520 + rng.randint(-60, 60), 90 + rng.randint(0, 110), 0.8 + rng.random() * 0.6)
    hills(c, w, 440, 70, 260, 0.2, "#A6E59A")
    for i in range(int(w // 200) + 2):
        x = 60 + i * 200 + rng.randint(-40, 40)
        if rng.random() < 0.35:
            small_house_far(c, x, 440 + rng.randint(-4, 8), 0.9)
        else:
            round_tree(c, x, 450 + rng.randint(-6, 6), 70 + rng.randint(-10, 20), "#7BD37A", "#9A7B55")
    windmill(c, 520, 436, 1.1)
    hills(c, w, 515, 40, 200, 1.7, "#86D673")
    c.rect(0, 535, w, WH, "#79CE5D")


def near_race(c, w, seed=6, road=True):
    rng = random.Random(seed)
    vgrad(c, [(0, "#85DA58"), (0.5, "#6BC84A"), (1, "#54B13B")], 520, WH)
    if road:
        c.poly([(0, 560), (w, 560), (w, 700), (0, 700)], fill="#EBCB91")
        c.poly([(0, 575), (w, 575), (w, 690), (0, 690)], fill="#F3DBAA")
        for x in range(0, int(w), 120):
            c.rrect(x + 20, 628, x + 80, 636, 3, fill="#FFFFFF")
    for i in range(int(w // 330) + 1):
        x = 180 + i * 330 + rng.randint(-60, 60)
        if rng.random() < 0.6:
            round_tree(c, x, 548, 190 + rng.randint(-20, 40), "#44B34E")
        else:
            bush(c, x, 548, 1.0 + rng.random() * 0.4)
    cols = ["#FF6B8B", "#FFD23F", "#FFFFFF", "#B58CFF", "#FF9A3D"]
    for _ in range(int(w / 28)):
        x, y = rng.uniform(0, w), rng.choice([rng.uniform(534, 556), rng.uniform(704, 716)])
        flower_dot(c, x, y, 0.7, rng.choice(cols))
    for _ in range(int(w / 40)):
        tuft(c, rng.uniform(0, w), rng.uniform(530, 556), 0.9, "#4FAE35")


def river_x(y, w=1280):
    """Left and right bank of the river on the ground row y (it gets wider toward the viewer)."""
    u = (y - 540.0) / 180.0
    return w * (0.36 - 0.06 * u), w * (0.64 + 0.06 * u)


def near_river(c, w, seed=8):
    rng = random.Random(seed)
    vgrad(c, [(0, "#85DA58"), (0.4, "#6BC84A"), (1, "#54B13B")], 520, WH)
    round_tree(c, 70, 560, 250, "#3FAE49")
    round_tree(c, w - 80, 556, 270, "#46B650")
    bush(c, 235, 548, 1.0)
    bush(c, w - 250, 546, 1.1)
    ys = list(range(534, WH + 13, 12))
    c.poly([(river_x(y, w)[0] - 18 - (y - 540) * 0.06, y) for y in ys] + [(river_x(y, w)[1] + 18 + (y - 540) * 0.06, y) for y in reversed(ys)], fill="#EAD7A0")
    c.poly([(river_x(y, w)[0] - 8 - (y - 540) * 0.03, y) for y in ys] + [(river_x(y, w)[1] + 8 + (y - 540) * 0.03, y) for y in reversed(ys)], fill="#D9BE82")
    for y in range(540, WH + 1, 5):                                                    # the water: light at the far end, deeper toward us
        u = (y - 540) / 180.0
        col = mix("#8FDBFF", "#3E9BE8", min(1.0, u))
        a, b = river_x(y, w), river_x(y + 6, w)
        c.poly([(a[0], y), (a[1], y), (b[1], y + 6), (b[0], y + 6)], fill=col)
    for _ in range(26):                                                                # little waves
        y = rng.uniform(552, 708)
        xl, xr = river_x(y, w)
        x = rng.uniform(xl + 30, xr - 70)
        c.line([(x + i * 8, y + 3 * math.sin(i * 1.6)) for i in range(7)], "#D5F1FF", 2.4)
    for lx, ly in ((w * 0.45, 600), (w * 0.57, 668)):                                   # lily pads
        c.ellipse(lx, ly, 24, 8, fill="#3FAE49")
        c.poly([(lx, ly), (lx + 24, ly - 3), (lx + 24, ly + 3)], fill="#3E9BE8")
        c.ellipse(lx - 6, ly - 4, 5, 3, fill="#FF8FB0")
    for side in (0, 1):                                                                # reeds on both banks
        for i in range(7):
            y = 548 + i * 24 + rng.uniform(-4, 4)
            xb = river_x(y, w)[side] + (-26 if side == 0 else 26) + rng.uniform(-10, 10)
            c.line([(xb, y), (xb + rng.uniform(-8, 8), y - 54)], "#3E9B3A", 3)
            c.ellipse(xb, y - 58, 4.5, 11, fill="#8B5A2B")
    cols = ["#FF6B8B", "#FFD23F", "#FFFFFF", "#B58CFF", "#FF9A3D"]
    for _ in range(34):
        x, y = rng.uniform(0, w), rng.uniform(540, 705)
        xl, xr = river_x(y, w)
        if xl - 50 < x < xr + 50:
            continue
        flower_dot(c, x, y, 0.7 + (y - 520) / 300, rng.choice(cols))
    for _ in range(26):
        x, y = rng.uniform(0, w), rng.uniform(530, 710)
        xl, xr = river_x(y, w)
        if xl - 40 < x < xr + 40:
            continue
        tuft(c, x, y, 0.8 + rng.random() * 0.6, rng.choice(["#4FAE35", "#5BBE3E"]))


def far_sunset(c, w):
    vgrad(c, [(0, "#5A6FD0"), (0.45, "#E88FB0"), (1, "#FFD8A0")], 0, 580)
    sun_shape(c, 640, 400, 70, "#FFB347", "#FFD9A0")
    hills(c, w, 480, 40, 200, 0.4, "#6B8FD0")
    hills(c, w, 530, 36, 160, 2.0, "#4F7A9F")
    c.rect(0, 545, w, WH, "#4C8F5A")


BACKDROPS = {
    "meadow": (far_meadow, near_meadow),
    "meadow_dawn": (lambda c, w: far_meadow(c, w, "dawn"), near_meadow),
    "meadow_dusk": (lambda c, w: far_meadow(c, w, "dusk"), lambda c, w: near_meadow(c, w, path=False)),
    "meadow_open": (far_meadow, lambda c, w: near_meadow(c, w, path=False, flowers=60, trees=False, fence_on=False)),
    "forest": (far_forest, near_forest),
    "room": (far_room, near_room),
    "room_night": (lambda c, w: far_room(c, w, night=True), near_room),
    "race": (far_race, near_race),
    "river": (far_meadow, near_river),
    "sunset": (far_sunset, lambda c, w: near_meadow(c, w, path=False, trees=False, fence_on=False, flowers=20)),
}

_CACHE = {}


def backdrop(name, w):
    """Returns (far_image, near_image) for a world of width w (cached per process)."""
    key = (name, int(w), D.SS)
    if key not in _CACHE:
        far_fn, near_fn = BACKDROPS[name]
        wf = int(1280 + (w - 1280) * 0.35)
        cf = layer(wf)
        far_fn(cf, wf)
        cn = layer(w, rgba=True)
        near_fn(cn, int(w))
        _CACHE[key] = (cf.img, cn.img, wf)
    return _CACHE[key]
