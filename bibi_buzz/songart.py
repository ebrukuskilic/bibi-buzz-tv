"""Farm backdrops for the song videos: a red barn, a silo, hay and fences under a sunny sky.

They are registered in storyart2.BACKDROPS when this module is imported (songs.py does that), under the names
'farm', 'farm_dawn', 'farm_dusk' and 'farm_open' (the same farm without the fence in front, so that the friends have room).
"""
import math
import random

from . import draw as D
from . import storyart2 as B
from . import vibe as VB
from .draw import INK, darker, mix

WH = B.WH


def box(c, x0, y0, x1, y1, fill, outline=None, width=0):
    """A rectangle with an outline (Canvas.rect has none)."""
    c.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill=fill, outline=outline, width=width)


def barn(c, x, gy, s=1.0, wall="#D9473B", roof="#9C3027"):
    """A red barn with white trim, a hay loft window and big doors with white crosses (x = middle, gy = the ground)."""
    w, h = 230 * s, 118 * s
    x0, x1 = x - w / 2, x + w / 2
    box(c, x0, gy - h, x1, gy, wall, outline=INK, width=2.4)
    for i in range(1, 9):                                                               # the boards
        bx = x0 + w * i / 9
        c.line([(bx, gy - h + 4 * s), (bx, gy - 3 * s)], darker(wall, 0.16), 1.6)
    top = gy - h
    c.poly([(x0 - 14 * s, top + 6 * s), (x0 + w * 0.17, top - 62 * s), (x, top - 84 * s), (x1 - w * 0.17, top - 62 * s), (x1 + 14 * s, top + 6 * s)],
           fill=roof, outline=INK, width=2.4)
    c.poly([(x0 + w * 0.17, top - 62 * s), (x, top - 84 * s), (x1 - w * 0.17, top - 62 * s), (x1 - w * 0.2, top + 2 * s), (x0 + w * 0.2, top + 2 * s)],
           fill=wall, outline=INK, width=2.0)                                           # the gable under the roof, with the loft window
    c.rrect(x - 21 * s, top - 62 * s, x + 21 * s, top - 22 * s, 4 * s, fill="#7A3A22", outline="#FFFFFF", width=3.2)
    c.line([(x - 21 * s, top - 62 * s), (x + 21 * s, top - 22 * s)], "#FFFFFF", 3 * s)
    c.line([(x + 21 * s, top - 62 * s), (x - 21 * s, top - 22 * s)], "#FFFFFF", 3 * s)
    dw, dh = 74 * s, 82 * s                                                              # the big doors
    box(c, x - dw, gy - dh, x + dw, gy, "#F8E8D0", outline="#FFFFFF", width=4)
    for sx in (-1, 1):
        a, b = (x, x + sx * dw)
        box(c, min(a, b), gy - dh + 3 * s, max(a, b), gy, "#E05A48", outline="#FFFFFF", width=3.2)
        c.line([(a, gy - dh + 3 * s), (b, gy)], "#FFFFFF", 3.2 * s)
        c.line([(b, gy - dh + 3 * s), (a, gy)], "#FFFFFF", 3.2 * s)
    c.line([(x, gy - dh), (x, gy)], "#FFFFFF", 3.5)


def silo(c, x, gy, s=1.0):
    w, h = 62 * s, 190 * s
    box(c, x - w / 2, gy - h, x + w / 2, gy, "#D8E4EE", outline=INK, width=2.2)
    c.rect(x - w / 2 + w * 0.62, gy - h, x + w / 2, gy, "#BCCBDA")
    for k in range(1, 6):
        yy = gy - h * k / 6
        c.line([(x - w / 2, yy), (x + w / 2, yy)], "#8FA3B8", 2.0)
    c.ellipse(x, gy - h, w / 2, 26 * s, fill="#E9A39A", outline=INK, width=2.2)
    c.rect(x - w / 2, gy - h - 1, x + w / 2, gy - h + 2, "#D8E4EE")


def haystack(c, x, gy, s=1.0):
    c.ellipse(x, gy - 4 * s, 62 * s, 12 * s, fill="#66B650")
    c.poly([(x - 56 * s, gy), (x - 44 * s, gy - 46 * s), (x - 16 * s, gy - 72 * s), (x + 16 * s, gy - 72 * s), (x + 44 * s, gy - 46 * s), (x + 56 * s, gy)],
           fill="#F4C84A", outline=INK, width=2.2)
    for dx, dy in ((-30, -20), (0, -34), (28, -18), (-10, -54), (16, -52)):
        c.line([(x + dx * s - 9 * s, gy + dy * s), (x + dx * s + 9 * s, gy + dy * s - 4 * s)], "#D9A52B", 2.4)


def hay_bale(c, x, gy, s=1.0):
    c.ellipse(x, gy - 2 * s, 50 * s, 9 * s, fill="#47A033")
    c.ellipse(x, gy - 38 * s, 40 * s, 38 * s, fill="#F2C94B", outline=INK, width=2.4)
    for r in (28, 17, 7):
        c.ellipse(x, gy - 38 * s, r * s, r * s, fill=None, outline="#D4A12E", width=2.2)


def far_farm(c, w, mood="day", seed=5):
    rng = random.Random(seed)
    if mood == "dawn":
        B.vgrad(c, [(0, "#8FB8FF"), (0.5, "#FFD0B0"), (1, "#FFEBC8")], 0, 580)
    elif mood == "dusk":
        B.vgrad(c, [(0, "#7A86DE"), (0.5, "#F7AFC0"), (1, "#FFDDB0")], 0, 580)
    else:
        B._sky(c, y1=580)
    B.sun_shape(c, 1060, 118, 56, "#FFE066" if mood == "day" else "#FFC25A")
    for i in range(int(w // 520) + 3):
        B.cloud_shape(c, 120 + i * 520 + rng.randint(-60, 60), 84 + rng.randint(0, 80), 0.8 + rng.random() * 0.5)
    B.hills(c, w, 470, 54, 210, 1.2, "#A8E39B" if mood != "dusk" else "#9BD58F")
    B.windmill(c, 900, 462, 1.0)
    B.round_tree(c, 60, 474, 92, "#6CCB74", "#9A7B55")
    B.round_tree(c, 1230, 474, 86, "#6CCB74", "#9A7B55")
    silo(c, 505, 484, 1.0)
    barn(c, 350, 488, 1.0)
    haystack(c, 650, 492, 0.8)
    B.hills(c, w, 528, 36, 170, 2.4, "#88D675")
    B.fence(c, 0, w, 548, 0.55, color="#F8EBD0")
    c.rect(0, 546, w, WH, "#7AD05F")


def near_farm(c, w, seed=6, fence_on=True, bales=True):
    rng = random.Random(seed)
    B.vgrad(c, [(0, "#86DC5A"), (0.4, "#6BC84A"), (1, "#54B13B")], 530, WH)
    if fence_on:
        B.fence(c, 0, min(w, 300), 548, 0.9)
        B.fence(c, max(0, w - 260), w, 548, 0.9)
    if bales:
        hay_bale(c, 1160, 600, 0.9)
        hay_bale(c, 118, 612, 0.8)
    B.bush(c, 250, 560, 0.9)
    cols = ["#FF6B8B", "#FFD23F", "#FFFFFF", "#B58CFF", "#FF9A3D"]
    for _ in range(46):
        x, y = rng.uniform(0, w), rng.uniform(552, 705)
        B.flower_dot(c, x, y, 0.7 + (y - 520) / 300, rng.choice(cols))
    for _ in range(34):
        B.tuft(c, rng.uniform(0, w), rng.uniform(540, 712), 0.8 + rng.random() * 0.6, rng.choice(["#4FAE35", "#5BBE3E"]))


B.BACKDROPS["farm"] = (far_farm, near_farm)
B.BACKDROPS["farm_dawn"] = (lambda c, w: far_farm(c, w, "dawn", 7), lambda c, w: near_farm(c, w, 8))
B.BACKDROPS["farm_dusk"] = (lambda c, w: far_farm(c, w, "dusk", 9), lambda c, w: near_farm(c, w, 10, bales=False))
B.BACKDROPS["farm_open"] = (lambda c, w: far_farm(c, w, "day", 11), lambda c, w: near_farm(c, w, 12, fence_on=False, bales=False))

# the living layer (birds, butterflies, swaying grass in front) works by the name of the backdrop
VB.STORY_AMBIENT.update({"farm": ("day", False), "farm_dawn": ("day", False), "farm_dusk": ("day", True), "farm_open": ("day", False)})
VB.FG_GRASS.update({"farm": "#3FA33A", "farm_dawn": "#4CA84A", "farm_dusk": "#C98A2E", "farm_open": "#3FA33A"})
