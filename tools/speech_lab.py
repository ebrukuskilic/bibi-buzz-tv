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
  cast        the CASTING sweep (--only cast): every character type of the tales says its own line in several Kokoro voices / sizes (bibi_buzz/ktts.py speak(): a
              smaller or bigger person by shift_voice, not by a pitch shifter), measured (UTMOS, words wrong, pitch F0), plus a ladder of sizes and a comparison with
              the pitch shifter; one gallery mp3 per language (cast-<language>.mp3: the narrator says the type, then every candidate says the line)
  palette     (--only palette) EVERY voice (English: the 28 of Kokoro-82M; Turkish: mixes of elif and emre, and voices of the English model tried on the Turkish one)
              at several sizes, measured (PAL lines: F0, UTMOS, words wrong); palette-<language>.mp3 = the voices one after the other, the narrator says their number
              (GALLERY lines: number = voice)
  studio      (--only studio) the same clips as they are and through two EQ + compression chains (STUDIO lines)
  gallery     (--only gallery) the casting of some tales the way the daily videos make it (bibi_buzz.tales.cast_voices), every character says its type's line:
              gallery-<language>.mp3, GAL lines (F0, UTMOS, words wrong), GALWARN lines for the pairs of one tale that may sound alike by their pitch and SIM lines:
              the cosine of the ECAPA voice prints of every pair of one tale (speechbrain; 1.0 = the same voice; the pairs at or above SIM_ALIKE are marked)
  world       (--only world) a smaller person without the chipmunk: the same lively line of some voices resampled (pitch and formants by one factor: what ktts.py does)
              and made by the WORLD vocoder (pitch by a factor, the vocal tract by a smaller one): WORLD lines, world-<language>.mp3
  ext         (the jobs ext-prepare / ext-collect around tools/ext_synth.py, which runs in its own environment) the new voice engines: Pocket TTS Turkish (six voices, emotion
              tags; the casting of the six tales: GAL lines with the tag tr-pocket, gallery-tr-pocket.mp3) and Phonon 31m English (every English voice of its catalog):
              EXT lines (F0, UTMOS, words wrong, seconds of work), palette-<engine>.mp3
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


# ------------------------------------------------------------------------------------------------------------------------ Kokoro-Turkish (a Turkish fine-tune of Kokoro-82M, Apache 2.0: huggingface.co/empiriolabsai/canora-turkish, kokoro-turkish until 21 Nov 2026)
KTR_REPO = "empiriolabsai/canora-turkish"
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
        from bibi_buzz import ktts as KT0
        try:
            log("the files of the Turkish model:", list_repo_files(KT0.TR_REPOS[0]))
        except Exception:
            log("list_repo_files failed", traceback.format_exc()[-200:])
        g2p = TurkishG2P()
        # only data is downloaded from the model's page: its config (json), its weights (loaded by kokoro with weights_only=True) and the voices (loaded below the same way);
        # the page was renamed on 21 Nov 2026 (kokoro-turkish -> canora-turkish, the weights file with it): bibi_buzz.ktts tries the names the model has had
        repo, config, weights = KT0._tr_fetch()
        log("the Turkish model comes from", repo)
        _M["ktr-repo"] = repo
        net = KModel(repo_id=repo, config=config, model=weights).eval()
        _M["ktr"] = (g2p, net, {})
    return _M["ktr"]


def ktr_style(blend):
    import torch
    from huggingface_hub import hf_hub_download
    cache = ktr()[2]
    out = None
    for name, w in blend.items():
        if name not in cache:
            cache[name] = torch.load(hf_hub_download(_M.get("ktr-repo", KTR_REPO), "voices/%s.pt" % name), weights_only=True)
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


def cbx_collect(a, key="7-chatterbox", pre="_cbx_"):
    for lang in ("tr", "en"):
        d = os.path.join(OUT, "%s%s" % (pre, lang))
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
        finish(lang, key, ys, lines, secs)
        for k in sorted(times, key=int):
            log("   line %s: %.1f s of audio in %.1f s of work" % (k, times[k][1], times[k][0]))


# ------------------------------------------------------------------------------------------------------------------------ the user's own voice (Chatterbox copies the voice of a short reference clip)
MV_STYLE = {"nar": (0.45, 0.45), "mama": (0.55, 0.5), "pig1": (0.65, 0.45), "pig3": (0.6, 0.5), "wolf": (0.75, 0.4)}      # (exaggeration, cfg_weight) of the roles of the ten lines


def myvoice_prepare(a):
    """The reference clips are NOT in the repository: they come from the secrets MYVOICE_TR and MYVOICE_EN of the repository (base64 of a short opus clip), are decoded
    into out/speech/_ref (a folder that is never copied to the result) and measured (UTMOS, what Whisper hears); then the job files of Chatterbox are written: the
    ten lines of the tale, every role in the same voice (a person who reads a story aloud), with the feeling of the role."""
    import base64
    refdir = os.path.join(OUT, "_ref")
    os.makedirs(refdir, exist_ok=True)
    for lang in ("tr", "en"):
        b64 = (os.environ.get("MYVOICE_" + lang.upper()) or "").strip()
        if not b64:
            log("myvoice %s: no reference clip (the secret MYVOICE_%s is empty)" % (lang, lang.upper()))
            continue
        try:
            src = os.path.join(refdir, lang + ".opus")
            with open(src, "wb") as f:
                f.write(base64.b64decode(b64))
            wav = os.path.join(refdir, lang + ".wav")
            r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", str(KSR), "-ac", "1", wav], capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError(r.stderr[-200:])
        except Exception:
            log("myvoice %s: the reference clip could not be decoded" % lang, traceback.format_exc()[-300:])
            continue
        try:
            with wave.open(wav) as w:
                y = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
            sc = score(y, "", lang)
            # (what she says in the clip stays private: lab.txt is public, so only the number of the words that Whisper hears is logged, never the words)
            log("myvoice %s: reference clip %.1f s, F0 %s Hz, UTMOS %s; Whisper hears %d words" % (lang, len(y) / float(KSR), ("%.0f" % f0_of(y)) if f0_of(y) else "-",
                                                                                                  ("%.2f" % sc["mos"]) if "mos" in sc else "-", len(sc.get("heard", "").split())))
        except Exception:
            log("myvoice %s: the reference clip could not be measured" % lang, traceback.format_exc()[-200:])
        lines = get_lines(lang)
        job = {"lang": lang, "budget": 1300, "lines": [dict(i=k, role=role, text=text, ref=wav, ex=MV_STYLE.get(role, (0.5, 0.5))[0], cfg=MV_STYLE.get(role, (0.5, 0.5))[1])
                                                        for k, (role, text) in enumerate(lines)]}
        with open(os.path.join(OUT, "_myvoice_%s.json" % lang), "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False, indent=1)


def myvoice_collect(a):
    cbx_collect(a, key="8-myvoice", pre="_myvoice_")


def myvox_prepare(a):
    """Her voice with VoxCPM2 (instead of Chatterbox): myvoice_prepare decodes her reference clips from the secrets and measures them; the job file of tools/ext_synth.py clones
    the ten lines of the three-pigs tale from them (the instruction in front of a line steers the feeling of its role: FD_STYLE).  Only the numbers go to the log, never her words."""
    myvoice_prepare(a)
    items = []
    for lang in ("en", "tr"):
        try:
            job = json.load(open(os.path.join(OUT, "_myvoice_%s.json" % lang), encoding="utf-8"))
        except Exception:
            continue
        for ln in job["lines"]:
            items.append(dict(id="mv-%s-%d" % (lang, ln["i"]), engine="vox", voice="me", design=FD_STYLE.get(ln["role"], FD_STYLE["nar"]), ref=ln["ref"], text=ln["text"],
                              group="myvox", lang=lang))
    with open(os.path.join(OUT, "_myvox.json"), "w", encoding="utf-8") as f:
        json.dump({"budget": 1500, "items": items}, f, ensure_ascii=False, indent=1)
    log("myvox-prepare: %d lines to clone" % len(items))


def myvox_collect(a):
    """Measures her cloned lines: MYVOX lines (ECAPA cos of every line to her reference clip: the same person is 0.7 and more, two people usually below 0.5), the usual lines of the
    lab, and tr-8-myvoice-vox.mp3 / en-8-myvoice-vox.mp3 (the word 'myvoice' in the name: the workflow publishes the scene only encrypted)."""
    d = os.path.join(OUT, "_myvox")
    try:
        man = json.load(open(os.path.join(d, "manifest.json"), encoding="utf-8"))
    except Exception:
        log("myvox: nothing was made (no manifest.json)")
        return
    by = {m["id"]: m for m in man if m.get("ok")}
    for lang in ("tr", "en"):
        lines = get_lines(lang)
        refw = os.path.join(OUT, "_ref", lang + ".wav")
        ref_e = try_embed(_read_wav24(refw)) if os.path.exists(refw) else None
        ys, secs, cs = [], 0.0, []
        for k, (role, text) in enumerate(lines):
            m = by.get("mv-%s-%d" % (lang, k))
            if not m:
                ys.append(None)
                continue
            y = _read_wav24(os.path.join(d, m["id"] + ".wav"))
            ys.append(y)
            secs += m["work"]
            e = try_embed(y)
            if ref_e is not None and e is not None:
                cs.append(float(np.dot(e, ref_e)))
                log("MYVOX %s line %d %-5s cos to her reference %.2f" % (lang, k, role, cs[-1]))
        if cs:
            log("MYVOXSUM %s: cos of the clones to her reference mean %.2f min %.2f (the same person: 0.7 and more; two people: usually below 0.5)" % (lang, float(np.mean(cs)), min(cs)))
        if any(y is not None for y in ys):
            finish(lang, "8-myvoice-vox", ys, lines, secs)


# ------------------------------------------------------------------------------------------------------------------------ the casting sweep (--only cast)
# type -> candidates (Kokoro voice or mix, rate, pitch); the pitch is "+X Hz" = a factor of 1 + X / 150 (a smaller / bigger person: bibi_buzz/ktts.py shift_voice)
CAST_EN = {
    "nar": [("af_heart", "-8%", "+0Hz"), ("af_heart", "-4%", "+0Hz"), ("af_bella", "-6%", "+0Hz")],
    "girl": [("af_bella", "-2%", "+10Hz"), ("af_aoede", "-2%", "+14Hz"), ("af_kore", "-2%", "+16Hz")],
    "teen": [("af_kore", "-2%", "+0Hz"), ("af_sarah", "-2%", "+6Hz"), ("af_aoede", "-2%", "+0Hz")],
    "boy": [("am_puck", "+4%", "+16Hz"), ("am_puck", "+4%", "+24Hz"), ("am_michael", "+4%", "+30Hz")],
    "baby": [("af_bella", "+0%", "+40Hz"), ("af_aoede", "+0%", "+38Hz"), ("af_kore", "+0%", "+40Hz")],
    "woman": [("af_bella", "-4%", "+0Hz"), ("af_nicole", "-4%", "+0Hz"), ("bf_emma", "-4%", "+0Hz")],
    "granny": [("bf_emma", "-14%", "-10Hz"), ("af_nicole", "-14%", "-14Hz"), ("bf_isabella", "-14%", "-10Hz")],
    "fakegranny": [("am_michael", "-8%", "+30Hz"), ("am_puck", "-8%", "+16Hz")],
    "man": [("am_michael", "-6%", "+0Hz"), ("am_fenrir", "-6%", "+8Hz"), ("am_puck", "-6%", "-8Hz")],
    "grandpa": [("bm_fable", "-14%", "-8Hz"), ("am_michael", "-14%", "-14Hz"), ("bm_george", "-14%", "-8Hz")],
    "prince": [("am_puck", "+0%", "+0Hz"), ("am_michael", "+0%", "+8Hz"), ("bm_fable", "+0%", "+6Hz")],
    "king": [("bm_george", "-14%", "-12Hz"), ("am_fenrir", "-14%", "-14Hz"), ("bm_fable", "-14%", "-14Hz")],
    "lord": [("bm_fable", "-8%", "-4Hz"), ("bm_george", "-8%", "-6Hz")],
    "queen": [("bf_emma", "-10%", "-8Hz"), ("bf_isabella", "-10%", "-8Hz"), ("af_nicole", "-10%", "-10Hz")],
    "stepmother": [("af_nicole", "-12%", "-10Hz"), ("bf_isabella", "-12%", "-12Hz")],
    "stepsister": [("af_kore", "+6%", "+12Hz"), ("af_sarah", "+6%", "+14Hz"), ("af_aoede", "+6%", "+12Hz")],
    "witch": [("af_nicole", "-14%", "-20Hz"), ("bf_emma", "-14%", "-20Hz"), ("af_nicole", "-14%", "-14Hz")],
    "fairy": [("af_aoede", "-8%", "+14Hz"), ("af_sarah", "-8%", "+14Hz")],
    "mirror": [("bm_fable", "-18%", "-6Hz"), ("bm_george", "-18%", "-10Hz")],
    "dwarf": [("am_michael", "+6%", "+20Hz"), ("am_puck", "+6%", "+4Hz")],
    "elf": [("am_puck", "+10%", "+24Hz"), ("am_puck", "+10%", "+30Hz")],
    "elfgirl": [("af_bella", "+10%", "+28Hz"), ("af_aoede", "+10%", "+28Hz")],
    "troll": [("am_fenrir", "-16%", "-26Hz"), ("am_fenrir", "-16%", "-34Hz"), ("am_onyx", "-16%", "-28Hz")],
    "giant": [("am_fenrir", "-16%", "-34Hz"), ("am_onyx", "-16%", "-34Hz")],
    "pig": [("am_puck", "+2%", "+12Hz"), ("am_puck", "+2%", "+20Hz"), ("am_michael", "+2%", "+20Hz")],
    "wolf": [("am_fenrir", "-10%", "-20Hz"), ("am_fenrir", "-10%", "-28Hz"), ("bm_george", "-10%", "-22Hz")],
    "hare": [("am_puck", "+8%", "+16Hz"), ("am_puck", "+8%", "+24Hz")],
    "tortoise": [("am_michael", "-20%", "-8Hz"), ("bm_fable", "-20%", "-10Hz")],
    "bear": [("am_fenrir", "-12%", "-12Hz"), ("am_michael", "-12%", "-18Hz")],
    "mamabear": [("af_nicole", "-8%", "-14Hz"), ("bf_emma", "-8%", "-14Hz")],
    "goat_little": [("am_puck", "+4%", "+22Hz"), ("af_sky", "+4%", "+20Hz")],
    "goat_mid": [("am_michael", "+0%", "+8Hz"), ("am_puck", "+0%", "+0Hz")],
    "goat_big": [("am_fenrir", "-14%", "-14Hz"), ("am_fenrir", "-14%", "-22Hz")],
    "hen": [("af_kore", "+4%", "+10Hz"), ("af_sarah", "+4%", "+12Hz")],
    "fox": [("bm_fable", "-4%", "+0Hz"), ("am_puck", "-4%", "-6Hz")],
    "tiny": [("af_bella", "+8%", "+45Hz"), ("af_aoede", "+8%", "+45Hz"), ("af_sky", "+8%", "+40Hz")],
    "lion": [("am_fenrir", "-12%", "-28Hz"), ("am_fenrir", "-12%", "-34Hz")],
}
E9, E8, E7 = "elif=0.9,emre=0.1", "elif=0.8,emre=0.2", "elif=0.7,emre=0.3"
M8, M7 = "elif=0.2,emre=0.8", "elif=0.3,emre=0.7"
CAST_TR = {
    "nar": [("elif", "-5%", "+0Hz"), ("elif", "-8%", "+0Hz"), (E9, "-5%", "+0Hz")],
    "girl": [("elif", "-2%", "+15Hz"), ("elif", "-2%", "+24Hz"), (E9, "-2%", "+20Hz")],
    "teen": [("elif", "-2%", "+6Hz"), ("elif", "-2%", "+0Hz")],
    "boy": [("emre", "+4%", "+18Hz"), ("emre", "+4%", "+26Hz"), (M7, "+4%", "+20Hz")],
    "baby": [("elif", "+0%", "+40Hz"), ("elif", "+0%", "+32Hz")],
    "woman": [(E8, "-8%", "+0Hz"), ("elif", "-8%", "-4Hz")],
    "granny": [("elif", "-14%", "-10Hz"), (E8, "-14%", "-12Hz")],
    "fakegranny": [("emre", "-8%", "+30Hz"), ("emre", "-8%", "+20Hz")],
    "man": [("emre", "-6%", "+0Hz"), (M8, "-6%", "+0Hz")],
    "grandpa": [("emre", "-12%", "-10Hz"), ("emre", "-12%", "-14Hz")],
    "prince": [("emre", "-2%", "+6Hz"), (M8, "-2%", "+8Hz")],
    "king": [("emre", "-14%", "-14Hz"), ("emre", "-14%", "-20Hz")],
    "lord": [("emre", "-10%", "-8Hz"), ("emre", "-10%", "-12Hz")],
    "queen": [("elif", "-12%", "-10Hz"), (E9, "-12%", "-12Hz")],
    "stepmother": [(E8, "-10%", "-10Hz"), ("elif", "-10%", "-12Hz")],
    "stepsister": [("elif", "+6%", "+16Hz"), ("elif", "+6%", "+24Hz")],
    "witch": [("elif", "-14%", "-20Hz"), (E7, "-14%", "-22Hz")],
    "fairy": [("elif", "-14%", "+8Hz"), ("elif", "-14%", "+14Hz")],
    "mirror": [("emre", "-16%", "-8Hz"), ("emre", "-16%", "-12Hz")],
    "dwarf": [("emre", "+8%", "+16Hz"), ("emre", "+8%", "+24Hz")],
    "elf": [("emre", "+10%", "+26Hz"), ("emre", "+10%", "+34Hz")],
    "elfgirl": [("elif", "+10%", "+28Hz"), ("elif", "+10%", "+34Hz")],
    "troll": [("emre", "-16%", "-28Hz"), ("emre", "-16%", "-34Hz")],
    "giant": [("emre", "-18%", "-38Hz"), ("emre", "-18%", "-44Hz")],
    "pig": [("emre", "+4%", "+12Hz"), ("emre", "+4%", "+20Hz")],
    "wolf": [("emre", "-10%", "-20Hz"), ("emre", "-10%", "-28Hz")],
    "hare": [("emre", "+8%", "+24Hz"), ("emre", "+8%", "+32Hz")],
    "tortoise": [("emre", "-20%", "-8Hz"), ("emre", "-20%", "-12Hz")],
    "bear": [("emre", "-12%", "-20Hz"), ("emre", "-12%", "-26Hz")],
    "mamabear": [("elif", "-10%", "-14Hz"), (E8, "-10%", "-16Hz")],
    "goat_little": [("elif", "+4%", "+28Hz"), ("elif", "+4%", "+36Hz")],
    "goat_mid": [("emre", "+2%", "+14Hz"), ("emre", "+2%", "+20Hz")],
    "goat_big": [("emre", "-10%", "-20Hz"), ("emre", "-10%", "-28Hz")],
    "hen": [("elif", "+2%", "+20Hz"), ("elif", "+2%", "+28Hz")],
    "fox": [("emre", "-4%", "+6Hz"), ("emre", "-4%", "+12Hz")],
    "tiny": [("elif", "+8%", "+45Hz"), ("elif", "+8%", "+38Hz")],
    "lion": [("emre", "-12%", "-28Hz"), ("emre", "-12%", "-34Hz")],
}
LADDER = {"en": ["af_bella", "am_michael"], "tr": ["elif", "emre"]}
LADDER_LINE = {"en": "The little bird sat on the branch and sang a happy song.", "tr": "Küçük kuş dalın üstüne konup neşeli bir şarkı söyledi."}
LADDER_F = [0.75, 0.85, 0.92, 1.0, 1.08, 1.16, 1.25, 1.35, 1.45]
VS_PS = {"en": [("boy", "am_puck", "+24Hz"), ("wolf", "am_fenrir", "-28Hz"), ("baby", "af_bella", "+40Hz")],
         "tr": [("boy", "emre", "+26Hz"), ("wolf", "emre", "-28Hz"), ("baby", "elif", "+40Hz")]}


def f0_of(y, sr=KSR):
    """Median pitch (Hz) of the voiced frames of a clip: normalized autocorrelation by FFT on a copy at a third of the sample rate; None when there is no pitch."""
    n3 = len(y) // 3 * 3
    y = np.asarray(y[:n3], dtype=np.float64).reshape(-1, 3).mean(axis=1)
    sr //= 3
    fl, hop = int(0.04 * sr), int(0.01 * sr)
    lo, hi = int(sr / 520), int(sr / 70)
    if len(y) < fl + hop * 4:
        return None
    idx = np.arange(0, len(y) - fl, hop)
    fr = np.stack([y[i:i + fl] for i in idx])
    fr = (fr - fr.mean(axis=1, keepdims=True)) * np.hanning(fl)
    e = np.sqrt((fr ** 2).mean(axis=1))
    nfft = 1 << (2 * fl - 1).bit_length()
    sp = np.fft.rfft(fr, n=nfft, axis=1)
    ac = np.fft.irfft(sp * np.conj(sp), axis=1)[:, :hi + 1]
    ac = ac / (ac[:, :1] + 1e-12)
    out = []
    thr = 0.35 * np.percentile(e, 90)
    for k in range(len(idx)):
        if e[k] < thr:
            continue
        seg = ac[k, lo:hi + 1]
        j = int(np.argmax(seg))
        if seg[j] > 0.55 and 0 < j < len(seg) - 1:
            a, b, c = seg[j - 1], seg[j], seg[j + 1]
            d = a - 2 * b + c
            out.append(sr / (lo + j + (0.5 * (a - c) / d if abs(d) > 1e-12 else 0.0)))
    return float(np.median(out)) if len(out) >= 8 else None


def cast_sweep(a):
    """Every character type of the tales says its line in the candidate voices; every clip is measured; one gallery mp3 per language."""
    os.environ["BIBI_KOKORO_INPROC"] = "1"                              # (the model is loaded once, in this process)
    try:
        _cast_sweep()
    finally:
        os.environ.pop("BIBI_KOKORO_INPROC", None)                      # (the engines after it work the way the daily videos do: Kokoro in a worker process)


def _cast_sweep():
    from bibi_buzz import ktts as KT
    try:
        from test_tale import VOICE_LINES, VOICE_NAMES
    except Exception:
        log("test_tale could not be imported", traceback.format_exc()[-400:])
        return
    for lang, table in (("en", CAST_EN), ("tr", CAST_TR)):
        i = 0 if lang == "en" else 1
        pre = "k:" if lang == "en" else "kt:"
        gap1, gap2 = np.zeros(int(0.35 * KSR)), np.zeros(int(1.0 * KSR))
        parts, rows = [], []
        log("---- cast sweep %s: type  voice  rate  pitch   seconds  F0 Hz  UTMOS  words wrong   (the best of a type by UTMOS is marked *)" % lang)
        for typ, cands in table.items():
            line = VOICE_LINES[typ][i]
            try:
                parts += [KT.speak(VOICE_NAMES[typ][i], pre + ("af_heart" if lang == "en" else "elif"), "-8%", "+0Hz"), gap1]
            except Exception:
                log("   narrator failed", typ, traceback.format_exc()[-200:])
            made = []
            for body, rate, pitch in cands:
                try:
                    y = KT.speak(line, pre + body, rate, pitch)
                except Exception:
                    log("   %-11s %-22s %-4s %-6s FAILED %s" % (typ, body, rate, pitch, traceback.format_exc()[-160:].replace("\n", " | ")))
                    continue
                sc = score(y, line, lang)
                made.append((sc.get("mos", 0.0), sc.get("wer", 1.0), body, rate, pitch, y, f0_of(y)))
                parts += [y, gap1]
            parts.append(gap2)
            best = max(made, key=lambda m: m[0] - 2.0 * max(0.0, m[1] - 0.2), default=None)
            for m in made:
                log("   %-11s %-22s %-4s %-6s %5.1f s  F0 %5s  UTMOS %.2f  wrong %3.0f%% %s" % (typ, m[2], m[3], m[4], len(m[5]) / float(KSR), ("%.0f" % m[6]) if m[6] else "-", m[0], 100 * m[1],
                                                                                              "*" if m is best else ""))
                rows.append(m)
        if rows:
            log("   %s: %d clips, mean UTMOS %.2f, mean words wrong %.0f%%" % (lang, len(rows), np.mean([m[0] for m in rows]), 100 * np.mean([m[1] for m in rows])))
        VL.save("cast-" + lang, np.concatenate(parts) if parts else np.zeros(KSR), KSR)

        log("---- ladder %s: the same voice as a smaller or a bigger person (factor 1.00 = the voice as it is)" % lang)
        for body in LADDER[lang]:
            for f in LADDER_F:
                try:
                    y = KT.speak(LADDER_LINE[lang], pre + body, "+0%", "%+.1fHz" % ((f - 1.0) * 150))
                except Exception:
                    log("   %-10s %.2f FAILED" % (body, f))
                    continue
                sc = score(y, LADDER_LINE[lang], lang)
                log("   %-10s x%.2f  F0 %5s  UTMOS %.2f  wrong %3.0f%%" % (body, f, ("%.0f" % f0_of(y)) if f0_of(y) else "-", sc.get("mos", 0.0), 100 * sc.get("wer", 1.0)))

        log("---- the way of the first test (a pitch shifter: ffmpeg rubberband) against the new way (shift_voice) %s" % lang)
        for typ, body, pitch in VS_PS[lang]:
            line = VOICE_LINES[typ][i]
            f = KT.pitch_factor(pitch)
            try:
                new = KT.speak(line, pre + body, "-0%", pitch)
                old = pitch_shift(KT.speak(line, pre + body, "-0%", "+0Hz"), f, "shifted")
            except Exception:
                log("   %s comparison failed %s" % (typ, traceback.format_exc()[-200:].replace("\n", " | ")))
                continue
            for name, y in (("rubberband", old), ("shift_voice", new)):
                sc = score(y, line, lang)
                log("   %-5s %-10s x%.2f  %-11s F0 %5s  UTMOS %.2f  wrong %3.0f%%" % (typ, body, f, name, ("%.0f" % f0_of(y)) if f0_of(y) else "-", sc.get("mos", 0.0), 100 * sc.get("wer", 1.0)))


# ------------------------------------------------------------------------------------------------------------------------ the palette: every voice, as a smaller and a bigger person
EN_VOICES = ["af_alloy", "af_aoede", "af_bella", "af_heart", "af_jessica", "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
             "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael", "am_onyx", "am_puck", "am_santa",
             "bf_alice", "bf_emma", "bf_isabella", "bf_lily", "bm_daniel", "bm_fable", "bm_george", "bm_lewis"]
PAL_CALM = {"en": "Once upon a time, a little rabbit found a shiny red ball in the garden.",
            "tr": "Bir varmış bir yokmuş, küçük bir tavşan bahçede parlak kırmızı bir top bulmuş."}
PAL_LIVELY = {"en": "Look! I can jump so high! Come and play with me!",
              "tr": "Bak, ne kadar yükseğe zıplayabiliyorum! Gel, benimle oyna!"}
PAL_F = {"en": [0.85, 1.2, 1.4], "tr": [0.85, 0.92, 1.1, 1.2, 1.3]}                   # (and 1.0, for both lines)
TR_STYLES = ["elif", "elif=0.8,emre=0.2", "elif=0.6,emre=0.4", "elif=0.4,emre=0.6", "elif=0.2,emre=0.8", "emre", "elif=1.25,emre=-0.25", "elif=-0.25,emre=1.25"]
TR_CROSS = ["af_heart", "af_kore", "af_aoede", "af_sky", "af_sarah", "af_bella", "bf_emma", "bf_isabella", "am_michael", "am_puck", "am_fenrir", "bm_fable", "bm_george",
            "elif=0.5,af_kore=0.5", "elif=0.5,af_sky=0.5", "emre=0.5,am_michael=0.5", "emre=0.5,bm_fable=0.5"]       # (voices of Kokoro-82M tried on the Turkish model)
_NUM = {"en": ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
               "seventeen", "eighteen", "nineteen"],
        "tr": ["sıfır", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz", "on", "on bir", "on iki", "on üç", "on dört", "on beş", "on altı", "on yedi",
               "on sekiz", "on dokuz"]}
_TENS = {"en": ["", "", "twenty", "thirty", "forty", "fifty"], "tr": ["", "", "yirmi", "otuz", "kırk", "elli"]}


def number_words(n, lang):
    """1..59 in words (a voice reads words, not digits)"""
    if n < 20:
        return _NUM[lang][n]
    t, u = divmod(n, 10)
    return _TENS[lang][t] + (" " + _NUM[lang][u] if u else "")


def palette(a):
    """Every voice at several sizes: PAL lines (F0, UTMOS, words wrong), and one mp3 per language with the voices one after the other, the narrator says the number."""
    os.environ["BIBI_KOKORO_INPROC"] = "1"
    try:
        _palette()
    finally:
        os.environ.pop("BIBI_KOKORO_INPROC", None)


def _pal_one(KT, lang, body, kind, f):
    line = (PAL_CALM if kind == "calm" else PAL_LIVELY)[lang]
    pre = "k:" if lang == "en" else "kt:"
    try:
        y = KT.speak(line, pre + body, "+0%", "%+.1fHz" % ((f - 1.0) * 150))
    except Exception:
        log("PAL %s %s x%.2f %s FAILED %s" % (lang, body, f, kind, traceback.format_exc()[-170:].replace("\n", " | ")))
        return None
    sc = score(y, line, lang)
    f0 = f0_of(y)
    log("PAL %s %-24s x%.2f %-6s F0 %5s UTMOS %.2f WER %3.0f%% SEC %.1f" % (lang, body, f, kind, ("%.0f" % f0) if f0 else "-", sc.get("mos", 0.0), 100 * sc.get("wer", 1.0), len(y) / float(KSR)))
    return y


def _palette():
    from bibi_buzz import ktts as KT
    gap = np.zeros(int(0.30 * KSR))
    for lang in ("en", "tr"):
        names = EN_VOICES if lang == "en" else TR_STYLES + TR_CROSS
        log("---- palette %s: PAL language voice factor line F0 UTMOS WER seconds   (factor 1.00 = the voice as it is; the lively line is the one that is moved)" % lang)
        parts = []
        for n, body in enumerate(names, 1):
            log("GALLERY %s %d = %s" % (lang, n, body))
            y = _pal_one(KT, lang, body, "calm", 1.0)
            if y is not None:
                try:
                    parts += [KT.speak(number_words(n, lang), "k:af_heart" if lang == "en" else "kt:elif", "-6%", "+0Hz"), gap, y, np.zeros(int(0.8 * KSR))]
                except Exception:
                    log("   announcer failed", traceback.format_exc()[-150:].replace("\n", " | "))
            for f in [1.0] + PAL_F[lang]:
                _pal_one(KT, lang, body, "lively", f)
        VL.save("palette-" + lang, np.concatenate(parts) if parts else np.zeros(KSR), KSR)


# ------------------------------------------------------------------------------------------------------------------------ a studio chain (EQ and compression) for the clips
STUDIO = {
    "s0": "",
    "s1": "highpass=f=70,equalizer=f=3000:t=q:w=1.1:g=2,treble=g=1.5:f=8000,acompressor=threshold=0.09:ratio=2:attack=10:release=150:makeup=1.2",
    "s2": "highpass=f=80,equalizer=f=250:t=q:w=1.0:g=1.2,equalizer=f=3500:t=q:w=1.2:g=2.5,treble=g=2:f=9000,acompressor=threshold=0.08:ratio=2.5:attack=8:release=120:makeup=1.3",
}
STUDIO_VOICES = {                                             # role -> (voice spec, rate, pitch): the casting of the first test of the whole tale
    "en": {"nar": ("k:af_heart", "-6%", "+0Hz"), "mama": ("k:af_bella", "-4%", "+12Hz"), "pig1": ("k:am_puck", "+2%", "+27Hz"), "wolf": ("k:am_fenrir", "-10%", "-28Hz")},
    "tr": {"nar": ("kt:elif", "-6%", "+0Hz"), "mama": ("kt:elif=0.8,emre=0.2", "-8%", "-18Hz"), "pig1": ("kt:emre", "+4%", "+37Hz"), "wolf": ("kt:emre", "-10%", "-36Hz")},
}


def _chain(y, chain):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        from bibi_buzz import ktts as KT
        KT.write_wav(src, y, KSR)
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", chain, "-ar", str(KSR), "-ac", "1", dst], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError("ffmpeg: " + r.stderr[-200:])
        z, _sr = KT.read_wav(dst)
        return z


def studio_ab(a):
    """The same four clips of each language as they are and through two studio chains: does the chain cost naturalness (UTMOS sees the band below 8 kHz only)?"""
    os.environ["BIBI_KOKORO_INPROC"] = "1"
    try:
        from bibi_buzz import ktts as KT
        for lang in ("en", "tr"):
            want = {}
            for role, text in get_lines(lang):
                want.setdefault(role, text)
            clips = {}
            for role, (v, r, p) in STUDIO_VOICES[lang].items():
                if role in want:
                    try:
                        clips[role] = (want[role], KT.speak(want[role], v, r, p))
                    except Exception:
                        log("   studio clip failed", lang, role, traceback.format_exc()[-150:].replace("\n", " | "))
            log("---- studio %s: STUDIO language chain role UTMOS WER (s0 = as it is)" % lang)
            parts = []
            for name, chain in STUDIO.items():
                ms, ws = [], []
                for role, (text, y) in clips.items():
                    try:
                        z = _chain(y, chain) if chain else y
                    except Exception:
                        log("   chain failed", name, traceback.format_exc()[-150:].replace("\n", " | "))
                        continue
                    sc = score(z, text, lang)
                    ms.append(sc.get("mos", 0.0))
                    ws.append(sc.get("wer", 1.0))
                    log("STUDIO %s %s %-5s UTMOS %.2f WER %3.0f%%" % (lang, name, role, sc.get("mos", 0.0), 100 * sc.get("wer", 1.0)))
                    if role in ("nar", "mama"):
                        parts += [level(z), np.zeros(int(0.6 * KSR))]
                if ms:
                    log("STUDIO %s %s MEAN UTMOS %.2f WER %.0f%%" % (lang, name, np.mean(ms), 100 * np.mean(ws)))
                parts.append(np.zeros(int(1.0 * KSR)))
            VL.save("studio-" + lang, np.concatenate(parts) if parts else np.zeros(KSR), KSR)
    finally:
        os.environ.pop("BIBI_KOKORO_INPROC", None)


# ------------------------------------------------------------------------------------------------------------------------ voice prints: do two characters sound like two people?
SIM_ALIKE = 0.55                                              # cos of two ECAPA voice prints from which on two characters of one tale are marked (a first guess: the lab shows what the pairs of the tales are)


def ecapa():
    if "ecapa" not in _M:
        try:
            from speechbrain.inference.speaker import EncoderClassifier
        except Exception:
            from speechbrain.pretrained import EncoderClassifier
        _M["ecapa"] = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir=os.path.join(OUT, "_ecapa"), run_opts={"device": "cpu"})
    return _M["ecapa"]


def embed(y):
    """the voice print of a clip (ECAPA-TDNN of speechbrain, unit length): the cosine of two of them is how much alike two voices are (the same person about 0.8 and more)"""
    import torch
    y16 = VL.resample(level(y), KSR, 16000).astype(np.float32)
    with torch.no_grad():
        e = ecapa().encode_batch(torch.from_numpy(y16)[None]).reshape(-1).cpu().numpy()
    return e / (float(np.linalg.norm(e)) + 1e-9)


def try_embed(y):
    try:
        return embed(y)
    except Exception:
        if "ecapa-failed" not in _M:
            _M["ecapa-failed"] = 1
            log("ECAPA failed (said once)", traceback.format_exc()[-400:].replace("\n", " | "))
        return None


def sim_report(tag, emb):
    """SIM lines: emb = {tale: [(who, type, voice print)]}; every pair of a tale, the pairs at or above SIM_ALIKE marked"""
    n_alike = 0
    for key, es in emb.items():
        for x in range(len(es)):
            for z in range(x + 1, len(es)):
                if es[x][2] is None or es[z][2] is None:
                    continue
                c = float(np.dot(es[x][2], es[z][2]))
                alike = c >= SIM_ALIKE
                n_alike += alike
                log("SIM %s %-20s %-8s (%s) ~ %-8s (%s) cos %.2f%s" % (tag, key, es[x][0], es[x][1], es[z][0], es[z][1], c, "   <-- alike" if alike else ""))
    log("SIMSUM %s pairs at or above %.2f: %d" % (tag, SIM_ALIKE, n_alike))


def nearest_report(tag, emb):
    """NEAR lines: for every voice of an engine the other voice it is most alike (cosine of the ECAPA voice prints): which voices are really different people"""
    names = [n for n in emb if emb[n] is not None]
    for n in names:
        best = max(((float(np.dot(emb[n], emb[o])), o) for o in names if o != n), default=None)
        if best:
            log("NEAR %s %-12s ~ %-12s cos %.2f%s" % (tag, n, best[1], best[0], "   <-- alike" if best[0] >= SIM_ALIKE else ""))


# ------------------------------------------------------------------------------------------------------------------------ the gallery: the casting of some tales, the way the videos make it
GALLERY_TALES = ["three-little-pigs", "goldilocks", "red-riding-hood", "cinderella", "magic-porridge-pot", "gingerbread-man"]


def gallery(a):
    """Every character of some tales says its type's line with the voice, speed, pitch and effect of the daily videos' casting (bibi_buzz.tales.cast_voices with
    BIBI_KOKORO set; the Edge voice stands in for a line Kokoro cannot make); the narrator says who is next.  One mp3 per language (gallery-<language>.mp3; English once more with the child voices of Edge: gallery-en-kidsedge.mp3), every
    line measured (GAL lines) and a warning for every pair of a tale that sounds alike (GALWARN lines)."""
    from bibi_buzz import tales as T
    from bibi_buzz import voice as VO
    from test_tale import VOICE_LINES, VOICE_NAMES
    rest = [k for k in T.CASTING if k not in GALLERY_TALES]                  # (the other tales: measured too, so that every type of the casting has a line)
    for lang, tag, env, keys in (("en", "", {}, GALLERY_TALES), ("en", "-kidsedge", {"BIBI_KIDS": "edge"}, GALLERY_TALES), ("tr", "", {}, GALLERY_TALES),         # (English twice: the children with a
                                 ("tr", "-xplant", {"BIBI_XPLANT": "1"}, GALLERY_TALES), ("tr", "-rest", {}, rest), ("tr", "-xplant-rest", {"BIBI_XPLANT": "1"}, rest)):  # Kokoro voice, and with the child voices of Edge; Turkish twice: KTYPES and XPLANT_TR)
        i = 0 if lang == "en" else 1
        names = ("BIBI_KOKORO", "BIBI_KIDS", "BIBI_XPLANT")
        old = {k: os.environ.get(k) for k in names}
        os.environ["BIBI_KOKORO"] = lang
        os.environ.pop("BIBI_KIDS", None)
        os.environ.pop("BIBI_XPLANT", None)
        os.environ.update(env)
        try:
            plan, items = [], []
            for key in keys:
                cv = T.cast_voices(key, lang)
                nar = cv["nar"]
                title = T.build(key, lang).title
                plan.append(("title", key, None, None, (title,) + tuple(nar)))
                items.append(plan[-1][4])
                seen, count = {}, {}
                for who, spec in T.CASTING[key].items():
                    typ = spec if isinstance(spec, str) else spec[0]
                    seen[typ] = seen.get(typ, 0) + 1
                for who, spec in T.CASTING[key].items():
                    typ = spec if isinstance(spec, str) else spec[0]
                    count[typ] = count.get(typ, 0) + 1
                    name = VOICE_NAMES[typ][i] + ((" " + number_words(count[typ], lang)) if seen[typ] > 1 else "")
                    plan.append(("name", key, who, typ, (name,) + tuple(nar)))
                    items.append(plan[-1][4])
                    plan.append(("line", key, who, typ, (VOICE_LINES[typ][i],) + tuple(cv[who])))
                    items.append(plan[-1][4])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                clips = VO.synth_items(items, "ffmpeg", os.path.join(OUT, "_cache_gallery_" + lang + tag))
            for ln in buf.getvalue().splitlines():
                log("   " + ln)
        except Exception:
            log("GALLERY %s%s FAILED %s" % (lang, tag, traceback.format_exc()[-1200:]))
            continue
        finally:
            for k in names:
                if old[k] is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = old[k]
        log("---- gallery %s%s: GAL language tale character type F0 UTMOS WER voice" % (lang, tag))
        parts, rows, emb, dump = [], {}, {}, []
        for kind, key, who, typ, item in plan:
            y = VL.resample(clips[item], 44100, KSR)
            if kind == "title":
                parts += [np.zeros(int(1.2 * KSR)), level(y), np.zeros(int(0.7 * KSR))]
                continue
            if kind == "name":
                parts += [level(y), np.zeros(int(0.25 * KSR))]
                continue
            sc = score(y, item[0], lang)
            f0 = f0_of(y)
            rows.setdefault(key, []).append((who, typ, item[1], f0))
            e_ = try_embed(y)
            emb.setdefault(key, []).append((who, typ, e_))
            dump.append({"tale": key, "who": who, "type": typ, "spec": item[1], "f0": round(f0, 1) if f0 else None, "mos": round(sc.get("mos", 0.0), 3), "wer": round(sc.get("wer", 1.0), 3),
                         "emb": [round(float(x), 4) for x in e_] if e_ is not None else None})
            log("GAL %s %-20s %-8s %-11s F0 %5s UTMOS %.2f WER %3.0f%%  %s" % (lang + tag, key, who, typ, ("%.0f" % f0) if f0 else "-", sc.get("mos", 0.0), 100 * sc.get("wer", 1.0), item[1]))
            parts += [level(y), np.zeros(int(0.8 * KSR))]
        sim_report(lang + tag, emb)
        with open(os.path.join(OUT, "gallery-emb-%s%s.txt" % (lang, tag)), "w", encoding="utf-8") as f:                       # (the voice prints of every line: the casting can be compared offline, mode against mode)
            for r_ in dump:
                f.write(json.dumps(r_) + "\n")
        for key, rs in rows.items():
            for x in range(len(rs)):
                for z in range(x + 1, len(rs)):
                    a_, b_ = rs[x], rs[z]
                    if a_[3] and b_[3]:
                        ratio = max(a_[3], b_[3]) / min(a_[3], b_[3])
                        same = a_[2].split("|")[0] == b_[2].split("|")[0]
                        if (same and ratio < 1.25) or ratio < 1.10:
                            log("GALWARN %s %s: %s (%s) and %s (%s) may sound alike: F0 %.0f and %.0f Hz (x%.2f)%s" % (lang + tag, key, a_[0], a_[1], b_[0], b_[1], a_[3], b_[3], ratio,
                                                                                                                          ", the same voice" if same else ""))
        VL.save("gallery-" + lang + tag, np.concatenate(parts) if parts else np.zeros(KSR), KSR)


# ------------------------------------------------------------------------------------------------------------------------ the voice grid: how many different people can the Kokoro models make? (--only grid)
GRID_LINES = {"tr": ["Bir varmış bir yokmuş, küçük bir tavşan bahçede parlak kırmızı bir top bulmuş.",
                     "Ağaçların arasından geçen yaşlı kurt, yavru kuzuların çiçekli çayırda koştuğunu görünce gülümsedi."],
              "en": ["Once upon a time, a little rabbit found a shiny red ball in the garden.",
                     "The old wolf walked between the tall trees and smiled when he saw the baby lambs running through the flowery meadow."]}   # (a calm line, and a harder one for the voice at its own size)
GRID_PITCH = {"tr": [-45, -23, -8, 0, 15, 30, 45], "en": [-45, -23, 0, 22, 45]}              # (Hz in the way of the casting: a factor of 1 + Hz / 150)


def _grid_candidates(lang):
    """[(spec body, [pitches], harder line too?)].  Turkish: the blends of elif and emre the tales use now (the baseline), then every voice of Kokoro-82M as a TIMBRE on the Turkish
    way of speaking ("elif:p=1,af_kore:t=1": the durations, pitch and energy of elif, the voice of af_kore; a woman's timbre on elif, a man's on emre) at every pitch, then the same
    with half of the own timbre of elif / emre in it (a more Turkish voice, less far from what the model knows)."""
    out = []
    if lang == "en":
        return [(v, GRID_PITCH["en"], False) for v in EN_VOICES]
    out += [(b, GRID_PITCH["tr"], False) for b in TR_STYLES]
    for v in EN_VOICES:
        p = "elif" if v[1] == "f" else "emre"
        out.append(("%s:p=1,%s:t=1" % (p, v), GRID_PITCH["tr"], True))
    for v in EN_VOICES:
        p = "elif" if v[1] == "f" else "emre"
        out.append(("%s:p=1,%s:t=0.5,%s:t=0.5" % (p, p, v), [0], True))
    return out


def voice_grid(a):
    """GRID lines (F0, UTMOS, words wrong, seconds) of every candidate at every pitch and, in grid-<language>.txt, one JSON line per clip with its ECAPA voice print, so that the
    casting of the tales can be chosen OFFLINE (the voices of one tale as far apart as can be) from one measurement."""
    os.environ["BIBI_KOKORO_INPROC"] = "1"                              # (the model is loaded once, in this process)
    try:
        _voice_grid()
    finally:
        os.environ.pop("BIBI_KOKORO_INPROC", None)


def _voice_grid():
    from bibi_buzz import ktts as KT
    for lang in ("tr", "en"):
        pre = "k:" if lang == "en" else "kt:"
        rows = []
        log("---- voice grid %s: GRID language spec pitch(Hz) line F0 UTMOS WER seconds   (line 1 is the harder one: only at the pitch 0)" % lang)
        for body, pitches, hard in _grid_candidates(lang):
            for hz in pitches:
                for k, line in enumerate(GRID_LINES[lang][:2] if (hard and hz == 0) else GRID_LINES[lang][:1]):
                    try:
                        y = KT.speak(line, pre + body, "+0%", "%+dHz" % hz)
                    except Exception:
                        log("GRID %s %s %+d L%d FAILED %s" % (lang, body, hz, k, traceback.format_exc()[-150:].replace("\n", " | ")))
                        continue
                    sc = score(y, line, lang)
                    f0 = f0_of(y)
                    e = try_embed(y)
                    wer = sc.get("wer", 1.0)
                    log("GRID %s %-34s %+4d L%d F0 %5s UTMOS %.2f WER %3.0f%% SEC %.1f%s" % (lang, body, hz, k, ("%.0f" % f0) if f0 else "-", sc.get("mos", 0.0), 100 * wer, len(y) / float(KSR),
                                                                                           ("  heard: " + sc.get("heard", "")) if wer > 0.12 else ""))
                    rows.append({"spec": body, "hz": hz, "line": k, "f0": round(f0, 1) if f0 else None, "mos": round(sc.get("mos", 0.0), 3), "wer": round(wer, 3), "sec": round(len(y) / float(KSR), 2),
                                 "emb": [round(float(x), 4) for x in e] if e is not None else None})
        with open(os.path.join(OUT, "grid-%s.txt" % lang), "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        log("GRIDSUM %s: %d clips, mean UTMOS %.2f, mean words wrong %.0f%%" % (lang, len(rows), np.mean([r["mos"] for r in rows]) if rows else 0.0, 100 * np.mean([r["wer"] for r in rows]) if rows else 0.0))


# ------------------------------------------------------------------------------------------------------------------------ WORLD: a smaller person without the chipmunk (--only world)
WORLD_BODIES = {"en": ["af_sarah", "bf_isabella", "af_river"], "tr": ["elif=0.8,emre=0.2", "elif"]}
WORLD_SET = [("resample", 1.2, 1.0), ("resample", 1.35, 1.0), ("resample", 1.5, 1.0),             # (method, pitch factor, formant factor)
             ("world", 1.2, 1.06), ("world", 1.35, 1.10), ("world", 1.35, 1.18), ("world", 1.5, 1.12), ("world", 1.5, 1.22)]


def world_test(a):
    """The same lively line of some voices made a smaller person in two ways: resampling (pitch and formants by one factor: what bibi_buzz/ktts.py does) and the WORLD
    vocoder (the pitch by a factor, the vocal tract by a smaller one).  WORLD lines (F0, UTMOS, words wrong); world-<language>.mp3: per voice the plain clip, then
    resample 1.2 / 1.35 / 1.5, then WORLD 1.2/1.06, 1.35/1.10, 1.35/1.18, 1.5/1.12, 1.5/1.22 (pitch factor / formant factor)."""
    os.environ["BIBI_KOKORO_INPROC"] = "1"
    try:
        _world()
    finally:
        os.environ.pop("BIBI_KOKORO_INPROC", None)


def _world():
    try:
        import pyworld  # noqa: F401
    except Exception:
        log("WORLD: pyworld is not installed", traceback.format_exc()[-200:].replace("\n", " | "))
        return
    import ext_synth as ES
    from bibi_buzz import ktts as KT
    gap = np.zeros(int(0.30 * KSR))
    for lang in ("en", "tr"):
        pre = "k:" if lang == "en" else "kt:"
        line = PAL_LIVELY[lang]
        log("---- world %s: WORLD language voice method pitch-factor formant-factor F0 UTMOS WER seconds   (resample: pitch and formants move by the pitch factor)" % lang)
        parts = []
        for body in WORLD_BODIES[lang]:
            try:
                base = KT.speak(line, pre + body, "+0%", "+0Hz")
            except Exception:
                log("WORLD %s %s FAILED %s" % (lang, body, traceback.format_exc()[-170:].replace("\n", " | ")))
                continue
            for method, pf, ef in [("plain", 1.0, 1.0)] + WORLD_SET:
                try:
                    if method == "plain":
                        y = base
                    elif method == "resample":
                        y = KT.speak(line, pre + body, "+0%", "%+.1fHz" % ((pf - 1.0) * 150))
                    else:
                        t0 = time.time()
                        y = ES.world_shift(base, KSR, pf, ef)
                        if body == WORLD_BODIES[lang][0] and (pf, ef) == (1.2, 1.06):
                            log("   WORLD analysis + synthesis of %.1f s of speech took %.1f s" % (len(base) / float(KSR), time.time() - t0))
                except Exception:
                    log("WORLD %s %s %s x%.2f e%.2f FAILED %s" % (lang, body, method, pf, ef, traceback.format_exc()[-170:].replace("\n", " | ")))
                    continue
                sc = score(y, line, lang)
                f0 = f0_of(y)
                log("WORLD %s %-22s %-8s f0x%.2f envx%.2f F0 %5s UTMOS %.2f WER %3.0f%% SEC %.1f" % (lang, body, method, pf, ef, ("%.0f" % f0) if f0 else "-", sc.get("mos", 0.0),
                                                                                                    100 * sc.get("wer", 1.0), len(y) / float(KSR)))
                parts += [level(y), gap]
            parts.append(np.zeros(int(0.8 * KSR)))
        if parts:
            VL.save("world-" + lang, np.concatenate(parts), KSR)


# ------------------------------------------------------------------------------------------------------------------------ the new engines (tools/ext_synth.py runs in its own environment)
# type -> (Pocket TTS Turkish voice, emotion, pitch factor, formant factor) or a list of them (the 1st, 2nd, 3rd character of that type in one tale): a first casting to listen to
POCKET_CAST = {
    "nar": ("female_2", None, 1.0, 1.0),
    "woman": ("female_2", "sakin", 1.0, 1.0),
    "girl": [("female_1", "mutlu", 1.25, 1.10), ("female_3", "mutlu", 1.18, 1.08)],
    "teen": ("female_1", None, 1.0, 1.0),
    "boy": ("male_2", "mutlu", 1.30, 1.12),
    "baby": ("female_1", "mutlu", 1.55, 1.22),
    "tiny": ("female_1", "şaşkın", 1.60, 1.25),
    "granny": [("female_3", "sakin", 0.88, 0.97), ("female_2", "sakin", 0.90, 0.97)],
    "fakegranny": ("male_3", None, 1.10, 1.05),
    "man": ("male_3", None, 1.0, 1.0),
    "grandpa": ("male_1", "sakin", 0.90, 0.96),
    "prince": ("male_2", None, 1.0, 1.0),
    "king": ("male_1", "kızgın", 0.85, 0.94),
    "lord": ("male_3", None, 0.92, 0.97),
    "queen": ("female_3", "kızgın", 0.95, 1.0),
    "stepmother": ("female_3", "kızgın", 0.92, 0.98),
    "stepsister": [("female_1", "kızgın", 1.05, 1.03), ("female_3", "kızgın", 1.12, 1.05)],
    "witch": ("female_3", "kızgın", 0.80, 0.93),
    "fairy": ("female_2", "mutlu", 1.12, 1.05),
    "mirror": ("male_1", "sakin", 0.82, 0.94),
    "dwarf": ("male_2", "mutlu", 1.15, 1.06),
    "elf": ("male_2", "mutlu", 1.35, 1.14),
    "elfgirl": ("female_1", "mutlu", 1.35, 1.14),
    "troll": ("male_1", "kızgın", 0.70, 0.88),
    "giant": ("male_1", "kızgın", 0.62, 0.84),
    "pig": [("male_2", None, 1.10, 1.04), ("male_3", None, 1.05, 1.02), ("male_1", None, 1.15, 1.06)],
    "wolf": ("male_1", "kızgın", 0.80, 0.92),
    "hare": ("male_2", "mutlu", 1.18, 1.08),
    "tortoise": ("male_1", "sakin", 0.90, 0.96),
    "bear": ("male_1", "kızgın", 0.75, 0.90),
    "mamabear": ("female_3", "kızgın", 0.80, 0.94),
    "goat_little": ("female_1", "mutlu", 1.40, 1.16),
    "goat_mid": ("male_2", None, 1.0, 1.0),
    "goat_big": ("male_1", "kızgın", 0.75, 0.90),
    "hen": ("female_1", "mutlu", 1.15, 1.06),
    "fox": ("male_3", "şaşkın", 1.0, 1.0),
    "lion": ("male_1", "kızgın", 0.72, 0.89),
}
POCKET_VOICES = ["female_1", "female_2", "female_3", "male_1", "male_2", "male_3"]
POCKET_EMOTIONS = [("mutlu", "mutlu"), ("üzgün", "uzgun"), ("kızgın", "kizgin"), ("şaşkın", "sasgin"), ("sakin", "sakin")]       # (the tag, the same without the Turkish letters for a file name)
NARR = {"en": "Once upon a time, in a little house at the edge of a big green forest, there lived three small pigs. One sunny morning, they said goodbye to their mother, and off they went to build houses of their own.",
        "tr": "Bir varmış, bir yokmuş. Büyük, yeşil bir ormanın kenarındaki küçük bir evde üç küçük domuz yaşarmış. Güneşli bir sabah anneleriyle vedalaşmışlar ve kendi evlerini yapmak için yola çıkmışlar."}      # (a paragraph of a tale: how does a voice carry a longer text?)
PHONON_NARR = ["Everly", "Hadley", "Juniper", "Delia", "Hugh", "Imogen", "Harper", "Maeve"]                 # (the calmer voices of the catalog read the paragraph)
PHONON_KIDS = [("Freya", 1.15, 1.04), ("Freya", 1.30, 1.10), ("Elodie-Rose", 1.20, 1.06), ("Micah", 1.25, 1.08), ("Alfie", 1.30, 1.10)]      # (voice, pitch factor, formant factor: a child out of a young voice)
VOX_DESIGNS = [               # (who, the type whose line it says, the English description VoxCPM2 designs the voice from), the most important first (the time of the test is limited)
    ("narrator", "nar", "A warm, kind woman reading a bedtime story to small children, gentle, clear and lively"),
    ("girl", "girl", "A cheerful five-year-old girl, high-pitched, bright and playful, a small child's voice"),
    ("wolf", "wolf", "A big bad wolf, low, growly and sly, scary but funny, a cartoon villain for small children"),
    ("mother", "woman", "A kind, warm mother in her thirties, soft and caring"),
    ("boy", "boy", "A cheeky six-year-old boy, high-pitched, excited and full of energy, a small child's voice"),
    ("baby", "baby", "A tiny toddler, very high-pitched, sweet and a little shy, a very small child's voice"),
    ("granny", "granny", "An old grandmother, a little shaky, warm and slow"),
    ("pig", "pig", "A nervous little pig, squeaky, fast and worried, a cartoon animal"),
    ("fairy", "fairy", "A magical fairy, light, airy and sweet, with a little sparkle"),
    ("witch", "witch", "A cackling old witch, raspy and nasty, a cartoon villain"),
    ("king", "king", "A booming king, deep, proud and royal"),
    ("man", "man", "A friendly father, a deep, warm and relaxed voice"),
]


# ------------------------------------------------------------------------------------------------------------------------ the VoxCPM2 "foundry": a designed voice per role, kept for a whole scene by cloning it
FD_REFTEXT = {"en": "The little house stood at the edge of the forest, and the sun was shining on its red roof.",
              "tr": "Küçük ev ormanın kenarında duruyordu ve güneş kırmızı çatısının üstünde parlıyordu."}      # (what the designed reference voices say: about five seconds, the same for every role)
FD_DESIGN = {                 # role of the ten lines -> the English description of the voice VoxCPM2 designs once per language (the reference of the role)
    "nar": "A warm, kind woman in her thirties reading a bedtime story to small children, gentle, clear and lively",
    "mama": "A kind, warm mother in her forties, soft, caring and a little worried",
    "pig1": "A cheerful young man, light and bouncy, excited and a little nervous",
    "pig3": "A calm, confident young man, steady, clever and proud",
    "wolf": "A deep, gravelly man's voice, sly and menacing but playful, like a cartoon wolf",
}
FD_STYLE = {                  # the instruction before every line of the role when its reference is cloned (the voice is the reference's, the instruction steers feeling and speed)
    "nar": "a warm storyteller, calm and expressive",
    "mama": "kind and caring, a little worried",
    "pig1": "cheerful and excited",
    "pig3": "calm and proud",
    "wolf": "deep, growly and sly",
}
FD_KIDS = [("girl-a", "A little girl, about six years old, with a sweet, clear, cheerful voice"),
           ("girl-b", "A young girl of seven, lively and curious, speaking clearly and brightly"),
           ("girl-c", "A child's voice: a cheerful girl, five years old"),
           ("boy-a", "A little boy, about six years old, with a bright, clear, excited voice"),
           ("boy-b", "A young boy of seven, lively and curious, speaking clearly"),
           ("boy-c", "A child's voice: a cheeky boy, five years old")]            # (the first designs of the children got a UTMOS of 1.3-1.5: which words make a child that sounds like one?)
FD_SPEED = [("en", 10, 2.0), ("en", 4, 2.0), ("en", 6, 2.0), ("en", 16, 2.0), ("en", 10, 1.5), ("tr", 10, 2.0), ("tr", 6, 2.0)]      # (language, inference_timesteps, cfg_value): speed against quality


def foundry_items():
    """The job file of the VoxCPM2 foundry (EXT_ENGINES=vox; the order matters, the time of the run is limited): 1. a designed reference voice for every role of the ten lines of
    the three-pigs tale, in Turkish and in English; 2. the ten lines of both languages, every line cloned from the reference of its role; 3. the speed test (steps and cfg of the
    narrator's first sentences); 4. children's voices by six descriptions."""
    refp = lambda lang, role: os.path.join(OUT, "_ext", "fd-%s-%s-ref.wav" % (lang, role))
    items = []
    for lang in ("tr", "en"):
        for role in sorted({r for r, _ in get_lines(lang)}):
            items.append(dict(id="fd-%s-%s-ref" % (lang, role), engine="vox", voice=role, design=FD_DESIGN[role], text=FD_REFTEXT[lang], group="fd-ref", lang=lang, catalog=FD_DESIGN[role]))
    for lang in ("en", "tr"):
        for k, (role, text) in enumerate(get_lines(lang)):
            items.append(dict(id="fs-%s-%d" % (lang, k), engine="vox", voice=role, design=FD_STYLE[role], ref=refp(lang, role), text=text, group="fd-scene", lang=lang,
                              catalog="clone of the %s reference, style: %s" % (role, FD_STYLE[role])))
    sents = {l: re.split(r"(?<=[.!?])\s+", NARR[l]) for l in ("en", "tr")}
    para = {"en": sents["en"][0], "tr": " ".join(sents["tr"][:2])}
    for lang, steps, cfg in FD_SPEED:
        items.append(dict(id="fv-%s-s%d-c%.1f" % (lang, steps, cfg), engine="vox", voice="nar", design=FD_STYLE["nar"], ref=refp(lang, "nar"), text=para[lang], steps=steps, cfg=cfg,
                          group="fd-speed", lang=lang, catalog="steps %d cfg %.1f" % (steps, cfg)))
    for name, design in FD_KIDS:
        items.append(dict(id="fk-%s" % name, engine="vox", voice=name, design=design, text=PAL_LIVELY["en"], group="fd-probe", lang="en", catalog=design))
    return items


def ext_prepare(a):
    """The job file of tools/ext_synth.py: Pocket TTS Turkish (palette: its six voices with a calm and a lively line, the five emotions of two voices, WORLD lifts of two voices;
    the casting of the six tales: every character says its type's line) and Phonon 31m English (palette: every English voice of its catalog, a calm and a lively line).
    With VOX=foundry only the VoxCPM2 foundry (foundry_items)."""
    if os.environ.get("VOX") == "foundry":
        fitems = foundry_items()
        with open(os.path.join(OUT, "_ext.json"), "w", encoding="utf-8") as f:
            json.dump({"budget": 1700, "items": fitems}, f, ensure_ascii=False, indent=1)
        with open(os.path.join(OUT, "_ext_plan.json"), "w", encoding="utf-8") as f:
            json.dump([], f)
        log("ext-prepare: the VoxCPM2 foundry, %d clips to make" % len(fitems))
        return
    from bibi_buzz import tales as T
    from test_tale import VOICE_LINES, VOICE_NAMES
    items, plan = [], []
    calm, lively = PAL_CALM["tr"], PAL_LIVELY["tr"]
    for key in GALLERY_TALES:
        plan.append(dict(kind="title", key=key, text=T.build(key, "tr").title))
        seen, count = {}, {}
        for who, spec in T.CASTING[key].items():
            typ = spec if isinstance(spec, str) else spec[0]
            seen[typ] = seen.get(typ, 0) + 1
        for who, spec in T.CASTING[key].items():
            typ = spec if isinstance(spec, str) else spec[0]
            count[typ] = count.get(typ, 0) + 1
            plan.append(dict(kind="name", key=key, who=who, typ=typ, text=VOICE_NAMES[typ][1] + ((" " + number_words(count[typ], "tr")) if seen[typ] > 1 else "")))
            c = POCKET_CAST.get(typ) or POCKET_CAST["woman"]
            voice, emo, f0, env = c[min(count[typ] - 1, len(c) - 1)] if isinstance(c, list) else c
            iid = "pg-%s-%s" % (key, who)
            plan.append(dict(kind="line", key=key, who=who, typ=typ, id=iid, text=VOICE_LINES[typ][1]))
            items.append(dict(id=iid, engine="pocket", voice=voice, emotion=emo, text=VOICE_LINES[typ][1], f0=f0, env=env, group="gallery", lang="tr"))
    for v in POCKET_VOICES:
        items.append(dict(id="pk-%s-calm" % v, engine="pocket", voice=v, emotion=None, text=calm, group="palette", lang="tr"))
        items.append(dict(id="pk-%s-lively" % v, engine="pocket", voice=v, emotion="mutlu", text=lively, group="palette", lang="tr"))
    for v in ("female_2", "male_1"):
        for emo, tag in POCKET_EMOTIONS:
            items.append(dict(id="pk-%s-emo-%s" % (v, tag), engine="pocket", voice=v, emotion=emo, text=lively, group="emotion", lang="tr"))
    for v, f0, env in (("female_1", 1.25, 1.10), ("female_1", 1.5, 1.20), ("male_2", 1.3, 1.12)):
        items.append(dict(id="pk-%s-world-%.2f-%.2f" % (v, f0, env), engine="pocket", voice=v, emotion="mutlu", text=lively, f0=f0, env=env, group="world", lang="tr"))
    items.append(dict(id="ph-calm-*", engine="phonon", voice="*", text=PAL_CALM["en"], group="palette-en", lang="en"))
    items.append(dict(id="ph-lively-*", engine="phonon", voice="*", text=PAL_LIVELY["en"], group="palette-en", lang="en"))
    for v in PHONON_NARR:                                         # a paragraph of a tale: calm voices of Phonon (English) and the three women of Pocket (Turkish)
        items.append(dict(id="ph-narr-%s" % v, engine="phonon", voice=v, text=NARR["en"], group="narr-en", lang="en"))
    for v in ("female_1", "female_2", "female_3"):
        items.append(dict(id="pk-narr-%s" % v, engine="pocket", voice=v, emotion=None, text=NARR["tr"], group="narr-tr", lang="tr"))
    for v, f0, env in PHONON_KIDS:                                # a child out of a young voice (WORLD: the pitch by a factor, the vocal tract by a smaller one)
        items.append(dict(id="ph-kid-%s-%.2f-%.2f" % (v, f0, env), engine="phonon", voice=v, text=PAL_LIVELY["en"], f0=f0, env=env, group="world", lang="en"))
    if os.environ.get("VOX") == "yes":                            # VoxCPM2: voice design (the description of the voice in parentheses), in Turkish and in English, the important voices first
        def vx(lang, i, para=False):
            who, typ, design = VOX_DESIGNS[i]
            return dict(id="vx-%s-%s%s" % (lang, who, "-paragraph" if para else ""), engine="vox", voice=who, design=design, seed=7, group="vox", lang=lang,
                        text=NARR[lang] if para else VOICE_LINES[typ][0 if lang == "en" else 1], catalog=design + (" (a paragraph)" if para else ""))
        for lang in ("tr", "en"):
            items += [vx(lang, 0), vx(lang, 0, True)] + [vx(lang, i) for i in (1, 2, 3)]
        for i in range(4, len(VOX_DESIGNS)):
            items += [vx(lang, i) for lang in ("tr", "en")]
    with open(os.path.join(OUT, "_ext.json"), "w", encoding="utf-8") as f:
        json.dump({"budget": 2400, "items": items}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "_ext_plan.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)
    log("ext-prepare: %d clips to make (%d lines of the tales)" % (len(items), sum(1 for e in plan if e["kind"] == "line")))


def _read_wav24(path):
    with wave.open(path) as w:
        y = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
        sr = w.getframerate()
    return VL.resample(y, sr, KSR) if sr != KSR else y


def ext_collect(a):
    """Measures what tools/ext_synth.py made: EXT lines for the palettes, GAL and SIM lines for the casting of the tales with Pocket TTS Turkish, and the mp3s to listen to."""
    os.environ["BIBI_KOKORO_INPROC"] = "1"
    try:
        _ext_collect()
    finally:
        os.environ.pop("BIBI_KOKORO_INPROC", None)


def _foundry_collect(man, d):
    """What the VoxCPM2 foundry made: the ten lines of the three-pigs tale in both languages (every line a clone of the designed reference of its role: the usual lines of
    the lab and tr-9-vox-foundry.mp3 / en-9-vox-foundry.mp3), FDCONS (do two lines of one role sound like one person: ECAPA cos), FDREF (and like their designed reference),
    SIM (are the roles of the scene different people), FDSPEED (steps and cfg against quality and time), FDPROBE (children by six descriptions: kids-vox.mp3)."""
    by = {m["id"]: m for m in man if m.get("ok")}
    gap = np.zeros(int(0.30 * KSR))
    for lang in ("tr", "en"):
        lines = get_lines(lang)
        refs = {}
        for role in sorted({r for r, _ in lines}):
            m = by.get("fd-%s-%s-ref" % (lang, role))
            if m:
                refs[role] = try_embed(_read_wav24(os.path.join(d, m["id"] + ".wav")))
        ys, secs, emb = [], 0.0, {}
        for k, (role, text) in enumerate(lines):
            m = by.get("fs-%s-%d" % (lang, k))
            if not m:
                ys.append(None)
                continue
            y = _read_wav24(os.path.join(d, m["id"] + ".wav"))
            ys.append(y)
            secs += m["work"]
            emb.setdefault(role, []).append(try_embed(y))
        if not any(y is not None for y in ys):
            log("FDL %s: no line was made" % lang)
            continue
        finish(lang, "9-vox-foundry", ys, lines, secs)
        means = []
        for role, es in emb.items():
            es = [e for e in es if e is not None]
            if len(es) >= 2:
                cs = [float(np.dot(es[i], es[j])) for i in range(len(es)) for j in range(i + 1, len(es))]
                log("FDCONS %s %-5s %d lines: cos between its lines mean %.2f min %.2f" % (lang, role, len(es), float(np.mean(cs)), min(cs)))
            if role in refs and refs[role] is not None and es:
                cr = [float(np.dot(e, refs[role])) for e in es]
                log("FDREF %s %-5s cos of its lines to the designed reference: mean %.2f min %.2f" % (lang, role, float(np.mean(cr)), min(cr)))
            if es:
                v = np.mean(es, axis=0)
                means.append((role, role, v / (np.linalg.norm(v) + 1e-9)))
        sim_report("vox-foundry-" + lang, {"ten-lines": means})
    log("---- foundry speed test: FDSPEED language steps cfg UTMOS WER seconds-of-audio seconds-of-work real-time-factor")
    parts = []
    for m in man:
        if m.get("ok") and str(m["id"]).startswith("fv-"):
            y = _read_wav24(os.path.join(d, m["id"] + ".wav"))
            sc = score(y, m["text"], m["lang"])
            log("FDSPEED %s steps %2d cfg %.1f UTMOS %.2f WER %3.0f%% SEC %.1f WORK %.1f RTF %.2f" % (
                m["lang"], m.get("steps", 10), m.get("cfg", 2.0), sc.get("mos", 0.0), 100 * sc.get("wer", 1.0), m["audio"], m["work"], m["work"] / max(0.1, m["audio"])))
            parts += [level(y), gap]
    if parts:
        VL.save("speed-vox", np.concatenate(parts), KSR)
    log("---- foundry children: FDPROBE name F0 UTMOS WER seconds-of-audio seconds-of-work [description]")
    parts, pe = [], {}
    for m in man:
        if m.get("ok") and str(m["id"]).startswith("fk-"):
            y = _read_wav24(os.path.join(d, m["id"] + ".wav"))
            sc = score(y, m["text"], m["lang"])
            f0 = f0_of(y)
            pe[m["voice"]] = try_embed(y)
            log("FDPROBE %-8s F0 %5s UTMOS %.2f WER %3.0f%% SEC %.1f WORK %.1f  [%s]" % (m["voice"], ("%.0f" % f0) if f0 else "-", sc.get("mos", 0.0), 100 * sc.get("wer", 1.0),
                                                                                         m["audio"], m["work"], (m.get("catalog") or "")[:70]))
            parts += [level(y), gap]
    if parts:
        VL.save("kids-vox", np.concatenate(parts), KSR)
        nearest_report("vox-kids", pe)


def _ext_collect():
    from bibi_buzz import ktts as KT
    d = os.path.join(OUT, "_ext")
    try:
        man = json.load(open(os.path.join(d, "manifest.json"), encoding="utf-8"))
    except Exception:
        log("ext: nothing was made (no manifest.json)")
        return
    by = {m["id"]: m for m in man if m.get("ok")}
    log("ext: %d clips made, %d failed" % (len(by), sum(1 for m in man if not m.get("ok"))))
    for m in man:
        if not m.get("ok"):
            log("EXTFAIL %s %s" % (m.get("id"), (m.get("error") or "")[-200:].replace("\n", " | ")))
    gap = np.zeros(int(0.30 * KSR))
    pal = ("palette", "palette-en", "emotion", "world", "narr-en", "narr-tr", "vox")
    for engine, lang in (("pocket", "tr"), ("phonon", "en"), ("vox", "tr"), ("vox", "en")):
        voices = []
        for m in man:
            if m.get("ok") and m["engine"] == engine and m.get("lang") == lang and m["group"] in pal and m["voice"] not in voices:
                voices.append(m["voice"])
        if not voices:
            continue
        parts, pal_emb = [], {}
        log("---- ext %s %s: EXT engine group voice emotion pitch-factor formant-factor F0 UTMOS WER seconds-of-audio seconds-of-work" % (engine, lang))
        for n, v in enumerate(voices, 1):
            log("EXTPAL %s %s %d = %s" % (engine, lang, n, v))
            try:
                parts += [KT.speak(number_words(n, lang), "k:af_heart" if lang == "en" else "kt:elif", "-6%", "+0Hz"), gap]
            except Exception:
                log("   announcer failed", traceback.format_exc()[-150:].replace("\n", " | "))
            for m in man:
                if not (m.get("ok") and m["engine"] == engine and m.get("lang") == lang and m["voice"] == v and m["group"] in pal):
                    continue
                y = _read_wav24(os.path.join(d, m["id"] + ".wav"))
                sc = score(y, m["text"], m["lang"])
                f0 = f0_of(y)
                if v not in pal_emb and m["group"] in ("palette", "palette-en", "vox") and not m.get("f0"):
                    pal_emb[v] = try_embed(y)
                log("EXT %-7s %-10s %-12s %-8s f0x%.2f envx%.2f F0 %5s UTMOS %.2f WER %3.0f%% SEC %.1f WORK %.1f%s" % (
                    engine, m["group"], v, m.get("emotion") or "-", m.get("f0", 1.0), m.get("env", 1.0), ("%.0f" % f0) if f0 else "-", sc.get("mos", 0.0),
                    100 * sc.get("wer", 1.0), m["audio"], m["work"], ("  [" + m["catalog"][:70] + "]") if m.get("catalog") else ""))
                parts += [level(y), gap]
            parts.append(np.zeros(int(0.8 * KSR)))
        nearest_report(engine + "-" + lang, pal_emb)
        if parts:
            VL.save("palette-" + engine + ("-" + lang if engine == "vox" else ""), np.concatenate(parts), KSR)
    if any(str(m.get("group", "")).startswith("fd-") for m in man):
        try:
            _foundry_collect(man, d)
        except Exception:
            log("FOUNDRY collect failed", traceback.format_exc()[-1200:])
    try:
        plan = json.load(open(os.path.join(OUT, "_ext_plan.json"), encoding="utf-8"))
    except Exception:
        plan = []
    parts, emb, tag = [], {}, "tr-pocket"
    log("---- gallery %s: GAL language tale character type F0 UTMOS WER voice" % tag)
    for e in plan:
        if e["kind"] in ("title", "name"):
            try:
                y = KT.speak(e["text"], "kt:elif", "-5%", "+0Hz")
            except Exception:
                log("   announcer failed", traceback.format_exc()[-150:].replace("\n", " | "))
                continue
            parts += [np.zeros(int(1.2 * KSR)), level(y), np.zeros(int(0.7 * KSR))] if e["kind"] == "title" else [level(y), np.zeros(int(0.25 * KSR))]
            continue
        m = by.get(e["id"])
        if not m:
            log("GALFAIL %s %s %s: no audio" % (tag, e["key"], e["who"]))
            continue
        y = _read_wav24(os.path.join(d, e["id"] + ".wav"))
        sc = score(y, e["text"], "tr")
        f0 = f0_of(y)
        emb.setdefault(e["key"], []).append((e["who"], e["typ"], try_embed(y)))
        log("GAL %s %-20s %-8s %-11s F0 %5s UTMOS %.2f WER %3.0f%%  pocket:%s/%s/f0x%.2f/envx%.2f" % (
            tag, e["key"], e["who"], e["typ"], ("%.0f" % f0) if f0 else "-", sc.get("mos", 0.0), 100 * sc.get("wer", 1.0), m["voice"], m.get("emotion") or "-",
            m.get("f0", 1.0), m.get("env", 1.0)))
        parts += [level(y), np.zeros(int(0.8 * KSR))]
    if emb:
        sim_report(tag, emb)
    if parts:
        VL.save("gallery-" + tag, np.concatenate(parts), KSR)


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
    special = [("cast", cast_sweep), ("palette", palette), ("studio", studio_ab), ("gallery", gallery), ("world", world_test), ("grid", voice_grid)]            # (jobs of their own: not an engine of the ten lines)
    for key, fn in special:
        if key in only:
            try:
                fn(a)
            except Exception:
                log("%s FAILED" % key.upper(), traceback.format_exc()[-1500:])
            only = [x for x in only if x != key]
            if not only:
                return
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
    ap.add_argument("job", choices=["main", "cbx-prepare", "cbx-collect", "myvoice-prepare", "myvoice-collect", "myvox-prepare", "myvox-collect", "ext-prepare", "ext-collect"])
    ap.add_argument("--out", default="out/speech")
    ap.add_argument("--only", default="", help="engine keys, comma separated (main only)")
    a = ap.parse_args()
    OUT = a.out
    VL.OUT = OUT
    os.makedirs(OUT, exist_ok=True)
    VL._LOG = open(os.path.join(OUT, "lab.txt"), "a", encoding="utf-8")
    log("=" * 20, a.job, time.strftime("%H:%M:%S"))
    try:
        {"main": job_main, "cbx-prepare": cbx_prepare, "cbx-collect": cbx_collect, "myvoice-prepare": myvoice_prepare, "myvoice-collect": myvoice_collect,
         "myvox-prepare": myvox_prepare, "myvox-collect": myvox_collect, "ext-prepare": ext_prepare, "ext-collect": ext_collect}[a.job](a)
        if a.job in ("cbx-collect", "myvoice-collect", "myvox-collect"):
            summary()
    except Exception:
        log("JOB FAILED:", a.job, "\n" + traceback.format_exc()[-2500:])


if __name__ == "__main__":
    main()
