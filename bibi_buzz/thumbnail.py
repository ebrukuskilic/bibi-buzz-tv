"""YouTube thumbnails (1280x720).

make_thumbnail          episode 1: big Bibi, colourful flowers and 'COLORS!' text
make_lesson_thumbnail   every long lesson: big sticker title, three big pictures and Bibi
"""
from .draw import Canvas, bibi, pip, mo, lila, flower, sun, cloud, big_label, star


def make_thumbnail(bg, path):
    c = Canvas(bg.copy())
    sun(c, 0.0)
    cloud(c, 190, 110, 1.1)
    cloud(c, 700, 70, 1.3)
    cols = ["#E8383D", "#3E7BEA", "#FFC81E", "#FF8A1F"]
    for i, (x, h) in enumerate(((760, 330), (900, 400), (1040, 340), (1170, 290))):
        flower(c, x, 640, h, cols[i], 1.0, 0.8 + i, i)
    c.ellipse(330, 640, 190, 22, fill="#5DB04B")
    bibi(c, 330, 420, 2.5, 0.6, "open", look=(10, 0))
    big_label(c, "COLORS!", 760, 130, 150, "#FF4F86", 1.0)
    for x, y, r in ((560, 250, 20), (1230, 180, 24), (90, 250, 18)):
        star(c, x, y, r, "#FFF27A", 15)
    c.final().save(path)
    print("Thumbnail ->", path)


TITLE_COLORS = ["#FF4F86", "#3E8EDE", "#FF8A1F", "#9B59D0"]


def _title_lines(c, text, size, max_w):
    """Splits a title into one or two lines of (nearly) the same width."""
    words = text.split()
    if len(words) < 2 or (len(words) == 2 and c.text_width(text, size) <= max_w):
        return [text]
    cands = [[" ".join(words[:k]), " ".join(words[k:])] for k in range(1, len(words))]
    return min(cands, key=lambda ln: max(c.text_width(x, size) for x in ln))


def make_lesson_thumbnail(lesson, path):
    """Designed thumbnail of a long lesson, drawn from its title segment (title + first emoji pictures)."""
    import re
    from . import stage as ST
    from . import vibe as VB
    L = ST.layout("long")
    d = lesson.segs[0].data
    c = Canvas(ST.background(L, lesson.theme).copy(), w=L.w, h=L.h)
    ST.decor(c, L, lesson.theme, 0.0)
    ring_i = sum(ord(ch) for ch in lesson.id) % len(ST.RINGS)
    VB.ambient(c, L, lesson.theme, 8.0 + ring_i)                  # birds / fish / fireflies... caught in mid-air
    ST.chip(c, L)

    # Bibi's friends peek in from behind him
    pip(c, 64, 596, 0.95, 0.3, "smile", (6, -2))
    mo(c, 452, 604, 0.82, 0.3, "smile", (-6, -2))
    lila(c, 118, 178, 0.85, 0.5, "smile", (5, -2))

    # Bibi on the left, mouth open
    bibi(c, 250, 452, 2.25, 0.6, "open", look=(10, -2))

    # three big pictures, each on a sticker plate, with light rays behind them
    codes = list(d["codes"])[:3]
    n = len(codes)
    size, gap = 250, 252
    x0 = 862 - gap * (n - 1) / 2
    for k, code in enumerate(codes):
        VB.rays(c, x0 + k * gap, 530 + (-14 if k % 2 else 6), 110, 215, 1.0 + k * 2.0,
                ST.mix(ST.RINGS[(ring_i + k) % len(ST.RINGS)], "#FFFFFF", 0.66), n=12)
    for k, code in enumerate(codes):
        y = 530 + (-14 if k % 2 else 6)
        ST.icon(c, code, x0 + k * gap, y, size, ST.RINGS[(ring_i + k) % len(ST.RINGS)])

    # sticker title: one or two lines of the same size; "Part 2" becomes a small pill under it.
    # The whole block is centred in the band above the pictures (y 40..392).
    text = d["title"].upper()
    m = re.match(r"^(.*?)\s+PART\s+(\d+)$", text)
    main, part = (m.group(1), "PART " + m.group(2)) if m else (text, "")
    max_w = 740
    size_t = 156
    lines = _title_lines(c, main, size_t, max_w)
    if part and len(lines) == 2:
        size_t = 124
    while size_t > 70 and max(c.text_width(x, size_t) for x in lines) > max_w:
        size_t *= 0.95
    lh = size_t * 1.03
    pill_h = 68
    total = lh * len(lines) + (16 + pill_h if part else 0)
    top = 40 + (352 - total) / 2
    color = TITLE_COLORS[ring_i % len(TITLE_COLORS)]
    for i, line in enumerate(lines):
        ST.label(c, line, 862, top + (i + 0.5) * lh, size_t, color, 1.0, max_w + 40)
    if part:
        py = top + lh * len(lines) + 16 + pill_h / 2
        pw = c.text_width(part, 46) + 78
        c.rrect(862 - pw / 2, py - pill_h / 2, 862 + pw / 2, py + pill_h / 2, pill_h / 2, fill="#FFFFFF", outline=color, width=6)
        c.text(862, py + 1, part, 46, color)

    for x, y, r in ((520, 312, 20), (1236, 330, 22), (460, 130, 16)):
        star(c, x, y, r, "#FFF27A", 15)
    c.final().convert("RGB").save(path, quality=92)
    return path
