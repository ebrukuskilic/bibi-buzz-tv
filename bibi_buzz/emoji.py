"""Emoji sprites (Google Noto Color Emoji, Apache-2.0) used as the pictures in the lessons.

PNGs (512 px) are downloaded once from the noto-emoji repository into assets/emoji/ and cached.
For offline layout tests set BIBI_PLACEHOLDER=1: missing sprites are replaced by coloured blobs.
"""
import hashlib
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw

from .draw import ROOT, SS, font

DIR = os.path.join(ROOT, "assets", "emoji")
URLS = [  # glossy 3D set first, flat 2D set as a fallback (both contain the same emoji)
    "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/3D/png/512/emoji_u{c}.png",
    "https://cdn.jsdelivr.net/gh/googlefonts/noto-emoji@main/3D/png/512/emoji_u{c}.png",
    "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/2D/png/512/emoji_u{c}.png",
]
_base = {}      # code -> square RGBA sprite (512)
_scaled = {}    # (code, px) -> resized sprite


def path(code):
    return os.path.join(DIR, code + ".png")


def fetch(code):
    p = path(code)
    if os.path.exists(p):
        return True
    os.makedirs(DIR, exist_ok=True)
    for attempt in range(3):
        for u in URLS:
            try:
                req = urllib.request.Request(u.format(c=code), headers={"User-Agent": "bibi-buzz-tv"})
                data = urllib.request.urlopen(req, timeout=30).read()
                if data[:4] == b"\x89PNG":
                    with open(p + ".part", "wb") as f:
                        f.write(data)
                    os.replace(p + ".part", p)
                    return True
            except Exception:
                pass
    return False


def prefetch(codes):
    """Downloads every needed sprite; returns the list of codes that could not be fetched."""
    codes = sorted(set(codes))
    if os.environ.get("BIBI_PLACEHOLDER"):
        return []
    with ThreadPoolExecutor(8) as ex:
        ok = list(ex.map(fetch, codes))
    return [c for c, good in zip(codes, ok) if not good]


def _placeholder(code):
    h = int(hashlib.md5(code.encode()).hexdigest()[:6], 16)
    col = (90 + (h >> 16) % 140, 90 + (h >> 8) % 140, 90 + h % 140, 255)
    im = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([30, 30, 482, 482], fill=col, outline=(60, 40, 20, 255), width=14)
    d.text((256, 256), code[-5:], font=font(75), fill=(255, 255, 255, 255), anchor="mm")
    return im


def _normalise(im):
    """Crop transparent margins and centre in a square so every picture fills its box alike."""
    im = im.convert("RGBA")
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    s = max(im.size)
    sq = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sq.paste(im, ((s - im.width) // 2, (s - im.height) // 2), im)
    return sq


def base(code):
    if code not in _base:
        p = path(code)
        if os.path.exists(p):
            _base[code] = _normalise(Image.open(p))
        elif os.environ.get("BIBI_PLACEHOLDER"):
            _base[code] = _normalise(_placeholder(code))
        elif code != "2b50" and os.path.exists(path("2b50")):
            print("[emoji] sprite %s is missing - drawing a star instead" % code, flush=True)
            _base[code] = base("2b50")
        else:
            raise FileNotFoundError("emoji sprite %s is missing (run prefetch)" % code)
    return _base[code]


def scaled(code, size):
    """Sprite resized so that its long side is `size` layout pixels (x SS for the canvas)."""
    px = max(2, int(round(size * SS / 4.0)) * 4)
    key = (code, px)
    im = _scaled.get(key)
    if im is None:
        if len(_scaled) > 600:
            _scaled.clear()
        src = base(code)
        im = src.resize((px, px), Image.LANCZOS)
        _scaled[key] = im
    return im
