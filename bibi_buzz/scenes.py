"""All scenes of episode 1. Every scene function takes (canvas, local_t, global_t)."""
import math
import random

from . import timeline as T
from .draw import (W, H, bibi, pip, mo, lila, flower, park, star, heart,
                   word_pop_text, big_label, lyric_line, pop, smooth, lerp, clamp, darker)

GROUND = 625
SHADOW = "#5DB04B"


def fly(a, b, t, t0, t1):
    return lerp(a, b, smooth((t - t0) / (t1 - t0)))


def shadow(c, x, w=70, y=GROUND + 4):
    c.ellipse(x, y, w, 12, fill=SHADOW)


# ------------------------------------------------------------------- 1. logo
def logo(c, t, g):
    park(c, g)
    span = T.S_LOGO[1]

    def pos(tt):
        return lerp(-160, W + 160, tt / span), 205 + math.sin(tt * 2.2) * 45

    for i in range(1, 9):
        tt = t - i * 0.12
        if tt > 0:
            px, py = pos(tt)
            c.ellipse(px, py + 30, 5 - 0.4 * i, 5 - 0.4 * i, fill="#FFFFFF")
    bx, by = pos(t)
    bibi(c, bx, by, 0.8, g, "open")
    for i, (fn, x, y) in enumerate(((pip, 300, 575), (mo, 520, 560), (lila, 780, 520), (bibi, 1000, 540))):
        p = min(pop(t, 2.6 + i * 0.3, 0.6), 1.0)
        fn(c, x, y + (1 - p) * 240, 0.62 if fn is not bibi else 0.55, g, "smile")
    word_pop_text(c, ["Bibi", "Buzz", "TV"], ["#FFB400", "#FF5C8A", "#3E8EDE"], W / 2, 350, 150, t, 0.4, 0.3)
    p = pop(t, 1.8)
    if p > 0.02:
        c.text(W / 2, 470, "Songs & Fun for Kids", 52 * min(p, 1.1), "#2B3A55", stroke=8, stroke_fill="#FFFFFF")


# ------------------------------------------------------------- 2. intro song
def intro(c, t, g):
    park(c, g)
    cols = ["#E8383D", "#FFC81E", "#3E7BEA", "#B058E8", "#FF8A1F"]
    for i, x in enumerate((700, 830, 960, 1090, 1200)):
        flower(c, x, GROUND, 120, cols[i], pop(t, 2.0 + 0.4 * i, 0.6), g, i)
    bx = fly(-200, 400, t, 0, 2.2)
    idx = int((t - T.INTRO_LINE_START) // T.INTRO_LINE_DUR)
    active = t >= T.INTRO_LINE_START and 0 <= idx < len(T.INTRO_LINES)
    shadow(c, bx)
    bibi(c, bx, 430, 1.35, g, "open" if active else "smile", look=(8, 0))
    if active:
        lyric_line(c, T.INTRO_LINES[idx], (t - T.INTRO_LINE_START - idx * T.INTRO_LINE_DUR) / T.INTRO_LINE_DUR)


# ---------------------------------------------------------- 3. colour lessons
def color_seg(c, t, g, i):
    word, col, st, dur, fx, l1, l2, note = T.COLOR_SEGS[i]
    park(c, g)
    bx = fly(220, fx - 330, t, 0, 1.6)
    talk = any(s <= t < s + d for s, d in (T.SEG_L1, T.SEG_L2))
    mood = "open" if talk else ("wow" if T.SEG_LABEL_T <= t < T.SEG_LABEL_T + 1.2 else "smile")
    grow = pop(t, T.SEG_FLOWER_POP, 0.9)
    if t >= T.SEG_HOP:
        grow *= 1 - smooth((t - T.SEG_HOP) / 0.8)
    flower(c, fx, GROUND, 360, col, grow, g, i)
    shadow(c, bx)
    hop_p = pop(t, T.SEG_HOP + 0.6, 0.5) if t >= T.SEG_HOP + 0.6 else 0
    bibi(c, bx, 400, 1.3, g, mood, look=(10, 0), flower_color=col if hop_p else None, flower_pop=hop_p)
    big_label(c, word, 470, 150, 170, col, pop(t, T.SEG_LABEL_T, 0.6))
    for (s, d), txt in ((T.SEG_L1, l1), (T.SEG_L2, l2)):
        if s <= t < s + d:
            lyric_line(c, txt, (t - s) / d)


# ---------------------------------------------------------------- 4. mixing
def mixing(c, t, g):
    park(c, g)
    lyr = next(((s, d, txt) for s, d, txt in T.MIX_LINES if s <= t < s + d), None)
    talk = lyr is not None
    shadow(c, 230)
    bibi(c, 230, 420, 1.25, g, "open" if talk else "smile", look=(8, -2))
    px = lerp(1500, 1010, smooth(t / 3.0))
    if t < 3.0:
        hop = abs(math.sin(t * 5)) * 22
    elif T.MIX_FLOWER_T <= t < T.MIX_FLOWER_T + 7:
        hop = abs(math.sin((t - T.MIX_FLOWER_T) * 4)) * 50
    else:
        hop = 0
    pmood = "wow" if T.MIX_ORANGE_T <= t < T.MIX_ORANGE_T + 3.5 else ("open" if talk else "smile")
    shadow(c, px, 66)
    pip(c, px, 535 - hop, 1.15, g, pmood)
    pb = min(pop(t, T.MIX_BLOBS_T, 0.5), 1.1)
    mp = smooth((t - T.MIX_MERGE_T) / 2.2)
    if t < T.MIX_ORANGE_T:
        for x0, color, label in ((360, "#E8383D", "RED"), (920, "#FFC81E", "YELLOW")):
            x = lerp(x0, 640, mp)
            r = 76 * pb
            if r > 2:
                c.ellipse(x, 270, r, r, fill=color, outline=darker(color), width=5)
                if mp < 0.5:
                    big_label(c, label, x, 270 - r - 48, 64, color, pb)
    else:
        po = min(pop(t, T.MIX_ORANGE_T, 0.7), 1.1)
        r = 118 * po * (1 - smooth((t - T.MIX_FLOWER_T) / 1.0))
        if r > 2:
            c.ellipse(640, 270, r, r, fill=T.ORANGE, outline=darker(T.ORANGE), width=6)
        if t < T.MIX_ORANGE_T + 4:
            for k in range(8):
                a = math.radians(k * 45 + t * 60)
                d = 148 + 10 * math.sin(t * 8 + k)
                star(c, 640 + math.cos(a) * d, 270 + math.sin(a) * d * 0.9, 16, "#FFF27A", k * 20 + t * 90)
    word_pop_text(c, ["RED", "+", "YELLOW", "=", "ORANGE"],
                  ["#E8383D", "#2B3A55", "#E6A800", "#2B3A55", T.ORANGE], 640, 78, 62, t, T.MIX_TEXT_T, 0.3, stroke=10)
    flower(c, 640, GROUND, 380, T.ORANGE, pop(t, T.MIX_FLOWER_T, 0.9), g, 3)
    if lyr:
        s, d, txt = lyr
        lyric_line(c, txt, (t - s) / d)


# --------------------------------------------------------------- 5. counting
def counting(c, t, g):
    park(c, g)
    slide = smooth(t / 2.5)
    n = int(clamp((t - T.COUNT_T0) // T.COUNT_STEP, 0, 4)) if t >= T.COUNT_T0 else -1
    since = (t - T.COUNT_T0) - n * T.COUNT_STEP if n >= 0 else 99
    cheer = t >= 22.0
    speaker = n % 4 if n >= 0 else -1

    def mood(i):
        return "open" if (cheer or (speaker == i and since < 1.4)) else "smile"

    shadow(c, lerp(-200, 330, slide))
    mo(c, lerp(-200, 330, slide), 500, 1.0, g, mood(0))
    shadow(c, 590, 66)
    pip(c, 590, 505, 1.05, g, mood(1))
    bibi(c, 830, 340, 0.95, g, mood(2))
    lila(c, lerp(1500, 1050, slide), 330, 0.95, g, mood(3))
    cols = T.COUNT_COLORS
    for i, x in enumerate((130, 460, 740, 960, 1190)):
        flower(c, x, 640, 190, cols[i], pop(t, T.COUNT_T0 + T.COUNT_STEP * i, 0.6), g, i)
    if cheer:
        big_label(c, "5 FLOWERS!", 640, 110, 120, "#FF4F86", pop(t, 22.0, 0.6))
    elif n >= 0:
        p = pop(t, T.COUNT_T0 + T.COUNT_STEP * n, 0.5)
        big_label(c, str(n + 1), 640, 100, 170, cols[n], p)
        big_label(c, T.COUNT_WORDS[n], 640, 210, 56, "#2B3A55", p)


# --------------------------------------------------------- 6. bouquet & rainbow
_rng = random.Random(3)
CONFETTI = [(_rng.uniform(0, W), _rng.uniform(80, 260), _rng.random(), _rng.uniform(5, 10),
             _rng.choice(["#E8383D", "#FFC81E", "#3E7BEA", "#4FBF5A", "#B058E8", "#FF8A1F", "#FF5C8A"]))
            for _ in range(70)]


def bouquet(c, t, g):
    park(c, g)
    p = smooth((t - T.RAINBOW_T0) / (T.RAINBOW_T1 - T.RAINBOW_T0))
    rainbow = ["#E8383D", "#FF8A1F", "#FFD21E", "#4FBF5A", "#3E8EDE", "#5B5BD6", "#B058E8"]
    if p > 0.005:
        for i, col in enumerate(rainbow):
            r = 430 - i * 26
            c.arc(640, 600, r, r, 180, 180 + 180 * p, col, 27)
    shadow(c, 130, 66)
    pip(c, 130, 535, 1.0, g, "open")
    shadow(c, 1150, 80)
    mo(c, 1150, 515, 1.0, g, "open")
    bibi(c, 235, 300, 1.0, g, "open")
    lila(c, 1045, 300, 1.0, g, "open")
    cols = ["#E8383D", "#3E7BEA", "#FFC81E", T.ORANGE, "#B058E8"]
    spec = [(-210, 250), (-105, 305), (0, 340), (105, 305), (210, 250)]
    for i, ((dx, h), col) in enumerate(zip(spec, cols)):
        flower(c, 640, 625, h, col, pop(t, T.BOUQ_T0 + 0.3 * i, 0.7), g, i, dx=dx)
    if t > T.BOUQ_T0 + 1.5:
        for s in (-1, 1):
            c.poly([(640, 600), (640 + s * 56, 568), (640 + s * 60, 634)], fill="#FF5C8A", outline="#B02A5A", width=3)
        c.ellipse(640, 601, 14, 14, fill="#FF8FB4", outline="#B02A5A", width=3)
    if t > 5:
        for i in range(8):
            hy = 560 - ((t * 55 + i * 97) % 420)
            heart(c, 180 + i * 135 + math.sin(t * 2 + i) * 18, hy, 12 + (i % 3) * 4,
                  "#FF5C8A" if i % 2 == 0 else "#FF9BD2")
    if t > T.CONFETTI_T:
        for x0, y0, ph, sz, col in CONFETTI:
            y = ((t - T.CONFETTI_T) * (90 + ph * 90) + ph * H) % (H + 40) - 20
            x = x0 + math.sin(t * 2 + ph * 6) * 25
            c.ellipse(x, y, sz, sz * 0.7, fill=col)
    big_label(c, "GREAT JOB!", 640, 72, 92, "#FF4F86", pop(t, T.PRAISE_T, 0.6))


# ------------------------------------------------------------------- 7. bye
def bye(c, t, g):
    park(c, g)

    def b(ph):
        return abs(math.sin(g * 5 + ph)) * 14

    shadow(c, 250, 80)
    mo(c, 250, 520 - b(0), 1.0, g, "open")
    shadow(c, 520, 66)
    pip(c, 520, 530 - b(1), 1.0, g, "open")
    bibi(c, 800, 440 - b(2) * 0.5, 1.3, g, "open")
    lila(c, 1050, 380, 1.0, g, "open")
    big_label(c, "BYE BYE!", 640, 130, 150, "#FF5C8A", pop(t, T.BYE_T, 0.6))
    big_label(c, "See you soon!", 640, 255, 76, "#3E8EDE", pop(t, T.SOON_T, 0.6))
    p = min(pop(t, T.SUB_T, 0.5), 1.1)
    if p > 0.02:
        hw, hh = 215 * p, 36 * p
        c.rrect(640 - hw, 665 - hh, 640 + hw, 665 + hh, hh, fill="#E8383D", outline="#FFFFFF", width=5)
        c.text(640, 666, "SUBSCRIBE", 44 * p, "#FFFFFF")
        bx = 640 + hw + 55 * p
        c.ellipse(bx, 662, 24 * p, 26 * p, fill="#FFC81E", outline="#B07A00", width=3)
        c.rect(bx - 25 * p, 662, bx + 25 * p, 662 + 22 * p, "#FFC81E")
        c.ellipse(bx, 690, 8 * p, 8 * p, fill="#B07A00")


# ----------------------------------------------------------------- dispatcher
def render(c, t):
    if t < T.S_LOGO[1]:
        logo(c, t, t)
    elif t < T.S_INTRO[1]:
        intro(c, t - T.S_INTRO[0], t)
    elif t < T.S_COLORS[1]:
        idx = max(i for i, s in enumerate(T.COLOR_SEGS) if s[2] <= t)
        color_seg(c, t - T.COLOR_SEGS[idx][2], t, idx)
    elif t < T.S_MIX[1]:
        mixing(c, t - T.S_MIX[0], t)
    elif t < T.S_COUNT[1]:
        counting(c, t - T.S_COUNT[0], t)
    elif t < T.S_BOUQUET[1]:
        bouquet(c, t - T.S_BOUQUET[0], t)
    else:
        bye(c, t - T.S_BYE[0], t)
