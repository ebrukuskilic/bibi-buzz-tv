#!/usr/bin/env python3
"""Test render of one fairy tale in one language, or of lessons - nothing of the daily pipeline is touched.

  python tools/test_tale.py three-little-pigs tr --out out/test --seconds 40
  python tools/test_tale.py d003-L1,d003-L4 en --out out/test --seconds 0 --tail 22      # lessons: ids of curriculum.plan(day)

A tale gets <out>/<key>-<lang>-cover.jpg, <key>-<lang>-sheet.png (two frames of every scene), <key>-<lang>.txt (the lines with their
voice and duration, the chapters, the metadata) and a short clip <key>-<lang>-clip.mp4 with real voices (the first --seconds seconds).
It uses the real text-to-speech voices, so it also shows whether a voice of the language works on the machine.
A lesson (dNNN-L1 ... dNNN-S5) gets <out>/<id>-sheet.png and <id>.txt (every segment with its cues: time, length, text).
With --tail 22 it also writes <name>-tail.mp4: the last 22 seconds (the end and the "Like / Subscribe" card, to check that the
pointer clicks on the words).
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bibi_buzz import curriculum as CU      # noqa: E402
from bibi_buzz import draw as D             # noqa: E402
from bibi_buzz import story as SY           # noqa: E402
from bibi_buzz import tales as TL           # noqa: E402


def test_tale(a, ffmpeg, key):
    base = os.path.join(a.out, f"{key}-{a.lang}")
    t = TL.build(key, a.lang)
    t.id = f"test-{key}-{a.lang}"
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
        f.write("sync problems: %s\nduration %.1fs, voice %.1fs\n\n" % ("none" if not problems else "\n  " + "\n  ".join(str(p) for p in problems),
                                                                       st["duration"], st["voice_seconds"]))
        for sc in t.scenes:
            for b in sc.beats:
                if b.text:
                    f.write("%6.1fs  %-5s %-22s %s\n" % (sc.t_start + b.v0, b.who or "nar", t.voice_of(b.voice or b.who)[0], b.text))
        f.write("\n" + chapters_text + "\n\n" + json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    print("voices used:", sorted({t.voice_of(b.voice or b.who)[0] for sc in t.scenes for b in sc.beats if b.text}), flush=True)

    if a.seconds > 0:
        info = SY.render(t, base + "-clip.mp4", ffmpeg, a.cache, t_range=(0.0, a.seconds), quiet=True)
        print("clip:", info["file"], "(first %.0f s, with the real voices) rendered in %ss" % (a.seconds, info["seconds_to_render"]), flush=True)
    if a.tail > 0:
        info = SY.render(t, base + "-tail.mp4", ffmpeg, a.cache, t_range=(max(0.0, t.duration - a.tail), t.duration), quiet=True)
        print("tail clip:", info["file"], "(the last %.0f s, with the real voices) rendered in %ss" % (a.tail, info["seconds_to_render"]), flush=True)


def render_lesson_range(les, clips, path, ffmpeg, t0, t1):
    """A piece (t0..t1 seconds) of a lesson with its real sound: only those frames are drawn."""
    from bibi_buzz import music as MU
    from bibi_buzz import stage as ST
    from bibi_buzz import voice as VO
    mix = MU.mix(les, clips)
    wav = path + ".wav"
    MU.write_wav(wav, mix[int(t0 * VO.SR):int(t1 * VO.SR)])
    L = ST.layout(les.fmt)
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{L.w}x{L.h}", "-r", str(ST.FPS), "-i", "-",
           "-i", wav, "-map", "0:v", "-map", "1:a", "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
           "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "160k", "-t", "%.3f" % (t1 - t0), "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(t0 * ST.FPS), int(math.ceil(t1 * ST.FPS))):
        proc.stdin.write(ST.render_frame(les, i / ST.FPS).tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed for " + path)
    os.remove(wav)


def test_lesson(a, ffmpeg, lid):
    from bibi_buzz import emoji as E
    from bibi_buzz import pipeline as PL
    day = int(lid[1:4])
    les = next((l for l in CU.plan(day) if l.id == lid), None)
    if les is None:
        sys.exit("no lesson %s on day %d (ids: %s)" % (lid, day, ", ".join(l.id for l in CU.plan(day))))
    D.set_language("en")
    base = os.path.join(a.out, lid)
    clips = PL.prepare(les, ffmpeg, a.cache)                                # the real voice
    problems, st = PL.sync_report(les)
    print(lid, les.title, "| sync problems:", problems or "none", "| duration %.1fs, bpm %s, voice %.1fs" % (st["duration"], les.bpm, st["voice_seconds"]), flush=True)
    missing = E.prefetch(les.codes())
    if missing:
        print("[emoji] could not download %d sprites: %s" % (len(missing), ", ".join(missing)), flush=True)
    try:
        PL.contact_sheet(les, base + "-sheet.png")
    except Exception as e:                                                  # (e.g. an emoji sprite that could not be downloaded)
        print("contact sheet failed:", repr(e), flush=True)
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write("%s  %s\nbpm %s  beat %.3f s  duration %.2f s\n" % (lid, les.title, les.bpm, les.beat, les.duration))
        for seg in les.segs:
            f.write("\n-- %s  %.2f .. %.2f s\n" % (seg.kind, seg.t0, seg.t1))
            for c in seg.cues:
                if c.text:
                    f.write("%7.2fs  %5.2fs  %s\n" % (c.t, c.dur, c.text))
    if a.tail > 0:
        render_lesson_range(les, clips, base + "-tail.mp4", ffmpeg, max(0.0, les.duration - a.tail), les.duration)
        print("tail clip:", lid + "-tail.mp4", "(the last %.0f s, with the real voice)" % a.tail, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("key", help="a tale key (%s) or lesson ids like d003-L1,d003-L4" % ", ".join(sorted(TL.TALES)))
    ap.add_argument("lang", nargs="?", default="en", choices=["en", "tr"], help="language of a tale")
    ap.add_argument("--out", default="out/test")
    ap.add_argument("--seconds", type=float, default=40.0, help="length of the clip with real voices (0 = no clip; tales only)")
    ap.add_argument("--tail", type=float, default=0.0, help="also render the LAST n seconds (the end card) with real voices (0 = no)")
    ap.add_argument("--cache", default=os.path.join("out", "tts-cache"))
    a = ap.parse_args()

    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg = "ffmpeg"
    os.makedirs(a.out, exist_ok=True)
    for key in [k.strip() for k in a.key.split(",") if k.strip()]:
        if key in TL.TALES:
            test_tale(a, ffmpeg, key)
        elif re.fullmatch(r"d\d{3}-[LS]\d+", key):
            test_lesson(a, ffmpeg, key)
        else:
            sys.exit("unknown key %r: use a tale (%s) or a lesson id like d003-L1" % (key, ", ".join(sorted(TL.TALES))))


if __name__ == "__main__":
    main()
