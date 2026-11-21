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


# ================================================================================================ the lake: Row, row, row your boat
LAKE_Y = 408                                                   # the horizon: where the far shore meets the water
LAKE_MOODS = {
    "day":   dict(sky=[(0, "#79C8FF"), (0.55, "#B6E7FF"), (1, "#F2FBFF")], water=("#A8E4FF", "#3E9BE8"), tint="#3E9BE8", mount="#9DB9E3", snow="#FFFFFF",
                  hill="#7FD07A", tree="#3FAE49", bank=("#6BC84A", "#4FAE35"), fg="#3FA33A", glow="#FFFFFF"),
    "dawn":  dict(sky=[(0, "#8FB8FF"), (0.5, "#FFD0B0"), (1, "#FFEBC8")], water=("#FFDCC4", "#5C9FE0"), tint="#5C9FE0", mount="#B9A6D6", snow="#FFE9E0",
                  hill="#8FC77E", tree="#4CA84A", bank=("#79C95A", "#58B243"), fg="#4CA84A", glow="#FFE0B0"),
    "dusk":  dict(sky=[(0, "#5A6FD0"), (0.45, "#E88FB0"), (1, "#FFD8A0")], water=("#FFC89A", "#6A74C8"), tint="#6A74C8", mount="#7B79BE", snow="#FFD9E0",
                  hill="#5E8CA8", tree="#3F7C74", bank=("#5BA85A", "#418E4C"), fg="#C98A2E", glow="#FFD27A"),
    "night": dict(sky=[(0, "#0F1A4C"), (0.55, "#2A3B88"), (1, "#5B5FAA")], water=("#3E4C9A", "#18265E"), tint="#18265E", mount="#243780", snow="#8C9CE0",
                  hill="#1F4A5C", tree="#1B5A4E", bank=("#2C7A62", "#184A41"), fg="#2F4A8A", glow="#FFF6C8"),
}


def _water_col(mood, y):
    a, b = LAKE_MOODS[mood]["water"]
    return mix(a, b, clamp((y - LAKE_Y) / (WH - LAKE_Y)))


def _mountains(c, w, base, color, snow, peaks):
    for px, h in peaks:
        c.poly([(px - h * 1.05, base + 4), (px - h * 0.35, base - h * 0.72), (px, base - h), (px + h * 0.4, base - h * 0.7), (px + h * 1.05, base + 4)], fill=color)
        cap = [(px - h * 0.2, base - h * 0.8), (px, base - h), (px + h * 0.17, base - h * 0.8), (px + h * 0.07, base - h * 0.73), (px - h * 0.03, base - h * 0.79),
               (px - h * 0.1, base - h * 0.72)]
        c.poly(cap, fill=snow)


def lighthouse(c, x, gy, s=1.0, lit=False):
    """A red and white lighthouse on a little rock (x = middle, gy = the water)."""
    c.ellipse(x, gy + 2 * s, 78 * s, 14 * s, fill="#8E8A9E")
    c.ellipse(x - 12 * s, gy - 4 * s, 52 * s, 10 * s, fill="#A9A6B8")
    h, wb, wt = 168 * s, 25 * s, 16 * s
    for i in range(4):                                                              # four stripes, red and white
        y0, y1 = gy - 4 * s - h * i / 4, gy - 4 * s - h * (i + 1) / 4
        w0, w1 = wb + (wt - wb) * i / 4, wb + (wt - wb) * (i + 1) / 4
        c.poly([(x - w0, y0), (x + w0, y0), (x + w1, y1), (x - w1, y1)], fill="#E2574C" if i % 2 == 0 else "#FFFFFF", outline=INK, width=2.0)
    top = gy - 4 * s - h
    c.rrect(x - 26 * s, top - 6 * s, x + 26 * s, top + 4 * s, 3 * s, fill="#4A4A5E", outline=INK, width=2.0)       # the gallery
    c.rrect(x - 15 * s, top - 40 * s, x + 15 * s, top - 6 * s, 5 * s, fill="#FFE27A" if not lit else "#FFF6B0", outline=INK, width=2.0)   # the lamp room
    c.poly([(x - 20 * s, top - 40 * s), (x + 20 * s, top - 40 * s), (x, top - 66 * s)], fill="#E2574C", outline=INK, width=2.0)
    c.ellipse(x, top - 70 * s, 3.5 * s, 3.5 * s, fill=INK)
    if lit:
        VB.glow(c, x, top - 23 * s, 70 * s, "#FFF3A8", 0.75)


def _moon(c, x, y):
    for i, a in enumerate((2.3, 1.75, 1.35)):
        c.ellipse(x, y, 52 * a, 52 * a, fill=mix("#2A3B88", "#FFF3B0", 0.1 + 0.12 * i))
    c.ellipse(x, y, 52, 52, fill="#FFF8D0")
    for dx, dy, rr in ((-16, -10, 9), (13, 14, 7), (17, -16, 5)):
        c.ellipse(x + dx, y + dy, rr, rr, fill="#F0E6B0")


def far_lake(c, w, mood="day", seed=31):
    """Sky, sun (or moon), clouds, far mountains, the far shore with a lighthouse, and the water with a path of light."""
    rng = random.Random(seed)
    M = LAKE_MOODS[mood]
    B.vgrad(c, M["sky"], 0, LAKE_Y + 14)
    if mood == "night":
        for _ in range(90):
            D.star(c, rng.uniform(0, w), rng.uniform(10, 330), rng.choice((3, 4, 5, 6)), rng.choice(("#FFF3A8", "#FFFFFF", "#CFE3FF")))
        sx = 1060
        _moon(c, sx, 118)
    elif mood == "dusk":
        sx = 700
        B.sun_shape(c, sx, 384, 78, "#FFB347", "#FFD9A0")
    elif mood == "dawn":
        sx = 330
        B.sun_shape(c, sx, 372, 66, "#FFC25A", "#FFE3B0")
    else:
        sx = 1050
        B.sun_shape(c, sx, 118, 56, "#FFE066")
    if mood != "night":
        cl = {"day": ("#FFFFFF", "#E6F3FF"), "dawn": ("#FFF1E6", "#F6CFC4"), "dusk": ("#FFD3C2", "#E89AAE")}[mood]
        for i in range(int(w // 430) + 3):
            B.cloud_shape(c, 100 + i * 430 + rng.randint(-60, 60), 80 + rng.randint(0, 120), 0.8 + rng.random() * 0.55, cl[0], cl[1])
    peaks = {"dawn": [(40, 110), (560, 150), (800, 115), (1010, 170), (1220, 125)],                                    # (the sun gets a gap between the mountains)
             "dusk": [(110, 150), (350, 112), (1010, 150), (1210, 176)]}.get(mood, [(150, 150), (380, 112), (600, 170), (900, 130), (1110, 175), (1290, 120)])
    _mountains(c, w, LAKE_Y - 8, M["mount"], M["snow"], peaks)
    B.hills(c, w, LAKE_Y - 18, 26, 160, 0.9, M["hill"])
    B.hills(c, w, LAKE_Y - 2, 14, 110, 2.6, mix(M["hill"], M["tree"], 0.35))
    for x in (40, 96, 150, 905, 960, 1015, 1075, 1140, 1210):                          # trees along the far shore
        if rng.random() < 0.5:
            B.pine_tree(c, x + rng.randint(-8, 8), LAKE_Y + 4, 66 + rng.randint(-8, 22), M["tree"])
        else:
            B.round_tree(c, x + rng.randint(-8, 8), LAKE_Y + 4, 58 + rng.randint(-8, 18), M["tree"], "#7A5A38")
    B.small_house_far(c, 800, LAKE_Y + 3, 1.0, "#F7E8C8" if mood != "night" else "#C9CCE8", "#D9654F" if mood != "night" else "#6C5FC7")
    lighthouse(c, 250, LAKE_Y + 4, 0.95, lit=(mood in ("dusk", "night")))
    B.vgrad(c, [(0, M["water"][0]), (1, M["water"][1])], LAKE_Y, WH)                                                  # the water
    for i in range(40):                                                                 # soft bands of light on it
        u = (i / 40.0) ** 1.6
        y = LAKE_Y + 8 + u * 296
        ln = 40 + 220 * u
        x = rng.uniform(-40, w - ln + 40)
        c.line([(x, y), (x + ln, y)], mix(_water_col(mood, y), "#FFFFFF", 0.22), 2.0 + 2.4 * u)
    for j in range(15):                                                                 # the path of light under the sun / moon
        y = LAKE_Y + 8 + j * 21
        rx = 12 + j * 6.5 + rng.uniform(-3, 3)
        c.ellipse(sx + rng.uniform(-8, 8) * (1 + j * 0.2), y, rx, 2.4 + j * 0.16, fill=mix(_water_col(mood, y), M["glow"], max(0.18, 0.62 - j * 0.03)))
    c.line([(0, LAKE_Y), (w, LAKE_Y)], mix(M["hill"], "#FFFFFF", 0.25), 2.0)


def _lily(c, x, y, s, rng, flower=False, pad="#3FAE49"):
    c.ellipse(x, y + 3 * s, 34 * s, 11 * s, fill=darker(pad, 0.25))
    c.ellipse(x, y, 34 * s, 11 * s, fill=pad)
    c.poly([(x, y), (x + 36 * s, y - 7 * s), (x + 36 * s, y + 1 * s)], fill=mix(pad, "#3E9BE8", 0.55))
    c.ellipse(x - 9 * s, y - 3 * s, 11 * s, 3.4 * s, fill=mix(pad, "#FFFFFF", 0.3))
    if flower:
        for dx, rr in ((-9, 7), (9, 7), (0, 9)):
            c.ellipse(x - 12 * s + dx * s, y - 12 * s, rr * s * 0.8, rr * s * 1.3, fill="#FF8FB0", outline=INK, width=1.4)
        c.ellipse(x - 12 * s, y - 10 * s, 3 * s, 3 * s, fill="#FFD23F")


def _reed(c, x, y, s, rng, col="#3E9B3A"):
    for i in range(4):
        dx = rng.uniform(-14, 14) * s
        hh = rng.uniform(70, 120) * s
        c.line([(x + dx * 0.3, y), (x + dx, y - hh)], col, 3.2 * s)
        if i % 2 == 0:
            c.ellipse(x + dx, y - hh - 8 * s, 4.6 * s, 12 * s, fill="#8B5A2B")
    for dx in (-18, -6, 10, 22):
        c.poly([(x + dx * s - 3, y), (x + dx * s + 3, y), (x + dx * s * 1.7, y - 42 * s)], fill=col)


def near_lake(c, w, mood="day", seed=32):
    """The two grassy banks in the bottom corners, with trees, flowers and reeds; lily pads on the water."""
    rng = random.Random(seed)
    M = LAKE_MOODS[mood]
    g_hi, g_lo = M["bank"]
    sand = mix("#EAD7A0", M["water"][1], 0.35 if mood == "night" else 0.0)
    left = [(-20, 520), (50, 526), (118, 548), (176, 584), (214, 630), (236, 684), (244, 740), (-20, 740)]
    right = [(w + 20, 520), (w - 50, 528), (w - 120, 552), (w - 182, 590), (w - 220, 636), (w - 240, 690), (w - 248, 740), (w + 20, 740)]
    for pts, sgn in ((left, 1), (right, -1)):
        c.poly([(x + sgn * 12, y - 6) for x, y in pts[:-2]] + pts[-2:], fill=sand)                       # the sandy edge
        c.poly(pts, fill=g_hi)
        c.poly(pts, fill=None, outline=darker(g_hi, 0.35), width=2.0)
    B.round_tree(c, 70, 574, 270, M["tree"] if mood != "day" else "#3FAE49")
    B.round_tree(c, w - 84, 566, 292, M["tree"] if mood != "day" else "#46B650")
    B.bush(c, 190, 590, 0.95, mix(M["bank"][0], "#2F8A3A", 0.2))
    B.bush(c, w - 176, 598, 1.0, mix(M["bank"][0], "#2F8A3A", 0.2))
    cols = ["#FF6B8B", "#FFD23F", "#FFFFFF", "#B58CFF", "#FF9A3D"]
    for _ in range(26):
        x = rng.uniform(0, 150) if rng.random() < 0.5 else rng.uniform(w - 150, w)
        y = rng.uniform(604, 710)
        B.flower_dot(c, x, y, 0.7 + (y - 520) / 300, rng.choice(cols))
    for _ in range(20):
        x = rng.uniform(0, 190) if rng.random() < 0.5 else rng.uniform(w - 190, w)
        B.tuft(c, x, rng.uniform(600, 716), 0.8 + rng.random() * 0.6, rng.choice([M["bank"][1], mix(M["bank"][1], "#FFFFFF", 0.1)]))
    for x, y, s in ((236, 612, 0.9), (w - 252, 626, 1.0)):                                               # cattails at the water's edge
        _reed(c, x, y, s, rng, mix("#3E9B3A", M["bank"][1], 0.4))
    _lily(c, 330, 668, 0.9, rng, True)
    _lily(c, 404, 700, 0.7, rng)
    _lily(c, w - 340, 676, 0.85, rng)
    _lily(c, w - 420, 706, 0.7, rng, True)


for _name, _mood in (("lake", "day"), ("lake_dawn", "dawn"), ("lake_dusk", "dusk"), ("lake_night", "night")):
    B.BACKDROPS[_name] = (lambda c, w, m=_mood, n=_name: far_lake(c, w, m, 31 + len(n)), lambda c, w, m=_mood, n=_name: near_lake(c, w, m, 32 + len(n)))
    VB.FG_GRASS[_name] = LAKE_MOODS[_mood]["fg"]
VB.STORY_AMBIENT.update({"lake": ("day", False), "lake_dawn": ("day", False), "lake_dusk": ("day", True), "lake_night": ("night", True)})


# ---------------------------------------------------------------- the rowing boat (a side view: two props, so that the friends sit between them)
BOAT_L = 400.0                                                 # half the length of the hull
OAR_X, OAR_Y = -10.0, -66.0                                    # the oarlock (in the boat's own units: x to the bow, y down, 0 = the waterline)


def _ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def _sheer(u):
    """The top edge of the hull at u = -1 (stern) .. 1 (bow): it sags in the middle and rises toward the bow."""
    return -64.0 - 34.0 * u * u - 40.0 * max(0.0, u) ** 3


def _keel(u):
    return 34.0 * max(0.0, 1.0 - u * u) ** 0.55 - 8.0


def _hull(inset=0.0, n=24):
    top = [(BOAT_L * (2.0 * i / n - 1.0), _sheer(2.0 * i / n - 1.0) + inset) for i in range(n + 1)]
    bot = [(BOAT_L * (0.93 - 1.83 * i / n), _keel(0.93 - 1.83 * i / n) - inset) for i in range(n + 1)]
    return top + bot


def _band(d0, d1, u0=-0.985, u1=0.97, n=30):
    """A strip that follows the sheer line, from d0 to d1 below it."""
    us = [u0 + (u1 - u0) * i / n for i in range(n + 1)]
    return [(BOAT_L * u, _sheer(u) + d0) for u in us] + [(BOAT_L * u, _sheer(u) + d1) for u in reversed(us)]


def _boat_rig(c, x, y, k, t, st):
    """The rig of the boat: it bobs and rocks a little, once in two strokes of the oar."""
    bar = st.get("bar", 0.0) or 2.0
    ph = 2.0 * math.pi * t / (2.0 * bar) + st.get("ph", 0.0)
    rock = st.get("rock", 1.0)
    return Rig(c, x, st.get("wl", y) + 3.5 * rock * math.sin(ph + 1.1) * k, k, face=st.get("face", 1), lean=1.25 * rock * math.sin(ph))


def _lens(c, x, y, k, t, tint, R=470.0, depth=78.0):
    """The water in front of the hull: see-through, with a waving foam line on top, its ends and its bottom fading away. Returns the rig of the level water."""
    w = Rig(c, x, y, k)
    n = 52

    def wave(px):
        return 3.6 * math.sin(px / 36.0 + t * 2.3) + 2.0 * math.sin(px / 16.0 - t * 3.0)
    for f, a in ((1.0, 0.20), (0.9, 0.20), (0.78, 0.20), (0.62, 0.18)):
        top = [(R * f * (2.0 * i / n - 1.0), wave(R * f * (2.0 * i / n - 1.0))) for i in range(n + 1)]
        bot = [(R * f * math.cos(math.pi * j / 24), depth * f * math.sin(math.pi * j / 24)) for j in range(25)]
        _tint(c, [w.P(*p) for p in top + bot], tint, a)
    line = [(R * 0.97 * (2.0 * i / n - 1.0), wave(R * 0.97 * (2.0 * i / n - 1.0))) for i in range(n + 1)]
    w.line(line, "#EAF7FF", 3.2)
    for j in range(7):                                                                          # foam
        px = -R * 0.85 + j * R * 0.28 + 12.0 * math.sin(t * 1.3 + j)
        w.ell(px, wave(px) + 6.0, 20.0, 3.2, "#F4FBFF", None)
    return w


def _oar(r, c, t, bar, tint, k):
    """The near oar: the handle swings opposite the blade; the blade is in the water for the first half of the stroke (the pull) and comes back through the air."""
    px, py = OAR_X, OAR_Y
    s = (t / bar) % 1.0 if bar else 0.0
    inwater = False
    if bar:
        if s < 0.5:
            u = _ease(s / 0.5)
            bx, by = px + 150.0 + (-210.0 - 150.0) * u, 14.0 - 12.0 * clamp((s - 0.43) / 0.07)
            inwater = s < 0.46
        else:
            u = (s - 0.5) / 0.5
            bx = px - 210.0 + 360.0 * _ease(u)
            by = 2.0 + 10.0 * _ease(clamp((u - 0.84) / 0.16)) - 46.0 * math.sin(math.pi * u) ** 0.8
    else:
        bx, by = px - 175.0, -108.0
    dx, dy = bx - px, by - py
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux
    hx, hy = px - ux * 54.0, py - uy * 54.0
    sx_, sy_ = bx - ux * 70.0, by - uy * 70.0
    wood, red = "#C98A52", "#E2574C"
    r.limb((hx, hy), (sx_ + ux * 4, sy_ + uy * 4), 8.0, wood, INK, 2.4)
    r.poly([(sx_ + nx * 6, sy_ + ny * 6), (bx - ux * 6 + nx * 15, by - uy * 6 + ny * 15), (bx + ux * 8 + nx * 9, by + uy * 8 + ny * 9),
            (bx + ux * 8 - nx * 9, by + uy * 8 - ny * 9), (bx - ux * 6 - nx * 15, by - uy * 6 - ny * 15), (sx_ - nx * 6, sy_ - ny * 6)], red, INK, 2.4)
    r.line([(sx_ + ux * 14, sy_ + uy * 14), (bx - ux * 4, by - uy * 4)], "#FFFFFF", 4.0)
    r.dot(hx, hy, 8.0, "#E8B27A")
    r.ell(hx, hy, 8.0, 8.0, None, INK, 2.2)
    r.ell(px, py + 3, 9.0, 9.0, None, "#6A6A7E", 3.2)                                           # the oarlock ring
    return bx, by, inwater


@prop
def boat_back(c, x, y, k, t, st):
    """The far half of the rowing boat: its shadow on the water, the inside of the far wall. (y only sets the depth order; st['wl'] is the waterline.)
    st: face (1 = the bow points to the right), bar = seconds of one oar stroke (the boat rocks to it), wl = the waterline."""
    r = _boat_rig(c, x, y, k, t, st)
    wl = st.get("wl", y)
    _tint(c, [(x + BOAT_L * 1.02 * math.cos(math.pi * j / 20), wl + 7 + 20 * math.sin(math.pi * j / 20)) for j in range(41)], "#14305A", 0.26)
    r.poly(_band(-17, 50), "#EBC38B", INK, 2.8)
    for off in (6, 22, 38):
        r.line([(BOAT_L * u / 30.0, _sheer(u / 30.0) + off) for u in range(-29, 30)], "#D4A46A", 2.0)
    r.poly(_band(-17, -7), "#B8793C", INK, 2.4)
    return r


@prop
def boat_front(c, x, y, k, t, st):
    """The near wall of the boat with its stripes and portholes, the oar, the pennant, a lantern, and the water around it (put it in front of the friends).
    st: face, bar (0 = the oar rests), wl, water = the colour of the water, flag = the colour of the pennant, lantern = 0..1."""
    r = _boat_rig(c, x, y, k, t, st)
    wl = st.get("wl", y)
    bar = st.get("bar", 0.0)
    body, rail, stripe = "#FFC93C", "#B8793C", "#3E8EDE"
    r.poly(_hull(), body, INK, 3.4)
    r.poly(_band(30, 46), stripe, None)
    r.poly(_band(10, 12), "#E8A81E", None)
    for off in (62, 80):                                                                        # planks
        run = []
        for i in range(-29, 30):
            u = i / 30.0
            if _sheer(u) + off < _keel(u) - 9.0:
                run.append((BOAT_L * u, _sheer(u) + off))
            elif len(run) > 1:
                r.line(run, "#E8A81E", 2.0)
                run = []
            else:
                run = []
        if len(run) > 1:
            r.line(run, "#E8A81E", 2.0)
    r.poly(_band(0, 13), rail, INK, 2.8)
    for u in (-0.9, -0.7, -0.5, -0.3, -0.1, 0.1, 0.3, 0.5, 0.7, 0.9):                           # rivets
        r.dot(BOAT_L * u, _sheer(u) + 38.0, 3.0, "#FFFFFF")
    r.poly([(BOAT_L * 0.992, _sheer(0.992)), (BOAT_L * 1.012, _sheer(1.0) - 16), (BOAT_L * 0.94, _sheer(0.94) - 6)], rail, INK, 2.4)         # the curl of the bow
    r.ell(BOAT_L * 0.99, _sheer(1.0) - 11, 6.0, 6.0, "#E8B27A", INK, 2.2)
    bx, by, inwater = _oar(r, c, t, bar, st.get("water", "#3E9BE8"), k)
    px_, ty_ = BOAT_L * 0.93, _sheer(0.93) - 104.0                                              # the pennant on its pole
    r.limb((px_, _sheer(0.93) + 6), (px_, ty_), 6.0, "#E8B27A", INK, 2.2)
    r.dot(px_, ty_ - 4, 6.0, "#FFD21F")
    fl = st.get("flag", "#E2574C")
    w1, w2 = 7.0 * math.sin(t * 6.5), 7.0 * math.sin(t * 6.5 + 1.4)
    r.poly([(px_ - 4, ty_ + 2), (px_ - 78, ty_ + 15 + w1), (px_ - 4, ty_ + 30)], fl, INK, 2.4)
    r.poly([(px_ - 4, ty_ + 8), (px_ - 44, ty_ + 15 + w2 * 0.6), (px_ - 4, ty_ + 22)], mix(fl, "#FFFFFF", 0.35), None)
    lan = st.get("lantern", 0.0)
    if lan > 0.01:                                                                              # a lantern that hangs from the pole
        lx_, ly_ = px_ + 26.0, ty_ + 50.0 + 3.0 * math.sin(t * 2.0)
        _glow_at(c, *r.P(lx_, ly_), 150.0 * lan * k, "#FFE9A0", 0.85 * lan)
        r.line([(px_, ty_ + 12), (lx_, ly_ - 18)], INK, 2.0)
        r.rrect(lx_ - 11, ly_ - 18, lx_ + 11, ly_ + 18, 5, "#FFF3A8", INK, 2.6)
        r.rrect(lx_ - 13, ly_ - 22, lx_ + 13, ly_ - 15, 3, "#4A4A5E", INK, 2.0)
        r.rrect(lx_ - 13, ly_ + 15, lx_ + 13, ly_ + 22, 3, "#4A4A5E", INK, 2.0)
    wr = _lens(c, x, wl, k, t, st.get("water", "#3E9BE8"))
    for j in range(2):                                                                          # rings that spread from the bow and the stern
        ph = (t * 0.45 + j * 0.5) % 1.0
        for sx_ in (-1, 1):
            wr.ell(sx_ * BOAT_L * 0.98, 8.0, 34.0 + 90.0 * ph, 5.0 + 12.0 * ph, None, "#EAF7FF", 2.4 * (1.0 - ph) + 0.4)
    if bar and inwater:                                                                         # the blade stirs the water
        wx, wy = r.P(bx, by)
        s = (t / bar) % 1.0
        for j in range(2):
            ph = (s * 2.0 + j * 0.5) % 1.0
            c.ellipse(wx, wy + 4 * k, (16 + 34 * ph) * k, (4 + 8 * ph) * k, outline="#EAF7FF", width=2.4 * (1.0 - ph) + 0.4)
    return r


def _glow_at(c, x, y, r, color, alpha):
    """A soft round glow at the world point (x, y) (radius r in world units)."""
    VB.glow(c.c, c.X(x), c.Y(y), r * c.z, color, alpha)


# ---------------------------------------------------------------- the living water behind everything
@prop
def lake_water(c, x, y, k, t, st):
    """Glints that slide along the water (toward the stern: the boat sails forward). Put it at y = 420, behind everything.
    st: mood (day / dawn / dusk / night), speed (1 = normal; 0 = the water stands still), face (1 = the boat sails to the right)."""
    mood = st.get("mood", "day")
    dirn = -st.get("face", 1)
    sp = st.get("speed", 1.0)
    glint = mix(LAKE_MOODS[mood]["water"][1], "#FFFFFF", 0.5)
    for i in range(36):
        u = ((i * 0.61803) % 1.0) ** 1.4
        yy = LAKE_Y + 14 + u * 292
        ln = 22 + 82 * u
        v = (12 + 54 * u) * (0.8 + 0.4 * ((i * 7) % 5) / 4.0) * sp
        xx = ((i * 211.0 + dirn * t * v) % 1500.0) - 110.0
        wob = math.sin(t * 2.0 + i)
        col = mix(_water_col(mood, yy), glint if mood != "night" else "#9FB4F0", 0.55 + 0.2 * wob)
        c.line([(xx - ln / 2, yy), (xx - ln * 0.1, yy - 1.6 - wob), (xx + ln / 2, yy + 0.8)], col, 2.2 + 1.8 * u)
    sx = {"day": 1050, "dawn": 330, "dusk": 700, "night": 1060}[mood]                           # the path of the sun / moon twinkles
    for j in range(14):
        yy = LAKE_Y + 12 + j * 21
        wd = (10 + j * 6.2) * (0.7 + 0.3 * math.sin(t * 2.6 + j * 1.7)) * (1.0 if mood != "day" else 0.55)
        c.ellipse(sx + 7 * math.sin(t * 1.4 + j), yy, wd, 2.2 + j * 0.14, fill=mix(_water_col(mood, yy), LAKE_MOODS[mood]["glow"], 0.55 - j * 0.02))
    return None


# ---------------------------------------------------------------- the friends of the lake: a duck, a frog on a lily pad, a fish, a little bird
def _open_at(wins, t, pad=0.0):
    """0..1: how far a beak (or a mouth) is open at time t, for the windows (start, end) in `wins` (a smooth open-and-shut in every window)."""
    o = 0.0
    for a, b in wins or ():
        if a - pad <= t <= b:
            o = max(o, math.sin(math.pi * clamp((t - a) / max(0.05, b - a))) ** 0.7)
    return o


def _hop_at(times, t, dur=0.7):
    """0..1 (the height of a hop as a fraction of its peak) for hops that start at the given times."""
    for t0 in times or ():
        if t0 <= t <= t0 + dur:
            return math.sin(math.pi * (t - t0) / dur)
    return 0.0


def _surface(c, x, y, k, t, tint, half=80.0, depth=20.0, ring=True, alphas=(0.28, 0.26)):
    """A bit of see-through water over the lower part of something that swims (and a foam line, and a ring that spreads)."""
    w = Rig(c, x, y, k)
    n = 24
    wave = lambda px: 2.2 * math.sin(px / 20.0 + t * 2.6)
    for f, a in zip((1.0, 0.8), alphas):
        top = [(half * f * (2.0 * i / n - 1.0), wave(half * f * (2.0 * i / n - 1.0))) for i in range(n + 1)]
        bot = [(half * f * math.cos(math.pi * j / 12), depth * f * math.sin(math.pi * j / 12)) for j in range(13)]
        _tint(c, [w.P(*p) for p in top + bot], tint, a)
    w.line([(half * 0.95 * (2.0 * i / n - 1.0), wave(half * 0.95 * (2.0 * i / n - 1.0))) for i in range(n + 1)], "#EAF7FF", 2.6)
    if ring:
        ph = (t * 0.6) % 1.0
        w.ell(0, 3, half * (0.8 + 0.5 * ph), 6 + 8 * ph, None, "#EAF7FF", 2.2 * (1.0 - ph) + 0.4)


@prop
def duck(c, x, y, k, t, st):
    """A yellow duck swimming: (x, y) = the water line in the middle of it.
    st: face (1 = looks to the right), talk = [(start, end), ...] seconds in which it quacks (the bill opens), water = colour of the water, dx = it swims this far sideways,
    sleep = 1: the eyes are shut."""
    face = st.get("face", 1)
    x += st.get("dx", 0.0) * k
    seed = st.get("seed", 0.0)
    r = Rig(c, x, y + 2.4 * math.sin(t * 2.4 + seed) * k, k, face=face, lean=2.0 * math.sin(t * 1.7 + seed))
    o = _open_at(st.get("talk"), t)
    yel, yel2, org = "#FFD93B", "#FFC21F", "#FF9F1C"
    r.poly([(-52, -42), (-90, -70), (-76, -30)], yel2, INK, 2.8)                                   # tail
    r.ell(34, -52, 20, 30, yel, INK, 2.8, ang=-18)                                                 # neck
    r.ell(0, -28, 62, 35, yel, INK, 3.0)                                                           # body
    r.ell(-6, -32, 38, 22, yel2, INK, 2.4, ang=-8)                                                 # wing
    for dx in (-24, -8, 8):
        r.arc(dx, -30, 16, 9, 20, 150, darker(yel2, 0.25), 2.0)
    r.ell(46, -74, 29, 28, yel, INK, 3.0)                                                          # head
    for dx, dy in ((38, -102), (47, -104), (55, -100)):
        r.line([(dx - 2, dy + 8), (dx + 1, dy - 5)], INK, 2.4)
    r.ell(44, -66, 8, 5, "#FF9DB0", None)
    if st.get("sleep"):
        r.arc(57, -80, 7.5, 4.5, 15, 165, INK, 2.8)
    else:
        r.ell(56, -80, 7.0, 7.6, "#FFFFFF", INK, 1.8)
        r.dot(58.2, -80, 4.2, INK)
        r.dot(59.6, -82, 1.5, "#FFFFFF")
    a = math.radians(22.0 * o)                                                                     # the lower bill drops open around (68, -68)
    cs, sn = math.cos(a), math.sin(a)
    low = [(70 + (px - 70) * cs - (py + 67) * sn, -67 + (px - 70) * sn + (py + 67) * cs) for px, py in ((70, -66), (99, -66), (96, -59), (71, -59))]
    if o > 0.08:
        r.poly([(70, -68), (101, -72), low[1], low[0]], "#8A2B2B", INK, 2.0)
        r.ell(80, -68 + 7.0 * o, 7 + 3 * o, 3 + 3 * o, "#FF8FA3", None)
    r.poly(low, "#F28A0F", INK, 2.4)
    r.poly([(66, -81), (101, -76), (103, -71), (70, -67)], org, INK, 2.4)
    r.dot(86, -76.5, 1.4, darker(org, 0.4))
    _surface(c, x, y, k, t, st.get("water", "#3E9BE8"), half=84, depth=26)
    return r


@prop
def frog_pad(c, x, y, k, t, st):
    """A big lily pad with a frog on it: (x, y) = the middle of the pad on the water.
    st: croak = [(start, end), ...] seconds in which the frog croaks (its throat swells), hops = [t, ...] times of hops (up and down), face (1 = looks to the right), water, sleep = 1: the eyes are shut."""
    face = st.get("face", 1)
    o = _open_at(st.get("croak"), t)
    hop = _hop_at(st.get("hops"), t)
    r = Rig(c, x, y, k, face=face)
    green, belly = "#59C84A", "#E6F8B0"
    _tint(c, [r.P(112 * math.cos(math.pi * j / 18), 8 + 20 * math.sin(math.pi * j / 18)) for j in range(37)], "#14305A", 0.22)
    r.ell(0, 3, 104, 28, darker("#3FAE49", 0.28), INK, 2.6)                                        # the pad
    r.ell(0, 0, 104, 28, "#4CC055", INK, 2.8)
    r.ell(-30, -6, 40, 9, mix("#4CC055", "#FFFFFF", 0.28), None)
    for a in (20, 70, 120, 160, 200, 250, 300, 340):
        r.line([(0, 0), (86 * math.cos(math.radians(a)), 22 * math.sin(math.radians(a)))], darker("#4CC055", 0.2), 2.0)
    r.poly([(0, 0), (112, -12), (112, 14)], mix(st.get("water", "#3E9BE8"), "#FFFFFF", 0.1), None)             # the notch
    fr = Rig(c, x, y - 70.0 * hop * k, k, face=face)
    sq = 1.0 + 0.0 * hop
    for sx in (-1, 1):                                                                             # the folded back legs and their feet
        fr.ell(sx * 54, -24, 28, 17, green, INK, 2.8, ang=sx * -25)
        fr.ell(sx * 78, -8, 19, 8, green, INK, 2.4)
    fr.ell(0, -42, 51, 40, green, INK, 3.0)                                                        # the body (and the head)
    fr.ell(0, -32, 33, 27, belly, None)
    for sx in (-1, 1):                                                                             # the front legs
        fr.ell(sx * 25, -10, 11, 17, green, INK, 2.6)
        fr.ell(sx * 25, -1, 14, 6, green, INK, 2.2)
    for sx in (-1, 1):                                                                             # the bulging eyes
        fr.ell(sx * 27, -80, 18, 18, green, INK, 3.0)
        if st.get("sleep"):
            fr.arc(sx * 27, -82, 11, 6, 15, 165, INK, 3.0)
        else:
            fr.ell(sx * 27, -81, 13, 13, "#FFFFFF", INK, 2.0)
            fr.dot(sx * 27 + 3.2 * face * face, -80, 6.2, INK)
            fr.dot(sx * 27 + 5, -83, 2.0, "#FFFFFF")
        fr.ell(sx * 36, -56, 9, 6, "#FF9DB0", None)
    fr.dot(-8, -68, 2.0, darker(green, 0.4))
    fr.dot(8, -68, 2.0, darker(green, 0.4))
    if o > 0.06:                                                                                   # croak: the mouth opens, the throat swells
        fr.ell(0, -36, 14 + 17 * o, 6 + 17 * o, "#FFB0C0", INK, 2.6)
        fr.ell(0, -52, 30, 4 + 11 * o, "#8A2B2B", INK, 2.4)
    else:
        fr.arc(0, -56, 30, 12, 12, 168, INK, 3.0)
    return r


@prop
def fish(c, x, y, k, t, st):
    """A friendly orange fish. (x, y) = the water surface where it lives; between its jumps it swims under the surface.
    st: jumps = [(start, seconds, dx, height), ...] (it leaps out of the water at (x - dx / 2) and dives back in at (x + dx / 2): give the jumps
    alternate signs of dx and it swims on from where it dived in), face, water, dy = how deep it swims, sleep = 1: the eye is shut."""
    seed = st.get("seed", 0.0)
    jumps = sorted(st.get("jumps") or ())
    air = None
    for (t0, dur, dx, h) in jumps:
        if t0 <= t <= t0 + dur:
            u = (t - t0) / dur
            air = (x + dx * (u - 0.5), y - 4.0 * h * u * (1.0 - u), math.degrees(math.atan2(-4.0 * h * (1.0 - 2.0 * u), abs(dx))), 1 if dx >= 0 else -1)
            break
    if air is None:
        prev = nxt = None
        for jp in jumps:
            if jp[0] + jp[1] <= t:
                prev = jp
            elif jp[0] > t and nxt is None:
                nxt = jp
        sx = x + prev[2] / 2.0 if prev else (x - nxt[2] / 2.0 if nxt else x)
        ex = x - nxt[2] / 2.0 if nxt else sx
        ta = prev[0] + prev[1] if prev else t - 1.0
        tb = nxt[0] if nxt else t + 1.0
        u = clamp((t - ta) / max(0.05, tb - ta))
        px = sx + (ex - sx) * u * u * (3.0 - 2.0 * u)
        edge = min(t - ta if prev else 9.0, tb - t if nxt else 9.0)
        depth = st.get("dy", 36.0) * clamp(edge / 0.3)
        py = y + depth + 4.0 * math.sin(t * 2.2 + seed) * clamp(edge / 0.3)
        ang = 4.0 * math.sin(t * 3.1 + seed)
        face = (1 if ex > sx else -1) if abs(ex - sx) > 4 else st.get("face", 1)
        under = True
    else:
        px, py, ang, face = air
        under = False
    r = Rig(c, px, py, k, face=face, lean=ang * face)
    wag = 9.0 * math.sin(t * 9.0 + seed)
    orange, dark = "#FF9A3D", "#FF7A1F"
    r.poly([(-48, 0), (-92, -30 + wag), (-82, 0 + wag * 0.4), (-92, 30 + wag)], dark, INK, 2.8)         # tail
    r.poly([(-14, -30), (10, -56), (36, -30)], dark, INK, 2.8)                                     # fins
    r.poly([(-4, 26), (16, 52), (30, 24)], dark, INK, 2.6)
    r.ell(0, 0, 58, 36, orange, INK, 3.0)                                                          # body
    r.ell(6, 13, 44, 18, "#FFD08A", None)
    for dx in (-18, -2):
        r.arc(dx, 0, 16, 32, -62, 62, "#FFFFFF", 4.0)
    r.ell(2, 6, 20, 9, dark, INK, 2.2, ang=28)
    if st.get("sleep"):
        r.arc(35, -9, 8, 5, 15, 165, INK, 2.8)
    else:
        r.ell(34, -9, 10, 10.5, "#FFFFFF", INK, 2.0)
        r.dot(36.5, -9, 5.4, INK)
        r.dot(38, -11.5, 1.8, "#FFFFFF")
    r.ell(40, 8, 8, 5, "#FF9DB0", None)
    r.arc(48, 5, 9, 7, 20, 150, INK, 2.8)
    if under:
        _surface(c, px, y, k, t, st.get("water", "#3E9BE8"), half=140, depth=96, ring=False, alphas=(0.2, 0.18))
    return r


@prop
def songbird(c, x, y, k, t, st):
    """A little blue bird that sits on a branch: (x, y) = its feet. st: talk = [(start, end), ...] seconds in which it sings, face (1 = looks to the right),
    branch = 1: a branch that comes from the right (a tree), 0: none, sleep = 1: the eyes are shut."""
    face = st.get("face", 1)
    o = _open_at(st.get("talk"), t)
    r = Rig(c, x, y, k, face=face)
    if st.get("branch", 1.0) > 0.5:
        r.limb((150, 20), (-70, 2), 11, "#8A5A30", INK, 2.6)
        r.limb((40, 8), (96, -26), 6, "#8A5A30", INK, 2.2)
        for (lx, ly, an) in ((-52, -8, -30), (-34, 12, 20), (92, -34, -40), (108, -18, 10)):
            r.ell(lx, ly, 17, 7.5, "#4CC055", INK, 2.0, ang=an)
    b = Rig(c, x, y - 3.0 * o * k, k, face=face)
    blue, dark = "#4A8FE7", "#2E6BC4"
    for dy, an in ((-30, 28), (-20, 18)):
        b.poly([(-26, dy), (-74, dy + 14 - an * 0.3), (-70, dy - 2 - an * 0.3), (-26, dy - 14)], dark if dy == -30 else blue, INK, 2.4)
    b.limb((-2, -8), (-2, 0), 4.0, "#FF9F1C", None)
    b.limb((12, -8), (12, 0), 4.0, "#FF9F1C", None)
    b.ell(0, -40, 38, 36, blue, INK, 3.0)
    b.ell(8, -30, 25, 24, "#CFE6FF", None)
    b.ell(-8, -42, 25, 17, dark, INK, 2.4, ang=-18 - 14 * o)
    b.arc(-6, -42, 16, 8, 190, 330, "#8FB8F5", 2.0)
    b.ell(22, -74, 25, 24, blue, INK, 3.0)
    for dx, dy in ((14, -98), (23, -101), (31, -97)):
        b.poly([(dx - 4, dy + 6), (dx, dy - 10), (dx + 4, dy + 6)], blue, INK, 2.0)
    a = math.radians(24.0 * o)
    cs, sn = math.cos(a), math.sin(a)
    low = [(44 + (px - 44) * cs - (py + 67) * sn, -67 + (px - 44) * sn + (py + 67) * cs) for px, py in ((44, -67), (62, -65), (44, -62))]
    if o > 0.08:
        b.poly([(44, -71), (63, -68), low[1], low[0]], "#8A2B2B", INK, 1.8)
    b.poly(low, "#F28A0F", INK, 2.0)
    b.poly([(44, -78), (64, -70), (44, -67)], "#FF9F1C", INK, 2.2)
    if st.get("sleep"):
        b.arc(33, -78, 7, 4, 15, 165, INK, 2.6)
    else:
        b.ell(32, -78, 6.4, 7.0, "#FFFFFF", INK, 1.8)
        b.dot(34, -78, 3.8, INK)
        b.dot(35.2, -79.8, 1.3, "#FFFFFF")
    b.ell(30, -66, 7, 4.6, "#FF9DB0", None)
    return r


# ---------------------------------------------------------------- effects on the water
@fx
def ripples(c, s, x, y, dt, r=80.0, n=3, **_):
    """Rings that spread over the water from (x, y) and fade away."""
    if dt > 1.8:
        return
    for i in range(n):
        u = (dt - i * 0.22) / 1.25
        if u <= 0.0 or u >= 1.0:
            continue
        rr = r * (0.25 + 0.75 * u)
        c.ellipse(x, y, rr, rr * 0.2, outline="#EAF7FF", width=3.2 * (1.0 - u) + 0.6)


@fx
def droplets(c, s, x, y, dt, n=12, power=1.0, **_):
    """Drops of water that fly up out of (x, y) in a fan and fall back."""
    if dt > 1.1:
        return
    for i in range(n):
        a = math.radians(228.0 + 84.0 * ((i * 0.618) % 1.0))
        sp = (230.0 + 130.0 * ((i * 37) % 10) / 10.0) * power
        px = x + math.cos(a) * sp * 0.55 * dt
        py = y + math.sin(a) * sp * dt + 0.5 * 700.0 * dt * dt
        rr = (6.0 - 2.5 * dt) * (0.7 + 0.3 * ((i * 13) % 5) / 4.0)
        c.ellipse(px, py, rr * 0.8, rr * 1.15, fill="#BFE6FF", outline="#3E8EDE", width=1.6)
        c.ellipse(px - rr * 0.25, py - rr * 0.3, rr * 0.22, rr * 0.3, fill="#FFFFFF")


@fx
def bubbles(c, s, x, y, dt, n=7, **_):
    """Bubbles that rise from (x, y), wobbling a little."""
    if dt > 2.4:
        return
    for i in range(n):
        ph = (dt - i * 0.2) / 1.3
        if ph <= 0.0 or ph >= 1.0:
            continue
        bx = x + math.sin(ph * 6.0 + i * 1.7) * 14.0 + (i - n / 2.0) * 8.0
        by = y - ph * 130.0
        rr = 5.0 + 6.0 * ((i * 7) % 5) / 4.0
        c.ellipse(bx, by, rr, rr, fill="#E6F6FF", outline="#8FD3FF", width=1.8)
        c.ellipse(bx - rr * 0.3, by - rr * 0.3, rr * 0.26, rr * 0.26, fill="#FFFFFF")
