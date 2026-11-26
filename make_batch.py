#!/usr/bin/env python3
"""Makes one day of Bibi Buzz TV videos (long lessons / a fairy tale + 5 Shorts) and a manifest.json for the uploader.
A day normally has 5 long lessons; on the days listed in curriculum.TALE_QUEUE the 5th one is an animated fairy tale (id dNNN-T1).

  python make_batch.py --day 1 --out out/2026-11-20
  python make_batch.py --day 1 --only d001-S1 --sheet         # one video + a contact sheet to check the layout
  python make_batch.py --day 1 --dry                          # only print the plan with durations (needs the voice)
  python make_batch.py --day 1 --thumbs-only                  # only the designed thumbnails of the long videos (fast)
  python make_batch.py --day 1 --only ep1                     # only the cover of episode 1 (ep1.png)
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bibi_buzz import curriculum as CU          # noqa: E402
from bibi_buzz import draw as D                 # noqa: E402
from bibi_buzz import pipeline as PL            # noqa: E402
from bibi_buzz import story as SY               # noqa: E402
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


def make_ep1_thumb(out_dir):
    """Cover of episode 1 (COLORS!) as ep1.png; it can be set on that video by hand in Studio."""
    from bibi_buzz.draw import make_background
    from bibi_buzz.thumbnail import make_thumbnail
    make_thumbnail(make_background(), os.path.join(out_dir, "ep1.png"))


WEEKLY_FIRST_DAY = 14                                             # (3 December 2026, then every 7 days: the long video of the week)


def weekly_day(day, manifest, out_dir, ffmpeg, failures):
    """Every 7 days from WEEKLY_FIRST_DAY: the long video of the week (dNNN-W1, bibi_buzz/compilation.weekly) from the compilations (dNNN-C1) and the English songs
    of the days that are on the media branch next to this one (the last three days) and of this day, oldest first."""
    import shutil
    from bibi_buzz import compilation as CO
    if any(v["id"].endswith("-W1") for v in manifest["videos"]):
        return
    root = os.path.dirname(os.path.abspath(out_dir))
    entries = []
    for d in sorted(x for x in os.listdir(root) if x[:2] == "20" and os.path.isdir(os.path.join(root, x))):
        try:
            m = manifest if os.path.abspath(os.path.join(root, d)) == os.path.abspath(out_dir) else json.load(open(os.path.join(root, d, "manifest.json")))
        except Exception:
            continue
        for v in m.get("videos", []):
            p = os.path.join(root, d, v["file"])
            if (v["id"].endswith("-C1") or (v["id"].endswith("-M1") and v.get("lang", "en") == "en")) and os.path.exists(p) and not v.get("parts"):
                entries.append(dict(v, path=p))
    if sum(float(e.get("duration") or 0) for e in entries) < 20 * 60:
        failures.append((f"d{day:03d}-W1", "not enough videos for the long video of the week"))
        return
    try:
        w = CO.weekly(day, entries, out_dir, ffmpeg, CU.SUBSCRIBE_URL, week=(day - WEEKLY_FIRST_DAY) // 7 + 1)
        src = next((os.path.join(os.path.dirname(e["path"]), e["id"] + ".jpg") for e in entries if e["id"].endswith("-C1")), None)
        if src and os.path.exists(src):
            shutil.copyfile(src, os.path.join(out_dir, w["id"] + ".jpg"))
        manifest["videos"].append(w)
        manifest["videos"].sort(key=lambda v: v["id"])
        print(f"== {w['id']}  long  {w['title']}\n   ok  {w['duration']:.1f}s (the long video of the week, {len(entries)} videos, {len(w.get('parts') or [])} parts)", flush=True)
    except Exception as e:
        failures.append((f"d{day:03d}-W1", repr(e)))
        print(f"   long video of the week FAILED: {e!r}", flush=True)


def compile_day(day, manifest, out_dir, ffmpeg, failures):
    """From curriculum.MIX_DAY on: the day's lessons (dNNN-L*) leave the upload list (manifest "parts") and are joined, with the
    English tale, into the compilation dNNN-C1 (bibi_buzz/compilation.py), whose cover is the cover of the first lesson."""
    import shutil
    from bibi_buzz import compilation as CO
    parts = {p["id"]: p for p in manifest.get("parts", [])}
    keep = []
    for v in manifest["videos"]:
        if "-L" in v["id"]:
            parts[v["id"]] = v
        else:
            keep.append(v)
    manifest["videos"], manifest["parts"] = keep, [parts[k] for k in sorted(parts)]
    if any(v["id"].endswith("-C1") for v in keep):
        return
    lessons = [p for p in manifest["parts"] if os.path.exists(os.path.join(out_dir, p["file"]))]
    tale = [v for v in keep if v["id"].endswith("-T1") and os.path.exists(os.path.join(out_dir, v["file"]))]
    if len(lessons) < 2:
        failures.append((f"d{day:03d}-C1", "not enough lessons for the compilation"))
        return
    try:
        c = CO.make(day, lessons + tale, out_dir, ffmpeg, CU.SUBSCRIBE_URL)
        src = os.path.join(out_dir, lessons[0]["id"] + ".jpg")
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(out_dir, c["id"] + ".jpg"))
        manifest["videos"].append(c)
        manifest["videos"].sort(key=lambda v: v["id"])
        print(f"== {c['id']}  long  {c['title']}\n   ok  {c['duration']:.1f}s (compilation of {len(lessons) + len(tale)} videos)", flush=True)
        for p in lessons:                                         # the parts are in the compilation now: no need to publish them
            for ext in (".mp4", ".jpg", "-sheet.png"):
                f = os.path.join(out_dir, p["id"] + ext)
                if os.path.exists(f):
                    os.remove(f)
    except Exception as e:
        failures.append((f"d{day:03d}-C1", repr(e)))
        print(f"   compilation FAILED: {e!r}", flush=True)


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
    if only and "ep1" in only:                      # --only ep1: the cover of episode 1 (no lessons are rendered for it)
        make_ep1_thumb(a.out)
        only.discard("ep1")
        if not only:
            return
    lessons = [l for l in CU.plan(day) if not only or l.id in only]
    manifest = dict(day=day, date=str(date), videos=[])
    failures = []
    for les in lessons:
        tale = getattr(les, "kind", "") == "tale"
        D.set_language(getattr(les, "lang", "en"))          # Turkish tales are drawn with the Turkish font (Baloo 2)
        print(f"== {les.id}  {les.fmt}  {les.title}", flush=True)
        try:
            if a.thumbs_only:
                if les.fmt == "long":
                    if tale:
                        SY.make_cover(les, os.path.join(a.out, les.id + ".jpg"))
                    else:
                        make_thumb(les, a.out)
                    print("   thumbnail ok", flush=True)
                continue
            if a.dry:
                if tale:
                    SY.prepare(les, ffmpeg, a.cache)
                    problems, st = SY.sync_report(les)
                else:
                    PL.prepare(les, ffmpeg, a.cache, a.voice)
                    problems, st = PL.sync_report(les)
                print(f"   {st['duration']:.1f}s  bpm {les.bpm}  cues {st['cues']}  problems: {problems or 'none'}")
                continue
            path = os.path.join(a.out, les.id + ".mp4")
            if tale:
                SY.prepare(les, ffmpeg, a.cache)
                problems, _st = SY.sync_report(les)
                if problems:
                    raise RuntimeError("sync problems in %s: %s" % (les.id, "; ".join(problems[:5])))
                st = SY.render(les, path, ffmpeg, a.cache, workers=a.workers or None)
                if a.sheet:
                    SY.contact_sheet(les, os.path.join(a.out, les.id + "-sheet.png"), cols=6, thumb=300, times=SY.sample_times(les, 2))
            else:
                st = PL.render(les, path, ffmpeg, a.cache, a.voice, workers=a.workers or None)
                if a.sheet:
                    PL.contact_sheet(les, os.path.join(a.out, les.id + "-sheet.png"))
            if les.fmt == "long":  # designed thumbnail; if that fails, a still of the first lesson picture
                try:
                    if tale:
                        SY.make_cover(les, os.path.join(a.out, les.id + ".jpg"))
                    else:
                        make_thumb(les, a.out)
                except Exception as e:
                    print(f"   thumbnail failed ({e!r}) - using a still instead", flush=True)
                    if tale:
                        SY.render_frame(les, les.duration * 0.25).convert("RGB").save(os.path.join(a.out, les.id + ".jpg"), quality=92)
                    else:
                        from bibi_buzz import stage as ST
                        ST.render_frame(les, ST.sample_times(les)[1]).convert("RGB").save(os.path.join(a.out, les.id + ".jpg"), quality=92)
            meta = CU.metadata(les, st.pop("chapters_text"))
            manifest["videos"].append(dict(id=les.id, type=les.fmt, lang=getattr(les, "lang", "en"), file=st["file"],
                                           duration=round(st["duration"], 1), chapters=st["chapters"], **meta))
            print(f"   ok  {st['duration']:.1f}s  rendered in {st['seconds_to_render']}s", flush=True)
        except Exception as e:                      # one bad video must not stop the others
            failures.append((les.id, repr(e)))
            print(f"   FAILED: {e!r}", flush=True)
    if not a.dry and not a.thumbs_only:
        mpath = os.path.join(a.out, "manifest.json")
        if os.path.exists(mpath):                   # partial re-run: keep what is already there
            try:
                prev = json.load(open(mpath))
                old = {v["id"]: v for v in prev.get("videos", [])}
                manifest["parts"] = prev.get("parts", [])
            except Exception:
                old = {}
            old.update({v["id"]: v for v in manifest["videos"]})
            manifest["videos"] = [old[k] for k in sorted(old)]
        if day >= CU.MIX_DAY:
            compile_day(day, manifest, a.out, ffmpeg, failures)
        if day >= WEEKLY_FIRST_DAY and (day - WEEKLY_FIRST_DAY) % 7 == 0:
            weekly_day(day, manifest, a.out, ffmpeg, failures)
        with open(mpath, "w") as f:
            json.dump(manifest, f, indent=1, ensure_ascii=False)
        print(f"manifest: {len(manifest['videos'])} videos, {len(failures)} failed")
    if failures:
        print("FAILURES:", failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
