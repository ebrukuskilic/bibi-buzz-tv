"""Pictures for the song videos: farm backdrops (a red barn, a silo, hay and fences under a sunny sky), a sack of wool, a rainbow and a puff of wool.

The backdrops are registered in storyart2.BACKDROPS when this module is imported (songs.py does that), under the names
'farm', 'farm_dawn', 'farm_dusk' and 'farm_open' (the same farm without the fence in front, so that the friends have room).
The props 'wool_bag' and 'rainbow' and the effects 'wool_burst' and 'word_pop' are registered in storyprops.PROPS / FX.
"""
import math
import random

from . import draw as D
from . import storyart2 as B
from . import vibe as VB
from .draw import INK, clamp, darker, mix, ease_out_back
from .storyart import Rig
from .storyprops import prop, fx, _tint

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


# ================================================================================================ the rainbow sheep: a sack of wool, a rainbow, a puff of wool
RAINBOW6 = ["#E2362F", "#FF8A1F", "#FFD21F", "#3DB54A", "#3E8EDE", "#8C5BC8"]          # red, orange, yellow, green, blue, purple


def _colors(v, default="#FFFFFF"):
    return [v] if isinstance(v, str) else (list(v) if v else [default])


@prop
def wool_bag(c, x, y, k, t, st):
    """A cloth sack tied at the top with a fluffy puff of wool coming out of it; (x, y) = the middle of its bottom.
    st: wool = the colour of the wool (a colour, or a list of colours for a rainbow puff), n = the number on the sack (0 = no number)."""
    ws = _colors(st.get("wool"))
    n = int(round(st.get("n", 0)))
    cloth, rope = "#E9D5A1", "#C0742B"
    r = Rig(c, x, y, k)
    _tint(c, [r.P(52 * math.cos(2 * math.pi * i / 20), -2 + 9 * math.sin(2 * math.pi * i / 20)) for i in range(20)], "#1E4D1A", 0.26)     # the shadow on the grass
    for i, (px, py, rr) in enumerate(((-27, -90, 19), (27, -90, 19), (-15, -107, 21), (15, -107, 21), (0, -116, 17), (0, -96, 22))):      # the puff of wool
        r.ell(px, py, rr, rr * 0.94, ws[i % len(ws)], INK, 2.8)
    r.ell(-13, -112, 8, 4.5, mix(ws[2 % len(ws)], "#FFFFFF", 0.5), None, ang=-25)
    r.poly([(-21, -58), (21, -58), (15, -88), (-15, -88)], cloth, INK, 2.8)                                                             # the neck
    r.ell(0, -36, 47, 37, cloth, INK, 3.0)                                                                                              # the belly of the sack
    r.ell(-17, -52, 17, 9, mix(cloth, "#FFFFFF", 0.55), None, ang=-30)
    for (sx, sy) in ((-34, -22), (30, -20), (-8, -14), (36, -44)):                                                                      # stitches
        r.line([(sx - 5, sy - 3), (sx + 5, sy + 3)], darker(cloth, 0.22), 2.2)
    r.poly([(-22, -73), (22, -73), (20, -64), (-20, -64)], rope, INK, 2.4)                                                              # the rope
    r.poly([(0, -69), (-13, -80), (-6, -62)], rope, INK, 2.0)
    r.poly([(0, -69), (13, -80), (6, -62)], rope, INK, 2.0)
    r.dot(0, -69, 5.2, darker(rope, 0.18))
    if n > 0:                                                                                                                            # the number, on a round patch in the colour of the wool
        r.ell(0, -33, 21, 21, ws[0], INK, 2.8)
        px, py = r.P(0, -32)
        c.text(px, py, str(n), 34 * k, "#FFFFFF", stroke=3.2 * k, stroke_fill=INK)
    return r


@prop
def rainbow(c, x, y, k, t, st):
    """A rainbow of six bands in an arch (x, y = the middle of its base, on the ground behind everybody).
    st: grow = 0..1, how much of it is painted (from left to right: it sweeps across the sky), r = outer radius, band = width of a band, clouds = 1: a cloud at both ends."""
    grow = clamp(st.get("grow", 1.0))
    if grow <= 0.004:
        return None
    R, bw = st.get("r", 330.0), st.get("band", 17.0)
    r = Rig(c, x, y, k)
    a_end = 180.0 - 180.0 * grow
    steps = max(4, int(46 * grow))
    for i, col in enumerate(RAINBOW6):
        ro, ri = R - i * bw, R - (i + 1) * bw - (0.7 if i < 5 else 0.0)
        pts = [(ro * math.cos(math.radians(180.0 + (a_end - 180.0) * j / steps)), -ro * math.sin(math.radians(180.0 + (a_end - 180.0) * j / steps))) for j in range(steps + 1)]
        pts += [(ri * math.cos(math.radians(a_end + (180.0 - a_end) * j / steps)), -ri * math.sin(math.radians(a_end + (180.0 - a_end) * j / steps))) for j in range(steps + 1)]
        r.poly(pts, col, None)
    for rad in (R, R - 6 * bw):                                                                  # a thin outline around the whole arch
        r.arc(0, 0, rad, rad, -180.0, -a_end, INK, 3.0, n=max(6, int(60 * grow)))
    if st.get("clouds", 1.0) > 0.5:
        mid = R - 3 * bw
        if grow > 0.04:
            B.cloud_shape(c, *r.P(-mid, -6), 1.05 * k)
        if grow > 0.97:
            B.cloud_shape(c, *r.P(mid, -6), 1.05 * k)
    return r


@fx
def wool_burst(c, s, x, y, dt, color="#E2362F", r=210, n=14, **_):
    """Soft puffs of wool in the given colour (or a list of colours) fly out of (x, y), slow down and float to the ground."""
    if dt > 1.5:
        return
    cols = _colors(color)
    u = dt / 1.5
    for i in range(n):
        ang = (i + 0.5) / n * 2 * math.pi + 0.5 * math.sin(i * 7.3)
        sp = r * (0.5 + 0.5 * ((i * 37) % 10) / 10.0)
        d = sp * (1.0 - (1.0 - min(1.0, dt / 0.9)) ** 2.4)
        px, py = x + d * math.cos(ang), y + d * math.sin(ang) * 0.8 + 70.0 * u * u
        rad = (11.0 + 9.0 * ((i * 13) % 5) / 4.0) * (1.0 - u ** 3)
        if rad <= 1.0:
            continue
        col = cols[i % len(cols)]
        for dx, dy in ((-0.6, 0.12), (0.6, 0.12), (-0.28, -0.5), (0.34, -0.46)):                  # a fluffy tuft: a ring of little puffs round a filled middle
            c.ellipse(px + dx * rad, py + dy * rad, rad * 0.62, rad * 0.6, fill=col, outline=INK, width=1.8)
        c.ellipse(px, py - 0.02 * rad, rad * 0.86, rad * 0.7, fill=col)
        c.ellipse(px - rad * 0.3, py - rad * 0.3, rad * 0.34, rad * 0.22, fill=mix(col, "#FFFFFF", 0.55))


@fx
def word_pop(c, s, x, y, dt, text="RED", color="#E2362F", size=1.0, hold=0.8, **_):
    """A big colour word that pops up (in its own colour) at (x, y), stays for `hold` seconds and shrinks away."""
    sc = ease_out_back(clamp(dt / 0.22)) * size
    if dt > hold:
        sc *= clamp(1.0 - (dt - hold) / 0.2)
    if sc <= 0.03:
        return
    wob = 1.0 + 0.04 * math.sin(dt * 14.0)
    c.text(x, y, text, 78 * sc * wob, color, stroke=8 * sc, stroke_fill=INK)
