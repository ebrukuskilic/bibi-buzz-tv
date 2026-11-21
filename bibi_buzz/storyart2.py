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


def far_forest(c, w, seed=3, dusk=False):
    """dusk = a dark, bluish forest at twilight (with a few fireflies), for the scary parts of a tale."""
    rng = random.Random(seed)
    if dusk:
        vgrad(c, [(0, "#1F3550"), (0.6, "#3A6070"), (1, "#5C8C84")], 0, 560)
        for i in range(7):
            x = 100 + i * (w / 7)
            c.poly([(x, 0), (x + 50, 0), (x + 190, 560), (x + 60, 560)], fill=mix("#3A6070", "#9EC4C8", 0.18))
    else:
        vgrad(c, [(0, "#8CD3C7"), (0.6, "#C6EBD4"), (1, "#F0FAE4")], 0, 560)
        for i in range(7):                                                             # light rays
            x = 100 + i * (w / 7)
            c.poly([(x, 0), (x + 50, 0), (x + 190, 560), (x + 60, 560)], fill=mix("#C6EBD4", "#FFFFFF", 0.45))
    for i in range(int(w // 120) + 2):
        pine_tree(c, 40 + i * 120 + rng.randint(-20, 20), 500 + rng.randint(-8, 8), 190 + rng.randint(-20, 30), "#2E6B58" if dusk else "#5BB88B")
    hills(c, w, 520, 30, 120, 1.3, "#2F7A52" if dusk else "#6CC27E")
    for i in range(int(w // 150) + 2):
        round_tree(c, 60 + i * 150 + rng.randint(-30, 30), 530, 230 + rng.randint(-20, 40), "#256A43" if dusk else "#3C9F57", "#5A3A20" if dusk else "#7C5230")
    c.rect(0, 545, w, WH, "#2F7646" if dusk else "#5FB864")
    if dusk:                                                                           # fireflies: a glowing dot in a soft ring
        for _ in range(int(w // 55)):
            x, y = rng.uniform(30, w - 30), rng.uniform(250, 520)
            c.ellipse(x, y, 9, 9, fill="#4F8A72")
            c.ellipse(x, y, 5.5, 5.5, fill="#B9E08A")
            c.ellipse(x, y, 2.8, 2.8, fill="#FFF6B0")


def near_forest(c, w, seed=4, dusk=False):
    rng = random.Random(seed)
    vgrad(c, [(0, "#3E8A4A"), (0.5, "#2F7040"), (1, "#245A34")] if dusk else [(0, "#72C45B"), (0.5, "#5BAE49"), (1, "#478F3A")], 530, WH)
    for x in (40, w - 50):
        tw = 62
        c.rrect(x - tw, -20, x + tw, 580, 20, fill="#5E3C22" if dusk else "#8A5A30")
        for yy in (80, 200, 330, 450):
            c.arc(x, yy, tw * 0.5, 30, 200, 340, "#46301C" if dusk else "#6E4524", 5)
        c.ellipse(x, 584, tw + 18, 18, fill="#46301C" if dusk else "#6E4524")
    for x in (120, w - 140):
        bush(c, x, 560, 1.2, "#2A7A3C" if dusk else "#3E9E4B")
    for _ in range(14):
        mushroom(c, rng.uniform(80, w - 80), rng.uniform(600, 700), 0.8 + rng.random() * 0.5, rng.choice(["#E2574C", "#FF9A3D"]))
    for _ in range(40):
        tuft(c, rng.uniform(0, w), rng.uniform(540, 710), 0.9 + rng.random() * 0.6, rng.choice(["#2E7A36", "#3C8E3A"] if dusk else ["#3E9B3A", "#52B045"]))
    for _ in range(26):
        x, y = rng.uniform(0, w), rng.uniform(560, 710)
        c.ellipse(x, y, 9, 4, fill=rng.choice(["#B07F2E", "#A8602E", "#96492E"] if dusk else ["#E8A33A", "#D9783A", "#C95A3A"]))


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


def gorge_x(y, w=1280):
    """Left and right edge of the gorge on the ground row y: the cliffs lean in toward the water at the bottom."""
    xl = 350.0 + max(0.0, y - 472.0) * 0.34
    return xl, w - xl


def near_gorge(c, w, seed=11):
    """Two grassy cliff tops (the left one is dry and bare, the right one is a lush meadow) with a gorge between them: far below, a strip of
    valley and a stream. A wooden bridge (props.bridge) goes across at the height of the cliff tops, where the goats' feet stand (y = 440)."""
    rng = random.Random(seed)
    vgrad(c, [(0, "#79CE5D"), (1, "#6BC54F")], 541, 612)
    vgrad(c, [(0, "#8FDBFF"), (1, "#3E9BE8")], 612, WH)
    for _ in range(18):                                                                # little waves
        y = rng.uniform(624, 714)
        xl, xr = gorge_x(y, w)
        x = rng.uniform(xl + 24, xr - 80)
        c.line([(x + i * 8, y + 3 * math.sin(i * 1.6)) for i in range(7)], "#D5F1FF", 2.4)
    for lx, ly in ((w * 0.45, 640), (w * 0.56, 696)):                                   # lily pads
        c.ellipse(lx, ly, 24, 8, fill="#3FAE49")
        c.poly([(lx, ly), (lx + 24, ly - 3), (lx + 24, ly + 3)], fill="#3E9BE8")
        c.ellipse(lx - 6, ly - 4, 5, 3, fill="#FF8FB0")
    for side in (0, 1):
        sgn = -1 if side == 0 else 1
        out = -14 if side == 0 else w + 14
        edge = lambda y, s_=side: gorge_x(y, w)[s_]
        ys = list(range(472, 734, 12))
        c.poly([(out, 472), (edge(472), 472)] + [(edge(y), y) for y in ys[1:]] + [(out, 734)], fill="#B98B5E")         # the cliff face
        for yy in (508, 548, 590, 632, 676):                                                                              # strata
            c.line([(out, yy), (edge(yy) - sgn * 3, yy + rng.uniform(-3, 3))], "#9C7249", 4.5)
            c.line([(out, yy + 7), (edge(yy + 7) - sgn * 3, yy + 7 + rng.uniform(-2, 2))], "#CFA277", 2.6)
        for _ in range(5):
            yy = rng.uniform(500, 700)
            xx = (edge(yy) - rng.uniform(40, 220)) if side == 0 else (edge(yy) + rng.uniform(40, 220))
            rx = rng.uniform(16, 30)
            c.ellipse(xx, yy, rx, rx * 0.62, fill="#A9A8B4", outline=INK, width=2)
            c.ellipse(xx - rx * 0.25, yy - rx * 0.2, rx * 0.5, rx * 0.2, fill="#C9C8D4")
        c.line([(edge(y), y) for y in ys], "#D7AE82", 5)                                                                  # sunlit edge
        for yy in (640, 668, 698, 724):                                                                                   # foam at the foot of the cliff
            c.ellipse(edge(yy) - sgn * 6, yy, 16, 4, fill="#FFFFFF")
        xe = edge(472) + sgn * 8                                                                                          # the cliff top
        back = [(x, 398 + 9 * math.sin(x / 70.0 + 1.7 * side)) for x in range(int(min(out, xe)), int(max(out, xe)) + 1, 20)]
        c.poly(back + [(max(out, xe), 478), (min(out, xe), 478)], fill="#6BC84A")
        c.poly([(min(out, xe), 444), (max(out, xe), 444), (max(out, xe), 478), (min(out, xe), 478)], fill="#85DA58")
        for x in range(int(min(out, xe)), int(max(out, xe)) + 1, 26):                                                     # grass hanging over the edge
            c.ellipse(x, 480, 17, 10, fill="#4E9A38")
            c.ellipse(x, 476, 17, 10, fill="#85DA58")
    xl_, xr_ = gorge_x(472, w)
    for _ in range(5):                                                                 # the left side is dry: bare earth, rocks, brown tufts
        c.ellipse(rng.uniform(10, xl_ - 20), rng.uniform(424, 470), rng.uniform(26, 48), rng.uniform(6, 10), fill="#CDB77C")
    for _ in range(14):
        tuft(c, rng.uniform(6, xl_ - 10), rng.uniform(412, 472), 0.8 + rng.random() * 0.4, "#B7B15C")
    for xx, yy, rx in ((38, 466, 26), (300, 424, 20)):
        c.ellipse(xx, yy, rx, rx * 0.6, fill="#A9A8B4", outline=INK, width=2)
        c.ellipse(xx - rx * 0.25, yy - rx * 0.2, rx * 0.5, rx * 0.2, fill="#C9C8D4")
    round_tree(c, 64, 410, 190, "#A9B552", "#7A5A38")
    bush(c, 225, 418, 0.7, "#A8B84E")
    cols = ["#FF6B8B", "#FFD23F", "#FFFFFF", "#B58CFF", "#FF9A3D"]
    for _ in range(46):                                                                # the right side is lush: flowers, clover, trees
        flower_dot(c, rng.uniform(xr_ + 10, w - 6), rng.uniform(408, 466), 0.75 + rng.random() * 0.2, rng.choice(cols))
    for _ in range(22):
        tuft(c, rng.uniform(xr_ + 6, w - 6), rng.uniform(410, 472), 0.9 + rng.random() * 0.5, rng.choice(["#4FAE35", "#5BBE3E"]))
    round_tree(c, w - 66, 410, 270, "#3FAE49")
    round_tree(c, w - 262, 412, 180, "#46B650")
    bush(c, w - 150, 424, 1.0)
    mushroom(c, w - 345, 466, 1.0)


def far_sunset(c, w):
    vgrad(c, [(0, "#5A6FD0"), (0.45, "#E88FB0"), (1, "#FFD8A0")], 0, 580)
    sun_shape(c, 640, 400, 70, "#FFB347", "#FFD9A0")
    hills(c, w, 480, 40, 200, 0.4, "#6B8FD0")
    hills(c, w, 530, 36, 160, 2.0, "#4F7A9F")
    c.rect(0, 545, w, WH, "#4C8F5A")


# ---------------------------------------------------------------- the night garden, the castle and the ballroom (Cinderella)
def far_night(c, w, castle=False, seed=7, storm=False):
    """A starry night with a big moon over dark hills (castle=True: a palace with lit windows on the hill; storm=True: no stars and no moon,
    but a heavy, dark sky full of rain clouds)."""
    rng = random.Random(seed)
    if storm:
        vgrad(c, [(0, "#1B2236"), (0.55, "#36405C"), (1, "#5A6486")], 0, 580)
        for i in range(14):
            cloud_shape(c, rng.uniform(-40, w + 40), rng.uniform(20, 300), rng.uniform(1.9, 3.1), "#4B5476", "#363E5A")
        for i in range(8):
            cloud_shape(c, rng.uniform(-40, w + 40), rng.uniform(30, 200), rng.uniform(2.0, 3.0), "#3C4463", "#2B3250")
        hills(c, w, 470, 54, 190, 0.6, "#2D3D5E")
    else:
        vgrad(c, [(0, "#0F1A4C"), (0.55, "#2A3B88"), (1, "#5B5FAA")], 0, 580)
        for i in range(80):
            D.star(c, rng.uniform(0, w), rng.uniform(10, 420), rng.choice((3, 4, 5, 6)), rng.choice(("#FFF3A8", "#FFFFFF", "#CFE3FF")))
        mx = w * 0.82 if w < 1500 else 1120
        for i, a in enumerate((2.3, 1.75, 1.35)):
            c.ellipse(mx, 125, 58 * a, 58 * a, fill=mix("#2A3B88", "#FFF3B0", 0.1 + 0.12 * i))
        c.ellipse(mx, 125, 58, 58, fill="#FFF8D0")
        c.ellipse(mx - 17, 113, 10, 10, fill="#F0E6B0")
        c.ellipse(mx + 14, 140, 8, 8, fill="#F0E6B0")
        c.ellipse(mx + 18, 106, 6, 6, fill="#F0E6B0")
        hills(c, w, 470, 54, 190, 0.6, "#34558A")
    if castle:
        cx = w * 0.5
        roof, wall, lit = "#6C5FC7", "#C9CCE8", "#FFE27A"
        for dx, th, tw in ((-190, 150, 34), (190, 150, 34), (-110, 210, 40), (110, 210, 40)):          # the towers
            x = cx + dx
            c.rect(x - tw, 468 - th, x + tw, 470, wall)
            c.poly([(x - tw - 8, 468 - th), (x + tw + 8, 468 - th), (x, 468 - th - 78)], fill=roof)
            c.rect(x - 6, 468 - th * 0.72 - 14, x + 6, 468 - th * 0.72 + 14, lit)
            c.rect(x - 6, 468 - th * 0.3 - 14, x + 6, 468 - th * 0.3 + 14, lit)
        c.line([(cx - 110, 468 - 210 - 78), (cx - 110, 468 - 210 - 112)], "#5A4A3A", 3)
        c.poly([(cx - 110, 468 - 210 - 112), (cx - 80, 468 - 210 - 102), (cx - 110, 468 - 210 - 92)], fill="#E2574C")
        c.line([(cx + 110, 468 - 210 - 78), (cx + 110, 468 - 210 - 112)], "#5A4A3A", 3)
        c.poly([(cx + 110, 468 - 210 - 112), (cx + 140, 468 - 210 - 102), (cx + 110, 468 - 210 - 92)], fill="#E2574C")
        c.rect(cx - 90, 330, cx + 90, 470, wall)                                                    # the main hall
        for k in range(7):
            c.rect(cx - 90 + k * 30, 316, cx - 76 + k * 30, 332, wall)                              # battlements
        c.poly([(cx - 34, 470), (cx - 34, 410), (cx, 386), (cx + 34, 410), (cx + 34, 470)], fill="#7A5A3A")
        for dx in (-62, -22, 22, 62):
            c.rrect(cx + dx - 8, 350, cx + dx + 8, 392, 8, fill=lit)
    hills(c, w, 520, 40, 150, 2.2, "#25456B")
    c.rect(0, 540, w, WH, "#1F3D5C")


def near_night(c, w, seed=8):
    rng = random.Random(seed)
    vgrad(c, [(0, "#2C7A62"), (0.4, "#226553"), (1, "#184A41")], 520, WH)
    round_tree(c, 70, 560, 250, "#1E5E52")
    round_tree(c, w - 80, 556, 270, "#216657")
    bush(c, 230, 548, 1.0, "#1F6A57")
    bush(c, w - 250, 546, 1.1, "#1F6A57")
    for _ in range(34):                                                                           # glowing flowers
        x, y = rng.uniform(0, w), rng.uniform(545, 705)
        flower_dot(c, x, y, 0.7 + (y - 520) / 300, rng.choice(("#FFE27A", "#FF9DC3", "#BFD2FF", "#FFFFFF")))
    for _ in range(30):
        tuft(c, rng.uniform(0, w), rng.uniform(530, 710), 0.8 + rng.random() * 0.6, rng.choice(["#2D8A5E", "#3A9A66"]))
    for _ in range(26):                                                                           # fireflies
        D.star(c, rng.uniform(40, w - 40), rng.uniform(380, 690), rng.choice((3, 4)), "#FFF59A")


def near_castle(c, w):
    """The palace terrace: a wide staircase with a red carpet up to the doors, the stone ground in front of it."""
    cx = w * 0.5
    vgrad(c, [(0, "#8E94B8"), (1, "#6F7599")], 476, WH)
    for i in range(6):
        yt = 478 + 26 * i
        hw = 250 + 26 * i
        c.rect(cx - hw, yt, cx + hw, yt + 26, "#B9B3C8")
        c.rect(cx - hw, yt, cx + hw, yt + 9, "#E9E4F2")
        c.rect(cx - 66 - i * 3, yt, cx + 66 + i * 3, yt + 26, "#C9314D")
        c.rect(cx - 66 - i * 3, yt, cx + 66 + i * 3, yt + 9, "#EF5A74")
        c.rect(cx - 70 - i * 3, yt, cx - 66 - i * 3, yt + 26, "#FFD21F")
        c.rect(cx + 66 + i * 3, yt, cx + 70 + i * 3, yt + 26, "#FFD21F")
    for s in (-1, 1):                                                                             # stone posts with lamps
        x = cx + s * 300
        c.rrect(x - 16, 400, x + 16, 620, 5, fill="#CFC9DE", outline="#9993B0", width=2)
        c.rrect(x - 22, 392, x + 22, 410, 4, fill="#E9E4F2", outline="#9993B0", width=2)
        c.ellipse(x, 372, 15, 20, fill="#FFE27A", outline="#B8933A", width=2)
    for y in range(646, WH, 30):                                                                  # paving
        c.rect(0, y, w, y + 2, "#7A80A4")


def far_ballroom(c, w, day=False):
    """A golden ballroom: tall arched windows with the night (or, with day=True, a sunny day) outside, gold pillars, chandeliers and a shiny chequered floor."""
    vgrad(c, [(0, "#FFF6DC"), (1, "#F6DDA2")], 0, 560)
    cx = w * 0.5
    for dx in (-390, 0, 390):                                                                     # arched windows
        x = cx + dx
        c.rect(x - 84, 150, x + 84, 440, "#F1C85A")
        c.ellipse(x, 150, 84, 84, fill="#F1C85A")
        c.rect(x - 70, 152, x + 70, 430, "#8FD3FF" if day else "#1F2C78")
        c.ellipse(x, 152, 70, 70, fill="#8FD3FF" if day else "#1F2C78")
        if day:
            c.ellipse(x - 30, 392, 64, 30, fill="#7FD16A")                                        # green hills, white clouds and a sun
            c.ellipse(x + 36, 402, 66, 28, fill="#69C45A")
            for ccx, ccy in ((-28, 250), (26, 336)):
                for ox, oy, orx, ory in ((0, 0, 24, 11), (-16, 4, 15, 9), (17, 3, 17, 10)):
                    c.ellipse(x + ccx + ox, ccy + oy, orx, ory, fill="#FFFFFF")
            if dx == 0:
                c.ellipse(x + 24, 196, 26, 26, fill="#FFE27A")
        else:
            for k in range(7):
                D.star(c, x - 52 + (k * 37) % 104, 110 + (k * 53) % 250, 4 + k % 3, "#FFF3A8")
            if dx == 0:
                c.ellipse(x + 20, 190, 26, 26, fill="#FFF8D0")
        c.rect(x - 3, 90, x + 3, 430, "#F1C85A")
        c.rect(x - 70, 290, x + 70, 296, "#F1C85A")
    for dx in (-195, 195, -585, 585):                                                             # gold pillars
        x = cx + dx
        c.rect(x - 24, 0, x + 24, 540, "#E8B93E")
        c.rect(x - 24, 0, x - 10, 540, "#F8DE7C")
        c.rect(x + 14, 0, x + 24, 540, "#C99A25")
        c.rrect(x - 36, 500, x + 36, 548, 6, fill="#D9A82E", outline="#B98A1E", width=2)
        c.rrect(x - 36, 0, x + 36, 36, 6, fill="#D9A82E", outline="#B98A1E", width=2)
    for dx in (-290, 290):                                                                        # chandeliers
        x = cx + dx
        c.line([(x, 0), (x, 60)], "#B98A1E", 5)
        c.poly([(x - 84, 150), (x + 84, 150), (x + 46, 100), (x - 46, 100)], fill="#E8B93E", outline="#B98A1E", width=2.5)
        c.ellipse(x, 150, 84, 13, fill="#D9A82E", outline="#B98A1E", width=2)
        c.ellipse(x, 98, 16, 12, fill="#D9A82E")
        for k in range(-3, 4):
            c.rect(x + k * 24 - 3.5, 118 + abs(k) * 5, x + k * 24 + 3.5, 140 + abs(k) * 2, "#FFFFFF")
            c.ellipse(x + k * 24, 112 + abs(k) * 5, 6, 10, fill="#FFE27A")
        for k in range(-3, 4):
            c.line([(x + k * 24, 158), (x + k * 24, 184 + (k % 2) * 14)], "#FFFFFF", 2.2)
            D.star(c, x + k * 24, 192 + (k % 2) * 14, 6, "#FFF3A8")
    c.rect(0, 520, w, 548, "#C99A25")                                                             # the dado
    def tw(y):
        return 36 + (y - 540) * 0.72                                                               # a tile is wider the closer it is
    for row, (y0, y1) in enumerate(((540, 556), (556, 576), (576, 600), (600, 630), (630, 668), (668, WH + 2))):    # the chequered floor in perspective
        for k in range(-int(cx // 36) - 3, int(cx // 36) + 4):
            col = "#FFF3D6" if (k + row) % 2 == 0 else "#F3B9C4"
            c.poly([(cx + (k - 0.5) * tw(y0), y0), (cx + (k + 0.5) * tw(y0), y0), (cx + (k + 0.5) * tw(y1), y1), (cx + (k - 0.5) * tw(y1), y1)], fill=col)


def near_ballroom(c, w):
    cx = w * 0.5
    c.poly([(cx - 150, 548), (cx + 150, 548), (cx + 330, WH), (cx - 330, WH)], fill="#C9314D")
    c.poly([(cx - 150, 548), (cx - 138, 548), (cx - 300, WH), (cx - 330, WH)], fill="#FFD21F")
    c.poly([(cx + 150, 548), (cx + 138, 548), (cx + 300, WH), (cx + 330, WH)], fill="#FFD21F")


BACKDROPS = {
    "meadow": (far_meadow, near_meadow),
    "garden_night": (far_night, near_night),
    "castle_night": (lambda c, w: far_night(c, w, castle=True), near_castle),
    "storm_castle": (lambda c, w: far_night(c, w, castle=True, storm=True), near_castle),
    "ballroom": (far_ballroom, near_ballroom),
    "ballroom_day": (lambda c, w: far_ballroom(c, w, day=True), near_ballroom),
    "meadow_dawn": (lambda c, w: far_meadow(c, w, "dawn"), near_meadow),
    "meadow_dusk": (lambda c, w: far_meadow(c, w, "dusk"), lambda c, w: near_meadow(c, w, path=False)),
    "meadow_open": (far_meadow, lambda c, w: near_meadow(c, w, path=False, flowers=60, trees=False, fence_on=False)),
    "forest": (far_forest, near_forest),
    "forest_dusk": (lambda c, w: far_forest(c, w, dusk=True), lambda c, w: near_forest(c, w, dusk=True)),
    "room": (far_room, near_room),
    "room_night": (lambda c, w: far_room(c, w, night=True), near_room),
    "race": (far_race, near_race),
    "river": (far_meadow, near_river),
    "meadow_gorge": (far_meadow, near_gorge),
    "meadow_gorge_dusk": (lambda c, w: far_meadow(c, w, "dusk"), near_gorge),
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
