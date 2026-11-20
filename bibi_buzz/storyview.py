"""A camera over a Canvas: everything drawn in WORLD coordinates is panned / zoomed on the way to the screen."""
from . import draw as D


class View:
    def __init__(self, canvas, cx=640.0, cy=360.0, z=1.0):
        self.c, self.cx, self.cy, self.z = canvas, cx, cy, z
        self.w, self.h = canvas.w, canvas.h

    def X(self, x):
        return (x - self.cx) * self.z + 640.0

    def Y(self, y):
        return (y - self.cy) * self.z + 360.0

    def P(self, x, y):
        return self.X(x), self.Y(y)

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, width=0):
        z = self.z
        self.c.ellipse(self.X(cx), self.Y(cy), rx * z, ry * z, fill, outline, width * z)

    def poly(self, pts, fill=None, outline=None, width=0):
        X, Y = self.X, self.Y
        self.c.poly([(X(x), Y(y)) for x, y in pts], fill, outline, width * self.z)

    def rect(self, x0, y0, x1, y1, fill):
        self.c.rect(self.X(x0), self.Y(y0), self.X(x1), self.Y(y1), fill)

    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, width=0):
        self.c.rrect(self.X(x0), self.Y(y0), self.X(x1), self.Y(y1), r * self.z, fill, outline, width * self.z)

    def line(self, pts, fill, width):
        X, Y = self.X, self.Y
        self.c.line([(X(x), Y(y)) for x, y in pts], fill, width * self.z)

    def arc(self, cx, cy, rx, ry, a0, a1, fill, width):
        z = self.z
        self.c.arc(self.X(cx), self.Y(cy), rx * z, ry * z, a0, a1, fill, width * z)

    def text(self, x, y, s, size, fill, anchor="mm", stroke=0, stroke_fill=None):
        z = self.z
        self.c.text(self.X(x), self.Y(y), s, size * z, fill, anchor=anchor, stroke=stroke * z, stroke_fill=stroke_fill)
