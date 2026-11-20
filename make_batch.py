#!/usr/bin/env python3
"""Makes one day of Bibi Buzz TV videos (5 long lessons + 5 Shorts) and a manifest.json for the uploader.

  python make_batch.py --day 1 --out out/2026-11-20
  python make_batch.py --day 1 --only d001-S1 --sheet         # one video + a contact sheet to check the layout
  python make_batch.py --day 1 --dry                          # only print the plan with durations (needs the voice)
  python make_batch.py --day 1 --thumbs-only                  # only the designed thumbnails of the long videos (fast)
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bibi_buzz import curriculum as CU          # noqa: E402
from bibi_buzz import pipeline as PL            # noqa: E402
from bibi_buzz import voice as VO               # noqa: E402


def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def make_thumb(les, out_dir):
    """Designed thumbnail <id>.jpg of a long lesson (the uploader sets it as the custom thumbnail)."""
    from bibi_buzz import emoji as E
    from bibi_buzz.thumbnail import make_lesson_thumbnail
    refs = [c for c in les.segs[0].data["codes"][:3] if not c.startswith(("#", "n:", "L:", "S:"))]
    missing = E.prefetch(refs)
    if missing:
        raise RuntimeError(f"emoji sprites not available: {missing}")
    make_lesson_thumbnail(les, os.path.join(out_dir, les.id + ".jpg"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int)
    ap.add_argument("--date", help="YYYY-MM-DD (default: today); the day number is counted from the channel start date")
    ap.add_argument("--out", default="out/batch")
    ap.add_argument("--only", help="comma separated lesson ids, e.g. d001-L1,d001-S2")
    ap.add_argument("--voice", default=VO.VOICE)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--sheet", action="store_true", help="also write a contact sheet PNG per video")
    ap.add_argument("--dry", action="store_true", help="plan only: build the timeline, no video")
    ap.add_argument("--thumbs-only", action="store_true", help="only (re)make the thumbnails of the long videos")
    ap.add_argument("--cache", default=os.path.join("out", "tts-cache"))
    a = ap.parse_args()

    date = datetime.date.fromisoformat(a.date) if a.date else datetime.date.today()
    day = a.day or CU.day_number(date)
    if day < 1:
        sys.exit("day must be >= 1")
    ffmpeg = get_ffmpeg()
    os.makedirs(a.out, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None
    lessons = [l for l in CU.plan(day) if not only or l.id in only]
    manifest = dict(day=day, date=str(date), videos=[])
    failures = []
    for les in lessons:
        print(f"== {les.id}  {les.fmt}  {les.title}", flush=True)
        try:
            if a.thumbs_only:
                if les.fmt == "long":
                    make_thumb(les, a.out)
                    print("   thumbnail ok", flush=True)
                continue
            if a.dry:
                PL.prepare(les, ffmpeg, a.cache, a.voice)
                problems, st = PL.sync_report(les)
                print(f"   {st['duration']:.1f}s  bpm {les.bpm}  cues {st['cues']}  problems: {problems or 'none'}")
                continue
            path = os.path.join(a.out, les.id + ".mp4")
            st = PL.render(les, path, ffmpeg, a.cache, a.voice, workers=a.workers or None)
            if a.sheet:
                PL.contact_sheet(les, os.path.join(a.out, les.id + "-sheet.png"))
            if les.fmt == "long":  # designed thumbnail; if that fails, a still of the first lesson picture
                try:
                    make_thumb(les, a.out)
                except Exception as e:
                    print(f"   thumbnail failed ({e!r}) - using a still instead", flush=True)
                    from bibi_buzz import stage as ST
                    ST.render_frame(les, ST.sample_times(les)[1]).convert("RGB").save(os.path.join(a.out, les.id + ".jpg"), quality=92)
            meta = CU.metadata(les, st.pop("chapters_text"))
            manifest["videos"].append(dict(id=les.id, type=les.fmt, file=st["file"], duration=round(st["duration"], 1),
                                           chapters=st["chapters"], **meta))
            print(f"   ok  {st['duration']:.1f}s  rendered in {st['seconds_to_render']}s", flush=True)
        except Exception as e:                      # one bad video must not stop the others
            failures.append((les.id, repr(e)))
            print(f"   FAILED: {e!r}", flush=True)
    if not a.dry and not a.thumbs_only:
        mpath = os.path.join(a.out, "manifest.json")
        if os.path.exists(mpath):                   # partial re-run: keep what is already there
            try:
                old = {v["id"]: v for v in json.load(open(mpath)).get("videos", [])}
            except Exception:
                old = {}
            old.update({v["id"]: v for v in manifest["videos"]})
            manifest["videos"] = [old[k] for k in sorted(old)]
        with open(mpath, "w") as f:
            json.dump(manifest, f, indent=1, ensure_ascii=False)
        print(f"manifest: {len(manifest['videos'])} videos, {len(failures)} failed")
    if failures:
        print("FAILURES:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
