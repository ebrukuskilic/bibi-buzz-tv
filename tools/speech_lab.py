#!/usr/bin/env python3
"""Speech laboratory (nothing of the daily videos is touched): which voices make the NARRATOR and the CHARACTERS of a fairy tale sound like people?

The same ten lines of "The Three Little Pigs" (the narrator, Mama, two pigs, the wolf; English and Turkish) are spoken by every engine below, once as a
little scene (one mp3 per engine, so they can be listened to one after the other) and every line is measured:
  UTMOS  a model trained on people's ratings of speech: how natural does it sound (1 to 5; plain good voices are 3.8 to 4.5)
  WER    a speech recogniser (Whisper small) listens: how many of the words does it get wrong (the Turkish of a voice that is not Turkish needs this)
  RTF    seconds of work per second of speech (what an engine would cost in the daily run)

  python tools/speech_lab.py main --out out/speech         # the voices of the daily videos, plain Edge voices, Kokoro (English; Turkish with Turkish sounds)
  python tools/speech_lab.py cbx-prepare --out out/speech  # the reference clips + job files for Chatterbox (it runs in its own environment: tools/cbx_synth.py)
  python tools/speech_lab.py cbx-collect --out out/speech  # measures what Chatterbox made, adds its scenes

engines
  cur         the voices of the daily videos as they are now (Edge voices pushed far up or down in pitch, a bass effect for the wolf)
  edge-mild   Edge voices with almost no pitch change (Turkish: Emel / Ahmet, the only two there are)
  edge-multi  Edge "Multilingual" voices (English: their own language; Turkish: do they speak it at all?)
  kokoro      Kokoro-82M, a different voice for every character (English)
  kokoro-own / kokoro-esp   Kokoro with Turkish sounds (our own spelling rules / espeak-ng's Turkish), Italian / Spanish / English voices
  chatterbox  Chatterbox multilingual (an expressive neural voice that copies the voice of a short reference clip; slow on a CPU)
  kokoro-tr / kokoro-tr-shift   Kokoro-Turkish (a Turkish fine-tune of Kokoro-82M: two voices, elif and emre), plain / with the pitch of the characters moved by rubberband
  prod-kokoro  the way the daily videos would do it: bibi_buzz.tales with BIBI_KOKORO=<language> (the Kokoro voices of bibi_buzz/ktts.py, the Edge voice when Kokoro
              cannot make a line), the WHOLE tale; every line is measured and the whole tale is written as one mp3 to listen to (<language>-full-prod.mp3)
"""
import argparse
import asyncio
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import time
import traceback
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import voice_lab as VL                                    # noqa: E402  (its helpers: log, save, kokoro, voice_pack, ids_of, tr_g2p, resample, _wer)
from voice_lab import log, KSR                            # noqa: E402

OUT = "out/speech"
PICK = [2, 4, 6, 7, 27, 28, 29, 30, 53, 62]               # beats of the tale (the same in both languages)
GAP = 0.45
RES = []                                                  # (language, engine, mean UTMOS, mean WER, RTF, lines)
_M = {}


# ------------------------------------------------------------------------------------------------------------------------ the lines
def tale_lines(lang):
    from bibi_buzz import tales as T
    t = T.build("three-little-pigs", lang)
    beats = [b for sc in t.scenes for b in sc.beats if b.text]
    return t, beats


def get_lines(lang):
    t, beats = tale_lines(lang)
    return [(beats[i].who or "nar", beats[i].text) for i in PICK]


# ------------------------------------------------------------------------------------------------------------------------ audio, measures
def level(y, rms=0.085):
    y = np.asarray(y, dtype=np.float64)
    act = np.abs(y) > 0.01 * (np.max(np.abs(y)) + 1e-9)
    r = float(np.sqrt(np.mean(y[act] ** 2))) if act.any() else 1.0
    return np.clip(y * (rms / (r + 1e-9)), -1, 1)


def scene_of(ys):
    gap = np.zeros(int(GAP * KSR))
    out = []
    for y in ys:
        if y is not None and len(y) > 100:
            out += [level(y), gap]
    return np.concatenate(out) if out else np.zeros(KSR)


def utmos():
    if "u" not in _M:
        import torch
        _M["u"] = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True)
    return _M["u"]


def whisper():
    if "w" not in _M:
        from faster_whisper import WhisperModel
        _M["w"] = WhisperModel("small", device="cpu", compute_type="int8")
    return _M["w"]


def score(y, text, lang):
    y16 = VL.resample(level(y), KSR, 16000).astype(np.float32)
    out = {}
    try:
        import torch
        with torch.no_grad():
            out["mos"] = float(utmos()(torch.from_numpy(y16)[None], 16000).reshape(-1)[0])
    except Exception:
        log("utmos failed", traceback.format_exc()[-300:])
    try:
        segs, _ = whisper().transcribe(y16, language=lang, beam_size=1, condition_on_previous_text=False)
        hyp = " ".join(s.text.strip() for s in segs)
        out["wer"] = VL._wer(text, hyp, lang)
        out["heard"] = hyp
    except Exception:
        log("whisper failed", traceback.format_exc()[-300:])
    return out


def finish(lang, key, ys, lines, secs):
    """Measures every line, writes the scene (one mp3), notes the summary."""
    ms, ws = [], []
    log("---- %s  %s" % (lang, key))
    for (role, text), y in zip(lines, ys):
        if y is None or len(y) < 1000:
            log("  %-5s no audio" % role)
            continue
        s = score(y, text, lang)
        if "mos" in s:
            ms.append(s["mos"])
        if "wer" in s:
            ws.append(s["wer"])
        log("  %-5s %4.1f s  utmos %s  words wrong %s   heard: %s" % (role, len(y) / float(KSR), ("%.2f" % s["mos"]) if "mos" in s else "-",
                                                                     ("%3.0f%%" % (100 * s["wer"])) if "wer" in s else "-", s.get("heard", "")))
    dur = sum(len(y) for y in ys if y is not None) / float(KSR)
    if dur <= 0:
        log("  nothing was made")
        return
    RES.append((lang, key, float(np.mean(ms)) if ms else float("nan"), float(np.mean(ws)) if ws else float("nan"), secs / dur, len(ms)))
    VL.save("%s-%s" % (lang, key), scene_of(ys), KSR)


def summary():
    log("=" * 20, "SUMMARY (UTMOS higher is better; words wrong lower is better; RTF = seconds of work per second of speech)")
    for lang, key, m, w, rtf, n in sorted(RES):
        log("  %s  %-14s UTMOS %.2f   words wrong %3.0f%%   RTF %.2f   (%d lines)" % (lang, key, m, 100 * w, rtf, n))


# ------------------------------------------------------------------------------------------------------------------------ Edge
def edge_say(text, voice, rate="+0%", pitch="+0Hz"):
    import edge_tts
    path = os.path.join(OUT, "_edge_tmp.mp3")
    last = None
    for _ in range(4):
        try:
            asyncio.run(edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(path))
            if os.path.exists(path) and os.path.getsize(path) > 800:
                break
        except Exception as e:
            last = e
            time.sleep(2)
    else:
        raise RuntimeError("edge-tts failed for %s: %r" % (voice, last))
    y = VL._read_audio(path, KSR)
    os.remove(path)
    return y


def list_edge_voices():
    try:
        import edge_tts
        vs = asyncio.run(edge_tts.list_voices())
        log("edge-tts: %d voices; Turkish: %s" % (len(vs), [v["ShortName"] for v in vs if v.get("Locale", "").startswith("tr-")]))
        for v in vs:
            n = v["ShortName"]
            if any(k in n for k in ("Multilingual", "Turbo", "HD", "Dragon")):
                log("   %-44s %-6s %s  other languages: %s" % (n, v.get("Locale"), v.get("Gender"), v.get("SecondaryLocaleList") or v.get("VoiceTag") or "-"))
    except Exception:
        log("edge voice list failed", traceback.format_exc()[-300:])


EDGE_MILD = {
    "en": {"nar": ("en-US-JennyNeural", "-6%", "+0Hz"), "mama": ("en-US-AriaNeural", "-4%", "+0Hz"), "pig1": ("en-US-AnaNeural", "+0%", "+0Hz"),
           "pig3": ("en-US-GuyNeural", "-4%", "+0Hz"), "wolf": ("en-US-ChristopherNeural", "-10%", "-10Hz")},
    "tr": {"nar": ("tr-TR-EmelNeural", "-6%", "+0Hz"), "mama": ("tr-TR-EmelNeural", "-8%", "-6Hz"), "pig1": ("tr-TR-AhmetNeural", "+4%", "+10Hz"),
           "pig3": ("tr-TR-AhmetNeural", "+0%", "+0Hz"), "wolf": ("tr-TR-AhmetNeural", "-10%", "-14Hz")},
}
EDGE_MULTI = {                                                # the same roles with the "Multilingual" voices (for Turkish: the question is whether they can)
    "en": {"nar": ("en-US-AvaMultilingualNeural", "-6%", "+0Hz"), "mama": ("en-US-EmmaMultilingualNeural", "-2%", "+0Hz"),
           "pig1": ("en-US-AnaNeural", "+0%", "+0Hz"), "pig3": ("en-US-BrianMultilingualNeural", "-4%", "+0Hz"),
           "wolf": ("en-US-AndrewMultilingualNeural", "-12%", "-12Hz")},
    "tr": {"nar": ("en-US-AvaMultilingualNeural", "-6%", "+0Hz"), "mama": ("en-US-EmmaMultilingualNeural", "-2%", "+0Hz"),
           "pig1": ("en-AU-WilliamMultilingualNeural", "+0%", "+0Hz"), "pig3": ("en-US-BrianMultilingualNeural", "-4%", "+0Hz"),
           "wolf": ("en-US-AndrewMultilingualNeural", "-12%", "-12Hz")},
}


def e_edge(table):
    def fn(lang, lines):
        spec = table[lang]
        ys = []
        for role, text in lines:
            v, r, p = spec[role]
            try:
                ys.append(edge_say(text, v, r, p))
            except Exception:
                log("edge failed", v, traceback.format_exc()[-300:])
                ys.append(None)
        return ys
    return fn


def e_cur(lang, lines):
    """The voices of the daily videos, exactly as the pipeline makes them (rate, pitch, effects)."""
    from bibi_buzz import voice as VO
    t, beats = tale_lines(lang)
    t.voice_items()
    keys = [beats[i].key for i in PICK]
    for k in keys:
        log("   cur:", k[1], k[2], k[3], k[4] or "-")
    clips = VO.synth_items(keys, "ffmpeg", os.path.join(OUT, "_cache_cur_" + lang))
    return [VL.resample(clips[k], 44100, KSR) for k in keys]


# ------------------------------------------------------------------------------------------------------------------------ Kokoro
KOKORO_EN = {"nar": ("af_heart", 0.92), "mama": ("af_bella", 0.95), "pig1": ("am_puck", 1.0), "pig3": ("am_michael", 0.95), "wolf": ("am_fenrir", 0.88)}
KOKORO_TR = {"nar": ("if_sara", 0.9), "mama": ("ef_dora", 0.9), "pig1": ("im_nicola", 0.95), "pig3": ("em_alex", 0.92), "wolf": ("em_santa", 0.88)}


def e_kokoro(lang, lines):
    p = VL.kokoro()
    ys = []
    for role, text in lines:
        v, sp = KOKORO_EN[role]
        try:
            parts = []
            for gs, ps, au in p(text, voice=v, speed=sp, split_pattern=r"\n+"):
                parts.append(au.numpy() if hasattr(au, "numpy") else np.asarray(au))
            ys.append(np.concatenate(parts))
        except Exception:
            log("kokoro failed", v, traceback.format_exc()[-300:])
            ys.append(None)
    return ys


def espeak_ipa(text):
    """Turkish spelling -> IPA by espeak-ng (clause by clause, the punctuation is put back: the voice breathes there)."""
    out = []
    for piece in re.findall(r"[^,.!?…]+[,.!?…]*", text):
        clause = re.sub(r"[,.!?…]+$", "", piece).strip()
        punct = piece[len(piece.rstrip(",.!?…")):]
        if not clause:
            continue
        r = subprocess.run(["espeak-ng", "-v", "tr", "-q", "--ipa", clause], capture_output=True, text=True)
        s = " ".join(r.stdout.split()).replace("dʒ", "ʤ").replace("tʃ", "ʧ").replace("_", "")
        out.append(s + punct[:1])
    return " ".join(out)


def e_kokoro_tr(g2p):
    def fn(lang, lines):
        import torch
        p = VL.kokoro()
        model = p.model
        ys = []
        for role, text in lines:
            v, sp = KOKORO_TR[role]
            try:
                ps = VL.tr_g2p(text) if g2p == "own" else espeak_ipa(text)
                log("   %s %s: %s" % (role, v, ps))
                ids = [0] + VL.ids_of(model, ps) + [0]
                pack = VL.voice_pack(v)
                ref_s = pack[min(len(ids) - 2, 510) - 1]
                with torch.no_grad():
                    au, _ = model.forward_with_tokens(torch.LongTensor([ids]).to(model.device), ref_s.to(model.device), sp)
                ys.append(au.cpu().numpy())
            except Exception:
                log("kokoro-tr failed", v, traceback.format_exc()[-300:])
                ys.append(None)
        return ys
    return fn


# ------------------------------------------------------------------------------------------------------------------------ Kokoro-Turkish (a Turkish fine-tune of Kokoro-82M, Apache 2.0: huggingface.co/empiriolabsai/kokoro-turkish)
KTR_REPO = "empiriolabsai/kokoro-turkish"
KTR_ROLES = {                         # role: (voice = a mix of the two voices of the model, speed, pitch ratio, 'shifted' = the formants move with the pitch: a smaller / bigger person)
    "nar": ({"elif": 1.0}, 0.95, 1.0, "shifted"),
    "mama": ({"elif": 0.7, "emre": 0.3}, 0.93, 0.97, "preserved"),
    "pig1": ({"elif": 0.4, "emre": 0.6}, 1.05, 1.22, "shifted"),
    "pig3": ({"emre": 1.0}, 0.97, 1.0, "shifted"),
    "wolf": ({"emre": 1.0}, 0.88, 0.84, "shifted"),
}


def pitch_shift(y, ratio, formant="shifted"):
    """ffmpeg's rubberband: the pitch x ratio ('preserved' keeps the size of the speaker, 'shifted' makes him smaller / bigger)."""
    if abs(ratio - 1.0) < 0.005:
        return y
    src, dst = os.path.join(OUT, "_ps_in.wav"), os.path.join(OUT, "_ps_out.wav")
    VL.write_wav(src, np.clip(y, -1, 1), KSR)
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", "rubberband=pitch=%.4f:formant=%s:pitchq=quality" % (ratio, formant), dst],
                       capture_output=True, text=True)
    if r.returncode:
        log("rubberband failed", r.stderr[:300])
        return y
    with wave.open(dst) as w:
        z = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    os.remove(src)
    os.remove(dst)
    return z


def ktr():
    """(its text-to-sounds module, the model, the voices already loaded)"""
    if "ktr" not in _M:
        import torch
        from huggingface_hub import hf_hub_download, list_repo_files
        from kokoro import KModel
        from bibi_buzz.g2p_tr import TurkishG2P                # the text-to-sounds module is kept (and was read through) in this repository: no code of the model's page is run
        torch.set_num_threads(os.cpu_count() or 2)
        try:
            log("kokoro-turkish files:", list_repo_files(KTR_REPO))
        except Exception:
            log("list_repo_files failed", traceback.format_exc()[-200:])
        g2p = TurkishG2P()
        # only data is downloaded from the model's page: its config (json), its weights (loaded by kokoro with weights_only=True) and the voices (loaded below the same way)
        net = KModel(repo_id=KTR_REPO, config=hf_hub_download(KTR_REPO, "config.json"), model=hf_hub_download(KTR_REPO, "kokoro-turkish.pth")).eval()
        _M["ktr"] = (g2p, net, {})
    return _M["ktr"]


def ktr_style(blend):
    import torch
    from huggingface_hub import hf_hub_download
    cache = ktr()[2]
    out = None
    for name, w in blend.items():
        if name not in cache:
            cache[name] = torch.load(hf_hub_download(KTR_REPO, "voices/%s.pt" % name), weights_only=True)
        out = cache[name] * w if out is None else out + cache[name] * w
    return out


def e_kokoro_ft(shift):
    def fn(lang, lines):
        import torch
        g2p, net, _ = ktr()
        ys = []
        for role, text in lines:
            blend, sp, ratio, fm = KTR_ROLES[role]
            try:
                ph, _ = g2p(text)
                log("   %s %s: %s" % (role, "+".join(blend), ph))
                st = ktr_style(blend)
                with torch.no_grad():
                    au = net(ph, st[len(ph) - 1], sp)
                y = au.numpy() if hasattr(au, "numpy") else np.asarray(au)
                ys.append(pitch_shift(y, ratio, fm) if shift else y)
            except Exception:
                log("kokoro-turkish failed", role, traceback.format_exc()[-500:])
                ys.append(None)
        return ys
    return fn


# ------------------------------------------------------------------------------------------------------------------------ the daily videos' way (bibi_buzz/ktts.py)
def e_prod(lang, lines):
    """The whole tale with the production casting (bibi_buzz.tales.cast_voices with BIBI_KOKORO set for this language and voice.synth_items, Edge as the stand-in):
    every line is measured, per character, and the whole tale is one mp3; the ten lines of the scene are returned for the usual table."""
    from bibi_buzz import voice as VO
    old = os.environ.get("BIBI_KOKORO")
    os.environ["BIBI_KOKORO"] = lang
    try:
        t, beats = tale_lines(lang)
        t.voice_items()
        keys = [b.key for b in beats]
        who = [b.who or "nar" for b in beats]
        log("   production casting:", {w: t.voices[w][0] for w in sorted(set(who))})
        buf = io.StringIO()
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            clips = VO.synth_items(keys, "ffmpeg", os.path.join(OUT, "_cache_prod_" + lang))
        work = time.time() - t0
        for ln in buf.getvalue().splitlines():
            log("   " + ln)
    finally:
        if old is None:
            os.environ.pop("BIBI_KOKORO", None)
        else:
            os.environ["BIBI_KOKORO"] = old
    ys = [VL.resample(clips[k], 44100, KSR) for k in keys]
    dur = sum(len(y) for y in ys) / float(KSR)
    log("   %d lines, %.0f s of speech, %.0f s of work (RTF %.2f, Kokoro model loading included)" % (len(ys), dur, work, work / max(dur, 1e-9)))
    _M["secs_override"] = work * (sum(len(ys[i]) for i in PICK) / float(KSR)) / max(dur, 1e-9)       # (the share of the ten lines)
    VL.save("%s-full-prod" % lang, scene_of(ys), KSR)
    agg = {}
    for w, b, y in zip(who, beats, ys):
        s = score(y, b.text, lang)
        a = agg.setdefault(w, [[], [], 0.0])
        if "mos" in s:
            a[0].append(s["mos"])
        if "wer" in s:
            a[1].append(s["wer"])
        a[2] += len(y) / float(KSR)
        if s.get("wer", 0) > 0.25 or s.get("mos", 5) < 3.2:
            log("   ATTENTION %-6s utmos %s words wrong %s   %r   heard: %r" % (w, ("%.2f" % s["mos"]) if "mos" in s else "-", ("%.0f%%" % (100 * s["wer"])) if "wer" in s else "-",
                                                                          b.text[:60], s.get("heard", "")[:60]))
    log("   per character (%s):  lines  seconds  UTMOS  words wrong" % lang)
    for w in sorted(agg):
        m, e, sec = agg[w]
        log("      %-6s %3d  %6.1f   %s   %s   voice %s" % (w, len(e) or len(m), sec, ("%.2f" % np.mean(m)) if m else " - ", ("%3.0f%%" % (100 * np.mean(e))) if e else " - ", t.voices[w][0]))
    return [ys[i] for i in PICK]


# ------------------------------------------------------------------------------------------------------------------------ Chatterbox (runs in its own environment: tools/cbx_synth.py)
CBX_REF_TEXT = {"en": "Once upon a time, in a little green valley, there lived a family of friendly animals. Every morning they woke up with the sun.",
                "tr": "Evvel zaman içinde, küçük yeşil bir vadide, dostane bir hayvan ailesi yaşarmış. Her sabah güneşle birlikte uyanırlarmış."}
CBX_REF = {                                                   # role -> the voice that makes the reference clip (the copy will speak with ITS voice)
    "en": {"nar": ("en-US-AvaMultilingualNeural", "-6%", "+0Hz"), "mama": ("en-US-EmmaMultilingualNeural", "-2%", "+0Hz"),
           "pig1": ("en-US-AnaNeural", "+0%", "+0Hz"), "pig3": ("en-US-BrianMultilingualNeural", "-4%", "+0Hz"),
           "wolf": ("en-US-AndrewMultilingualNeural", "-14%", "-18Hz")},
    "tr": {"nar": ("tr-TR-EmelNeural", "-6%", "+0Hz"), "mama": ("tr-TR-EmelNeural", "-8%", "-6Hz"), "pig1": ("en-US-AnaNeural", "+0%", "+0Hz"),
           "pig3": ("tr-TR-AhmetNeural", "+0%", "+0Hz"), "wolf": ("tr-TR-AhmetNeural", "-12%", "-24Hz")},
}
CBX_STYLE = {"nar": (0.5, 0.5), "mama": (0.55, 0.5), "pig1": (0.7, 0.4), "pig3": (0.6, 0.5), "wolf": (0.8, 0.3)}      # (exaggeration, cfg_weight)


def cbx_prepare(a):
    for lang in ("tr", "en"):
        lines = get_lines(lang)
        refdir = os.path.join(OUT, "_cbx_refs_" + lang)
        os.makedirs(refdir, exist_ok=True)
        refs = {}
        for role in sorted({r for r, _ in lines}):
            v, r, p = CBX_REF[lang][role]
            try:
                y = edge_say(CBX_REF_TEXT["tr" if v.startswith("tr-") else "en"], v, r, p)
                path = os.path.join(refdir, role + ".wav")
                VL.write_wav(path, level(y, 0.1), KSR)
                refs[role] = path
                log("reference", lang, role, v, "%.1f s" % (len(y) / float(KSR)))
            except Exception:
                log("reference failed", lang, role, traceback.format_exc()[-300:])
        job = {"lang": lang, "budget": 1300, "lines": [dict(i=k, role=role, text=text, ref=refs.get(role), ex=CBX_STYLE[role][0], cfg=CBX_STYLE[role][1])
                                                        for k, (role, text) in enumerate(lines) if refs.get(role)]}
        with open(os.path.join(OUT, "_cbx_%s.json" % lang), "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False, indent=1)


def cbx_collect(a):
    for lang in ("tr", "en"):
        d = os.path.join(OUT, "_cbx_%s" % lang)
        lines = get_lines(lang)
        try:
            times = json.load(open(os.path.join(d, "times.json")))
        except Exception:
            log("chatterbox", lang, "nothing was made (no times.json)")
            continue
        ys, secs = [], 0.0
        for k, _ in enumerate(lines):
            path = os.path.join(d, "%d.wav" % k)
            if os.path.exists(path):
                with wave.open(path) as w:
                    y = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
                    ys.append(VL.resample(y, w.getframerate(), KSR) if w.getframerate() != KSR else y)
                secs += float(times.get(str(k), [0, 0])[0])
            else:
                ys.append(None)
        finish(lang, "7-chatterbox", ys, lines, secs)
        for k in sorted(times, key=int):
            log("   line %s: %.1f s of audio in %.1f s of work" % (k, times[k][1], times[k][0]))


# ------------------------------------------------------------------------------------------------------------------------ main
ENGINES = [                                                   # (language, key, function)
    ("en", "1-cur", e_cur), ("en", "2-edge-multi", e_edge(EDGE_MULTI)), ("en", "3-kokoro", e_kokoro), ("en", "4-prod-kokoro", e_prod),
    ("tr", "1-cur", e_cur), ("tr", "2-edge-mild", e_edge(EDGE_MILD)), ("tr", "3-edge-multi", e_edge(EDGE_MULTI)),
    ("tr", "4-kokoro-tr", e_kokoro_ft(False)), ("tr", "5-kokoro-tr-shift", e_kokoro_ft(True)), ("tr", "6-prod-kokoro", e_prod),
]
# (the Italian-voice try, e_kokoro_tr("own") / e_kokoro_tr("esp"), is not an engine any more: 34 % / 74 % of its words were wrong in the first run)


def job_main(a):
    import platform
    log("python", sys.version.split()[0], platform.platform(), "cpus", os.cpu_count())
    for m in ("numpy", "scipy", "torch", "torchaudio", "kokoro", "misaki", "faster_whisper", "edge_tts"):
        try:
            mod = __import__(m)
            log("  ", m, getattr(mod, "__version__", "?"))
        except Exception as e:
            log("  ", m, "MISSING", repr(e)[:120])
    list_edge_voices()
    only = [x for x in (a.only or "").split(",") if x]
    for lang, key, fn in ENGINES:
        if only and key.split("-", 1)[1] not in only and key not in only:
            continue
        lines = get_lines(lang)
        t0 = time.time()
        _M.pop("secs_override", None)
        try:
            ys = fn(lang, lines)
        except Exception:
            log("ENGINE FAILED", lang, key, traceback.format_exc()[-1500:])
            continue
        finish(lang, key, ys, lines, _M.pop("secs_override", time.time() - t0))
    summary()


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("job", choices=["main", "cbx-prepare", "cbx-collect"])
    ap.add_argument("--out", default="out/speech")
    ap.add_argument("--only", default="", help="engine keys, comma separated (main only)")
    a = ap.parse_args()
    OUT = a.out
    VL.OUT = OUT
    os.makedirs(OUT, exist_ok=True)
    VL._LOG = open(os.path.join(OUT, "lab.txt"), "a", encoding="utf-8")
    log("=" * 20, a.job, time.strftime("%H:%M:%S"))
    try:
        {"main": job_main, "cbx-prepare": cbx_prepare, "cbx-collect": cbx_collect}[a.job](a)
        if a.job == "cbx-collect":
            summary()
    except Exception:
        log("JOB FAILED:", a.job, "\n" + traceback.format_exc()[-2500:])


if __name__ == "__main__":
    main()
