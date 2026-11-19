"""Render one Lesson to an mp4: voice first, beat-aligned timeline, music + sfx, parallel frame drawing."""
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np
from PIL import Image

from . import emoji as E
from . import music as MU
from . import schedule as SCH
from . import stage as ST
from . import voice as VO

SR = VO.SR
_LESSON = None


# ------------------------------------------------------------------------------ preparing
def envelope(y, hz=30):
    """Loudness of a clip at `hz` values per second (0..1) - drives Bibi's mouth."""
    hop = SR // hz
    n = max(1, len(y) // hop)
    e = np.sqrt(np.mean(y[: n * hop].reshape(n, hop) ** 2, axis=1)) if len(y) >= hop else np.array([0.5])
    ref = float(np.percentile(e, 90)) or 1e-6
    return np.clip(e / ref, 0, 1) ** 0.8


def prepare(lesson, ffmpeg, cache_dir, voice=VO.VOICE):
    clips = VO.synth_all(lesson.texts(), ffmpeg, cache_dir, voice)
    SCH.build(lesson, clips)
    lesson.all_cues = lesson.cues()
    lesson.env = {t: envelope(y) for t, y in clips.items()}
    return clips


def sync_report(lesson):
    """Checks that the voice never overlaps, every cue starts exactly on a beat and every segment ends on a bar."""
    beat = lesson.beat
    problems = []
    cues = lesson.cues()
    for cu in cues:
        off = (cu.t - lesson.grid0) / beat
        if abs(off - round(off)) > 1e-6:
            problems.append(f"cue off the beat grid: {cu.text!r} at {off:.3f} beats")
    voiced = [c for c in cues if c.text]
    for a, b in zip(voiced, voiced[1:]):
        if a.t + a.dur > b.t - 0.05:
            problems.append(f"voice lines overlap: {a.text!r} / {b.text!r}")
    for s in lesson.segs:
        bars = (s.t1 - s.t0) / (4 * beat)
        if abs(bars - round(bars)) > 1e-6:
            problems.append(f"segment {s.kind} does not end on a bar line ({bars:.3f} bars)")
    spoken = sum(c.dur for c in voiced)
    return problems, dict(duration=lesson.duration, cues=len(voiced), voice_seconds=spoken, bpm=lesson.bpm)


# -------------------------------------------------------------------------------- frames
def _init(lesson):
    global _LESSON
    _LESSON = lesson


def _work(rng):
    a, b = rng
    return b"".join(ST.render_frame(_LESSON, i / ST.FPS).tobytes() for i in range(a, b))


def _chapters_text(lesson):
    ch = SCH.chapters(lesson)
    return "\n".join(f"{SCH.fmt_time(t)} {label}" for t, label in ch), [(round(t, 2), label) for t, label in ch]


def contact_sheet(lesson, path, cols=4, thumb=360):
    """One picture with a representative frame of every segment (for checking the layout by eye)."""
    times = ST.sample_times(lesson)
    frames = [ST.render_frame(lesson, t) for t in times]
    fw = thumb if lesson.fmt == "long" else int(thumb * 9 / 16 * 1.0)
    fh = int(fw * frames[0].height / frames[0].width)
    cols = min(cols, len(frames)) if lesson.fmt == "long" else min(6, len(frames))
    rows = int(math.ceil(len(frames) / cols))
    sheet = Image.new("RGB", (cols * fw, rows * fh), "white")
    for i, fr in enumerate(frames):
        sheet.paste(fr.resize((fw, fh), Image.LANCZOS), ((i % cols) * fw, (i // cols) * fh))
    sheet.save(path)
    return path


def render(lesson, out_path, ffmpeg, cache_dir, voice=VO.VOICE, workers=None, quiet=False):
    """Full render. Returns metadata about the finished file."""
    t_start = time.time()
    clips = prepare(lesson, ffmpeg, cache_dir, voice)
    problems, stats = sync_report(lesson)
    if problems:
        raise RuntimeError("sync problems in %s: %s" % (lesson.id, "; ".join(problems[:5])))
    missing = E.prefetch(lesson.codes())
    if missing:
        print(f"[emoji] could not download {len(missing)} sprites (a star is drawn instead): {', '.join(missing)}", flush=True)
    mix = MU.mix(lesson, clips)
    wav = out_path + ".wav"
    MU.write_wav(wav, mix)

    L = ST.layout(lesson.fmt)
    nframes = int(math.ceil(lesson.duration * ST.FPS))
    out_w, out_h = (1080, 1920) if lesson.fmt == "short" else (1280, 720)
    vf = f"scale={out_w}:{out_h}:flags=lanczos,format=yuv420p" if lesson.fmt == "short" else "format=yuv420p"
    tmp = out_path + ".part.mp4"
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{L.w}x{L.h}",
           "-r", str(ST.FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-vf", vf,
           "-c:v", "libx264", "-preset", "veryfast", "-tune", "animation", "-crf", "23", "-g", str(ST.FPS * 2),
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "160k",
           "-t", f"{lesson.duration:.3f}", "-movflags", "+faststart", "-f", "mp4", tmp]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    workers = workers or os.cpu_count() or 2
    step = 8
    chunks = [(i, min(i + step, nframes)) for i in range(0, nframes, step)]
    done = 0
    try:
        with Pool(workers, initializer=_init, initargs=(lesson,)) as pool:
            for data in pool.imap(_work, chunks):
                proc.stdin.write(data)
                done += 1
                if not quiet and (done % max(1, len(chunks) // 10) == 0):
                    print(f"  [{lesson.id}] {100 * done // len(chunks)}%", flush=True)
        proc.stdin.close()
    except BrokenPipeError:
        pass
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError("ffmpeg failed (%s) for %s" % (rc, lesson.id))
    os.replace(tmp, out_path)
    os.remove(wav)
    text, chapters = _chapters_text(lesson)
    stats.update(file=os.path.basename(out_path), frames=nframes, seconds_to_render=round(time.time() - t_start, 1),
                 chapters=chapters, chapters_text=text)
    return stats
