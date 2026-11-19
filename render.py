#!/usr/bin/env python3
"""Bibi Buzz TV - renders episode 1 to an MP4 (1280x720, 30 fps).

Every scene is encoded to its own file (out/scenes/NN_name.mp4), the files are joined with
ffmpeg's concat demuxer (-c copy) and the soundtrack is muxed in (-c:v copy). Changing one
scene therefore only re-renders that scene.

Examples
  python render.py                       # full episode  -> out/bibi_buzz_ep01.mp4
  python render.py --voice               # + child-friendly TTS voice-over (needs edge-tts + internet)
  python render.py --resume              # keep scene files that already exist (continue an interrupted render)
  python render.py --scenes color_red    # re-render only these scenes (comma separated), then re-join
  python render.py --stills              # PNG previews of key moments -> out/stills/
  python render.py --stills --at 12,47   # PNG previews at chosen seconds
  python render.py --thumbnail           # YouTube thumbnail -> out/thumbnail.png
"""
import argparse
import os
import subprocess
import sys
import time
from multiprocessing import Pool

from PIL import Image

from bibi_buzz import timeline as T
from bibi_buzz import scenes
from bibi_buzz.draw import Canvas, make_background, W, H

_BG = None


def _init():
    global _BG
    _BG = make_background()


def frame_image(t):
    c = Canvas(_BG.copy())
    scenes.render(c, t)
    img = c.final()
    # fade in from white at the start / fade out to black at the end
    if t < 0.5:
        img = Image.blend(Image.new("RGB", (W, H), "white"), img, t / 0.5)
    elif t > T.DURATION - 1.0:
        img = Image.blend(img, Image.new("RGB", (W, H), "black"), min(1.0, (t - (T.DURATION - 1.0)) / 1.0))
    return img


def frame_bytes(i):
    return frame_image(i / T.FPS).tobytes()


def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def run(cmd):
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit("ffmpeg failed: " + " ".join(cmd[:6]) + " ...")


def encode_cmd(ffmpeg, out):
    return [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
            "-r", str(T.FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-g", str(T.FPS), out]


def render_scene(pool, ffmpeg, final, span):
    part = final[:-4] + ".part.mp4"  # still ends in .mp4, renamed only when ffmpeg succeeded
    frames = range(round(span[0] * T.FPS), round(span[1] * T.FPS))
    proc = subprocess.Popen(encode_cmd(ffmpeg, part), stdin=subprocess.PIPE)
    try:
        for fb in pool.imap(frame_bytes, frames, chunksize=4):
            proc.stdin.write(fb)
        proc.stdin.close()
    except BrokenPipeError:
        pass
    if proc.wait() != 0:
        sys.exit(f"ffmpeg failed while encoding {final}")
    os.replace(part, final)
    return len(frames)


def join_and_mux(ffmpeg, base, files, out, wav):
    lst = os.path.join(base, "_scenes.txt")
    with open(lst, "w") as f:
        for p in files:
            f.write("file '%s'\n" % os.path.relpath(p, base).replace("\\", "/"))
    video = os.path.join(base, "_video.part.mp4")
    run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])
    part = out[:-4] + ".part.mp4"
    if wav:
        run([ffmpeg, "-y", "-loglevel", "error", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", part])
    else:
        run([ffmpeg, "-y", "-loglevel", "error", "-i", video, "-c", "copy", "-movflags", "+faststart", part])
    os.replace(part, out)
    for p in (video, lst):
        if os.path.exists(p):
            os.remove(p)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="out/bibi_buzz_ep01.mp4")
    ap.add_argument("--scenes", help="comma separated scene names to (re-)render, e.g. color_red,bye")
    ap.add_argument("--resume", action="store_true", help="skip scenes whose file already exists")
    ap.add_argument("--voice", action="store_true", help="add TTS voice-over (edge-tts)")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--stills", action="store_true", help="save preview PNGs instead of a video")
    ap.add_argument("--at", help="with --stills: comma separated seconds")
    ap.add_argument("--thumbnail", action="store_true", help="make the YouTube thumbnail instead of a video")
    a = ap.parse_args()

    base = os.path.dirname(a.out) or "."
    os.makedirs(base, exist_ok=True)
    ffmpeg = get_ffmpeg()

    if a.thumbnail:
        from bibi_buzz.thumbnail import make_thumbnail
        _init()
        make_thumbnail(_BG, os.path.join(base, "thumbnail.png"))
        return
    if a.stills:
        _init()
        d = os.path.join(base, "stills")
        os.makedirs(d, exist_ok=True)
        times = [float(x) for x in a.at.split(",")] if a.at else [3, 10, 25, 31, 45, 60, 78, 84, 92, 108, 118, 133, 138, 143, 147]
        for t in times:
            frame_image(float(t)).save(os.path.join(d, f"t{int(t):03d}.png"))
        print("stills saved to", d)
        return

    scene_dir = os.path.join(base, "scenes")
    os.makedirs(scene_dir, exist_ok=True)
    plan = [(f"{i:02d}_{name}", name, span) for i, (name, span) in enumerate(T.scene_list())]
    wanted = set(a.scenes.split(",")) if a.scenes else None
    if wanted:
        unknown = wanted - {n for _, n, _ in plan}
        if unknown:
            sys.exit("unknown scene(s): %s (choose from: %s)" % (", ".join(sorted(unknown)), ", ".join(n for _, n, _ in plan)))
    files, todo = [], []
    for stem, name, span in plan:
        final = os.path.join(scene_dir, stem + ".mp4")
        files.append(final)
        if wanted is not None:
            if name in wanted:
                todo.append((final, span))
        elif not (a.resume and os.path.exists(final)):
            todo.append((final, span))

    if todo:
        total = sum(round(s[1] * T.FPS) - round(s[0] * T.FPS) for _, s in todo)
        print(f"Rendering {len(todo)} scene(s), {total} frames, {a.workers} worker(s) ...", flush=True)
        t0, done = time.time(), 0
        with Pool(a.workers, initializer=_init) as pool:
            for final, span in todo:
                done += render_scene(pool, ffmpeg, final, span)
                el = time.time() - t0
                print(f"  {os.path.basename(final)} ok  ({done}/{total} frames, {el:.0f}s elapsed, "
                      f"~{el / done * (total - done):.0f}s left)", flush=True)

    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        print("Not all scene files exist yet - run `python render.py` once to create them all.")
        return

    wav = None
    if not a.no_audio:
        from bibi_buzz.audio import build_wav
        print("Synthesising audio ...", flush=True)
        wav = build_wav(os.path.join(base, "_audio.wav"), ffmpeg, with_voice=a.voice)
    join_and_mux(ffmpeg, base, files, a.out, wav)
    if wav and os.path.exists(wav):
        os.remove(wav)
    print("Done ->", a.out)


if __name__ == "__main__":
    main()
