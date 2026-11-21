"""Song videos: a sing-along with dancing friends, the words lighting up as they are sung.

A song (songs.py) is written like sheet music: sections made of lines, every line with its words (syllables joined by hyphens),
its notes ("C4 C4 G4:2") and its chords ("C:4 F:2 C:2").  Everything on the clock comes from the notes and the tempo, never from the
length of a voice clip, so voice, music and pictures cannot drift apart:

  - the music (songmusic.py) is played from the notes and chords,
  - the voice sings: every word is spoken by a text-to-speech voice and then moved onto its notes (singer.py, psola.py),
  - the pictures are made with the story engine (story.py): one scene per section, friends who hop on the beat and whose mouths move
    with the singing, and the words of the line light up syllable by syllable (the 'lyrics' effect below).
"""
import math
import re

import numpy as np
from PIL import Image, ImageDraw

from . import draw as D
from . import singer as SG
from . import songmusic as SM
from . import story as SY
from . import storyaudio as SA
from . import storyprops as PR
from . import voice as VO
from .story import Tale

SR = VO.SR
ARTICLES = ("a", "an", "the")
SING_VOICE = {"en": ("en-US-AnaNeural", "-10%", "+0Hz"), "tr": ("tr-TR-EmelNeural", "-10%", "+0Hz")}
SFX_ALLOWED = ("pop", "ding", "tada", "cheer", "fanfare", "sparkle")       # the picture's sound effects that a song keeps (not the boing of every hop)
MASTER_RMS = 0.15                                                            # every song is brought to this rms (about -16.5 LUFS, like the lessons and the tales)
LIMIT_KNEE, LIMIT_CEIL = 0.80, 0.95                                          # above the knee the few loudest peaks are rounded off, never above the ceiling


def soft_limit(x, knee=LIMIT_KNEE, ceil=LIMIT_CEIL):
    """Rounds off the peaks above `knee` smoothly (tanh), so that nothing exceeds `ceil` and the part below the knee stays as it is."""
    a = np.abs(x)
    over = a > knee
    if not over.any():
        return x
    y = np.array(x, dtype=np.float64)
    y[over] = np.sign(y[over]) * (knee + (ceil - knee) * np.tanh((a[over] - knee) / (ceil - knee)))
    return y


# ================================================================================================ the words of a line
def parse_lyric(text):
    """'Twin-kle twin-kle lit-tle star' -> [dict(syl=['Twin','kle'], speak='twinkle', plain='twinkle'), ...]
    A word may carry the way it is spoken: 'E+I+E+I+O=ee_eye_ee_eye_oh' ('_' is a space)."""
    words = []
    for tok in text.split():
        disp, _, spoken = tok.partition("=")
        parts = re.split(r"([-+])", disp)                                 # '-' = a syllable break, '+' = a syllable break that is written with a hyphen (E+I+E+I+O)
        syl = [parts[0]]
        for sep, piece in zip(parts[1::2], parts[2::2]):
            if sep == "+":
                syl[-1] += "-"
            syl.append(piece)
        speak = spoken.replace("_", " ") if spoken else re.sub(r"[^\w'’ ]", "", "".join(syl))
        words.append(dict(syl=syl, speak=speak, plain=re.sub(r"[^\w]", "", "".join(syl)).lower()))
    return words


def chunks_of(words, lang="en"):
    """The words grouped into what is spoken in one go: 'a' / 'an' / 'the' go together with the next word (alone they are read as letters)."""
    out, cur = [], []
    for w in words:
        cur.append(w)
        if lang == "en" and w["plain"] in ARTICLES and w is not words[-1]:
            continue
        out.append(cur)
        cur = []
    if cur:
        out.append(cur)
    return out


def n_syllables(words):
    return sum(len(w["syl"]) for w in words)


def _smooth(x, w):
    """Moving average of width w (samples), same length as x."""
    cs = np.concatenate([[0.0], np.cumsum(x)])
    n = len(x)
    i0 = np.clip(np.arange(n) - w // 2, 0, n)
    i1 = np.clip(np.arange(n) + w // 2 + 1, 0, n)
    return (cs[i1] - cs[i0]) / np.maximum(i1 - i0, 1)



# ================================================================================================ see-through shapes
# (the canvas of the story engine draws a colour with an alpha as a solid colour, so soft shapes are pasted through a mask)
_GLOW = {}


def alpha_rrect(s, x0, y0, x1, y1, r, color, alpha):
    """A rounded rectangle of `color` at `alpha` (0..1) over whatever is already drawn (screen units)."""
    a, b = s._p(x0, y0), s._p(x1, y1)
    bx0, by0 = max(0, int(a[0])), max(0, int(a[1]))
    bx1, by1 = min(s.img.width, int(b[0]) + 1), min(s.img.height, int(b[1]) + 1)
    if bx1 <= bx0 or by1 <= by0:
        return
    m = Image.new("L", (bx1 - bx0, by1 - by0), 0)
    ImageDraw.Draw(m).rounded_rectangle([a[0] - bx0, a[1] - by0, b[0] - bx0, b[1] - by0], radius=r * D.SS, fill=int(255 * alpha))
    s.img.paste(D.hex2rgb(color), (bx0, by0), m)


def glow_disc(s, x, y, r, color="#FFF2A0", alpha=0.7):
    """A soft round glow of radius r (screen units): brightest in the middle, fading smoothly to nothing at the edge."""
    if "m" not in _GLOW:
        n = 256
        yy, xx = np.mgrid[0:n, 0:n]
        d = np.hypot(xx - (n - 1) / 2.0, yy - (n - 1) / 2.0) / (n / 2.0)
        _GLOW["m"] = Image.fromarray((np.clip(1.0 - d, 0.0, 1.0) ** 1.6 * 255).astype("uint8"), "L")
    cx, cy = s._p(x, y)
    rp = r * D.SS
    size = int(2 * rp)
    if size < 4:
        return
    m = _GLOW["m"].resize((size, size), Image.BILINEAR)
    if alpha < 1.0:
        m = m.point(lambda v: int(v * alpha))
    s.img.paste(D.hex2rgb(color), (int(cx - rp), int(cy - rp)), m)


# ================================================================================================ screen effects
def _lyrics_fx(c, s, x, y, dt, syl=(), size=62, **_):
    """The words of one line, syllable by syllable: white = still to come, yellow = sung, pink and bouncing = sung right now.
    syl = [(text, start, end, space_after)] in seconds from the start of the effect."""
    if not syl:
        return
    u = min(1.0, dt / 0.3)
    u = 1 - (1 - u) ** 3
    gap = size * 0.28
    words, w = [], []
    for item in syl:
        w.append(item)
        if item[3]:
            words.append(w)
            w = []
    if w:
        words.append(w)
    rows, cur, w_cur = [], [], 0.0                                   # wrap into rows of at most ~1120 px
    for wd in words:
        ww = sum(s.text_width(t[0], size) for t in wd)
        if cur and w_cur + gap + ww > 1120:
            rows.append((cur, w_cur))
            cur, w_cur = [], 0.0
        w_cur += (gap if cur else 0.0) + ww
        cur.append(wd)
    if cur:
        rows.append((cur, w_cur))
    lh = size * 1.18
    top = y - (len(rows) - 1) * lh / 2 + (1 - u) * 46
    pw = max(r[1] for r in rows) + 84
    ph = lh * len(rows) + 28
    y0 = top - lh / 2 - 10
    alpha_rrect(s, x - pw / 2 + 4, y0 + 7, x + pw / 2 + 4, y0 + ph + 7, 34, "#000000", 0.28)
    alpha_rrect(s, x - pw / 2, y0, x + pw / 2, y0 + ph, 34, "#2A1F5C", 0.9)
    s.rrect(x - pw / 2, y0, x + pw / 2, y0 + ph, 34, outline="#FFFFFF", width=3.5)
    for ri, (rw, wtot) in enumerate(rows):
        px = x - wtot / 2
        cy = top + ri * lh
        for wd in rw:
            for (txt, t0, t1, _sp) in wd:
                tw = s.text_width(txt, size)
                if dt >= t1:
                    col, k, dy = "#FFD21F", 1.0, 0.0
                elif dt >= t0:
                    p = min(1.0, (dt - t0) / max(0.05, t1 - t0) * 1.4)
                    col, k, dy = "#FF8FB5", 1.0 + 0.14 * math.sin(math.pi * p), -9 * math.sin(math.pi * p)
                else:
                    col, k, dy = "#FFFFFF", 1.0, 0.0
                s.text(px + tw / 2, cy + dy, txt, size * k, D.INK, stroke=size * 0.17, stroke_fill=D.INK)
                s.text(px + tw / 2, cy + dy, txt, size * k, col, stroke=0)
                px += tw
            px += gap


def _star_face_fx(c, s, x, y, dt, r=95, pulses=(), tint="#FFD21F", **_):
    """A big friendly star with a face that swells and sparkles on every time in `pulses` (seconds from the start of the effect)."""
    pulse = 0.0
    for tp in pulses:
        d = dt - tp
        if 0.0 <= d < 0.55:
            pulse = max(pulse, math.sin(math.pi * d / 0.55) ** 0.8)
    pop = D.ease_out_back(min(1.0, dt / 0.5))
    if pop <= 0.02:
        return
    rr = r * pop * (1.0 + 0.22 * pulse + 0.025 * math.sin(dt * 3.1))
    ang = 7.0 * math.sin(dt * 1.6)
    glow_disc(s, x, y, rr * 2.7, "#FFF2A0", 0.75)
    pts = []
    for i in range(10):
        q = rr if i % 2 == 0 else rr * 0.5
        a = math.radians(ang - 90 + i * 36)
        pts.append((x + math.cos(a) * q, y + math.sin(a) * q))
    s.poly(pts, fill=tint, outline=D.INK, width=5.0)
    for sx in (-1, 1):                                               # eyes, cheeks, smile
        ex, ey = x + sx * 0.17 * rr, y - 0.02 * rr
        s.ellipse(ex, ey, 0.085 * rr, 0.1 * rr * (0.2 if (dt * 0.9) % 3.1 < 0.12 else 1.0), fill=D.INK)
        s.ellipse(ex + 0.025 * rr, ey - 0.035 * rr, 0.03 * rr, 0.03 * rr, fill="#FFFFFF")
        s.ellipse(x + sx * 0.3 * rr, y + 0.1 * rr, 0.075 * rr, 0.05 * rr, fill="#FF9DB0")
    s.arc(x, y + 0.04 * rr, 0.17 * rr, 0.13 * rr, 15, 165, D.INK, max(2.0, 0.045 * rr))
    for i in range(4):                                               # little sparkles circling the star
        ph = (dt * 0.9 + i / 4.0) % 1.0
        a = ph * 2 * math.pi
        sz = 9 + 8 * pulse
        D.star(s, x + math.cos(a) * rr * 1.45, y + math.sin(a) * rr * 1.25, sz * math.sin(ph * math.pi) + 2, "#FFFFFF")


PR.FX["lyrics"] = _lyrics_fx
PR.FX["star_face"] = _star_face_fx


# ================================================================================================ the song
class Song(Tale):
    """A sing-along video made from a song spec (songs.py) in one language.  It behaves like a Tale for make_batch / story.render."""
    kind = "tale"                 # (the batch maker draws, renders and describes a song like a tale)
    song = True

    def __init__(self, spec, lang="en"):
        cover = spec.get("cover")
        if cover and lang in cover:
            cover = cover[lang]
        Tale.__init__(self, "song-%s-%s" % (spec["id"], lang), spec["title"][lang], spec["blurb"][lang], spec["tags"][lang],
                      {"nar": ("", "", "")}, cover=cover, lang=lang)
        self.spec = spec
        self.bpm = spec["bpm"]
        self.nbeats = spec.get("beats", 4)
        self.beat = 60.0 / self.bpm
        self.shift = spec.get("shift", {}).get(lang, 0)
        self._line_env = {}
        self._env = {}
        self._voc = None
        self._chunk_cache = {}
        self._layout()

    def __getstate__(self):                                  # the big sound arrays do not travel to the worker processes
        d = dict(self.__dict__)
        d["_voc"] = None
        d["_chunk_cache"] = {}
        return d

    def T(self, text):                                       # a song has no translated script: its texts are written per language already
        return text

    @property
    def env(self):
        return self._env

    @env.setter
    def env(self, d):                                        # story.prepare() sets the envelopes of the voice clips; the lines of the song stay
        self._env = dict(d)
        self._env.update(self._line_env)

    # ---- the clock
    def _layout(self):
        """sections -> dict(name, mode, b0 (global beat), t0, beats, dur, items=[dict(key, b0 (in the section), t0, beats, notes, words, chunks, chords)])"""
        spec, lang, beat = self.spec, self.lang, self.beat
        self.sections = []
        gb = 0.0
        for si, f in enumerate(spec["form"]):
            sec = dict(f)
            sec["index"] = si
            sec["b0"] = gb
            sec["t0"] = gb * beat
            sing = f.get("mode", "sing") == "sing"
            b = f.get("pre", 0.0)
            items = []
            for lk in f["lines"]:
                L = spec["lines"][lk]
                notes = SM.parse_notes(L.get(lang + "_notes") or L["notes"])
                nb = sum(d for _, d in notes)
                words = parse_lyric(L[lang]) if sing else []
                sung = [m for m, _ in notes if m is not None]
                if words and n_syllables(words) != len(sung):
                    raise ValueError("song %s, line %s (%s): %d syllables but %d notes" % (spec["id"], lk, lang, n_syllables(words), len(sung)))
                chords = SM.parse_chords(L["chords"]) if L.get("chords") else []
                if chords and abs(sum(d for _, d in chords) - nb) > 1e-6:
                    raise ValueError("song %s, line %s: the chords last %g beats, the notes %g" % (spec["id"], lk, sum(d for _, d in chords), nb))
                items.append(dict(key=lk, b0=b, t0=sec["t0"] + b * beat, beats=nb, notes=notes, words=words, chords=chords,
                                  chunks=chunks_of(words, lang)))
                b += nb
            b += f.get("post", 0.0)
            sec["items"] = items
            sec["beats"] = b
            sec["dur"] = b * beat
            gb += b
            self.sections.append(sec)
        self.total = gb * beat

    def syllable_spans(self, sec, it):
        """[(word, syllable index, start, end)] of the sung syllables of a line, in seconds from the start of the scene."""
        out, t, k = [], it["t0"] - sec["t0"], 0
        flat = [(w, j) for w in it["words"] for j in range(len(w["syl"]))]
        for m, d in it["notes"]:
            if m is not None and k < len(flat):
                w, j = flat[k]
                out.append((w, j, t, t + d * self.beat))
                k += 1
            t += d * self.beat
        return out

    def line_times(self, sec, it):
        """[(syllable text, start, end, space_after)] in seconds from the start of the scene (for the lyrics effect)."""
        return [(w["syl"][j], a, b, j == len(w["syl"]) - 1) for (w, j, a, b) in self.syllable_spans(sec, it)]

    def word_spans(self, sec, it):
        """[(word as lower case letters, start, end)] of the sung words of a line, in seconds from the start of the scene."""
        res = {}
        for w, j, a, b in self.syllable_spans(sec, it):
            r = res.setdefault(id(w), [w["plain"], a, b])
            r[2] = b
        return [tuple(r) for r in res.values()]

    def beat_times(self, sec, step=1.0, first=0.0):
        """Times (seconds from the start of the scene) of every `step` beats of a section."""
        out, b = [], first
        while b < sec["beats"] - 1e-6:
            out.append(b * self.beat)
            b += step
        return out

    # ---- the voice
    def _voice(self):
        return self.spec.get("voice", {}).get(self.lang) or SING_VOICE[self.lang]

    def _item_of(self, chunk):
        v, r, p = self._voice()
        return (" ".join(w["speak"] for w in chunk), v, r, p, "")

    def voice_items(self):
        out = set()
        for sec in self.sections:
            for it in sec["items"]:
                for ch in it["chunks"]:
                    out.add(self._item_of(ch))
        return sorted(out)

    def _sing_all(self, clips):
        """The whole voice track (float array, the length of the song) and the span (start, end seconds) of every sung line."""
        n = int(round(self.total * SR)) + 2 * SR
        voc = np.zeros(n)
        spans = {}
        for sec in self.sections:
            if sec.get("mode", "sing") != "sing":
                continue
            for li, it in enumerate(sec["items"]):
                chunks, notes, accents = [], [], []
                for ch in it["chunks"]:
                    item = self._item_of(ch)
                    key = (item, n_syllables(ch))
                    if key not in self._chunk_cache:
                        self._chunk_cache[key] = SG.Chunk(clips[item], SR, n_syllables(ch))
                    chunks.append(self._chunk_cache[key])
                t = it["t0"]
                for m, d in it["notes"]:
                    if m is not None:
                        pos = (it["b0"] + (t - it["t0"]) / self.beat - sec.get("grid", 0.0)) % self.nbeats
                        accents.append(1.0 if abs(pos) < 1e-6 else 0.9)
                        notes.append((t, t + d * self.beat, m + self.shift))
                    t += d * self.beat
                out, t0 = SG.sing_line(chunks, notes, accents, SR)
                i0 = int(round(t0 * SR))
                if i0 < 0:
                    out, i0 = out[-i0:], 0
                voc[i0:i0 + len(out)] += out[:max(0, n - i0)]
                spans[(sec["index"], li)] = (i0 / SR, (i0 + len(out)) / SR)
        return voc, spans

    def _ensure(self, clips):
        if self._voc is None or self._voc[2] is not clips:
            voc, spans = self._sing_all(clips)
            self._voc = (voc, spans, clips)
        return self._voc

    def compile(self, clips):
        voc, spans, _c = self._ensure(clips)
        total = Tale.compile(self, clips)
        for sec, sc in zip(self.sections, self.scenes):
            if abs(sc.t_start - sec["t0"]) > 0.02:
                raise ValueError("scene %r starts at %.3f s but its music at %.3f s" % (sc.name, sc.t_start, sec["t0"]))
            for li in range(len(sec["items"])):
                if (sec["index"], li) not in spans:
                    continue
                a, b = spans[(sec["index"], li)]
                key = ("song", sec["index"], li)
                self._line_env[key] = SY.envelope(voc[int(a * SR):int(b * SR)])
                singers = getattr(sc, "singers", None)
                if singers:
                    who = singers[li % len(singers)]
                    for w in ([who] if isinstance(who, str) else list(who)):
                        sc.speech.append((a - sc.t_start, b - sc.t_start, w, key, ""))
        self._env.update(self._line_env)
        return total

    # ---- the music and the mix
    def music(self, n):
        buf = np.zeros(n + 4 * SR)
        beat, nb, sh = self.beat, self.nbeats, self.shift
        for sec in self.sections:
            st = sec.get("style", {})
            sing = sec.get("mode", "sing") == "sing"
            lead = st.get("lead", "xylo")
            lead_gain = st.get("lead_gain", 0.20 if sing else 0.40)
            lead_oct = st.get("lead_oct", 12)
            org = sec["b0"] + sec.get("grid", 0.0)                          # where the first bar line of the section is (grid = 1: a one-beat pickup comes first)
            for it in sec["items"]:
                t, notes = it["t0"], []
                for m, d in it["notes"]:
                    if m is not None:
                        notes.append((t, m + sh + lead_oct, d * beat))
                    t += d * beat
                if st.get("melody", True):
                    SM.play_lead(buf, notes, lead, lead_gain)
                segs, cum = [], 0.0
                for sym, d in it["chords"]:
                    segs.append((sym, sec["b0"] + it["b0"] + cum, d))
                    cum += d
                SM.play_chords(buf, segs, self.bpm, nb, st.get("chords", "strum"), st.get("chord_gain", 1.0), st.get("bass_gain", 0.7),
                               shift=sh, origin=org)
            SM.play_drums(buf, sec["b0"], sec["b0"] + sec["beats"], self.bpm, nb, st.get("drums", "light"), st.get("drum_gain", 1.0), origin=org)
        return buf[:n]

    def mix_audio(self, clips, voices=True):
        """The soundtrack of exactly self.duration seconds: the sung voice (with a little room around it), the band, and the few sound effects
        of the pictures; the band gets a bit quieter while somebody sings."""
        n = int(round(self.duration * SR))
        voc = self._ensure(clips)[0]
        voc = voc[:n] if len(voc) >= n else np.pad(voc, (0, n - len(voc)))
        if not voices:
            voc = voc * 0.0
        voc = SM.reverb(voc, wet=0.14)
        music = self.music(n)
        sm = _smooth(np.abs(voc), int(0.12 * SR))
        duck = 1.0 - 0.30 * np.clip(sm / 0.05, 0.0, 1.0)
        sfx = np.zeros(n + 4 * SR)
        for (t, name, g) in self.sfx_events:
            if name in SFX_ALLOWED:
                SA.add(sfx, t, SA._sfx(name), g * SA.SFX_GAIN.get(name, 0.5))
        out = music * duck * 0.62 + sfx[:n] * 0.6 + voc
        fade = int(1.2 * SR)
        out[-fade:] *= np.linspace(1, 0, fade)
        rms = float(np.sqrt(np.mean(out ** 2))) or 1.0                  # the same loudness for every song: a single high peak does not set it
        out = soft_limit(out * (MASTER_RMS / rms))
        self.mix_stats = dict(voice_rms=float(np.sqrt(np.mean(voc ** 2))), music_rms=float(np.sqrt(np.mean((music * duck * 0.62) ** 2))))
        return out.astype(np.float32)

    # ---- helpers for the scene recipes (songs.py)
    def scene_for(self, si, bg, mood="happy", drift=0.03, clouds=True, title=None):
        sec = self.sections[si]
        sc = self.scene(sec["name"], bg, mood=mood, title=title, drift=drift, clouds=clouds)
        sc.sec = sec
        sc.singers = []
        return sc

    def finish_scene(self, sc, singers=(), dancers=(), hop=1.0, hop_mode="wave", hop_from=0.0, side=0.0, extra=(),
                     sing_pose="talk", rest_pose="happy", lyrics_y=640, size=62, cam=None):
        """Adds what every verse needs and closes the scene: the lyrics of every line, the singers' poses, hops on the beat, a slow camera.
        singers: who sings, one entry per line in turn (an entry may be a tuple: all of them sing that line);
        dancers: friends who hop, `hop` = beats between two hops; hop_mode 'wave' = one after the other, 'all' = together;
        side = how far (px) the dancers step to the side and back every two hops (0 = they stay)."""
        sec = sc.sec
        beat = self.beat
        acts = list(extra)
        sc.singers = list(singers)
        items = sec["items"]
        if sec.get("mode", "sing") == "sing":
            lines = []
            for it in items:
                syl = self.line_times(sec, it)
                lines.append((syl, syl[0][1], syl[-1][2]) if syl else None)
            prev_hide = 0.05
            for li, ln in enumerate(lines):
                if ln is None:
                    continue
                syl, first, last = ln
                nxt = next((l2 for l2 in lines[li + 1:] if l2), None)
                hide = last + 0.5
                if nxt is not None:
                    hide = min(hide, nxt[1])
                show = max(prev_hide, first - 0.4)
                prev_hide = hide
                rel = [(t, a - show, b - show, sp) for (t, a, b, sp) in syl]
                acts.append(("fx", "lyrics", 640, lyrics_y, {"at": show, "dur": max(0.5, hide - show), "syl": rel, "size": size, "sfx": False}))
                if singers:
                    who = singers[li % len(singers)]
                    for w in ([who] if isinstance(who, str) else list(who)):
                        acts.append(("pose", w, sing_pose, {"at": first - 0.05}))
                        acts.append(("pose", w, rest_pose, {"at": last + 0.1}))
        if hop and dancers:
            k = 0
            b = hop_from
            while b * beat < sec["dur"] - 0.6:
                who_list = list(dancers) if hop_mode == "all" else [dancers[k % len(dancers)]]
                for who in who_list:
                    acts.append(("hop", who, {"at": b * beat}))
                    if side and k % 2 == 1 and b * beat + 0.9 * beat + 0.2 < sec["dur"] - 0.05:        # (a step that ends after the scene would stretch it: the music would run away)
                        d = sc.actors[who]
                        sgn = 1 if (list(dancers).index(who) % 2 == 0) else -1
                        acts.append(("move", who, d.x + sgn * side * (1 if (k // 2) % 2 == 0 else 0), d.y, {"at": b * beat, "dur": 0.45 * 2 * beat}))
                k += 1
                b += hop
        if cam:
            acts.append(("cam", cam[0], cam[1], cam[2], {"at": 0.0, "dur": sec["dur"]}))
        sc.wait(sec["dur"] - 0.05, *acts)
        return sc

    def lyrics_text(self):
        """The words of the song for the description: every sung block of lines once, a blank line between the blocks."""
        out, seen = [], set()
        for sec in self.sections:
            if sec.get("mode", "sing") != "sing":
                continue
            block = tuple(it["key"] for it in sec["items"])
            if block in seen:
                continue
            seen.add(block)
            out.append("\n".join(" ".join("".join(w["syl"]) for w in it["words"]) for it in sec["items"]))
        return "\n\n".join(out)
