"""YouTube thumbnail: big Bibi, colourful flowers and 'COLORS!' text (1280x720)."""
from .draw import Canvas, bibi, flower, sun, cloud, big_label, star


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
