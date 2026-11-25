"""The daily compilation (dNNN-C1): the day's lessons and its English fairy tale, one after the other, in ONE long video.

Why: on a channel made for kids the money and the watch hours come from long videos (ads in the middle of a video need 8 minutes or
more, and the watch hours that YouTube asks for come only from long videos), and YouTube does not let channels that upload many
look-alike videos a day earn money.  So the day's four short lessons are no longer uploaded one by one: they become, with the
tale, a 10-20 minute "learn with Bibi" video, and the day uploads only a handful of videos (see curriculum.MIX_DAY).
"""
import os
import subprocess

from . import schedule as SCH

W, H, FPS = 1280, 720, 24
BRAND = "Bibi Buzz TV"


def _head(title):
    """'Learn Bugs and Insects for Kids | Butterfly ... | Bibi Buzz TV' -> 'Learn Bugs and Insects for Kids'"""
    return title.split(" | ")[0].replace(" #Shorts", "").strip()


def _topic(title):
    h = _head(title)
    for a, b in (("Learn to ", ""), ("Learn ", ""), (" for Kids", ""), (" Part 1", ""), (" Part 2", ""), (" Part 3", "")):
        h = h.replace(a, b)
    return h.strip()


def concat(paths, out, ffmpeg="ffmpeg"):
    """Joins the videos (any size / frame rate) into one 1280x720 24 fps video; returns the start time of every part."""
    import json
    durs = []
    for p in paths:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", p], capture_output=True, text=True, check=True)
        durs.append(float(json.loads(r.stdout)["format"]["duration"]))
    args = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    for p in paths:
        args += ["-i", p]
    parts = []
    for i in range(len(paths)):
        parts.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS},setsar=1,format=yuv420p[v{i}];"
                     f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo[a{i}];")
    fc = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(len(paths))) + f"concat=n={len(paths)}:v=1:a=1[v][a]"
    tmp = out[:-4] + ".part.mp4"
    args += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-tune", "animation",
             "-crf", "23", "-g", str(FPS * 2), "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", tmp]
    subprocess.run(args, check=True)
    os.replace(tmp, out)
    starts, t = [], 0.0
    for d in durs:
        starts.append(t)
        t += d
    return starts, t


def make(day, entries, out_dir, ffmpeg="ffmpeg", subscribe_url=""):
    """entries: manifest entries (dicts with id, file, title, chapters, ...) in the order they are joined.  Returns the manifest entry of the compilation."""
    paths = [os.path.join(out_dir, e["file"]) for e in entries]
    cid = f"d{day:03d}-C1"
    out = os.path.join(out_dir, cid + ".mp4")
    starts, total = concat(paths, out, ffmpeg)
    chapters = [(round(s, 2), _head(e["title"])) for s, e in zip(starts, entries)]
    minutes = max(1, int(round(total / 60.0)))
    lessons = [e for e in entries if "-L" in e["id"]]
    tales = [e for e in entries if "-T" in e["id"]]
    topics = [_topic(e["title"]) for e in lessons]
    tale = _head(tales[0]["title"]) if tales else ""
    tail = f" | {minutes} Min Learning Compilation for Kids | {BRAND}"
    head = "Learn with Bibi: " + ", ".join(topics)
    if len(head + (" & " + tale if tale else "") + tail) > 100:
        tale = ""                                                    # (the tale is still in the description and the chapters)
    while len(head + tail) > 100 and len(topics) > 1:
        topics = topics[:-1]
        head = "Learn with Bibi: " + ", ".join(topics) + " & More"
    title = (head + (" & " + tale if tale else "") + tail)[:100]
    words = []
    for e in lessons:
        d = e.get("description", "")
        for line in d.splitlines():
            if line.startswith("In this video: "):
                words.append(line[len("In this video: "):].rstrip("."))
    lines = [f"{minutes} minutes of learning with Bibi the bee and her friends! " + ", ".join(_topic(e["title"]) for e in lessons)
             + (f", and the fairy tale {_head(tales[0]['title'])}." if tales else "."),
             "Kids see every picture, hear the word, say it out loud and play fun quizzes. Perfect for toddlers and preschoolers (ages 2-6).", ""]
    if subscribe_url:
        lines += ["Subscribe to Bibi Buzz TV: " + subscribe_url, ""]
    if words:
        lines += ["In this video: " + "; ".join(words) + ".", ""]
    lines += ["Chapters"] + [f"{SCH.fmt_time(t)} {label}" for t, label in chapters] + [""]
    lines += ["New learning videos and fairy tales for toddlers and preschoolers on Bibi Buzz TV!",
              "Narrated with text-to-speech voices. All the artwork and music were made for Bibi Buzz TV. Emoji artwork: Google Noto Emoji (Apache License 2.0).", "",
              "#kidslearning #learnenglish #preschool #toddlers #BibiBuzzTV"]
    tags, seen, n = [], set(), 0
    for e in entries:
        for tg in e.get("tags", []):
            if tg.lower() not in seen and n + len(tg) + 1 <= 450:
                seen.add(tg.lower())
                tags.append(tg)
                n += len(tg) + 1
    for tg in ("kids compilation", "learning videos for toddlers", "preschool learning", "learn english for kids"):
        if tg not in seen and n + len(tg) + 1 <= 450:
            tags.append(tg)
            n += len(tg) + 1
    return dict(id=cid, type="long", lang="en", file=cid + ".mp4", duration=round(total, 1), chapters=chapters,
                title=title.replace("<", "").replace(">", ""), description="\n".join(lines).replace("<", "").replace(">", "")[:4900], tags=tags)
