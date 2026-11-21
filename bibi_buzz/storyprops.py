"""Props (houses, furniture, banners...) and effects for the Bibi story videos.

A prop is drawn with prop(view, x, y, k, t, st): (x, y) is the middle of its base on the ground, k the size,
t the scene time in seconds and st a dict of its animated values (build, collapse, door, ...).
Effects are fx(view, screen, x, y, dt, **kw): dt is the time since the effect started.
"""
import math
import random

from PIL import Image, ImageDraw

from . import draw as D
from .draw import INK, clamp, lerp, darker, mix, ease_out_back
from .storyart import Rig, star_pts

PROPS, FX = {}, {}


def prop(fn):
    PROPS[fn.__name__] = fn
    return fn


def fx(fn):
    FX[fn.__name__] = fn
    return fn


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


# ================================================================================================ small helpers
def beam_poly(r, pts, fill, ow=2.6):
    r.poly(pts, fill, INK, ow)


def brick_wall(r, x0, x1, y_bottom, y_top, bw=34, bh=18, colors=("#D9534F", "#C8453F", "#E0645A"), build=1.0, seed=3):
    rng = random.Random(seed)
    rows = int(round((y_bottom - y_top) / bh))
    shown = rows * clamp(build)
    for row in range(rows):
        if row + 1 > shown + 0.0001 and row >= shown:
            break
        yb = y_bottom - row * bh
        off = (bw / 2) * (row % 2)
        x = x0 - off
        while x < x1:
            a, b = max(x, x0), min(x + bw, x1)
            if b - a > 2:
                r.rrect(a + 0.8, yb - bh + 0.8, b - 0.8, yb - 0.8, 2, rng.choice(colors), None)
            x += bw
    return rows


def smoke_puffs(c, x, y, t, k=1.0, n=5, color="#F4F4F8"):
    for i in range(n):
        ph = ((t * 0.45 + i / n) % 1.0)
        px = x + (math.sin(ph * 6 + i) * 14 + ph * 40) * k
        py = y - ph * 130 * k
        rr = (10 + ph * 26) * k
        c.ellipse(px, py, rr, rr * 0.9, fill=mix(color, "#B8C4D8", ph * 0.5), outline="#C9D3E6", width=1.5)


def door_arch(r, x, ytop, w, h, wood="#A8682F", openv=0.0, knob="#FFD21F"):
    hw = w / 2
    pts = [(-hw, 0)] + [(hw * math.cos(math.radians(a)), -(h - hw) - hw * math.sin(math.radians(a))) for a in range(0, 181, 15)][::-1] + [(hw, 0)]
    pts = [(x + px, ytop + py) for px, py in pts]
    r.poly([(px, py) for px, py in pts], "#3A2316", INK, 2.6)
    if openv < 0.98:
        lw = hw * (1 - 0.88 * openv)
        leaf = [(x - hw, ytop)] + [(x - hw + 2 * lw * (a / 180.0), ytop - (h - hw) - hw * math.sin(math.radians(a))) for a in range(0, 181, 15)][::-1] + [(x - hw + 2 * lw, ytop)]
        r.poly(leaf, wood, INK, 2.6)
        for i in (1, 2):
            fx_ = x - hw + 2 * lw * i / 3
            r.line([(fx_, ytop - 2), (fx_, ytop - h + hw + 8)], darker(wood, 0.25), 2)
        r.dot(x - hw + 2 * lw * 0.82, ytop - h * 0.42, 4.2, knob)


def window(r, x, y, w, h, frame="#FFFFFF", glass="#BFE6FF", flowers=True, shutter=None, round_=False):
    if shutter:
        for s in (-1, 1):
            r.rrect(x + s * (w / 2 + 3) - (0 if s > 0 else 14), y - h / 2, x + s * (w / 2 + 3) + (14 if s > 0 else 0), y + h / 2, 3, shutter, INK, 2)
    if round_:
        r.ell(x, y, w / 2 + 4, w / 2 + 4, frame, INK, 2.6)
        r.ell(x, y, w / 2 - 2, w / 2 - 2, glass, INK, 1.6)
        r.line([(x - w / 2 + 2, y), (x + w / 2 - 2, y)], INK, 2)
        r.line([(x, y - w / 2 + 2), (x, y + w / 2 - 2)], INK, 2)
        return
    r.rrect(x - w / 2 - 4, y - h / 2 - 4, x + w / 2 + 4, y + h / 2 + 4, 4, frame, INK, 2.6)
    r.rrect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, 2, glass, INK, 1.6)
    r.line([(x, y - h / 2), (x, y + h / 2)], INK, 2)
    r.line([(x - w / 2, y), (x + w / 2, y)], INK, 2)
    r.poly([(x - w / 2 + 5, y - h / 2 + 4), (x - w / 2 + 16, y - h / 2 + 4), (x - w / 2 + 6, y - h / 2 + 18)], "#E6F6FF", None)
    if flowers:
        r.rrect(x - w / 2 - 6, y + h / 2 + 2, x + w / 2 + 6, y + h / 2 + 14, 3, "#B5683A", INK, 2)
        for i, col in enumerate(("#FF6B8B", "#FFD23F", "#FF9A3D", "#FF6B8B")):
            fxp = x - w / 2 + 4 + i * (w - 8) / 3
            r.dot(fxp, y + h / 2 - 1, 5.2, col)
            r.dot(fxp, y + h / 2 - 1, 1.8, "#FFE98A")
            r.line([(fxp, y + h / 2 + 2), (fxp, y + h / 2 + 8)], "#3E9B3A", 2)


# ================================================================================================ cottage
@prop
def cottage(c, x, y, k, t, st):
    r = Rig(c, x, y, k)
    wall, roof = st.get("wall", "#FFF1D0"), st.get("roof", "#D9654F")
    openv = st.get("door", 0.0)
    r.ell(0, 0, 215, 20, mix("#79CE5D", "#2F6B2F", 0.35), None)
    r.rrect(-165, -176, 165, 0, 8, wall, INK, 3.2)
    for bx in (-165, -75, 75, 165):                                                   # timber frame
        r.line([(bx, -176), (bx, 0)], "#8B5A2B", 8)
    r.line([(-165, -176), (165, -176)], "#8B5A2B", 8)
    r.line([(-165, -88), (-100, -88)], "#8B5A2B", 6)
    r.line([(100, -88), (165, -88)], "#8B5A2B", 6)
    r.rrect(95, -312, 135, -222, 4, "#B5483F", INK, 3)                                  # chimney
    for yy in (-298, -280, -262, -244):
        r.line([(95, yy), (135, yy)], "#8E352E", 2)
    r.rrect(89, -322, 141, -308, 4, "#8E352E", INK, 3)
    r.poly([(-205, -170), (205, -170), (0, -306)], roof, INK, 3.4)                      # roof
    for i, yy in enumerate((-186, -204, -222, -240)):
        span = 205 * (1 - (-170 - yy) / 136.0)
        for sx in range(int(-span) + 20, int(span) - 10, 36):
            r.arc(sx + (18 if i % 2 else 0), yy + 14, 18, 16, 20, 160, darker(roof, 0.25), 2.4)
    door_arch(r, 0, 0, 78, 120, openv=openv)
    window(r, -118, -108, 52, 48, shutter="#3E8EDE")
    window(r, 118, -108, 52, 48, shutter="#3E8EDE")
    r.rrect(-60, -2, 60, 10, 4, "#B8B2A6", INK, 2.4)                                    # door step
    if st.get("smoke", True):
        smoke_puffs(c, x + 115 * k, y - 322 * k, t, k)
    return r


# ================================================================================================ the three houses
_PIECES = {}


def _rng_piece(seed):
    return random.Random(seed)


def _pieces_straw():
    rng = _rng_piece(11)
    out, n = [], 0
    cols = ["#F4CF63", "#EBBD48", "#F8DB7C", "#E6B33E"]
    for row in range(3):
        for col in range(7):
            cx, cy = -120 + col * 40, -25 - row * 50
            polys = [([(-19, -24), (19, -24), (19, 24), (-19, 24)], cols[(row + col) % 4], INK, 2.2)]
            lines = [([(dx, -22), (dx + rng.uniform(-1, 1), 22)], darker(cols[(row + col) % 4], 0.22), 1.8) for dx in (-11, -3, 5, 13)]
            lines.append(([(-19, 4), (19, 4)], "#B7742E", 3.0))
            out.append(dict(cx=cx, cy=cy, polys=polys, lines=lines, s=0.04 + 0.62 * (row * 7 + col) / 21, w=40, h=50))
    for sgn in (-1, 1):
        pts = [(0, 18), (sgn * 178, 18), (0, -94)]
        pts2 = [(sgn * 6, 14), (sgn * 120, 14)]
        lines = []
        for i in range(7):
            f = i / 6.0
            lines.append(([(sgn * (14 + 150 * f), 14 - 8 * f), (sgn * (4 + 6 * f), -86 + 80 * f * 0.2 - 4)], "#C99A2E", 2.2))
        out.append(dict(cx=sgn * 0, cy=-168, polys=[(pts, "#EFC95A", INK, 3.0)], lines=lines, s=0.72 if sgn < 0 else 0.8, w=180, h=110, roof=True))
    out.append(dict(cx=0, cy=-34, polys=[([(-27, 34), (27, 34), (27, -20), (0, -34), (-27, -20)], "#A8682F", INK, 2.6)],
                    lines=[([(-9, 34), (-9, -26)], "#7A4A1F", 2), ([(9, 34), (9, -26)], "#7A4A1F", 2)], s=0.9, w=54, h=68, door=True))
    out.append(dict(cx=88, cy=-96, polys=[([(-21, -21), (21, -21), (21, 21), (-21, 21)], "#BFE6FF", INK, 2.6)],
                    lines=[([(0, -21), (0, 21)], INK, 2), ([(-21, 0), (21, 0)], INK, 2)], s=0.95, w=42, h=42))
    for i, p in enumerate(out):
        p["rnd"] = random.Random(100 + i)
    return out


def _pieces_sticks():
    rng = _rng_piece(12)
    out = []
    browns = ["#9B6B3A", "#8B5A2B", "#A8794A", "#7A4A25", "#B08050"]
    for i in range(14):
        cx = -130 + i * 20
        h = 150 + rng.randint(-6, 10)
        col = browns[i % len(browns)]
        polys = [([(-9, -h / 2), (9, -h / 2 + 3), (8, h / 2), (-8, h / 2 - 2)], col, INK, 2.2)]
        lines = [([(-2, -h / 2 + 8), (-1, h / 2 - 8)], darker(col, 0.25), 1.6)]
        out.append(dict(cx=cx, cy=-h / 2, polys=polys, lines=lines, s=0.03 + 0.5 * i / 14, w=20, h=h))
    for j, yy in enumerate((-30, -80, -128)):
        out.append(dict(cx=0, cy=yy, polys=[([(-148, -6), (148, -4), (150, 6), (-148, 8)], "#6F4421", INK, 2.2)], lines=[], s=0.5 + 0.06 * j, w=300, h=14))
    for sgn in (-1, 1):
        pts = [(0, 18), (sgn * 178, 18), (0, -94)]
        lines = []
        for i in range(8):
            f = i / 7.0
            lines.append(([(sgn * (12 + 160 * f), 16 - 6 * f), (sgn * (4 + 30 * f), -88 + 70 * f)], "#6F4421", 5.0))
        for i in range(5):
            lines.append(([(sgn * (30 + 24 * i), 8 - 14 * i), (sgn * (4 + 8 * i + 130 - 20 * i), 6 - 14 * i)], "#8B5A2B", 4.0))
        out.append(dict(cx=0, cy=-168, polys=[(pts, "#B8885A", INK, 3.0)], lines=lines, s=0.72 if sgn < 0 else 0.8, w=180, h=110, roof=True))
    out.append(dict(cx=0, cy=-34, polys=[([(-27, 34), (27, 34), (27, -22), (-27, -22)], "#8F5E2E", INK, 2.6)],
                    lines=[([(-9, 34), (-9, -20)], "#5E3A19", 2), ([(9, 34), (9, -20)], "#5E3A19", 2)], s=0.9, w=54, h=68, door=True))
    out.append(dict(cx=-84, cy=-92, polys=[([(-20, -20), (20, -20), (20, 20), (-20, 20)], "#BFE6FF", INK, 2.6)],
                    lines=[([(0, -20), (0, 20)], INK, 2), ([(-20, 0), (20, 0)], INK, 2)], s=0.95, w=40, h=40))
    for i, p in enumerate(out):
        p["rnd"] = random.Random(200 + i)
    return out


def _draw_pieces(c, x, y, k, st, kind):
    if kind not in _PIECES:
        _PIECES[kind] = _pieces_straw() if kind == "straw" else _pieces_sticks()
    b, col, d = st.get("build", 1.0), st.get("collapse", 0.0), st.get("dir", 1)
    shake = st.get("shake", 0.0)
    for p in _PIECES[kind]:
        q = clamp((b - p["s"]) / 0.14)
        if q <= 0:
            continue
        rnd = p["rnd"]
        rx = d * (80 + rnd.random() * 380) + rnd.uniform(-30, 30)
        ry_rest = -rnd.uniform(8, 20)
        rang = rnd.uniform(-160, 160) * d
        if p.get("roof"):
            rang = rnd.uniform(-22, 22) + 8 * d
        elif p["h"] > 100:
            rang = rnd.choice((-1, 1)) * rnd.uniform(75, 105)
        arc = 60 + rnd.random() * 190
        cd = rnd.random() * 0.35
        ce = clamp((col - cd) / (1 - cd)) if col > 0 else 0.0
        px, py, ang = p["cx"], p["cy"], 0.0
        if q < 1:
            py -= (1 - ease_out_back(q)) * 150
        if shake:
            px += math.sin(shake * 60 + p["cx"]) * 2.4
        if ce > 0:
            e = ease(ce)
            px = lerp(px, p["cx"] + rx, e)
            py = lerp(py, ry_rest - (p["h"] * 0.12 if not p.get("roof") else 0), ce) - arc * 4 * ce * (1 - ce)
            ang = rang * e
            if p.get("roof"):
                py = lerp(p["cy"], -22, ce) - arc * 4 * ce * (1 - ce)
        r = Rig(c, x + px * k, y + py * k, k, 1, lean=ang)
        for pts, fill, line, ow in p["polys"]:
            r.poly(pts, fill, line, ow)
        for pts, colr, w in p["lines"]:
            r.line(pts, colr, w)


@prop
def house(c, x, y, k, t, st):
    kind = st.get("kind", "straw")
    b = st.get("build", 1.0)
    if kind in ("straw", "sticks"):
        if b > 0.05:
            c.ellipse(x, y + 4 * k, 190 * k, 16 * k, fill=mix("#79CE5D", "#2F6B2F", 0.32))
        _draw_pieces(c, x, y, k, st, kind)
        return
    # bricks
    r = Rig(c, x, y, k)
    sh = st.get("shake", 0.0)
    if sh:
        r.x0 += math.sin(sh * 70) * 2.2 * k
    if b > 0.05:
        c.ellipse(x, y + 4 * k, 200 * k, 16 * k, fill=mix("#79CE5D", "#2F6B2F", 0.32))
    wall_top = -170
    r.rrect(-150, wall_top, 150, 0, 4, "#B5483F", INK, 3.2) if b > 0.98 else None
    brick_wall(r, -150, 150, 0, wall_top, build=b * 1.12)
    if b > 0.98:
        r.rrect(-150, wall_top, 150, 0, 3, None, INK, 3.2)
    if b > 0.9:                                                                    # chimney
        r.rrect(84, -310, 124, -214, 3, "#B5483F", INK, 3)
        for yy in (-296, -278, -260, -242, -224):
            r.line([(84, yy), (124, yy)], "#8E352E", 2)
        r.rrect(78, -320, 130, -306, 3, "#8E352E", INK, 3)
        if b > 0.98 and st.get("smoke", True):
            smoke_puffs(c, x + 104 * k, y - 322 * k, t, k)
    if b > 0.86:
        slide = (1 - ease(clamp((b - 0.86) / 0.12))) * -180
        r.poly([(-190, -166 + slide), (190, -166 + slide), (0, -300 + slide)], "#5F7BB5", INK, 3.4)
        for i, yy in enumerate((-182, -200, -218, -236, -254)):
            span = 190 * (1 - (-166 - yy) / 134.0)
            for sx in range(int(-span) + 20, int(span) - 10, 32):
                r.arc(sx + (16 if i % 2 else 0), yy + 13 + slide, 16, 14, 20, 160, "#3E5A94", 2.2)
    if b > 0.9:
        door_arch(r, 0, 0, 84, 124, wood="#3F6FB5", openv=st.get("door", 0.0), knob="#FFD21F")
        window(r, -100, -104, 50, 46, shutter="#FFFFFF", flowers=True)
        window(r, 100, -104, 50, 46, shutter="#FFFFFF", flowers=True)
        r.rrect(-64, -2, 64, 10, 4, "#B8B2A6", INK, 2.4)
        r.rrect(-80, 8, 80, 20, 4, "#C9C3B6", INK, 2.4)


# ================================================================================================ furniture
@prop
def table(c, x, y, k, t, st):
    r = Rig(c, x, y, k)
    r.ell(0, 2, 230, 18, mix("#C98A52", "#5A3A1A", 0.5), None)
    for sx in (-190, 190):
        r.poly([(sx - 12, -92), (sx + 12, -92), (sx + 9, 0), (sx - 9, 0)], "#9B5C2E", INK, 2.6)
    for sx in (-150, 150):
        r.poly([(sx - 8, -128), (sx + 8, -128), (sx + 6, -96), (sx - 6, -96)], "#7B4723", INK, 2.2)
    r.poly([(-176, -150), (176, -150), (222, -112), (-222, -112)], "#D9A066", INK, 3)
    r.rrect(-222, -112, 222, -92, 6, "#B8733A", INK, 3)
    for i in range(0, 7, 2):                                                              # check cloth
        r.poly([(-176 + i * 50, -150), (-136 + i * 50, -150), (-142 + i * 55, -112), (-190 + i * 56, -112)], "#FF8FA3", None)
    sizes = (("big", -118, 50, st.get("bowl1", 1.0), "#FF6B8B"), ("mid", 0, 40, st.get("bowl2", 1.0), "#3E8EDE"), ("small", 108, 30, st.get("bowl3", 1.0), "#FFD21F"))
    for name, bx, rr, left, colr in sizes:
        by = -126
        r.ell(bx, by + 2, rr * 1.12, rr * 0.22, "#B07A44", None)
        pts = [(bx + rr * math.cos(math.radians(a)), by - 4 + rr * 0.62 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
        r.poly(pts, colr, INK, 2.6)
        r.ell(bx, by - 4, rr, rr * 0.25, darker(colr, 0.1), INK, 2.4)
        if left > 0.02:
            r.ell(bx, by - 5, rr * 0.86, rr * 0.19, "#FFE9A8", None)
            r.ell(bx - rr * 0.2, by - 6, rr * 0.25, rr * 0.05, "#FFF8DB", None)
        else:
            r.ell(bx, by - 5, rr * 0.86, rr * 0.19, "#D9C8A0", None)
        if name == "small" and st.get("spoon", False):
            r.line([(bx + rr * 0.4, by - 8), (bx + rr * 1.2, by - 40)], "#B0B0B8", 4)
    return r


@prop
def chair(c, x, y, k, t, st):
    size = {"big": 1.35, "mid": 1.0, "small": 0.7}[st.get("size", "mid")]
    col = {"big": "#8B4F26", "mid": "#B8733A", "small": "#D9954F"}[st.get("size", "mid")]
    cushion = {"big": "#3E8EDE", "mid": "#3DB54A", "small": "#FF6B8B"}[st.get("size", "mid")]
    br = clamp(st.get("broken", 0.0))
    r = Rig(c, x, y, k * size, 1, lean=br * 28)
    r.ell(0, 3, 74 + 20 * br, 8, mix("#C98A52", "#5A3A1A", 0.5), None)
    spread = 1 + br * 0.7
    for sx in (-52, 52):                                                                    # legs
        r.poly([(sx * spread - 7, -64 + br * 28), (sx * spread + 7, -64 + br * 28), (sx * spread * 1.15 + 5, 0), (sx * spread * 1.15 - 5, 0)], col, INK, 2.4)
    r.rrect(-66, -86 + br * 28, 66, -62 + br * 28, 6, col, INK, 2.8)                        # seat
    r.rrect(-60, -102 + br * 28, 60, -86 + br * 28, 6, cushion, INK, 2.6)
    back_x = 52 + br * 14
    for sx in (-back_x, back_x):
        r.poly([(sx - 6, -102 + br * 28), (sx + 6, -102 + br * 28), (sx + 5 + br * 14, -200 + br * 34), (sx - 5 + br * 14, -200 + br * 34)], col, INK, 2.4)
    for yy in (-130, -166):
        r.rrect(-back_x, yy - 8 + br * 30, back_x, yy + 8 + br * 30, 5, col, INK, 2.4)
    return r


@prop
def bed(c, x, y, k, t, st):
    size = {"big": 1.35, "mid": 1.0, "small": 0.72}[st.get("size", "mid")]
    quilt = st.get("quilt") or {"big": "#3E8EDE", "mid": "#3DB54A", "small": "#FF6B8B"}[st.get("size", "mid")]        # (quilt / wood / hair can be given as colours)
    wood = st.get("wood") or {"big": "#8B4F26", "mid": "#B8733A", "small": "#D9954F"}[st.get("size", "mid")]
    hair = st.get("hair") or "#FFC83D"
    r = Rig(c, x, y, k * size)
    r.ell(0, 3, 150, 12, mix("#C98A52", "#5A3A1A", 0.5), None)
    r.rrect(-136, -128, -112, 0, 6, wood, INK, 2.8)                                           # headboard
    r.rrect(122, -78, 142, 0, 6, wood, INK, 2.8)
    r.rrect(-122, -66, 134, -28, 8, "#FFFFFF", INK, 2.8)                                      # mattress
    r.rrect(-122, -50, 134, -8, 8, quilt, INK, 2.8)
    for i in range(5):
        r.line([(-96 + i * 50, -48), (-96 + i * 50, -10)], mix(quilt, "#FFFFFF", 0.4), 3)
    r.ell(-84, -78, 44, 18, "#FFFFFF", INK, 2.6)                                              # pillow
    if st.get("girl", 0.0) > 0.5:
        r.ell(-82, -92, 28, 26, "#FFDDBF", INK, 2.8)
        for i in range(7):
            r.ell(-102 + i * 6.5, -108 + abs(i - 3) * 2.4, 9, 9, hair, INK, 2)
        r.ell(-106, -86, 10, 22, hair, INK, 2)
        r.arc(-90, -92, 6, 4, 22, 158, INK, 2.6)
        r.arc(-72, -92, 6, 4, 22, 158, INK, 2.6)
        r.dot(-98, -82, 4.4, "#FF9DB0")
        r.dot(-66, -82, 4.4, "#FF9DB0")
        r.arc(-82, -82, 6, 4, 20, 160, INK, 2.4)
        r.rrect(-72, -64, 134, -8, 10, quilt, INK, 2.8)
        for i in range(5):
            r.line([(-50 + i * 44, -62), (-50 + i * 44, -10)], mix(quilt, "#FFFFFF", 0.4), 3)
    if st.get("flowers", 0.0) > 0.5:                                                          # a bed of flowers: blossoms all along the quilt and the foot of the bed
        for i, (fx, fy) in enumerate(((-48, -8), (-12, -30), (22, -12), (58, -32), (92, -10), (124, -40), (-130, -14), (138, -14), (-6, 3), (66, 4), (-90, 2))):
            col = ("#FF6B8B", "#FFFFFF", "#FFD23F", "#B58CFF")[i % 4]
            r.line([(fx, fy), (fx - 3, fy + 9)], "#3E9B3A", 2.6)
            for j in range(5):
                a = math.radians(j * 72 + 18)
                r.dot(fx + 6.5 * math.cos(a), fy - 1 + 6.5 * math.sin(a), 4.6, col)
            r.dot(fx, fy - 1, 3.4, "#FFE98A")
    return r


@prop
def wardrobe(c, x, y, k, t, st):
    """A tall wooden wardrobe; st["door"] goes from 0 (shut) to 1 (both doors wide open, dark inside)."""
    r = Rig(c, x, y, k)
    op = clamp(st.get("door", 0.0))
    wood, dark = "#B8733A", "#8B4F26"
    r.ell(0, 3, 106, 10, mix("#C98A52", "#5A3A1A", 0.5), None)
    r.rrect(-88, -270, 88, 0, 8, dark, INK, 3.2)                                             # body
    r.rrect(-102, -288, 102, -262, 7, wood, INK, 3)                                          # cornice
    r.rrect(-96, -8, 96, 8, 5, wood, INK, 2.8)                                               # plinth
    if op > 0.02:
        r.rrect(-74, -254, 74, -14, 4, "#3B2A1C", INK, 2.6)                                  # the dark inside
        r.line([(-74, -214), (74, -214)], "#6B5236", 5)                                      # clothes rail
        for i, col in enumerate(("#FF8FA3", "#6CB7FF", "#FFD23F")):
            r.rrect(-58 + i * 44, -212, -34 + i * 44, -150, 6, darker(col, 0.25), None)      # a few clothes in the dark
    wd = 74 * (1.0 - 0.84 * op)                                                              # each door narrows as it swings open
    for s in (-1, 1):
        xa, xb = s * 74, s * (74 - wd)
        lo, hi = min(xa, xb), max(xa, xb)
        r.rrect(lo, -254, hi, -14, 4, wood, INK, 2.8)
        if wd > 30:
            r.rrect(lo + 9, -238, hi - 9, -138, 5, mix(wood, "#FFFFFF", 0.16), INK, 2)       # panels
            r.rrect(lo + 9, -122, hi - 9, -32, 5, mix(wood, "#FFFFFF", 0.16), INK, 2)
        r.dot(xb + s * 9, -130, 5.5, "#FFD21F")                                              # knob at the free edge
    return r


@prop
def fireplace(c, x, y, k, t, st):
    r = Rig(c, x, y, k)
    r.rrect(-150, -300, 150, 0, 10, "#B8B2A6", INK, 3.4)
    for row in range(6):
        for col in range(5):
            xx = -140 + col * 58 + (29 if row % 2 else 0)
            r.rrect(xx, -292 + row * 48, xx + 52, -250 + row * 48, 6, "#C9C3B6" if (row + col) % 2 else "#A9A397", INK, 1.6)
    r.rrect(-96, -190, 96, 0, 4, "#2B1B14", INK, 3)
    r.poly([(-120, -300), (120, -300), (96, -190), (-96, -190)], "#9B958A", INK, 3)
    for i, (fx_, h, colr) in enumerate(((-52, 80, "#FF8A3D"), (0, 110, "#FF6B2D"), (52, 76, "#FFB03D"), (-20, 70, "#FFD23F"), (26, 64, "#FFE98A"))):
        wob = math.sin(t * 9 + i * 2) * 5
        r.poly([(fx_ - 24, -2), (fx_ + wob - 4, -h - math.sin(t * 7 + i) * 8), (fx_ + 24, -2)], colr, None)
    r.line([(-110, -176), (110, -176)], "#3A3A3A", 5)
    pot_y = -112
    r.line([(0, -176), (0, pot_y - 44)], "#3A3A3A", 4)
    r.ell(0, pot_y, 62, 52, "#4A4A55", INK, 3)
    r.ell(0, pot_y - 44, 56, 12, "#2E2E38", INK, 3)
    r.ell(0, pot_y - 42, 50, 9, "#7CC8FF", None)
    for i in range(4):                                                                    # bubbles
        ph = (t * 1.6 + i * 0.27) % 1.0
        r.ell(-30 + i * 20, pot_y - 42 - ph * 8, 5 * (1 - ph) + 1, 3 * (1 - ph) + 1, "#E6F6FF", None)
    return r


@prop
def finish_line(c, x, y, k, t, st):
    r = Rig(c, x, y, k)
    tape = clamp(st.get("tape", 0.0))
    for sx in (-250, 250):
        r.rrect(sx - 9, -330, sx + 9, 0, 4, "#E8E8F0", INK, 3)
        r.dot(sx, -334, 13, "#FFD21F")
    r.rrect(-262, -330, 262, -258, 10, "#FFFFFF", INK, 3.4)
    cols = 16
    for i in range(cols):
        for j in range(3):
            if (i + j) % 2 == 0:
                r.rrect(-258 + i * 32.25, -326 + j * 22, -258 + (i + 1) * 32.25, -326 + (j + 1) * 22, 0, INK, None)
    r.rrect(-160, -318, 160, -270, 14, "#FF5C8A", INK, 3)
    c.text(*r.P(0, -294), D.word("FINISH"), 54 * k, "#FFFFFF", stroke=3 * k, stroke_fill=INK)
    for i in range(8):
        r.poly([(-250 + i * 62, -258), (-220 + i * 62, -258), (-235 + i * 62, -236)], ["#FF5C8A", "#FFD21F", "#3E8EDE", "#3DB54A"][i % 4], INK, 2)
    if tape < 0.02:
        r.line([(-250, -40), (250, -40)], "#FF3D5A", 7)
        r.line([(-250, -40), (250, -40)], "#FFFFFF", 2.4)
    else:
        sag = tape * 90
        r.line([(-250, -40), (-250 + 90, -40 + sag), (-250 + 150, 0)], "#FF3D5A", 7)
        r.line([(250, -40), (250 - 90, -40 + sag), (250 - 150, 0)], "#FF3D5A", 7)
    return r


@prop
def start_line(c, x, y, k, t, st):
    r = Rig(c, x, y, k)
    for sx in (-170, 170):
        r.rrect(sx - 8, -250, sx + 8, 0, 4, "#E8E8F0", INK, 3)
    r.rrect(-182, -276, 182, -214, 10, "#3DB54A", INK, 3.4)
    c.text(*r.P(0, -245), D.word("START"), 50 * k, "#FFFFFF", stroke=3 * k, stroke_fill=INK)
    for i in range(7):
        r.poly([(-168 + i * 56, -214), (-142 + i * 56, -214), (-155 + i * 56, -194)], ["#FF5C8A", "#FFD21F", "#3E8EDE", "#FF9A3D"][i % 4], INK, 2)
    r.rrect(-200, -4, 200, 6, 3, "#FFFFFF", INK, 2.4)
    return r


@prop
def bigtree(c, x, y, k, t, st):
    r = Rig(c, x, y, k)
    r.ell(0, 4, 190, 20, mix("#79CE5D", "#2F6B2F", 0.4), None)
    r.poly([(-48, 0), (-34, -150), (-20, -260), (20, -260), (34, -150), (48, 0)], "#8B5A2B", INK, 3.4)
    for yy in (-60, -140, -210):
        r.arc(0, yy, 24, 20, 200, 340, "#6E4524", 4)
    r.ell(-20, -64, 20, 26, "#3A2316", INK, 2.6)
    for dx, dy, rx, ry in ((-120, -290, 120, 90), (120, -290, 120, 90), (0, -350, 150, 110), (-60, -250, 110, 80), (70, -255, 110, 80)):
        r.ell(dx, dy, rx, ry, "#2F9A45", INK, 3)
    for dx, dy, rx, ry in ((-130, -300, 100, 70), (112, -300, 100, 70), (0, -360, 130, 90), (-54, -262, 90, 64), (66, -266, 90, 64)):
        r.ell(dx, dy, rx, ry, "#46B650", None)
    r.ell(-70, -380, 50, 22, "#7ED47A", None)
    return r


@prop
def signpost(c, x, y, k, t, st):
    r = Rig(c, x, y, k)
    r.rrect(-6, -170, 6, 0, 2, "#8B5A2B", INK, 2.6)
    r.poly([(-70, -170), (56, -170), (80, -146), (56, -122), (-70, -122)], "#D9A066", INK, 3)
    c.text(*r.P(-6, -146), D.word(st.get("text", "HOME")), 28 * k, INK)
    return r


@prop
def bundle(c, x, y, k, t, st):
    kind = st.get("kind", "straw")
    r = Rig(c, x, y, k)
    if kind == "straw":
        r.ell(0, 2, 70, 9, mix("#79CE5D", "#2F6B2F", 0.35), None)
        for i, (bx, rot) in enumerate(((-30, -8), (0, 0), (30, 8))):
            r.rrect(bx - 20, -62, bx + 20, 0, 8, ["#F4CF63", "#EBBD48", "#F8DB7C"][i], INK, 2.6)
            for dx in (-10, 0, 10):
                r.line([(bx + dx, -56), (bx + dx, -6)], "#C99A2E", 1.8)
        r.line([(-44, -30), (44, -30)], "#B7742E", 5)
    elif kind == "sticks":
        r.ell(0, 2, 70, 9, mix("#79CE5D", "#2F6B2F", 0.35), None)
        for i, (a, col) in enumerate(((-18, "#8B5A2B"), (-6, "#A8794A"), (6, "#7A4A25"), (18, "#9B6B3A"), (0, "#B08050"))):
            r.limb((a * 1.6, -2), (a * 0.4, -92 + i * 4), 9, col)
        r.line([(-30, -38), (30, -38)], "#B7742E", 5)
    else:                                                                                   # bricks
        r.ell(0, 2, 80, 9, mix("#79CE5D", "#2F6B2F", 0.35), None)
        for row in range(4):
            for col in range(4 - row % 2):
                xx = -60 + col * 32 + (16 if row % 2 else 0)
                r.rrect(xx, -(row + 1) * 20, xx + 30, -row * 20 - 1, 3, ["#D9534F", "#C8453F", "#E0645A"][(row + col) % 3], INK, 2)
    return r


@prop
def pie(c, x, y, k, t, st):
    r = Rig(c, x, y, k)
    r.ell(0, 2, 60, 8, "#B07A44", None)
    r.ell(0, -14, 56, 22, "#E0A458", INK, 2.8)
    r.ell(0, -22, 44, 14, "#F2C57C", INK, 2.4)
    for dx in (-24, 0, 24):
        r.line([(dx - 8, -26), (dx + 8, -20)], "#C98A3A", 3)
    for dx, dy in ((-14, -34), (10, -32)):
        r.dot(dx, dy, 3, "#E2574C")
    return r


@prop
def rock(c, x, y, k, t, st):
    r = Rig(c, x, y, k)
    r.ell(0, 2, 52, 8, mix("#79CE5D", "#2F6B2F", 0.35), None)
    r.ell(0, -22, 48, 28, "#A9A8B4", INK, 2.8)
    r.ell(-12, -30, 18, 10, "#C9C8D4", None)
    return r


@prop
def basket(c, x, y, k, t, st):
    r = Rig(c, x, y, k)
    r.arc(0, -36, 36, 36, 180, 360, "#9B5C2E", 6)
    r.rrect(-42, -40, 42, 0, 10, "#D9A066", INK, 2.8)
    for i in range(5):
        r.line([(-34 + i * 17, -36), (-34 + i * 17, -4)], "#B8733A", 2)
    r.line([(-42, -20), (42, -20)], "#B8733A", 2.4)
    for i, col in enumerate(st.get("flowers", ("#FF6B8B", "#FFD23F", "#B58CFF"))):
        r.dot(-20 + i * 20, -48 + (i % 2) * 6, 9, col)
        r.dot(-20 + i * 20, -48 + (i % 2) * 6, 3.4, "#FFE98A")
    return r


# ================================================================================================ the gingerbread man's world
@prop
def oven(c, x, y, k, t, st):
    """A cosy red stove; st["door"] goes from 0 (shut, the little window glows) to 1 (wide open, orange and hot inside)."""
    r = Rig(c, x, y, k)
    op = clamp(st.get("door", 0.0))
    red, cream = "#E2574C", "#F6EBD2"
    flick = 0.5 + 0.5 * math.sin(t * 5.0)
    r.ell(0, 3, 132, 11, mix("#C98A52", "#5A3A1A", 0.5), None)
    r.rrect(-110, -204, 110, -8, 10, red, INK, 3.2)                                           # body
    r.rrect(-118, -222, 118, -196, 8, cream, INK, 3)                                          # top plate
    r.rrect(-102, -12, 102, 4, 5, darker(red, 0.22), INK, 2.6)                                # plinth
    for kx in (-66, 0, 66):                                                                   # knobs
        r.ell(kx, -178, 11, 11, cream, INK, 2.4)
        r.line([(kx, -178), (kx + 5, -185)], INK, 2.6)
    if op > 0.02:                                                                             # the hot inside
        r.rrect(-82, -154, 82, -30, 7, "#5A2410", INK, 2.8)
        r.ell(0, -92, 66, 46, mix("#5A2410", "#FF9A3D", 0.45 + 0.3 * op + 0.1 * flick), None)
        r.ell(0, -88, 40, 26, mix("#5A2410", "#FFD27A", 0.5 + 0.2 * flick), None)
        r.line([(-80, -64), (80, -64)], "#B8B8C4", 4.4)                                       # the rack
    th = op * 1.75                                                                            # the door is hinged at the bottom
    yf = -30 - 124 * math.cos(th)
    hw = 86 + 14 * math.sin(th)
    r.poly([(-86, -30), (86, -30), (hw, yf), (-hw, yf)], cream, INK, 2.8)
    gl = mix("#8A4A1E", "#FFB347", 0.5 + 0.3 * flick)
    wy0, wy1 = -30 + (yf + 30) * 0.2, -30 + (yf + 30) * 0.84
    if abs(wy1 - wy0) > 6:
        r.rrect(-62, min(wy0, wy1), 62, max(wy0, wy1), 6, gl if op < 0.5 else "#7A3A18", INK, 2.4)
    hy = yf + 8 * math.cos(th)
    r.rrect(-62, hy - 4, 62, hy + 4, 3, "#C9C8D4", INK, 2.2)                                  # the handle on the free edge
    return r


@prop
def counter(c, x, y, k, t, st):
    """A kitchen counter with a rolling pin and a bowl; things stand on its top at y - 146."""
    r = Rig(c, x, y, k)
    r.ell(0, 3, 200, 14, mix("#C98A52", "#5A3A1A", 0.5), None)
    r.rrect(-176, -128, 176, 0, 6, "#D9A066", INK, 3)
    for sx in (-88, 88):
        r.rrect(sx - 72, -112, sx + 72, -14, 6, "#E8B87C", INK, 2.4)
        r.dot(sx + (-56 if sx > 0 else 56), -66, 5, "#FFD21F")
    r.rrect(-192, -148, 192, -122, 6, "#F6EBD2", INK, 3)
    r.ell(-30, -148, 84, 6, "#FFFFFF", None)                                                  # a dusting of flour
    r.rrect(78, -164, 160, -150, 6, "#C98A52", INK, 2.4)                                      # rolling pin
    for hx in (62, 160):
        r.rrect(hx - 8, -168, hx + 8, -146, 5, "#8B4F26", INK, 2.2)
    pts = [(-146 + 40 * math.cos(math.radians(a)), -158 + 26 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
    r.poly(pts, "#FF6B8B", INK, 2.6)                                                          # mixing bowl
    r.ell(-146, -158, 40, 9, darker("#FF6B8B", 0.1), INK, 2.4)
    r.ell(-146, -159, 33, 6, "#FFF4DA", None)
    return r


def _tint(view, pts, color, alpha):
    """Lays a see-through colour over whatever is already drawn inside the polygon (world coordinates)."""
    cv = view.c
    pp = [cv._p(*view.P(px, py)) for px, py in pts]
    x0, y0 = max(0, int(min(p[0] for p in pp))), max(0, int(min(p[1] for p in pp)))
    x1, y1 = min(cv.img.width, int(max(p[0] for p in pp)) + 2), min(cv.img.height, int(max(p[1] for p in pp)) + 2)
    if x1 <= x0 or y1 <= y0:
        return
    mask = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).polygon([(px - x0, py - y0) for px, py in pp], fill=int(255 * alpha))
    col = D.hex2rgb(color)
    cv.img.paste(col + (255,) if cv.img.mode == "RGBA" else col, (x0, y0), mask)


@prop
def water(c, x, y, k, t, st):
    """The front of the river: see-through water that hides the feet of whoever wades in it. Put it at y = 700, in front of everyone."""
    from .storyart2 import river_x
    w, top = st.get("world", 1280), st.get("top", 628.0)
    xl0, xr0 = river_x(top, w)
    xl1, xr1 = river_x(706, w)
    n = 40
    wave = [(lerp(xl0, xr0, i / n), top + 3.5 * math.sin(lerp(xl0, xr0, i / n) / 30.0 + t * 2.1) + 2.0 * math.sin(lerp(xl0, xr0, i / n) / 13.0 - t * 2.9)) for i in range(n + 1)]
    _tint(c, wave + [(xr1, 706), (xl1, 706)], "#3E9BE8", 0.58)
    c.line(wave, "#E9F7FF", 3.2)
    for i in range(5):                                                                        # a few ripples
        ph = (t * 0.5 + i * 0.2) % 1.0
        yy = top + 14 + i * 14
        xa, xb = river_x(yy, w)
        cx = lerp(xa + 40, xb - 40, (i * 0.37 + ph * 0.3) % 1.0)
        c.line([(cx - 22, yy), (cx - 8, yy - 3), (cx + 8, yy + 3), (cx + 22, yy)], "#D5F1FF", 2.4)
    return None


# ================================================================================================ the three billy goats' world
@prop
def bridge(c, x, y, k, t, st):
    """A wooden bridge over the gorge. (x, y) = the middle of the walking surface, where the goats' feet stand;
    st["shake"] (0..1) makes the deck tremble under heavy hooves. The troll lives in the dark between the two big posts."""
    sh = clamp(st.get("shake", 0.0))
    half = 346
    wood, light, dark = "#B8793C", "#D9A062", "#7A4A25"
    r = Rig(c, x, y, k)
    _tint(c, [r.P(-half + 20, 30), r.P(half - 20, 30), r.P(half - 70, 178), r.P(-half + 70, 178)], "#1B2A44", 0.30)    # the shade under the bridge
    for sx in (-1, 1):
        px = sx * 134
        r.rrect(px - 15, 26, px + 15, 270, 4, wood, INK, 3)                                 # two big posts that stand in the stream
        for gy in (84, 144, 204):
            r.line([(px - 8, gy), (px + 8, gy + 6)], dark, 2)
        r.limb((px, 110), (px + sx * 98, 28), 13, wood, INK, 2.6)                           # a brace under the deck
    rd = Rig(c, x, y + math.sin(t * 38.0) * 2.8 * sh * k, k)
    for px in range(-300, 301, 100):                                                      # the railing, behind the walkers
        rd.rrect(px - 7, -92, px + 7, -6, 4, wood, INK, 2.6)
        rd.ell(px, -94, 9, 6, light, INK, 2.2)
    rd.rrect(-half + 8, -76, half - 8, -62, 4, light, INK, 2.6)
    rd.rrect(-half + 8, -44, half - 8, -30, 4, light, INK, 2.6)
    rd.rrect(-half - 6, -9, half + 6, 3, 2, light, INK, 2.4)                              # the walking surface
    rd.rrect(-half, 0, half, 28, 4, wood, INK, 3.2)                                       # the front of the deck
    for i in range(-5, 6):
        rd.line([(i * 62, 4), (i * 62, 25)], dark, 2)
    rd.rrect(-half + 6, 3, half - 6, 9, 2, light, None)
    rd.rrect(-half, 22, half, 38, 3, dark, INK, 2.6)                                      # the beam below it
    return rd


@prop
def gorge_water(c, x, y, k, t, st):
    """The front of the stream at the bottom of the gorge: see-through water that hides the feet of whoever stands in it. Put it at y = 700, in front of everyone."""
    from .storyart2 import gorge_x
    top = st.get("top", 668.0)
    xl0, xr0 = gorge_x(top)
    xl1, xr1 = gorge_x(722)
    n = 40
    wave = [(lerp(xl0, xr0, i / n), top + 3.5 * math.sin(lerp(xl0, xr0, i / n) / 30.0 + t * 2.1) + 2.0 * math.sin(lerp(xl0, xr0, i / n) / 13.0 - t * 2.9)) for i in range(n + 1)]
    _tint(c, wave + [(xr1, 722), (xl1, 722)], "#3E9BE8", 0.58)
    c.line(wave, "#E9F7FF", 3.2)
    for i in range(4):                                                                        # a few ripples
        ph = (t * 0.5 + i * 0.25) % 1.0
        yy = top + 14 + i * 12
        xa, xb = gorge_x(yy)
        cx = lerp(xa + 40, xb - 40, (i * 0.37 + ph * 0.3) % 1.0)
        c.line([(cx - 22, yy), (cx - 8, yy - 3), (cx + 8, yy + 3), (cx + 22, yy)], "#D5F1FF", 2.4)
    return None


# ================================================================================================ the enormous turnip's world
@prop
def turnip(c, x, y, k, t, st):
    """The enormous turnip in its garden bed. (x, y) = the middle of the bed on the ground.
    st["grow"] 0..1: nothing but soil -> a tiny sprout -> an enormous turnip with a big bunch of leaves.
    st["wobble"] 0..1: how hard it is pulled (the leaves and the root tremble, the root creeps up out of the soil).
    st["bend"] 0..1: the leaves are gathered into one bunch that is pulled toward the puller's hands, the grip at (st["gx"], st["gy"])
        in the prop's own units (relative to (x, y), up = negative); st["gsw"] = how far the hands swing to and fro (units) while pulling.
    st["out"] 0..1: 0 = in the ground, 1 = out of the ground and lying in front of the hole (it jumps there in an arc)."""
    grow = clamp(st.get("grow", 1.0))
    wob = clamp(st.get("wobble", 0.0))
    bend = clamp(st.get("bend", 0.0))
    out = clamp(st.get("out", 0.0))
    gx, gy = st.get("gx", 330.0), st.get("gy", -190.0)
    gx += st.get("gsw", 0.0) * math.sin(t * 6.3)
    r = Rig(c, x, y, k)
    soil, soil_l, soil_d = "#8A5A32", "#A9733F", "#5E3A1E"
    leaf, leaf_l, leaf_d = "#3E9B3A", "#63BE4B", "#2C7A2C"
    hole = out > 0.02
    rim_first = out >= 0.12                      # (the front edge of the hole hides the root while it still comes up out of it)

    def front_rim():
        r.ell(0, 12, 160, 26, soil, None)
        r.ell(0, 8, 160, 24, soil_l, INK, 3)
        r.ell(0, 6, 98, 15, "#3E2412", INK, 2.6)
        for dx, dy, rr in ((-120, 10, 6), (-60, 22, 5), (122, 14, 7), (74, 26, 4)):
            r.dot(dx, dy, rr, soil_d)

    # the garden bed behind everything
    r.ell(0, 4, 175, 26, mix("#79CE5D", "#2F6B2F", 0.35), None)
    r.ell(0, 0, 160, 30, soil_d if hole else soil, INK, 3)
    if hole:
        r.ell(0, -2, 92, 15, "#3E2412", None)
        if rim_first:
            front_rim()
    # where the root is now
    shake = math.sin(t * 23.0) * 3.2 * wob
    lift = (6.0 + 12.0 * abs(math.sin(t * 8.5))) * wob
    rb = clamp((grow - 0.18) / 0.82) ** 0.75                 # the root's size 0..1
    rx_, ry_ = 112.0 * rb, 118.0 * rb
    ox = lerp(0.0, 150.0, ease(out))
    arc = math.sin(clamp(out) * math.pi) * 200.0
    cy_in = 26.0 * rb - ry_ - lift                           # centre height of the bulb while it is in the ground (up = negative): its bottom is buried
    cy_ = lerp(cy_in, -ry_ * 0.94 + 30.0, ease(out)) - arc   # ... and when it lies on the ground in front of the hole
    cx_ = ox + shake
    if rb > 0.02:
        # the tail root (only when the turnip is out of the ground)
        tail = 56.0 * rb * (1.0 - ease(out))
        if out > 0.02 and tail > 3:
            r.poly([(cx_ - 16 * rb, cy_ + ry_ * 0.86), (cx_ + 16 * rb, cy_ + ry_ * 0.86), (cx_ + 4, cy_ + ry_ + tail)], "#F2E8D5", INK, 2.6)
        # the bulb: cream with a purple top
        r.ell(cx_, cy_, rx_, ry_, "#FBF3E4", INK, 3.4)
        cap = []
        for j in range(0, 19):
            th = math.radians(180 + 180 * j / 18.0)
            cap.append((cx_ + rx_ * math.cos(th), cy_ + ry_ * math.sin(th)))
        for j in range(18, -1, -1):
            u = j / 18.0
            xx = cx_ - rx_ + 2 * rx_ * u
            yy = cy_ - ry_ * 0.20 + math.sin(u * 7.0) * 7 * rb + 24 * rb * (1 - abs(2 * u - 1)) ** 2
            cap.append((xx, yy))
        r.poly(cap, "#C86DD7", None)
        r.ell(cx_, cy_, rx_, ry_, None, INK, 3.4)
        r.ell(cx_ - rx_ * 0.38, cy_ - ry_ * 0.42, rx_ * 0.2, ry_ * 0.13, "#E7B6EE", None, ang=-30)            # shine
        r.ell(cx_ - rx_ * 0.30, cy_ + ry_ * 0.28, rx_ * 0.16, ry_ * 0.09, "#FFFFFF", None, ang=-30)
        for dx in (-0.45, 0.35):                                                                            # a few thin root hairs
            r.line([(cx_ + rx_ * dx, cy_ + ry_ * 0.78), (cx_ + rx_ * dx + 8, cy_ + ry_ * 0.95)], "#C9B89A", 2)
    # leaves: a fan from the top of the bulb (or one bunch pulled toward the hands)
    ls = clamp(grow / 0.55) ** 0.9 * (1.0 + 0.18 * clamp((grow - 0.55) / 0.45))
    topy = cy_ - ry_ * 0.86
    n_leaf = 7
    be = ease(bend)
    for i in range(n_leaf):
        a = -78 + i * 156.0 / (n_leaf - 1)
        sway = math.sin(t * 2.0 + i * 1.3) * 3.0 + math.sin(t * 17.0 + i) * 6.0 * wob
        ang = math.radians(a + sway)
        ln = (150.0 - 18.0 * abs(i - 3)) * ls
        wd = (34.0 - 3.0 * abs(i - 3)) * ls
        bx, by = cx_ + math.sin(ang * 0.35) * 14, topy + 6
        tx, ty = cx_ + math.sin(ang) * ln * 0.95, topy - math.cos(ang) * ln
        if be > 0.001:                                       # gathered into a bunch that ends in the puller's hands
            dxg, dyg = gx - bx, gy - by
            dl = math.hypot(dxg, dyg) or 1.0
            ux, uy = dxg / dl, dyg / dl
            reach = dl + 34.0 + 9.0 * (3 - abs(i - 3))
            off = (i - 3) * 8.0 + math.sin(t * 19.0 + i) * 3.5 * wob
            btx, bty = bx + ux * reach - uy * off, by + uy * reach + ux * off
            tx, ty = lerp(tx, btx, be), lerp(ty, bty, be)
            wd *= 1.0 - 0.12 * be
        dx_, dy_ = tx - bx, ty - by
        dl_ = math.hypot(dx_, dy_) or 1.0
        px_, py_ = -dy_ / dl_, dx_ / dl_                     # a unit vector across the leaf
        bow = (i - 3) * (3.0 + 6.0 * be) + 10.0 * be         # the leaves curve outward; pulled into a bunch they spread in the middle and sag a little
        mid = [(bx + dx_ * u + px_ * bow * math.sin(math.pi * u), by + dy_ * u + py_ * bow * math.sin(math.pi * u)) for u in (j / 10.0 for j in range(11))]
        hws = [wd * (math.sin(math.pi * j / 10.0) ** 0.75) * (1.0 - 0.3 * j / 10.0) + 0.8 for j in range(11)]
        edge_l = [(m[0] + px_ * h, m[1] + py_ * h) for m, h in zip(mid, hws)]
        edge_r = [(m[0] - px_ * h, m[1] - py_ * h) for m, h in zip(mid, hws)]
        r.poly(edge_l + edge_r[::-1], leaf if i % 2 == 0 else leaf_l, INK, 3)
        r.line(mid, leaf_d, 2.4)
    # the front of the soil hides the buried part of the root (only while it is in the ground)
    if not hole:
        pts = [(-152 + 304 * i / 30.0, -4 - 6 * math.sin(i * 0.45) - 3 * math.sin(i * 1.1 + 1)) for i in range(31)]
        pts += [(152 - 304 * i / 24.0, 8 + 24 * math.sqrt(max(0.0, 1 - (1 - 2 * i / 24.0) ** 2))) for i in range(25)]
        r.poly(pts, soil_l, INK, 3)
        for dx, dy, rr in ((-110, 6, 6), (-60, 20, 5), (-18, 9, 4), (32, 22, 6), (76, 8, 5), (118, 14, 4)):
            r.dot(dx, dy, rr, soil_d)
    elif not rim_first:
        front_rim()
    if grow < 0.2:                                                     # a tiny sprout of two leaves
        s = clamp(grow / 0.2)
        if s > 0.05:
            r.line([(0, 4), (0, 4 - 26 * s)], leaf_d, 5)
            for sx in (-1, 1):
                r.ell(sx * 12 * s, 4 - 28 * s, 14 * s, 7 * s, leaf_l, INK, 2.4, ang=sx * -28)
    return r


@prop
def pot(c, x, y, k, t, st):
    """A big soup pot on a little fire (steam is a separate effect). (x, y) = the middle of the fire on the ground."""
    r = Rig(c, x, y, k)
    r.ell(0, 4, 150, 17, mix("#79CE5D", "#2F6B2F", 0.45), None)
    for sx, ang in ((-1, -14), (1, 14)):                                                    # two crossed logs
        r.ell(sx * 62, -10, 62, 12, "#8B5A2B", INK, 2.8, ang=ang)
        r.ell(sx * 62 + sx * 52, -9 - sx * 8, 11, 10, "#C98A52", INK, 2.2)
    for i, (fx_, fh, col) in enumerate(((-52, 58, "#FF8A3D"), (0, 78, "#FF6B2E"), (54, 56, "#FF8A3D"))):    # flames
        fl = fh * (0.86 + 0.14 * math.sin(t * 9.0 + i * 2.1))
        r.poly([(fx_ - 24, -14), (fx_ - 10, -14 - fl * 0.55), (fx_ + 2 * math.sin(t * 7 + i), -14 - fl), (fx_ + 12, -14 - fl * 0.5), (fx_ + 24, -14)], col, INK, 2.6)
        r.poly([(fx_ - 11, -14), (fx_, -14 - fl * 0.55), (fx_ + 11, -14)], "#FFD54A", None)
    r.ell(0, -120, 112, 96, "#5F6F82", INK, 3.4)                                           # the pot
    r.ell(-38, -142, 34, 52, "#7C8EA3", None, ang=22)
    r.rrect(-110, -150, 110, -128, 8, "#4A5868", INK, 3)
    for sx in (-1, 1):                                                                      # handles
        r.arc(sx * 116, -128, 24, 20, -90 if sx > 0 else 90, 90 if sx > 0 else 270, INK, 9)
        r.arc(sx * 116, -128, 24, 20, -90 if sx > 0 else 90, 90 if sx > 0 else 270, "#4A5868", 5)
    if st.get("kind", "turnip") == "stone":
        _stone_soup(r, t, st)
    else:
        r.ell(0, -152, 102, 22, "#3C4856", INK, 3)                                          # the soup
        r.ell(0, -150, 92, 16, "#F7DE9A", None)
        for i, (bx_, by_, col) in enumerate(((-52, -151, "#C86DD7"), (-14, -147, "#FBF3E4"), (30, -152, "#C86DD7"), (60, -148, "#7ED47A"), (-76, -146, "#FBF3E4"))):
            r.ell(bx_, by_, 11, 5, col, INK, 1.8)
        for i in range(3):                                                                  # bubbles
            ph = (t * 0.9 + i * 0.37) % 1.0
            bb = 3 + 8 * ph
            if ph < 0.85:
                r.ell(-40 + i * 38, -152 - 4 * ph, bb, bb * 0.55, "#FFF8DB", "#E7C770", 1.6)
    sp = math.sin(t * 2.2) * 16 * clamp(st.get("stir", 1.0))                                # the wooden spoon
    r.line([(sp, -152), (70 + sp * 0.4, -232)], INK, 11)
    r.line([(sp, -152), (70 + sp * 0.4, -232)], "#C98A52", 6.5)
    return r


# ================================================================================================ the stone soup's world
STONE_SLOTS = {"carrot": ((-70, -150), (-2, -153), (56, -147)), "potato": ((-32, -146), (30, -152), (76, -151)),
               "cabbage": ((-84, -150), (12, -147), (48, -155)), "onion": ((-54, -153), (-8, -148), (68, -148)),
               "tomato": ((-20, -153), (36, -146), (-76, -146))}


def _soup_bit(r, kind, x, y, s, rot, broth):
    """A little piece of a vegetable floating in the soup (s = its size, 1.0 = full size)."""
    if kind == "carrot":                                                                   # a slice
        r.ell(x, y, 10 * s, 6.5 * s, "#FF8A2B", INK, 1.8)
        r.ell(x, y, 4.5 * s, 2.6 * s, "#FFC27A", None)
    elif kind == "potato":                                                                 # a chunk
        r.ell(x, y, 11 * s, 8 * s, "#E4BF82", INK, 1.8, ang=rot)
        r.dot(x - 3 * s, y - 1 * s, 1.6 * s, "#B88C52")
    elif kind == "cabbage":                                                                # a curly leaf
        r.ell(x, y, 13 * s, 6 * s, "#7ED47A", INK, 1.8, ang=rot * 0.4 - 8)
        r.ell(x - 2 * s, y - 1 * s, 7 * s, 2.4 * s, "#A7E89C", None, ang=rot * 0.4 - 8)
    elif kind == "onion":                                                                  # a ring
        r.ell(x, y, 10 * s, 6 * s, "#FFF4D8", INK, 1.8)
        r.ell(x, y, 5.2 * s, 2.8 * s, broth, None)
    else:                                                                                  # a piece of tomato
        r.ell(x, y, 9 * s, 7 * s, "#EE4B3E", INK, 1.8)
        r.ell(x - 3 * s, y - 2 * s, 3 * s, 1.8 * s, "#FF9A8F", None)


def _stone_soup(r, t, st):
    """The inside of the pot for the stone soup (see pot)."""
    water, cook = clamp(st.get("water", 0.0)), clamp(st.get("cook", 0.0))
    r.ell(0, -152, 102, 22, "#3C4856", INK, 3)                                              # the empty pot
    broth = mix("#9ED8F2", "#F2C66B", ease(cook))
    if water > 0.02:
        lvl = ease(water)                                                                   # the water rises
        r.ell(0, -150 - 2 * (1 - lvl), 92 * (0.6 + 0.4 * lvl), 16 * lvl, broth, None)
        r.ell(-26, -153, 34 * lvl, 4.4 * lvl, mix(broth, "#FFFFFF", 0.38), None)
    sd = clamp(st.get("stone", 0.0))                                                        # the stone drops in (it only peeks out of the water)
    if sd > 0.02:
        drop = (1.0 - ease(sd)) * 74
        r.ell(-46, -154 - drop, 21, 12, "#9EA7B3", INK, 2.4)
        r.ell(-52, -158 - drop, 7, 3.4, "#CDD3DB", None, ang=-20)
    bits = []
    for name, slots in STONE_SLOTS.items():
        v = clamp(st.get(name, 0.0))
        if v > 0.02:
            for j, (bx_, by_) in enumerate(slots):
                bits.append((by_, name, bx_, by_ - 2.4 * math.sin(t * 2.1 + bx_ * 0.1), ease_out_back(v), 25 * j))
    for _y, name, bx_, by_, sc, rot in sorted(bits):
        _soup_bit(r, name, bx_, by_, sc, rot, broth)
    for i in range(3):                                                                      # bubbles
        ph = (t * (0.5 + 0.7 * cook) + i * 0.37) % 1.0
        bb = 3 + 8 * ph
        if ph < 0.85 and water > 0.9:
            r.ell(-40 + i * 38, -152 - 4 * ph, bb, bb * 0.55, mix(broth, "#FFFFFF", 0.7), mix(broth, "#B8872E", 0.5), 1.6)


def _vegetable(r, kind, cx, cy, s=1.0, rot=0.0):
    """One whole vegetable centred at (cx, cy) in r's units (s = 1.0 is about 80 units long), turned by rot degrees.
    kind: carrot, potato, cabbage, onion, tomato, bowl (of porridge) or stone."""
    co, si = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def P(px, py):
        return (cx + (px * co - py * si) * s, cy + (px * si + py * co) * s)

    def E(px, py, rx, ry, fill, w=2.8, ang=0.0):
        r.ell(*P(px, py), rx * s, ry * s, fill, INK if w else None, w, ang=ang + rot)

    def Y(pts, fill, w=2.6):
        r.poly([P(*p) for p in pts], fill, INK if w else None, w)

    def L(pts, col, w=2.0):
        r.line([P(*p) for p in pts], col, w)

    if kind == "carrot":
        for a in (-30, 0, 30):                                                              # the green top
            ang = math.radians(a)
            tip = (math.sin(ang) * 40, -30 - math.cos(ang) * 40)
            Y([(-3, -30), (math.sin(ang) * 20 - 7 * math.cos(ang), -30 - math.cos(ang) * 20 - 7 * math.sin(ang)), tip,
               (math.sin(ang) * 20 + 7 * math.cos(ang), -30 - math.cos(ang) * 20 + 7 * math.sin(ang)), (3, -30)], "#4FAE4B", 2.2)
        Y([(-17, -26), (-9, -35), (9, -35), (17, -26), (7, 24), (0, 42), (-7, 24)], "#FF8A2B", 2.8)
        for a, b in (((-12, -14), (-3, -12)), ((3, 0), (12, 2)), ((-6, 14), (2, 16))):
            L([a, b], "#E0661A", 2.2)
        E(-8, -18, 3.4, 9, "#FFB35C", 0, 8)
    elif kind == "potato":
        E(0, 0, 38, 26, "#C99A5E", 2.8, -10)
        E(12, -8, 15, 9, "#D7AB6F", 0, -10)
        E(-12, -10, 10, 5, "#E4C48C", 0, -20)
        for ex, ey in ((-16, 2), (6, 10), (18, -4), (-4, -6)):
            E(ex, ey, 3.2, 2.4, "#8C6A3A", 0)
    elif kind == "cabbage":
        E(-22, 6, 15, 22, "#8AD983", 2.4, 20)
        E(22, 6, 15, 22, "#8AD983", 2.4, -20)
        E(0, 0, 32, 30, "#6FC66A", 3.0)
        E(0, -3, 22, 21, "#A7E89C", 2.2)
        for a, b in (((0, 16), (-8, -10)), ((0, 16), (8, -10)), ((0, 16), (0, -14)), ((-6, 8), (-20, 2)), ((6, 8), (20, 2))):
            L([a, b], "#4FA84F", 2.0)
        E(-12, -14, 7, 4, "#D5F7CC", 0, -30)
    elif kind == "onion":
        L([(0, -34), (-3, -52)], "#4FAE4B", 4.6)
        L([(0, -34), (6, -50)], "#4FAE4B", 3.6)
        Y([(-12, -12), (-5, -38), (0, -42), (5, -38), (12, -12)], "#F0CF8E", 2.6)
        E(0, 6, 27, 28, "#F0CF8E", 3.0)
        for a, b in (((-13, -8), (-15, 10)), ((0, -16), (0, 20)), ((13, -8), (15, 10))):
            L([a, b], "#D9AE60", 1.8)
        E(-9, -6, 6, 10, "#F9E7B8", 0, 12)
        for a, b in (((-6, 32), (-9, 42)), ((0, 33), (0, 44)), ((6, 32), (9, 42))):
            L([a, b], "#C9B89A", 2.0)
    elif kind == "tomato":
        E(0, 2, 29, 26, "#EE4B3E", 3.0)
        E(-11, -8, 9, 5, "#FF9A8F", 0, -30)
        star = []
        for i in range(10):
            ang = math.radians(-90 + 36 * i)
            rr = 15 if i % 2 == 0 else 6
            star.append((math.cos(ang) * rr, -24 + math.sin(ang) * rr * 0.7))
        Y(star, "#4FAE4B", 2.2)
    elif kind == "bowl":                                                                    # a bowl of porridge with a spoon in it
        L([(10, -14), (32, -46)], "#C98A52", 5.6)
        E(35, -51, 7, 9.5, "#D9A066", 2.2, -30)
        Y([(38 * math.cos(math.radians(a)), 6 + 30 * math.sin(math.radians(a))) for a in range(0, 181, 15)], "#6CB7FF", 3.0)
        L([(-30, 16), (30, 16)], "#FFFFFF", 3.0)
        E(0, 6, 38, 10, "#EAF4FF", 2.8)
        Y([(-31, 4), (-24, -9), (-8, -17), (8, -17), (24, -9), (31, 4)], "#FFF0C2", 2.6)
        E(-9, -10, 9, 3.6, "#FFFFFF", 0, -15)
        L([(-12, -4), (0, -9), (12, -4)], "#E9A94A", 2.6)
    else:                                                                                   # stone
        E(0, 2, 36, 24, "#9EA7B3", 2.8, -6)
        E(-10, -6, 12, 6, "#CDD3DB", 0, -20)
        L([(8, 8), (20, 4)], "#7E8794", 2.2)


@prop
def stone(c, x, y, k, t, st):
    """A smooth, round stone lying on the road. st["show"] 0 = it is gone (somebody picked it up)."""
    if st.get("show", 1.0) < 0.5:
        return None
    r = Rig(c, x, y, k)
    r.ell(0, 2, 44, 7, mix("#79CE5D", "#2F6B2F", 0.35), None)
    _vegetable(r, "stone", 0, -22, 1.0)
    return r


@prop
def veg(c, x, y, k, t, st):
    """A vegetable (st["kind"]: carrot, potato, cabbage, onion, tomato, bowl or stone) with (x, y) as its middle.
    st["u"] 0..1 = how far it has flown along its arc to (x + st["dx"], y + st["dy"]) (units of the prop; st["h"] = how high the arc is,
    st["turns"] = how often it spins on the way). It is only seen while 0 < u < 1, unless st["rest"] = 1: then it just stays at (x, y),
    popping up with st["pop"] 0..1 (st["size"] = its size)."""
    u = clamp(st.get("u", 0.0))
    rest = st.get("rest", 0.0) > 0.5
    size = st.get("size", 0.7)
    if rest:
        pop = clamp(st.get("pop", 1.0))
        if pop < 0.02:
            return None
        r = Rig(c, x, y, k)
        _vegetable(r, st.get("kind", "carrot"), 0, 0, size * ease_out_back(pop))
        return r
    if not 0.001 < u < 0.999:
        return None
    r = Rig(c, x, y, k)
    px, py = st.get("dx", 0.0) * u, st.get("dy", 0.0) * u - 4.0 * st.get("h", 160.0) * u * (1.0 - u)
    _vegetable(r, st.get("kind", "carrot"), px, py, size, 360.0 * st.get("turns", 1.0) * u)
    return r


# ================================================================================================ the magic porridge pot's world
CREAM, CREAM_D, CREAM_L = "#FFFDF5", "#FBE6CC", "#FFFFFF"


def _ellipse_world(r, lx, ly, rx, ry, n=30):
    return [r.P(lx + rx * math.cos(2 * math.pi * i / n), ly + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


@prop
def mpot(c, x, y, k, t, st):
    """The magic porridge pot: a little black pot with a golden star on its belly, standing on three stubby legs. (x, y) = the middle of its base.
    st: fill 0..1 = how full of porridge it is, over 0..1 = the porridge heaps up and runs down the sides, shake 0..1 = the pot rattles,
    glow 0..1 = a golden glow around it (the star flashes)."""
    fill, over = clamp(st.get("fill", 0.0)), clamp(st.get("over", 0.0))
    shake, glow = clamp(st.get("shake", 0.0)), clamp(st.get("glow", 0.0))
    r = Rig(c, x + math.sin(t * 34.0) * 3.2 * shake * k, y, k, lean=math.sin(t * 29.0 + 1.0) * 2.6 * shake)
    _tint(c, _ellipse_world(r, 0, 4, 84, 11), "#000000", 0.20)                              # the shadow on the floor
    if glow > 0.02:                                                                         # a soft golden glow
        pulse = 1.0 + 0.05 * math.sin(t * 7.0)
        for i in range(4):
            rr = (96 + 30 * i) * pulse
            _tint(c, _ellipse_world(r, 0, -70, rr, rr * 0.85, 40), "#FFE27A", 0.11 * glow)
    for sx in (-1, 1):                                                                      # the legs
        r.rrect(sx * 42 - 10, -28, sx * 42 + 10, 2, 5, "#24243A", INK, 2.6)
    for sx in (-1, 1):                                                                      # the handles
        r.arc(sx * 68, -78, 19, 19, -90 if sx > 0 else 90, 90 if sx > 0 else 270, INK, 10)
        r.arc(sx * 68, -78, 19, 19, -90 if sx > 0 else 90, 90 if sx > 0 else 270, "#34344A", 5.4)
    r.ell(0, -64, 68, 52, "#34344A", INK, 3.6)                                              # the body
    r.ell(-32, -86, 15, 23, "#5C5C7C", None, ang=26)
    r.rrect(-62, -120, 62, -100, 8, "#24243A", INK, 3.2)                                    # the rim
    r.rrect(-56, -118, -40, -112, 3, "#4A4A66", None)
    r.ell(0, -120, 56, 13, "#12121C", INK, 3)                                               # the inside
    if fill > 0.02:
        lvl = ease(fill)
        r.ell(0, -116 - 4 * lvl, 56 * (0.5 + 0.5 * lvl), 12 * lvl, CREAM, None)
        r.ell(-14, -118 - 4 * lvl, 18 * lvl, 3.2 * lvl, CREAM_L, None)
    ov = ease(over)
    if ov > 0.02:
        for i, (dx, lag, wd) in enumerate(((-48, 0.0, 9), (34, 0.14, 8), (52, 0.3, 7), (-30, 0.42, 7))):      # drips run down the pot
            ln = clamp((ov - lag) / (0.75 - lag)) * (30 + 22 * ((i * 7) % 3))
            if ln > 3:
                r.rrect(dx - wd, -116, dx + wd, -112 + ln, wd, CREAM, INK, 2.8)
                r.ell(dx - wd * 0.3, -112 + ln * 0.5, wd * 0.25, ln * 0.28, CREAM_L, None)
        hh = 16 + 74 * ov
        bulge = 11.0 * ov
        pts = [(math.cos(math.radians(a)) * (56 + bulge * math.sin(math.radians(a))), -120 - hh * math.sin(math.radians(a)) ** 0.85) for a in range(180, -1, -10)]
        pts += [(56 * math.cos(math.radians(a)), -120 + 13 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
        r.poly(pts, CREAM, INK, 3.2)
        r.ell(-18 - 6 * ov, -120 - hh * 0.62, 14 + 8 * ov, 6 + 5 * ov, CREAM_L, None, ang=-12)
        if ov > 0.4:                                                                        # a golden drizzle of honey on top
            r.line([(-28 + 11 * j, -120 - hh * (0.7 + 0.05 * math.sin(j * 1.9)) + 5 * math.sin(j * 1.3)) for j in range(6)], "#E9A94A", 4.0)
        for i in range(4):                                                                  # bubbles on the heap
            ph = (t * 1.3 + i * 0.27) % 1.0
            if ph < 0.85:
                bb = 3 + 8 * ph
                r.ell(-30 + i * 20, -120 - hh * (0.35 + 0.12 * (i % 2)), bb, bb * 0.8, "#FFF8DB", "#D9B25E", 1.6)
    spark = 0.5 + 0.5 * math.sin(t * 9.0)
    r.poly(star_pts(0, -62, 27, 11.5), mix("#FFD21F", "#FFFFFF", 0.45 * glow * spark), INK, 2.8)
    r.poly(star_pts(-2, -64, 14, 6), "#FFF1A0", None)
    if fill > 0.3 and over < 0.05:                                                          # a little steam
        for i in range(3):
            ph = (t * 0.5 + i * 0.33) % 1.0
            r.ell(-22 + i * 22 + 5 * math.sin(t * 2 + i), -128 - 52 * ph, 8 + 7 * ph, 6 + 6 * ph, "#FFFFFF", None)
    return r


@prop
def porridge(c, x, y, k, t, st):
    """A flood of porridge in front of everyone (put it at y = 700). st: h 0..1 = how high it stands (1 = about 200 units), l / r = where its
    left and right fronts are (world x, default far outside the screen)."""
    h = clamp(st.get("h", 0.0))
    if h < 0.01:
        return None
    xl, xr = st.get("l", -80.0), st.get("r", 1360.0)
    if xr - xl < 40:
        return None
    bottom, top0 = 760.0, 704.0 - 204.0 * h
    amp = clamp(h / 0.25)

    def ty(xx):
        return top0 + amp * (4.0 * math.sin(xx / 41.0 + t * 1.7) + 2.0 * math.sin(xx / 17.0 - t * 2.3) - 7.0 * abs(math.sin(xx / 53.0 + t * 0.8)))

    fw = min(100.0 + 130.0 * h, (xr - xl) / 2.0 - 1.0)
    n = max(8, int((xr - xl - 2 * fw) / 18.0))
    top = [(lerp(xl + fw, xr - fw, i / n), 0.0) for i in range(n + 1)]
    top = [(px, ty(px)) for px, _ in top]
    pts = list(top)
    for j in range(1, 9):                                                                   # the right front
        th = math.radians(90.0 * j / 8)
        y0 = ty(xr - fw)
        pts.append((xr - fw + fw * math.sin(th), y0 + (bottom - y0) * (1.0 - math.cos(th))))
    pts.append((xl + fw, bottom))
    yl = ty(xl + fw)
    for j in range(8, 0, -1):                                                               # the left front
        th = math.radians(90.0 * j / 8)
        pts.append((xl + fw - fw * math.sin(th), yl + (bottom - yl) * (1.0 - math.cos(th))))
    c.poly(pts, CREAM_D, INK, 3.4)
    band = 16.0 + 8.0 * h
    c.poly(top + [(px, py + band + 3.0 * math.sin(px / 23.0 + t)) for px, py in reversed(top)], CREAM, None, 0)
    c.line(top, INK, 3.4)
    rng = random.Random(11)
    for i in range(34):                                                                     # oat flecks, they stay where they are while the porridge rises
        fx_ = lerp(xl + fw, xr - fw, rng.random()) + 7.0 * math.sin(t * 0.8 + i)
        fy_ = lerp(top0 + 40, 740.0, rng.random() ** 0.8)
        if fy_ > ty(fx_) + band + 6.0 and xl + fw < fx_ < xr - fw:
            c.ellipse(fx_, fy_, 5.5, 2.5, fill="#C99A5E")
    for i in range(12):                                                                     # bubbles rise and pop at the top
        ph = (t * 0.42 + i * 0.137) % 1.0
        bx = lerp(xl + fw, xr - fw, (i * 0.6180339 + 0.13) % 1.0)
        by = lerp(ty(bx) + 62.0, ty(bx) + 5.0, ph)
        if ph < 0.92 and h > 0.12 and by < 716:
            rr = 4.0 + 8.0 * ph
            c.ellipse(bx, by, rr, rr * 0.82, fill="#FFF8DB", outline="#D9B25E", width=1.8)
    for i in range(5):                                                                      # shiny spots and a drizzle of honey on the top
        gx = lerp(xl + fw, xr - fw, (i * 0.37 + 0.11) % 1.0)
        c.ellipse(gx, ty(gx) + 8.0, 14, 2.6, fill=CREAM_L)
        hx_ = lerp(xl + fw, xr - fw, (i * 0.37 + 0.31) % 1.0)
        c.line([(hx_ - 26 + 9 * j, ty(hx_ - 26 + 9 * j) + 11.0 + 3.0 * math.sin(j * 1.7 + i)) for j in range(7)], "#E9A94A", 3.0)
    return None


# ================================================================================================ Cinderella's world
@prop
def carriage(c, x, y, k, t, st):
    """A big orange pumpkin that turns into a golden coach. (x, y) = the middle of its base. st: morph 0..1 (0 = pumpkin, 1 = coach),
    glow 0..1 = a golden glow around it, roll = how far the wheels have turned (degrees), shake 0..1 = it rattles while it changes."""
    m, glow, shake = clamp(st.get("morph", 0.0)), clamp(st.get("glow", 0.0)), clamp(st.get("shake", 0.0))
    dx = st.get("dx", 0.0)                                                                  # driving along: the wheels turn with the distance
    sc = 1.0 + 0.10 * math.sin(math.pi * clamp(m * 1.0)) if 0.02 < m < 0.98 else 1.0
    r = Rig(c, x + dx + math.sin(t * 40.0) * 4.0 * shake * k, y, k * sc)
    _tint(c, _ellipse_world(r, 0, 4, 150, 16), "#000000", 0.20)
    if glow > 0.02:
        pulse = 1.0 + 0.05 * math.sin(t * 7.0)
        for i in range(4):
            rr = (130 + 36 * i) * pulse
            _tint(c, _ellipse_world(r, 0, -100, rr, rr * 0.8, 40), "#FFE27A", 0.10 * glow)
    if m < 0.5:                                                                           # the pumpkin
        for dx, rx in ((-76, 50), (76, 50), (-44, 56), (44, 56)):
            r.ell(dx, -70, rx, 68, "#E8761A", INK, 3.2)
        r.ell(0, -70, 58, 72, "#F28C28", INK, 3.4)
        for dx in (-104, -62, 62, 104):                                                   # the grooves between the lobes
            r.arc(dx, -70, 10, 56, 100 if dx < 0 else -80, 260 if dx < 0 else 80, "#C9610F", 3)
        r.ell(-36, -102, 15, 24, "#FFC27A", None, ang=18)
        r.rrect(-10, -152, 12, -126, 4, "#4E8A2E", INK, 2.8)
        r.line([(10, -140), (36, -156), (58, -142)], INK, 8)
        r.line([(10, -140), (36, -156), (58, -142)], "#4E9B3A", 4.4)
    else:                                                                                 # the golden coach
        roll = st.get("roll", 0.0) + math.degrees(dx / (46.0 * k))
        for wx in (-92, 92):
            r.ell(wx, -44, 46, 46, "#FFD21F", INK, 4)
            r.ell(wx, -44, 36, 36, "#FFF3B0", INK, 2.4)
            for i in range(8):
                a = math.radians(roll + i * 45)
                r.line([(wx, -44), (wx + 35 * math.cos(a), -44 + 35 * math.sin(a))], "#D9A82E", 3.2)
            r.dot(wx, -44, 8, "#FFD21F")
            r.dot(wx, -44, 3.4, "#C99A25")
        r.rrect(-122, -88, 122, -62, 10, "#E8A21E", INK, 3.4)                             # the underbody
        r.ell(0, -126, 112, 72, "#FFC83D", INK, 3.6)                                      # the round cab
        for dx in (-84, -50, 50, 84):
            r.arc(dx, -126, 14 + abs(dx) * 0.06, 64, 100 if dx < 0 else -80, 260 if dx < 0 else 80, "#E8A21E", 3)
        r.ell(-48, -158, 18, 26, "#FFE98A", None, ang=22)
        r.rrect(-40, -168, 40, -96, 22, "#BFE6FF", INK, 3.2)                              # the window and its curtains
        r.poly([(-40, -168), (-18, -168), (-26, -120), (-40, -100)], "#FF8FB8", INK, 2.4)
        r.poly([(40, -168), (18, -168), (26, -120), (40, -100)], "#FF8FB8", INK, 2.4)
        r.ell(-24, -148, 5, 12, "#FFFFFF", None, ang=12)
        r.rrect(-8, -208, 10, -188, 4, "#4E8A2E", INK, 2.8)                               # the stalk is still there, with a star on top
        r.poly(star_pts(0, -222, 20, 8), "#FFD21F", INK, 2.6)
        r.dot(106, -118, 6, "#FFFFFF")
        r.rrect(96, -110, 130, -98, 5, "#E8A21E", INK, 2.4)
    return r


@prop
def clock(c, x, y, k, t, st):
    """A tall grandfather clock with a pendulum. (x, y) = the middle of its base. st: n 0..12 = the numeral that glows (the clock is striking),
    h / mn = the time (h = 12, mn = 0 is midnight; mn may run past 60), swing 0..1 = the pendulum swings, hit 0..1 = the clock shivers after a bong."""
    n = int(round(clamp(st.get("n", 0.0), 0, 12)))
    h, mn, swing, hit = st.get("h", 12.0), st.get("mn", 0.0), clamp(st.get("swing", 1.0)), clamp(st.get("hit", 0.0))
    r = Rig(c, x + math.sin(t * 55.0) * 3.0 * hit * k, y, k)
    _tint(c, _ellipse_world(r, 0, 4, 110, 14), "#000000", 0.20)
    wood, dark = "#8B5A2B", "#5E3A1A"
    r.rrect(-88, -64, 88, 0, 6, dark, INK, 3.4)                                           # the foot
    r.rrect(-70, -350, 70, -60, 6, wood, INK, 3.6)                                        # the long body
    r.rrect(-48, -300, 48, -112, 20, "#2B1B10", INK, 3)                                   # the pendulum window
    pa = math.radians(math.sin(t * 3.0) * 13.0 * swing)
    px, py = 0 + math.sin(pa) * 150, -290 + math.cos(pa) * 150
    r.line([(0, -290), (px, py)], "#D9A82E", 4)
    r.ell(px, py, 25, 25, "#FFD21F", INK, 3)
    r.ell(px - 6, py - 7, 8, 8, "#FFF3B0", None)
    r.rrect(-96, -470, 96, -340, 14, wood, INK, 3.6)                                      # the head
    r.poly([(-100, -468), (100, -468), (70, -510), (-70, -510)], dark, INK, 3.4)
    r.poly(star_pts(0, -532, 22, 9), "#FFD21F", INK, 2.6)
    cx_, cy_ = 0, -404
    r.ell(cx_, cy_, 78, 78, "#D9A82E", INK, 3.6)                                          # the face
    r.ell(cx_, cy_, 68, 68, "#FFF8E6", INK, 2.4)
    for i in range(1, 13):
        a = math.radians(i * 30 - 90)
        nx, ny = cx_ + 50 * math.cos(a), cy_ + 50 * math.sin(a)
        if i == n:
            pulse = 1.0 + 0.18 * math.sin(t * 16.0)
            r.ell(nx, ny, 24 * pulse, 24 * pulse, "#FFE27A", INK, 3)
            c.text(*r.P(nx, ny + 1), str(i), 30 * k, "#C9314D", stroke=2 * k, stroke_fill="#FFFFFF")
        else:
            c.text(*r.P(nx, ny + 1), str(i), 21 * k, "#3A2316")
    ha, ma = math.radians(((h + mn / 60.0) % 12.0) * 30.0), math.radians((mn % 60.0) * 6.0)
    r.line([(cx_, cy_), (cx_ + 34 * math.sin(ha), cy_ - 34 * math.cos(ha))], INK, 9)
    r.line([(cx_, cy_), (cx_ + 34 * math.sin(ha), cy_ - 34 * math.cos(ha))], "#3A2316", 5.4)
    r.line([(cx_, cy_), (cx_ + 52 * math.sin(ma), cy_ - 52 * math.cos(ma))], INK, 7)
    r.line([(cx_, cy_), (cx_ + 52 * math.sin(ma), cy_ - 52 * math.cos(ma))], "#3A2316", 3.6)
    r.dot(cx_, cy_, 6.5, "#D9A82E")
    return r


@prop
def slipper(c, x, y, k, t, st):
    """A lost glass slipper lying on the ground, twinkling. (x, y) = the middle of its base. st: shine 0..1 (default 1)."""
    shine = clamp(st.get("shine", 1.0))
    r = Rig(c, x, y, k)
    _tint(c, _ellipse_world(r, 0, 3, 60, 8), "#000000", 0.2)
    if shine > 0.02:
        pulse = 1.0 + 0.1 * math.sin(t * 5.0)
        for i in range(3):
            rr = (46 + 22 * i) * pulse
            _tint(c, _ellipse_world(r, 0, -26, rr, rr * 0.7, 30), "#FFF3B0", 0.12 * shine)
    sh_pts = [(-30, 0), (-31, -26), (-24, -37), (-11, -35), (-5, -23), (9, -17), (25, -14), (36, -8), (38, 0)]
    r.rrect(-38, -4, -24, 10, 3, "#BFE6FF", INK, 2.6)
    r.poly([(1.4 * px + 4, 1.4 * py - 2) for px, py in sh_pts], "#BFE6FF", INK, 3)
    r.poly([(1.4 * px + 4, 1.4 * py - 2) for px, py in ((-28, -4), (-29, -24), (-23, -33), (-14, -30), (-17, -12))], "#E6F6FF", None)
    r.dot(40, -18, 4.6, "#FF8FB8")
    for i in range(3):
        ph = (t * 0.9 + i * 0.33) % 1.0
        r.poly(star_pts(-28 + i * 36, -64 - 20 * ph, 11 * shine * (1.0 - abs(ph - 0.5)), 4, 4), "#FFFFFF", None)
    return r


# ================================================================================================ effects
@fx
def wind(c, s, x, y, dt, dir=1, power=1.0, dx=0, **_):
    """Huff-and-puff: wavy white streaks, bits of straw and leaves blowing along."""
    x = x + dir * dx
    n = 7
    for i in range(n):
        ph = (dt * 1.6 + i * 0.37) % 1.0
        yy = y + (i - n / 2) * 24 * power + math.sin(dt * 5 + i) * 6
        x0 = x + dir * ph * 150
        pts = [(x0 + dir * j * 24, yy + math.sin(j * 0.9 + dt * 9 + i) * 9) for j in range(0, 10)]
        c.line(pts, "#D6EEFF", 7)
        c.line(pts, "#FFFFFF", 3.4)
    for i in range(6):
        ph = (dt * 0.9 + i * 0.19) % 1.0
        bx = x + dir * (40 + ph * 520)
        by = y - 60 + math.sin(ph * 12 + i * 2) * 50 + i * 12
        c.ellipse(bx, by, 7, 3.2, fill=["#F4CF63", "#7ED47A", "#E8A33A"][i % 3])


@fx
def dust(c, s, x, y, dt, size=1.0, **_):
    if dt > 0.9:
        return
    u = dt / 0.9
    for i in range(7):
        a = i * 0.9 + 0.3
        px = x + math.cos(a) * (14 + 70 * u) * size
        py = y - 8 - abs(math.sin(a)) * (10 + 38 * u) * size
        rr = (9 + 22 * u) * (1 - u * 0.6) * size
        c.ellipse(px, py, rr, rr, fill="#FFF8EA", outline="#D9CBB0", width=2)


@fx
def sparkle(c, s, x, y, dt, r=90, n=7, **_):
    for i in range(n):
        ph = (dt * 1.4 + i / n) % 1.0
        a = i * 2.4
        px, py = x + math.cos(a) * r * (0.4 + 0.6 * ((i * 37) % 10) / 10), y + math.sin(a) * r * 0.8
        sz = 14 * math.sin(ph * math.pi)
        if sz > 1:
            D.star(c, px, py, sz, "#FFE066")
            D.star(c, px, py, sz * 0.5, "#FFFFFF")


@fx
def hearts(c, s, x, y, dt, **_):
    for i in range(4):
        ph = (dt * 0.7 + i * 0.25) % 1.0
        D.heart(c, x + math.sin(i * 2.1 + ph * 4) * 36, y - ph * 110, 10 + 8 * math.sin(ph * math.pi), "#FF5C8A")


@fx
def zzz(c, s, x, y, dt, **_):
    for i in range(3):
        ph = (dt * 0.5 + i / 3) % 1.0
        c.text(x + ph * 46 + i * 6, y - ph * 90, "Z", (20 + 22 * ph) * 1.0, "#6B7BFF", stroke=3, stroke_fill="#FFFFFF")


@fx
def steam(c, s, x, y, dt, **_):
    for i in range(3):
        ph = (dt * 0.55 + i / 3) % 1.0
        c.ellipse(x + math.sin(ph * 7 + i) * 8, y - ph * 70, 7 + 10 * ph, 7 + 10 * ph, fill=mix("#FFFFFF", "#DCE8F4", ph), outline="#E6EEF6", width=1.5)


@fx
def sweat(c, s, x, y, dt, **_):
    for i, (dx, dy) in enumerate(((-52, -18), (54, -26), (-40, -50))):
        ph = (dt * 1.2 + i * 0.33) % 1.0
        if ph < 0.7:
            px, py = x + dx, y + dy + ph * 38
            c.poly([(px, py - 15), (px - 7, py + 2), (px, py + 8), (px + 7, py + 2)], fill="#8FD3FF", outline="#3E8EDE", width=1.6)


@fx
def dizzy(c, s, x, y, dt, **_):
    for i in range(3):
        a = dt * 4 + i * 2.1
        D.star(c, x + math.cos(a) * 62, y + math.sin(a) * 14, 12, "#FFD21F")


@fx
def notes(c, s, x, y, dt, **_):
    """Floating music notes, drawn with shapes (the note glyph is missing from the fonts)."""
    for i in range(3):
        ph = (dt * 0.6 + i / 3) % 1.0
        px, py = x + math.sin(i * 2 + ph * 5) * 26 + i * 20, y - ph * 100
        col = ["#FF5C8A", "#3E8EDE", "#3DB54A"][i]
        c.line([(px + 9, py), (px + 9, py - 32)], "#FFFFFF", 9)
        c.poly([(px + 9, py - 33), (px + 27, py - 23), (px + 25, py - 10), (px + 9, py - 19)], fill="#FFFFFF", outline="#FFFFFF", width=3)
        c.ellipse(px, py, 12.5, 9.5, fill="#FFFFFF")
        c.line([(px + 9, py), (px + 9, py - 32)], col, 4)
        c.poly([(px + 9, py - 32), (px + 24, py - 23), (px + 22, py - 13), (px + 9, py - 20)], fill=col)
        c.ellipse(px, py, 9.5, 6.5, fill=col)


@fx
def splash(c, s, x, y, dt, **_):
    if dt > 1.0:
        return
    u = dt
    for i in range(9):
        a = math.radians(200 + i * 17)
        px = x + math.cos(a) * 120 * u
        py = y + math.sin(a) * 170 * u + 260 * u * u
        rr = 9 * (1 - u * 0.5)
        c.ellipse(px, py, rr, rr * 1.3, fill="#8FD3FF", outline="#3E8EDE", width=2)
    c.ellipse(x, y + 30, 56 + 60 * u, 12 + 10 * u, fill="#BFE6FF", outline="#3E8EDE", width=2) if u < 0.7 else None


@fx
def speed(c, s, x, y, dt, dir=1, **_):
    for i in range(5):
        ph = (dt * 3 + i * 0.21) % 1.0
        yy = y - 120 + i * 40
        x0 = x - dir * (40 + ph * 40 + i * 6)
        c.line([(x0, yy), (x0 - dir * (50 + 30 * ph), yy)], "#FFFFFF", 5)


@fx
def burst(c, s, x, y, dt, text="CRASH!", color="#FF5C3A", size=1.0, **_):
    u = clamp(dt / 0.25)
    sc = ease_out_back(u) * (1.0 + 0.04 * math.sin(dt * 18)) * size
    if dt > 1.5:
        sc *= clamp(1 - (dt - 1.5) / 0.25)
    if sc <= 0.02:
        return
    pts = []
    for i in range(28):
        rr = (96 if i % 2 == 0 else 62) * sc
        a = math.pi * 2 * i / 28 + 0.1
        pts.append((x + math.cos(a) * rr * 1.5, y + math.sin(a) * rr))
    c.poly(pts, fill="#FFE066", outline=INK, width=4)
    pts2 = [(x + (px - x) * 0.82, y + (py - y) * 0.82) for px, py in pts]
    c.poly(pts2, fill=color)
    c.text(x, y, text, 48 * sc, "#FFFFFF", stroke=5 * sc, stroke_fill=INK)


@fx
def mark(c, s, x, y, dt, text="?", color="#FF5C3A", **_):
    u = clamp(dt / 0.25)
    sc = ease_out_back(u)
    if sc <= 0.02:
        return
    c.ellipse(x, y, 30 * sc, 30 * sc, fill="#FFFFFF", outline=INK, width=3)
    c.text(x, y + 2, text, 46 * sc, color, stroke=0)


@fx
def confetti(c, s, x, y, dt, **_):
    rng = random.Random(5)
    for i in range(70):
        sx = rng.uniform(0, 1280)
        vy = rng.uniform(90, 200)
        py = -30 + ((dt * vy + rng.uniform(0, 700)) % 800)
        px = sx + math.sin(dt * 3 + i) * 24
        ang = dt * rng.uniform(2, 6) + i
        w, h = 14, 8
        pts = [(px + math.cos(ang) * w - math.sin(ang) * h, py + math.sin(ang) * w + math.cos(ang) * h),
               (px - math.cos(ang) * w - math.sin(ang) * h, py - math.sin(ang) * w + math.cos(ang) * h),
               (px - math.cos(ang) * w + math.sin(ang) * h, py - math.sin(ang) * w - math.cos(ang) * h),
               (px + math.cos(ang) * w + math.sin(ang) * h, py + math.sin(ang) * w - math.cos(ang) * h)]
        s.poly(pts, fill=["#FF5C8A", "#FFD21F", "#3E8EDE", "#3DB54A", "#B58CFF", "#FF9A3D"][i % 6])


@fx
def leaves(c, s, x, y, dt, **_):
    rng = random.Random(8)
    for i in range(10):
        sx = rng.uniform(0, 1280)
        vy = rng.uniform(40, 80)
        py = -20 + ((dt * vy + rng.uniform(0, 700)) % 760)
        px = sx + math.sin(dt * 1.6 + i) * 40
        s.ellipse(px, py, 11, 5, fill=["#E8A33A", "#D9783A", "#7ED47A"][i % 3])


@fx
def glow(c, s, x, y, dt, r=60, color="#FFF3A8", **_):
    p = 1.0 + 0.08 * math.sin(dt * 5)
    for i, a in enumerate((1.8, 1.4, 1.0)):
        c.ellipse(x, y, r * a * p, r * a * p, fill=mix("#FFFFFF", color, 0.25 + 0.3 * i))


@fx
def poof(c, s, x, y, dt, r=240, color="#FFF2A8", **_):
    """A magic flash: a soft golden burst and a ring of white stars that swells and fades away (somebody changes inside it)."""
    if dt > 1.1:
        return
    u = dt / 1.1
    a = (1.0 - u) ** 1.4
    rad = r * (0.45 + 0.75 * ease(u))
    for i, f in enumerate((1.0, 0.72, 0.46)):
        pts = [(x + rad * f * math.cos(2 * math.pi * j / 32), y + rad * f * 0.95 * math.sin(2 * math.pi * j / 32)) for j in range(32)]
        _tint(c, pts, color if i < 2 else "#FFFFFF", min(0.95, 0.5 * a * (1 + i * 0.6)))
    for i in range(10):
        ang = i * 0.628 + 0.4
        d = rad * (0.5 + 0.65 * u)
        D.star(c, x + d * math.cos(ang), y + d * 0.95 * math.sin(ang), 15 * a + 3, "#FFFFFF")


# ---- full-screen cards (drawn on the screen canvas `s`, not in the world)
def _fit_text(s, x, y, text, size, fill, max_w, stroke=0, stroke_fill=None):
    return s.text_fit(x, y, text, size, fill, max_w, stroke=stroke, stroke_fill=stroke_fill)


@fx
def title(c, s, x, y, dt, lines=("THE STORY",), sub="Story Time with Bibi Buzz TV", top=88, size=124, gap=132, pill=38, still=False, **_):
    """The poster title of a tale. top = centre of the pill, size / gap = height and spacing of the lines; still = no animation (covers)."""
    u = 1.0 if still else ease_out_back(clamp(dt / 0.8))
    if u <= 0.02:
        return
    top = top - (1 - u) * 260
    ph = pill * 1.0
    s.rrect(220, top - ph - 2, 1060, top + ph - 2, 30, fill="#FF5C8A", outline=D.INK, width=5)
    s.text(640, top, D.upper(sub), 38 if pill >= 38 else 30, "#FFFFFF", stroke=0)
    cols = ["#FFD21F", "#FFFFFF", "#9BE8FF"]
    base = top + (70 if pill >= 38 else 52)
    for i, line in enumerate(lines):
        yy = base + size * 0.53 + i * gap
        sc = 1.0 if still else 0.96 + 0.03 * math.sin(dt * 3 + i)
        _fit_text(s, 640, yy + 6 * sc, line, size * sc, D.INK, 1120, stroke=size * 0.113, stroke_fill=D.INK)
        _fit_text(s, 640, yy, line, size * sc, cols[i % 3], 1120, stroke=size * 0.073, stroke_fill=D.INK)


@fx
def the_end(c, s, x, y, dt, text="The End", sub="", **_):
    u = ease_out_back(clamp(dt / 0.8))
    if u <= 0.02:
        return
    s.text(640, 250, text, 170 * u, D.INK, stroke=16, stroke_fill=D.INK)
    s.text(640, 244, text, 170 * u, "#FFD21F", stroke=11, stroke_fill=D.INK)
    for i in range(7):
        a = i * 0.9 + dt * 0.8
        D.star(s, 640 + math.cos(a) * 420, 250 + math.sin(a * 1.3) * 90, 18 + 6 * math.sin(dt * 4 + i), ["#FFD21F", "#FF5C8A", "#9BE8FF"][i % 3])
    if sub:
        s.rrect(190, 372, 1090, 452, 38, fill="#FFFFFF", outline=D.INK, width=5)
        _fit_text(s, 640, 412, sub, 44, D.INK, 840)


@fx
def cta(c, s, x, y, dt, like=2.3, sub=3.2, k=1.0, **_):
    """The "Like" / "Subscribe" card of the last scene (YouTube turns its own end screens and subscribe watermark off on kids videos):
    two buttons around y, a pointer presses Like at `like` seconds and Subscribe at `sub` seconds after the effect started."""
    D.cta(s, 640, y, dt, k, like, sub)


@fx
def caption(c, s, x, y, dt, text="", color="#FFFFFF", **_):
    u = clamp(dt / 0.35)
    if u <= 0.02:
        return
    size = 46
    w = min(1180, s.text_width(text, size) + 90)
    yy = 650 + (1 - ease(u)) * 90
    s.rrect(640 - w / 2 + 4, yy - 38 + 6, 640 + w / 2 + 4, yy + 38 + 6, 36, fill="#00000030")
    s.rrect(640 - w / 2, yy - 38, 640 + w / 2, yy + 38, 36, fill="#FFF3A8", outline=D.INK, width=4.5)
    _fit_text(s, 640, yy + 2, text, size, D.INK, w - 70)
