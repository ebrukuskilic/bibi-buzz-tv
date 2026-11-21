#!/usr/bin/env python3
"""Voice laboratory (nothing of the daily videos is touched): other ways to make the SUNG voice sound like a person.

  python tools/voice_lab.py all --out out/lab                    # every experiment below, for the first two lines of Twinkle Twinkle (English)
  python tools/voice_lab.py env,speech --out out/lab
  python tools/voice_lab.py kokoro --song twinkle --lang en --lines 2 --out out/lab

jobs (comma separated):
  env      versions of the libraries, the source of the model's forward pass (lab.txt)
  speech   the neural voices of Kokoro-82M simply speaking a line (to hear how natural they are), plus a Turkish try with Turkish sounds
  psola    the voice of the song as the daily pipeline makes it now (Edge voices, moved onto the notes, a choir of three)  -> A-psola-choir
  vocos    that voice once more through a neural vocoder (it is rebuilt from its spectrogram: the buzz of the pitch shifting goes)  -> B-psola-vocos
  kokoro   Kokoro-82M sings: its own decoder is told the pitch of every note (with a person's vibrato, scoops and drift) and how long
           every sound lasts, so the timbre comes from a neural voice, not from a pitch-shifted recording        -> C-kokoro-single, D-kokoro-choir

Everything goes to --out (mp3 files to listen to, lab.txt with what happened).  Each job catches its own errors, so one that fails does not stop the rest.
"""
import argparse
import math
import os
import re
import subprocess
import sys
import time
import traceback
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

FR = 0.025                                    # one frame of the model (600 samples at 24 kHz)
KSR = 24000
OUT = "out/lab"
_LOG = None


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    if _LOG:
        _LOG.write(s + "\n")
        _LOG.flush()


def write_wav(path, y, sr):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


def save(name, y, sr, rms=0.085):
    """Writes <name>.mp3 (the loudness of every file is the same, so they can be compared by ear)."""
    y = np.asarray(y, dtype=np.float64)
    act = np.abs(y) > 0.01 * (np.max(np.abs(y)) + 1e-9)
    r = float(np.sqrt(np.mean(y[act] ** 2))) if act.any() else 1.0
    y = y * (rms / (r + 1e-9))
    pk = float(np.max(np.abs(y)))
    if pk > 0.95:
        y = y * (0.95 / pk)
    wav = os.path.join(OUT, name + ".wav")
    write_wav(wav, y, sr)
    mp3 = os.path.join(OUT, name + ".mp3")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "160k", mp3], capture_output=True, text=True)
    if r.returncode:
        log("mp3 failed", name, r.stderr[:200])
    else:
        os.remove(wav)
    log("wrote", name, "%.1f s" % (len(y) / sr))


def resample(y, sr_from, sr_to):
    from math import gcd
    from scipy.signal import resample_poly
    g = gcd(int(sr_from), int(sr_to))
    return resample_poly(y, int(sr_to) // g, int(sr_from) // g)


# ------------------------------------------------------------------------------------------------------------------------ phonemes
VOWEL = set("ɑɐɒæɔəɘɚɛɜɝɞɨɪʊʌᵻᵊiyuøoeaɯɤɵœɶʉAIOQWYɩ")
VOICED_C = set("bdvzʒðʤmnŋlɹwjɾɡɣɟʎɲrT")
STRESS = set("ˈˌ")
STOPS = set("ptkbdɡ")
SLIDE = set("lɹwj")                           # a consonant that can be the second sound of an onset (pl, tr, kw ...)


def is_vowel(c):
    return c in VOWEL


def frames_of(c):
    """How many frames (25 ms) a sound lasts when it is sung (the vowel gets the rest of the note)."""
    if c in STRESS or c == " " or c in "ɾʔT":
        return 1
    if c in "ʤʧfsʃθh":
        return 3
    return 2


def syllabify(ph, n):
    """The phoneme string of ONE word -> n syllables, each dict(on=[consonants], st=[stress marks], nu=[vowel sounds], co=[consonants]).
    A vowel run is the nucleus of a syllable; the consonants between two nuclei are split (one goes to the next syllable, a typical cluster like
    'st', 'pl', 'tr' goes there together), the stress mark stands before its nucleus."""
    ch = [c for c in ph if c != "ː"]
    runs, i = [], 0
    while i < len(ch):
        if is_vowel(ch[i]):
            j = i
            while j < len(ch) and is_vowel(ch[j]):
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1
    if not runs:                                                           # no vowel at all: the last sound carries the note
        ch.append("ə")
        runs = [[len(ch) - 1, len(ch)]]
    while len(runs) > n and len(runs) > 1:                                 # more vowels than notes: the two closest vowel runs are one nucleus
        gaps = [runs[k + 1][0] - runs[k][1] for k in range(len(runs) - 1)]
        k = int(np.argmin(gaps))
        runs[k] = [runs[k][0], runs[k + 1][1]]
        del runs[k + 1]
    while len(runs) < n:                                                   # fewer: split the longest run, or sing the same vowel twice
        k = max(range(len(runs)), key=lambda q: runs[q][1] - runs[q][0])
        a, b = runs[k]
        if b - a >= 2:
            m = (a + b) // 2
            runs[k:k + 1] = [[a, m], [m, b]]
        else:
            ch.insert(b, ch[a])
            for q in range(k + 1, len(runs)):
                runs[q] = [runs[q][0] + 1, runs[q][1] + 1]
            runs[k:k + 1] = [[a, b], [b, b + 1]]
    res = [dict(on=[], st=[], nu=ch[a:b], co=[]) for (a, b) in runs]
    lead0 = ch[:runs[0][0]]
    res[0]["on"] = [c for c in lead0 if c not in STRESS and c != " "]
    res[0]["st"] = [c for c in lead0 if c in STRESS]
    for k in range(len(runs)):
        cl = ch[runs[k][1]:(runs[k + 1][0] if k + 1 < len(runs) else len(ch))]
        cons = [c for c in cl if c not in STRESS and c != " "]
        marks = [c for c in cl if c in STRESS]
        if k + 1 == len(runs):
            res[k]["co"] = cons
            continue
        if len(cons) <= 1:
            on_n = len(cons)
        elif len(cons) >= 3 and cons[-3] == "s" and cons[-2] in "ptk" and cons[-1] in SLIDE:
            on_n = 3
        elif (cons[-2] == "s" and cons[-1] in "ptkmnwl") or (cons[-2] in STOPS | set("f") and cons[-1] in SLIDE):
            on_n = 2
        else:
            on_n = 1
        res[k]["co"] = cons[:len(cons) - on_n]
        res[k + 1]["on"] = cons[len(cons) - on_n:]
        res[k + 1]["st"] = marks
    return res


def plan_phrase(words_ph, counts, notes):
    """words_ph: the phoneme string of every word; counts: how many notes (syllables) every word has; notes: [(start, end, midi)] in seconds, in order.
    -> tokens [(sound, start, end, note index or None, voiced)] in seconds, and the notes extended backwards over their onset consonants."""
    sylls = []                                                              # one per note: dict(on, st, nu, co, last_of_word)
    k = 0
    for wi, ph in enumerate(words_ph):
        ss = syllabify(ph, counts[wi])
        for j, s in enumerate(ss):
            s = dict(s, last=(j == len(ss) - 1), note=k)
            sylls.append(s)
            k += 1
    assert len(sylls) == len(notes), (len(sylls), len(notes))
    on_fr = [sum(frames_of(c) for c in s["on"]) + len(s["st"]) for s in sylls]
    co_fr = [sum(frames_of(c) for c in s["co"]) + (1 if s["last"] and i + 1 < len(sylls) else 0) for i, s in enumerate(sylls)]
    toks, cursor = [], None
    ext = []
    for i, s in enumerate(sylls):
        a, b, m = notes[i]
        nxt_contig = i + 1 < len(sylls) and notes[i + 1][0] - b < 0.15
        vs = a
        don = on_fr[i] * FR
        # the vowel ends where the coda and the onset of the next syllable begin
        ve = max(vs + 0.08, b - co_fr[i] * FR - (on_fr[i + 1] * FR if nxt_contig else 0.03))
        t_on0 = vs - don
        if cursor is not None and t_on0 < cursor:                           # the onset does not fit: it is squeezed
            t_on0 = min(cursor, vs - 0.025 * max(1, len(s["on"]) + len(s["st"])))
        cons_on = list(s["on"])
        seq = [(c, False) for c in cons_on] + [(c, True) for c in s["st"]]
        wts = [frames_of(c) for c, _ in seq]
        tot = float(sum(wts)) or 1.0
        t = t_on0
        for (c, is_st), w in zip(seq, wts):
            dt = (vs - t_on0) * w / tot
            toks.append([c, t, t + dt, i, (c in VOICED_C) or is_st])
            t += dt
        nu = s["nu"]
        wn = [1.0] * len(nu)
        if len(nu) >= 2:
            wn = [0.62] + [0.38 / (len(nu) - 1)] * (len(nu) - 1)
        t = vs
        for c, w in zip(nu, wn):
            dt = (ve - vs) * w
            toks.append([c, t, t + dt, i, is_vowel(c) or c in VOICED_C])
            t += dt
        t = ve
        cons_co = list(s["co"]) + ([" "] if s["last"] and i + 1 < len(sylls) else [])
        wc = [frames_of(c) for c in cons_co]
        tc = float(sum(wc)) or 1.0
        span = co_fr[i] * FR
        for c, w in zip(cons_co, wc):
            dt = span * w / tc
            toks.append([c, t, t + dt, i, (c in VOICED_C)])
            t += dt
        cursor = t
        ext.append([t_on0, None, m])
    for i in range(len(ext)):                                               # every note begins where its first sound begins and lasts to the next one
        nxt_contig = i + 1 < len(ext) and notes[i + 1][0] - notes[i][1] < 0.15
        ext[i][1] = ext[i + 1][0] if nxt_contig else notes[i][1]
        if ext[i][1] <= ext[i][0]:
            ext[i][1] = ext[i][0] + 0.1
    return toks, [tuple(e) for e in ext]


def quantize(toks, t0):
    """Frame boundaries: [(sound, first frame, frames, note, voiced)] with t0 = the time of the frame 0."""
    out, b0 = [], 0
    for c, a, b, k, v in toks:
        b1 = max(b0 + 1, int(round((b - t0) / FR)))
        out.append((c, b0, b1 - b0, k, v))
        b0 = b1
    return out


# ------------------------------------------------------------------------------------------------------------------------ Kokoro
_K = {}


def kokoro():
    if "p" not in _K:
        import torch
        torch.set_num_threads(os.cpu_count() or 2)
        from kokoro import KPipeline
        _K["p"] = KPipeline(lang_code="a")
        _K["voices"] = {}
    return _K["p"]


def voice_pack(name):
    p = kokoro()
    if name not in _K["voices"]:
        _K["voices"][name] = p.load_voice(name)
    return _K["voices"][name]


def g2p_word(text):
    p = kokoro()
    r = p.g2p(text)
    ps = r[0] if isinstance(r, tuple) else r
    return str(ps).strip()


def ids_of(model, chars):
    return [model.vocab[c] for c in chars if c in model.vocab]


def sing_tokens(model, ids, ref_s, frames, f0):
    """Kokoro's forward pass with the length of every sound and the pitch told by us (what the model would predict is replaced).
    ids: token ids with 0 in front and at the end; frames: frames of every id; f0: Hz at 80 Hz (2 values per frame), 0 = no voice."""
    import torch
    dev = model.device
    input_ids = torch.LongTensor([ids]).to(dev)
    ref_s = ref_s.to(dev)
    input_lengths = torch.full((1,), input_ids.shape[-1], device=dev, dtype=torch.long)
    text_mask = torch.arange(input_lengths.max()).unsqueeze(0).expand(1, -1).type_as(input_lengths)
    text_mask = torch.gt(text_mask + 1, input_lengths.unsqueeze(1)).to(dev)
    with torch.no_grad():
        bert_dur = model.bert(input_ids, attention_mask=(~text_mask).int())
        d_en = model.bert_encoder(bert_dur).transpose(-1, -2)
        s = ref_s[:, 128:]
        d = model.predictor.text_encoder(d_en, s, input_lengths, text_mask)
        pred_dur = torch.LongTensor(frames).to(dev)
        indices = torch.repeat_interleave(torch.arange(input_ids.shape[1], device=dev), pred_dur)
        aln = torch.zeros((input_ids.shape[1], indices.shape[0]), device=dev)
        aln[indices, torch.arange(indices.shape[0])] = 1
        aln = aln.unsqueeze(0)
        en = d.transpose(-1, -2) @ aln
        f0_pred, n_pred = model.predictor.F0Ntrain(en, s)
        if f0 is None:
            f0t = f0_pred
        else:
            f0t = torch.from_numpy(np.asarray(f0, dtype=np.float32))[None].to(dev)
            if f0t.shape[-1] != f0_pred.shape[-1]:
                raise RuntimeError("f0 length %d, the model wants %d" % (f0t.shape[-1], f0_pred.shape[-1]))
        t_en = model.text_encoder(input_ids, input_lengths, text_mask)
        asr = t_en @ aln
        audio = model.decoder(asr, f0t, n_pred, ref_s[:, :128]).squeeze()
    return audio.cpu().numpy().astype(np.float64), f0_pred.cpu().numpy()[0]


def sing_phrase(words_ph, counts, notes, voice, hp, seed=0):
    """One phrase (words that follow each other without a rest) sung by one Kokoro voice. notes: [(start, end, midi)] in seconds.
    -> (audio at 24 kHz, time in seconds of its first sample)."""
    import torch
    from bibi_buzz import psola as P
    p = kokoro()
    model = p.model
    toks, ext = plan_phrase(words_ph, counts, notes)
    t0 = toks[0][1] - FR                                                     # one frame (silence) for the 'begin' mark in front
    q = quantize(toks, toks[0][1])
    chars = [c for c, *_ in q]
    ids = [0] + [model.vocab[c] for c in chars if c in model.vocab] + [0]
    keep = [i for i, c in enumerate(chars) if c in model.vocab]
    frames = [1] + [q[i][2] for i in keep] + [1]
    voiced = [False] + [q[i][4] for i in keep] + [False]
    notei = [None] + [q[i][3] for i in keep] + [None]
    nfr = int(sum(frames))
    pack = voice_pack(voice)
    ref_s = pack[min(len(ids) - 2, 510) - 1]
    sr_c = 1000                                                              # the note curve is asked in milliseconds
    nts = [(int(round(a * sr_c)), int(round(b * sr_c)), m) for (a, b, m) in ext]
    curve = P.note_curve_h(nts, sr_c, hp)
    tok_of_frame = np.repeat(np.arange(len(frames)), frames)
    f0 = np.zeros(2 * nfr)
    for k in range(2 * nfr):
        ti = tok_of_frame[k // 2]
        if voiced[ti] and notei[ti] is not None:
            t = t0 + (k + 0.5) * FR / 2.0
            f0[k] = curve(t * sr_c)
    if f0.max() <= 0:
        raise RuntimeError("no voiced sound")
    audio, _ = sing_tokens(model, ids, ref_s, frames, f0)
    # loudness like a person: swell and tremble of the long notes (singer.dynamics)
    from bibi_buzz import singer as SG
    for kk, (a, b, m) in enumerate(ext):
        s0 = max(0, int((a - t0) * KSR))
        s1 = min(len(audio), int((b - t0) * KSR))
        if s1 - s0 > 8:
            audio[s0:s1] *= SG.dynamics(s1 - s0, s0, s0, s1, curve.info[kk], KSR, hp)
    return audio, t0


def sing_lines(song, lang, nlines, voices, seed0=0):
    """The first nlines lines of the song with the voices (a choir when there are several) -> (track at 24 kHz, time of its sample 0)."""
    from bibi_buzz import psola as P
    from bibi_buzz import song as SO
    t = song
    items = []
    for sec in t.sections:
        if sec.get("mode", "sing") != "sing":
            continue
        for li, it in enumerate(sec["items"]):
            notes, tt = [], it["t0"]
            for m, d in it["notes"]:
                if m is not None:
                    notes.append((tt, tt + d * t.beat, m + t.shift))
                tt += d * t.beat
            items.append((sec, li, it, notes))
    items = items[:nlines]
    t_lo = items[0][3][0][0] - 0.5
    t_hi = items[-1][3][-1][1] + 0.8
    tracks = []
    for vi, V in enumerate(voices):
        tr = np.zeros(int((t_hi - t_lo) * KSR) + KSR)
        for sec, li, it, notes in items:
            words = it["words"]
            counts = [len(w["syl"]) for w in words]
            phs = [g2p_word(w["speak"]) for w in words]
            log("   line", it["key"], " ".join("%s=%s" % ("".join(w["syl"]), ph) for w, ph in zip(words, phs)))
            # a rest of a quarter second splits a line in phrases
            cut = [0]
            k = 0
            bounds = []
            for wi, w in enumerate(words):
                k += counts[wi]
                bounds.append(k)
            for wi in range(len(words) - 1):
                kk = bounds[wi]
                if notes[kk][0] - notes[kk - 1][1] > 0.25:
                    cut.append(wi + 1)
            cut.append(len(words))
            for ci in range(len(cut) - 1):
                w0, w1 = cut[ci], cut[ci + 1]
                n0 = sum(counts[:w0])
                n1 = sum(counts[:w1])
                shifted = [(a + V.get("dt", 0.0), b + V.get("dt", 0.0), m + V.get("cents", 0.0) / 100.0) for (a, b, m) in notes[n0:n1]]
                hp = P.human_params(seed=V["seed"] * 7919 + sec["index"] * 131 + li * 7 + ci, vib=V.get("vib", 1.0))
                try:
                    au, ts = sing_phrase(phs[w0:w1], counts[w0:w1], shifted, V["v"], hp)
                except Exception:
                    log("   phrase failed:", traceback.format_exc()[-600:])
                    continue
                i0 = int((ts - t_lo) * KSR)
                tr[i0:i0 + len(au)] += au[:max(0, len(tr) - i0)] * V.get("gain", 1.0)
        tracks.append(tr)
    mix = sum(tracks)
    r0 = float(np.sqrt(np.mean(tracks[0] ** 2))) + 1e-9
    r1 = float(np.sqrt(np.mean(mix ** 2))) + 1e-9
    return mix * (r0 / r1), t_lo


# ------------------------------------------------------------------------------------------------------------------------ jobs
def f0_report(name, y, sr, t_lo, notes_abs):
    """How well the sung notes are in tune (the median pitch of the middle of every note against the note)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import test_tale as TT
    errs = []
    for (a, b, m) in notes_abs:
        lo, hi = a + 0.22 * (b - a), b - 0.12 * (b - a)
        seg = y[int((lo - t_lo) * sr):int((hi - t_lo) * sr)]
        if len(seg) > int(0.12 * sr):
            f = TT._f0(seg, sr)
            if len(f) >= 3:
                errs.append(1200 * math.log2(float(np.median(f)) / (440.0 * 2 ** ((m - 69) / 12.0))))
    if errs:
        e = np.array(errs)
        log("%s: %d notes, median %+.0f cents, mean|e| %.0f, within 50: %d%%" % (name, len(e), np.median(e), np.mean(np.abs(e)), 100 * np.mean(np.abs(e) < 50)))
    else:
        log(name, ": no pitch found")


def job_env(a):
    import platform
    log("python", sys.version.split()[0], platform.platform(), "cpus", os.cpu_count())
    for m in ("numpy", "scipy", "torch", "torchaudio", "kokoro", "misaki", "vocos", "transformers", "huggingface_hub", "edge_tts"):
        try:
            mod = __import__(m)
            log("  ", m, getattr(mod, "__version__", "?"))
        except Exception as e:
            log("  ", m, "MISSING", repr(e)[:120])
    try:
        import inspect
        from kokoro import KModel
        log(inspect.getsource(KModel.forward_with_tokens))
        log("vocab size", len(kokoro().model.vocab), "".join(sorted(kokoro().model.vocab))[:300])
        r = kokoro().g2p("Twinkle twinkle little star, how I wonder what you are")
        log("g2p:", r[0] if isinstance(r, tuple) else r)
    except Exception:
        log(traceback.format_exc()[-1500:])


def job_speech(a):
    text = "Twinkle, twinkle, little star. How I wonder what you are."
    p = kokoro()
    for v in ("af_heart", "af_bella", "af_nicole", "bf_emma"):
        try:
            ys = []
            for gs, ps, au in p(text, voice=v, speed=0.9, split_pattern=r"\n+"):
                ys.append(au.numpy() if hasattr(au, "numpy") else np.asarray(au))
            save("speech-kokoro-%s" % v, np.concatenate(ys), KSR)
        except Exception:
            log(v, traceback.format_exc()[-500:])
    # Turkish with Turkish sounds (the model does not know Turkish; its Italian / Spanish / French voices may come close)
    tr_text = ["Parla parla küçük yıldız, ne olduğunu merak ediyorum.", "Bir varmış bir yokmuş, ormanda küçük bir tavşan yaşarmış."]
    model = p.model
    for v in ("if_sara", "ef_dora", "ff_siwis", "af_heart"):
        try:
            ys = []
            for line in tr_text:
                ps = tr_g2p(line)
                ids = [0] + ids_of(model, ps) + [0]
                pack = voice_pack(v)
                ref_s = pack[min(len(ids) - 2, 510) - 1]
                with __import__("torch").no_grad():
                    au, _ = model.forward_with_tokens(__import__("torch").LongTensor([ids]).to(model.device), ref_s.to(model.device), 0.9)
                ys.append(au.cpu().numpy())
                ys.append(np.zeros(int(0.5 * KSR)))
            save("speech-turkish-%s" % v, np.concatenate(ys), KSR)
        except Exception:
            log("tr", v, traceback.format_exc()[-500:])


TR_V = {"a": "ɑ", "e": "ɛ", "ı": "ɯ", "i": "i", "o": "o", "ö": "ø", "u": "u", "ü": "y"}
TR_C = {"b": "b", "c": "ʤ", "ç": "ʧ", "d": "d", "f": "f", "g": "ɡ", "h": "h", "j": "ʒ", "k": "k", "l": "l", "m": "m", "n": "n", "p": "p", "r": "ɾ", "s": "s",
        "ş": "ʃ", "t": "t", "v": "v", "y": "j", "z": "z", "ğ": ""}


def tr_g2p(text):
    """Turkish spelling -> the sounds of the model (stress on the last syllable of a word)."""
    out = []
    for word in re.findall(r"[a-zçğıöşüâîû]+|[,.!?]", text.replace("İ", "i").replace("I", "ı").lower()):
        if word in ",.!?":
            out.append(word)
            continue
        ph = []
        for c in word.replace("â", "a").replace("î", "i").replace("û", "u"):
            ph.append(TR_V.get(c) or TR_C.get(c, ""))
        last = max([i for i, c in enumerate(ph) if c in VOWEL] or [0])
        ph.insert(last, "ˈ")
        out.append("".join(ph))
    return " ".join(out).replace(" ,", ",").replace(" .", ".").replace(" !", "!").replace(" ?", "?")


def _song(a):
    from bibi_buzz import draw as D
    from bibi_buzz import songs as SS
    D.set_language(a.lang)
    return SS.build(a.song, a.lang)


def _crop(y, sr, t0, t1, t_lo=0.0):
    return y[max(0, int((t0 - t_lo) * sr)):int((t1 - t_lo) * sr)]


def _first_notes(t, nlines):
    notes = []
    items = []
    for sec in t.sections:
        if sec.get("mode", "sing") != "sing":
            continue
        for it in sec["items"]:
            items.append(it)
    for it in items[:nlines]:
        tt = it["t0"]
        for m, d in it["notes"]:
            if m is not None:
                notes.append((tt, tt + d * t.beat, m + t.shift))
            tt += d * t.beat
    return notes


def job_psola(a):
    from bibi_buzz import story as SY
    t = _song(a)
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ff = "ffmpeg"
    clips = SY.prepare(t, ff, os.path.join("out", "tts-cache"))
    voc, spans, _c = t._ensure(clips)
    notes = _first_notes(t, a.lines)
    t0, t1 = notes[0][0] - 0.5, notes[-1][1] + 0.8
    sr = 44100
    y = _crop(voc, sr, t0, t1)
    save("A-psola-choir", y, sr)
    f0_report("A-psola-choir", y, sr, t0, notes)
    np.save(os.path.join(OUT, "_psola.npy"), y.astype(np.float32))
    _K["psola"] = (y, t0)


def job_vocos(a):
    import torch
    from vocos import Vocos
    if "psola" not in _K:
        job_psola(a)
    y, t0 = _K["psola"]
    y24 = resample(y, 44100, KSR)
    y24 = y24 / (np.max(np.abs(y24)) + 1e-9) * 0.9
    v = Vocos.from_pretrained("charactr/vocos-mel-24khz").eval()
    with torch.no_grad():
        mel = v.feature_extractor(torch.from_numpy(y24).float()[None])
        out = v.decode(mel)[0].numpy()
    save("B-psola-vocos", out, KSR)
    notes = _first_notes(_song(a), a.lines)
    f0_report("B-psola-vocos", out, KSR, t0, notes)


CHOIR = [dict(v="af_heart", gain=1.0, dt=0.0, cents=0.0, vib=1.0, seed=11),
         dict(v="af_bella", gain=0.62, dt=0.012, cents=8.0, vib=0.9, seed=23),
         dict(v="bf_emma", gain=0.48, dt=-0.010, cents=-7.0, vib=1.1, seed=37)]


def job_kokoro(a):
    t = _song(a)
    notes = _first_notes(t, a.lines)
    t0, t1 = notes[0][0] - 0.5, notes[-1][1] + 0.8
    for name, voices in (("C-kokoro-single", CHOIR[:1]), ("D-kokoro-choir", CHOIR)):
        t_start = time.time()
        y, t_lo = sing_lines(t, a.lang, a.lines, voices)
        log("%s sung in %.1f s" % (name, time.time() - t_start))
        y = _crop(y, KSR, t0, t1, t_lo)
        save(name, y, KSR)
        f0_report(name, y, KSR, t0, notes)


def main():
    global OUT, _LOG
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs", nargs="?", default="all")
    ap.add_argument("--out", default="out/lab")
    ap.add_argument("--song", default="twinkle")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--lines", type=int, default=2)
    a = ap.parse_args()
    OUT = a.out
    os.makedirs(OUT, exist_ok=True)
    _LOG = open(os.path.join(OUT, "lab.txt"), "a", encoding="utf-8")
    jobs = ["env", "psola", "vocos", "speech", "kokoro"] if a.jobs == "all" else [j.strip() for j in a.jobs.split(",") if j.strip()]
    table = dict(env=job_env, speech=job_speech, psola=job_psola, vocos=job_vocos, kokoro=job_kokoro)
    for j in jobs:
        log("=" * 20, j, time.strftime("%H:%M:%S"))
        try:
            table[j](a)
        except Exception:
            log("JOB FAILED:", j, "\n" + traceback.format_exc()[-2500:])


if __name__ == "__main__":
    main()
