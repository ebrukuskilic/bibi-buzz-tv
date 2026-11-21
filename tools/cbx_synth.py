#!/usr/bin/env python3
"""Runs INSIDE the Chatterbox environment (python 3.11, torch 2.6, its own pinned libraries; see .github/workflows/speech-lab.yml).

  python tools/cbx_synth.py job.json out_dir

job.json: {"lang": "tr", "budget": 1300, "lines": [{"i": 0, "role": "nar", "text": "...", "ref": "ref.wav", "ex": 0.5, "cfg": 0.5}, ...]}
Writes out_dir/<i>.wav for every line that is ready (the time budget is in seconds) and out_dir/times.json = {i: [seconds of work, seconds of speech]}.
Chatterbox (Resemble AI, MIT licence) speaks in the voice of the reference clip, with an "exaggeration" of the feeling and a "cfg_weight" (lower = slower, more deliberate).
"""
import json
import os
import sys
import time
import traceback
import wave

import numpy as np


def write_wav(path, y, sr):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


def main():
    job = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    import torch
    torch.set_num_threads(os.cpu_count() or 2)
    t0 = time.time()
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    print("model loaded in %.0f s; sample rate %s; %d threads; language %s" % (time.time() - t0, model.sr, torch.get_num_threads(), job["lang"]), flush=True)
    times = {}
    t_start = time.time()
    for ln in job["lines"]:
        if time.time() - t_start > job.get("budget", 1300):
            print("time budget used up before line %d" % ln["i"], flush=True)
            break
        try:
            t1 = time.time()
            y, n = None, len(ln["text"].strip())
            for attempt in range(3):                                    # (the model sometimes stops far too early or never stops: such a try is made again)
                torch.manual_seed(1234 + attempt)
                with torch.inference_mode():
                    wav = model.generate(ln["text"], language_id=job["lang"], audio_prompt_path=ln["ref"], exaggeration=ln["ex"],
                                         cfg_weight=min(0.8, ln["cfg"] + 0.1 * attempt))
                cand = wav.squeeze().detach().cpu().numpy().astype(np.float32)
                secs = len(cand) / float(model.sr)
                good = 0.045 * n <= secs <= 0.20 * n + 2.0
                if y is None or good:
                    y = cand
                if good:
                    break
                print("line %d: %.1f s for %d characters is not right (try %d)" % (ln["i"], secs, n, attempt + 1), flush=True)
            write_wav(os.path.join(out, "%d.wav" % ln["i"]), y, model.sr)
            times[str(ln["i"])] = [time.time() - t1, len(y) / float(model.sr)]
            print("line %d (%s): %.1f s of speech in %.1f s of work: %s" % (ln["i"], ln["role"], times[str(ln["i"])][1], times[str(ln["i"])][0], ln["text"][:60]), flush=True)
        except Exception:
            print("line %d FAILED:\n%s" % (ln["i"], traceback.format_exc()[-1200:]), flush=True)
        json.dump(times, open(os.path.join(out, "times.json"), "w"))
    json.dump(times, open(os.path.join(out, "times.json"), "w"))
    print("done in %.0f s" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
