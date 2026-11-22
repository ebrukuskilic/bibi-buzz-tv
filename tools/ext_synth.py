#!/usr/bin/env python3
"""The new voice engines, in their own environment (python -m venv /opt/ext: torch, pocket-tts-turkish, ptts, pyworld).

The speech lab makes the job file (tools/speech_lab.py ext-prepare) and measures what this script made (ext-collect).

  python tools/ext_synth.py job.json outdir

job.json: {"budget": seconds, "items": [{"id", "engine": "pocket" | "phonon", "voice", "emotion", "text", "f0", "env", ...}]}
  pocket   Pocket TTS Turkish (wite-tech/pocket-tts-turkish, CC-BY-4.0; built on Kyutai's Pocket TTS): voices female_1..3 and male_1..3, emotion tags
           mutlu / uzgun / kizgin / sasgin / sakin (written with the Turkish letters), about 5x real time on one CPU thread
  phonon   Phonon 31m English (gradium/phonon-31m-en, Apache-2.0; a Rust runtime, no PyTorch): voice "*" = every English voice of the catalog
  f0, env  WORLD vocoder (pyworld): the pitch x f0 and the spectral envelope (the vocal tract = the formants) x env; 1.0 = untouched.  A plain resampling moves both
           by the same factor (a smaller person, and above x1.2 a chipmunk); here the pitch can move a lot and the vocal tract a little.
outdir: <id>.wav (24 kHz, mono), manifest.json (everything that was made: engine, voice, emotion, seconds of work and of audio)
"""
import json
import os
import re
import subprocess
import sys
import time
import traceback

import numpy as np

SR = 24000


def world_shift(y, sr, f0f=1.0, envf=1.0):
    """pitch x f0f, formants x envf (WORLD analysis -> change -> synthesis).  Duration and loudness stay."""
    if abs(f0f - 1.0) < 1e-3 and abs(envf - 1.0) < 1e-3:
        return y
    import pyworld as pw
    x = np.ascontiguousarray(y, dtype=np.float64)
    fp = 5.0
    f0, t = pw.harvest(x, sr, f0_floor=70.0, f0_ceil=650.0, frame_period=fp)
    f0 = pw.stonemask(x, f0, t, sr)
    sp = pw.cheaptrick(x, f0, t, sr)
    ap = pw.d4c(x, f0, t, sr)
    if abs(envf - 1.0) > 1e-3:
        nb = sp.shape[1]
        src = np.clip(np.arange(nb) / envf, 0, nb - 1)               # new(f) = old(f / envf): a formant at f moves to f * envf
        i0 = np.floor(src).astype(int)
        i1 = np.minimum(i0 + 1, nb - 1)
        w = src - i0
        sp = sp[:, i0] * (1 - w) + sp[:, i1] * w
        ap = ap[:, i0] * (1 - w) + ap[:, i1] * w
    z = pw.synthesize(f0 * f0f, np.ascontiguousarray(sp), np.ascontiguousarray(ap), sr, frame_period=fp)
    z = z[:len(x)] if len(z) >= len(x) else np.pad(z, (0, len(x) - len(z)))
    r0 = float(np.sqrt(np.mean(x ** 2)) + 1e-9)
    r1 = float(np.sqrt(np.mean(z ** 2)) + 1e-9)
    return np.clip(z * (r0 / r1), -1.0, 1.0)


def write_wav(path, y, sr):
    import soundfile as sf
    sf.write(path, np.asarray(y, dtype=np.float32), sr, subtype="PCM_16")


def resample(y, sr0, sr1):
    if sr0 == sr1:
        return y
    from scipy.signal import resample_poly
    from math import gcd
    g = gcd(int(sr0), int(sr1))
    return resample_poly(y, int(sr1) // g, int(sr0) // g)


def phonon_catalog():
    """(name, the catalog line) of every English voice of Phonon; the format of the list is not documented: the first word of a line is the name, and the line has to say 'en'"""
    names = []
    try:
        r = subprocess.run([sys.executable, "-m", "ptts", "--list-voices"], capture_output=True, text=True, timeout=300)
        print("ptts --list-voices: returncode", r.returncode, "stdout lines", len(r.stdout.splitlines()), flush=True)
        print(r.stdout[:6000], flush=True)
        if r.stderr.strip():
            print("stderr:", r.stderr[-600:], flush=True)
        for ln in r.stdout.splitlines():
            m = re.match(r"\s*([A-Za-z0-9_\-]+)\s+(.*)$", ln)
            if m and re.search(r"(^|[\s(\[,|:])en([-_ )\],|:]|$)", m.group(2) or "", re.I):
                names.append((m.group(1), ln.strip()))
    except Exception:
        print("the voice catalog could not be listed", traceback.format_exc()[-400:], flush=True)
    seen, out = set(), []
    for n, ln in names:
        if n.lower() not in seen and n.lower() not in ("name", "voice", "voices", "id"):
            seen.add(n.lower())
            out.append((n, ln))
    if not out:
        out = [("Easton", "fallback"), ("Zoey", "fallback")]
    return out[:70]


def main():
    job = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    budget = float(job.get("budget", 2400))
    t_all = time.time()
    eng = {}
    manifest = []

    def pocket():
        if "pocket" not in eng:
            t0 = time.time()
            from pocket_tts_turkish import TurkishTTS
            eng["pocket"] = TurkishTTS.from_pretrained()
            print("Pocket TTS Turkish loaded in %.1f s, sample rate %s" % (time.time() - t0, getattr(eng["pocket"], "sample_rate", "?")), flush=True)
        return eng["pocket"]

    def phonon():
        if "phonon" not in eng:
            t0 = time.time()
            import ptts
            eng["phonon"] = ptts.TTS("hf://gradium/phonon-31m-en", lang="en", quant="q8")
            print("Phonon 31m loaded in %.1f s" % (time.time() - t0), flush=True)
        return eng["phonon"]

    items = []
    for it in job["items"]:
        if it.get("engine") == "phonon" and it.get("voice") == "*":
            if "phonon_voices" not in eng:
                eng["phonon_voices"] = phonon_catalog()
                print("Phonon: %d English voices: %s" % (len(eng["phonon_voices"]), ", ".join(n for n, _ in eng["phonon_voices"])), flush=True)
            for n, ln in eng["phonon_voices"]:
                d = dict(it)
                d["voice"] = n
                d["catalog"] = ln
                d["id"] = it["id"].replace("*", n)
                items.append(d)
        else:
            items.append(it)

    for it in items:
        if time.time() - t_all > budget:
            print("the time budget is spent: the rest is not made", flush=True)
            break
        t0 = time.time()
        rec = dict(it)
        try:
            if it["engine"] == "pocket":
                tts = pocket()
                kw = {"voice": it["voice"]}
                if it.get("emotion"):
                    kw["emotion"] = it["emotion"]
                y = np.asarray(tts.generate(it["text"], **kw), dtype=np.float64).reshape(-1)
                sr = int(getattr(tts, "sample_rate", SR))
            elif it["engine"] == "phonon":
                tts = phonon()
                tmp = os.path.join(out, "_tmp_phonon.wav")
                tts.save(tmp, it["text"], voice=it["voice"])
                import soundfile as sf
                y, sr = sf.read(tmp, dtype="float64")
                y = y.reshape(len(y), -1).mean(axis=1) if y.ndim > 1 else y
            else:
                raise RuntimeError("unknown engine " + str(it.get("engine")))
            y = resample(y, sr, SR)
            work = time.time() - t0
            if abs(float(it.get("f0", 1.0)) - 1.0) > 1e-3 or abs(float(it.get("env", 1.0)) - 1.0) > 1e-3:
                y = world_shift(y, SR, float(it.get("f0", 1.0)), float(it.get("env", 1.0)))
                rec["world_s"] = round(time.time() - t0 - work, 2)
            write_wav(os.path.join(out, it["id"] + ".wav"), y, SR)
            rec.update(ok=True, work=round(work, 2), audio=round(len(y) / float(SR), 2))
            print("%-34s %-8s %-10s %-8s %5.1f s of audio in %5.1f s" % (it["id"], it["engine"], it["voice"], it.get("emotion") or "-", rec["audio"], work), flush=True)
        except Exception:
            rec.update(ok=False, error=traceback.format_exc()[-400:])
            print("FAILED", it.get("id"), traceback.format_exc()[-400:], flush=True)
        manifest.append(rec)
        with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=1)
    print("done: %d of %d clips in %.0f s" % (sum(1 for m in manifest if m.get("ok")), len(items), time.time() - t_all), flush=True)


if __name__ == "__main__":
    main()
