#!/usr/bin/env python3
"""Test render of one fairy tale in one language - nothing of the daily pipeline is touched.

  python tools/test_tale.py three-little-pigs tr --out out/test --seconds 40

Writes <out>/<key>-<lang>-cover.jpg, <key>-<lang>-sheet.png (two frames of every scene), <key>-<lang>.txt (the lines with their voice
and duration, the chapters, the metadata) and a short clip <key>-<lang>-clip.mp4 with real voices (the first --seconds seconds).
It uses the real text-to-speech voices, so it also shows whether a voice of the language works on the machine.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bibi_buzz import curriculum as CU      # noqa: E402
from bibi_buzz import draw as D             # noqa: E402
from bibi_buzz import story as SY           # noqa: E402
from bibi_buzz import tales as TL           # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("key", choices=sorted(TL.TALES))
    ap.add_argument("lang", choices=["en", "tr"])
    ap.add_argument("--out", default="out/test")
    ap.add_argument("--seconds", type=float, default=40.0, help="length of the clip with real voices (0 = no clip)")
    ap.add_argument("--cache", default=os.path.join("out", "tts-cache"))
    a = ap.parse_args()

    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg = "ffmpeg"
    os.makedirs(a.out, exist_ok=True)
    base = os.path.join(a.out, f"{a.key}-{a.lang}")
    t = TL.build(a.key, a.lang)
    t.id = f"test-{a.key}-{a.lang}"
    D.set_language(a.lang)
    print("font:", D._face(), flush=True)

    SY.prepare(t, ffmpeg, a.cache)                                          # real voices (and the Turkish fallback when needed)
    problems, st = SY.sync_report(t)
    print("sync problems:", problems or "none", "| duration %.1fs, voice %.1fs" % (st["duration"], st["voice_seconds"]), flush=True)
    SY.make_cover(t, base + "-cover.jpg")
    SY.contact_sheet(t, base + "-sheet.png", cols=4, thumb=480, times=[sc.t_start + sc.dur * f for sc in t.scenes for f in (0.35, 0.75)])

    ch = SY.chapters(t)
    chapters_text = "\n".join(f"{SY.fmt_time(s)} {label}" for s, label in ch)
    meta = CU.metadata(t, chapters_text)
    with open(base + ".txt", "w", encoding="utf-8") as f:
        for sc in t.scenes:
            for b in sc.beats:
                if b.text:
                    f.write("%6.1fs  %-5s %-22s %s\n" % (sc.t_start + b.v0, b.who or "nar", t.voice_of(b.who)[0], b.text))
        f.write("\n" + chapters_text + "\n\n" + json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    print("voices used:", sorted({t.voice_of(b.who)[0] for sc in t.scenes for b in sc.beats if b.text}), flush=True)

    if a.seconds > 0:
        info = SY.render(t, base + "-clip.mp4", ffmpeg, a.cache, t_range=(0.0, a.seconds), quiet=True)
        print("clip:", info["file"], "(first %.0f s, with the real voices) rendered in %ss" % (a.seconds, info["seconds_to_render"]), flush=True)


if __name__ == "__main__":
    main()
