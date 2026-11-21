#!/usr/bin/env python3
"""Test render of one fairy tale in one language, or of lessons - nothing of the daily pipeline is touched.

  python tools/test_tale.py three-little-pigs tr --out out/test --seconds 40
  python tools/test_tale.py d003-L1,d003-L4 en --out out/test --seconds 0 --tail 22      # lessons: ids of curriculum.plan(day)

A tale gets <out>/<key>-<lang>-cover.jpg, <key>-<lang>-sheet.png (two frames of every scene), <key>-<lang>.txt (the lines with their
voice and duration, the chapters, the metadata) and a short clip <key>-<lang>-clip.mp4 with real voices (the first --seconds seconds).
It uses the real text-to-speech voices, so it also shows whether a voice of the language works on the machine.
A lesson (dNNN-L1 ... dNNN-S5) gets <out>/<id>-sheet.png and <id>.txt (every segment with its cues: time, length, text).
With --tail 22 it also writes <name>-tail.mp4: the last 22 seconds (the end and the "Like / Subscribe" card, to check that the
pointer clicks on the words).

  python tools/test_tale.py voices en --out out/test        # the key "voices": every character TYPE of tales.TYPES says a line of its own
writes <out>/voices-<lang>.mp3 (the narrator says the type, then the character says its line, with its voice and effect) and
<out>/voices-<lang>.txt (a table: voice, effect, pitch F0, loudness) - to listen to and to tune the character voices.

  python tools/test_tale.py song:twinkle en --out out/test --seconds 40     # a song (bibi_buzz/songs.py): the sound (mp3), the voice alone, a table
      # that compares every sung syllable with its note (pitch in Hz and cents, how much of it is voiced), cover, sheet, clip, description

  python tools/test_tale.py voices-list en --out out/test   # which voices the machine offers (voices-list.txt)
  python tools/test_tale.py "lab=girl:en-US-AnaNeural|-2%|+10Hz|;boy:en-US-AnaNeural|+2%|-30Hz|" en --out out/test   # a voice laboratory (voices-lab-en.mp3 / .txt)
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bibi_buzz import curriculum as CU      # noqa: E402
from bibi_buzz import draw as D             # noqa: E402
from bibi_buzz import story as SY           # noqa: E402
from bibi_buzz import tales as TL           # noqa: E402


def test_tale(a, ffmpeg, key):
    base = os.path.join(a.out, f"{key}-{a.lang}")
    t = TL.build(key, a.lang)
    t.id = f"test-{key}-{a.lang}"
    D.set_language(a.lang)
    print("font:", D._face(), flush=True)

    SY.prepare(t, ffmpeg, a.cache)                                          # real voices (and the Turkish fallback when needed)
    problems, st = SY.sync_report(t)
    print("sync problems:", problems or "none", "| duration %.1fs, voice %.1fs" % (st["duration"], st["voice_seconds"]), flush=True)
    SY.make_cover(t, base + "-cover.jpg")
    SY.contact_sheet(t, base + "-sheet.png", cols=4, thumb=480, times=[sc.t_start + sc.dur * f for sc in t.scenes for f in (0.35, 0.75)])

    ch = SY.chapters(t)
    chapters_text = "\n".join(f"{SY.fmt_time(s)} {label}" for s, label in ch)
    meta = CU.metadata(t, chapters_text)
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write("sync problems: %s\nduration %.1fs, voice %.1fs\n\n" % ("none" if not problems else "\n  " + "\n  ".join(str(p) for p in problems),
                                                                       st["duration"], st["voice_seconds"]))
        for sc in t.scenes:
            for b in sc.beats:
                if b.text:
                    f.write("%6.1fs  %-5s %-22s %s\n" % (sc.t_start + b.v0, b.who or "nar", t.voice_of(b.voice or b.who)[0], b.text))
        f.write("\n" + chapters_text + "\n\n" + json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    print("voices used:", sorted({t.voice_of(b.voice or b.who)[0] for sc in t.scenes for b in sc.beats if b.text}), flush=True)

    if a.seconds > 0:
        info = SY.render(t, base + "-clip.mp4", ffmpeg, a.cache, t_range=(0.0, a.seconds), quiet=True)
        print("clip:", info["file"], "(first %.0f s, with the real voices) rendered in %ss" % (a.seconds, info["seconds_to_render"]), flush=True)
    if a.tail > 0:
        info = SY.render(t, base + "-tail.mp4", ffmpeg, a.cache, t_range=(max(0.0, t.duration - a.tail), t.duration), quiet=True)
        print("tail clip:", info["file"], "(the last %.0f s, with the real voices) rendered in %ss" % (a.tail, info["seconds_to_render"]), flush=True)


def _write_mp3(y, sr, path, ffmpeg, kbps=160):
    import wave
    import numpy as np
    wav = path[:-4] + ".wav"
    with wave.open(wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    r = subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "%dk" % kbps, path], capture_output=True, text=True)
    if r.returncode:
        print("mp3 failed:", r.stderr[:300], flush=True)
    else:
        os.remove(wav)


def test_song(a, ffmpeg, key):
    """A song of bibi_buzz/songs.py in one language, made with the real voice: <base>.mp3 (the whole sound), <base>-voice.mp3 (the sung voice alone),
    <base>.txt (every sung syllable: its note, the pitch that was measured in the voice, the error in cents, how much of it is voiced; the span of
    every line; the description), the cover, a contact sheet and a clip of the video (the first --seconds, and with --tail the last seconds)."""
    import numpy as np
    from bibi_buzz import songs as SS
    from bibi_buzz import voice as VO
    base = os.path.join(a.out, "song-%s-%s" % (key, a.lang))
    t = SS.build(key, a.lang)
    D.set_language(a.lang)
    sr = VO.SR
    clips = SY.prepare(t, ffmpeg, a.cache)                                  # the real voice: one clip for every word that is sung
    keys = sorted(clips, key=str)                                           # (the spoken words are kept too: the singing can then be worked on offline)
    np.savez_compressed(base + "-clips.npz", **{"c%03d" % i: np.asarray(clips[k], dtype=np.float32) for i, k in enumerate(keys)})
    with open(base + "-clips.json", "w", encoding="utf-8") as f:
        json.dump([list(k) for k in keys], f, ensure_ascii=False)
    problems, st = SY.sync_report(t)
    print("song %s (%s): %.1f s, %d scenes, sync problems: %s" % (key, a.lang, t.duration, len(t.scenes), problems or "none"), flush=True)
    mix = t.mix_audio(clips)
    voc, spans, _c = t._ensure(clips)
    voc = voc[:len(mix)]
    _write_mp3(mix, sr, base + ".mp3", ffmpeg)
    _write_mp3(voc / (float(np.max(np.abs(voc))) + 1e-9) * 0.9, sr, base + "-voice.mp3", ffmpeg, 128)
    print("mix:", {k: round(v, 4) for k, v in t.mix_stats.items()}, flush=True)

    rows, errs, unvoiced = [], [], 0
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    for sec in t.sections:
        if sec.get("mode", "sing") != "sing":
            continue
        for li, it in enumerate(sec["items"]):
            tt = it["t0"]                                                  # (global seconds of the note that is being looked at)
            syl = t.syllable_spans(sec, it)
            k = 0
            for mm, d in it["notes"]:
                if mm is not None and k < len(syl):
                    w, j, _a, _b = syl[k]
                    k += 1
                    exp = 440.0 * 2 ** ((mm + t.shift - 69) / 12.0)
                    lo, hi = tt + 0.22 * d * t.beat, tt + d * t.beat - 0.12 * d * t.beat
                    seg = voc[int(lo * sr):int(hi * sr)]
                    f = _f0(seg, sr) if len(seg) > int(0.12 * sr) else np.array([])
                    nb = (mm + t.shift) % 12
                    nm = "%s%d" % (names[nb], (mm + t.shift) // 12 - 1)
                    if len(f) >= 3:
                        got = float(np.median(f))
                        cents = 1200.0 * math.log2(got / exp)
                        errs.append(cents)
                        rows.append("%-9s %-3s %-10s %-4s %7.1f %7.1f %+7.0f   %3d%%" % (sec["name"], it["key"], w["syl"][j], nm, exp, got, cents,
                                                                                           100 * len(f) / max(1, (hi - lo) / 0.01)))
                    else:
                        unvoiced += 1
                        rows.append("%-9s %-3s %-10s %-4s %7.1f %7s %7s   (no pitch found)" % (sec["name"], it["key"], w["syl"][j], nm, exp, "-", "-"))
                tt += d * t.beat
    summary = "syllables with a pitch: %d, without: %d" % (len(errs), unvoiced)
    if errs:
        e = np.array(errs)
        summary += " | median error %+.0f cents, mean |error| %.0f cents, within 50 cents: %d%%, within 100 cents: %d%%" % (
            np.median(e), np.mean(np.abs(e)), 100 * np.mean(np.abs(e) < 50), 100 * np.mean(np.abs(e) < 100))
    print(summary, flush=True)
    meta = CU.metadata(t, "")
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write("song %s (%s)  %.2f s  bpm %s  shift %+d semitones  voice %s\n" % (key, a.lang, t.duration, t.bpm, t.shift, t._voice()))
        f.write("sync problems: %s\n%s\n\n" % (problems or "none", summary))
        f.write("%-9s %-3s %-10s %-4s %7s %7s %7s   %s\n" % ("section", "ln", "syllable", "note", "exp Hz", "got Hz", "cents", "voiced"))
        f.write("\n".join(rows) + "\n\n")
        for (si, li), (s0, s1) in sorted(spans.items()):
            sec = t.sections[si]
            it = sec["items"][li]
            f.write("line %-9s %-3s expected %7.2f .. %7.2f   sound %7.2f .. %7.2f\n" % (sec["name"], it["key"], it["t0"], it["t0"] + it["beats"] * t.beat, s0, s1))
        f.write("\n" + json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    SY.make_cover(t, base + "-cover.jpg")
    SY.contact_sheet(t, base + "-sheet.png", cols=4, thumb=480, times=[sc.t_start + sc.dur * f for sc in t.scenes for f in (0.3, 0.75)])
    if a.seconds > 0:
        info = SY.render(t, base + "-clip.mp4", ffmpeg, a.cache, t_range=(0.0, a.seconds), quiet=True)
        print("clip:", info["file"], "(first %.0f s, with the real voice) rendered in %ss" % (a.seconds, info["seconds_to_render"]), flush=True)
    if a.tail > 0:
        info = SY.render(t, base + "-tail.mp4", ffmpeg, a.cache, t_range=(max(0.0, t.duration - a.tail), t.duration), quiet=True)
        print("tail clip:", info["file"], "(the last %.0f s)" % a.tail, flush=True)


# what each character TYPE says in the "voices" check: (English, Turkish), and its name (English, Turkish)
VOICE_LINES = {
    "nar": ("Once upon a time, in a sunny green meadow, there lived a very fast hare.", "Bir varmış, bir yokmuş, güneşli yemyeşil bir çayırda çok hızlı bir tavşan yaşarmış."),
    "girl": ("Hello! I am a little girl. Do you want to play?", "Merhaba! Ben küçük bir kızım. Oynamak ister misin?"),
    "teen": ("Oh, I would love to go to the ball!", "Of, baloya gitmeyi çok isterdim!"),
    "boy": ("Look at me! I can run so fast!", "Bana bak! Çok hızlı koşabiliyorum!"),
    "baby": ("This porridge is just right!", "Bu yulaf lapası tam kıvamında!"),
    "woman": ("Come inside, my dears. Supper is ready.", "İçeri gelin canlarım. Yemek hazır."),
    "granny": ("Come here, my dear. Let me tell you a story.", "Gel bakalım canım. Sana bir masal anlatayım."),
    "fakegranny": ("Come closer, my dear, so I can see you.", "Yaklaş bakalım canım, seni göreyim."),
    "man": ("Good morning! What a fine day for work!", "Günaydın! Çalışmak için ne güzel bir gün!"),
    "grandpa": ("Long ago, when I was young, I planted this seed.", "Çok eskiden, ben gençken, bu tohumu ben ekmiştim."),
    "prince": ("Please, may I have this dance?", "Lütfen, bu dansı benimle yapar mısınız?"),
    "king": ("I am the king! Bring me my supper!", "Ben kralım! Bana yemeğimi getirin!"),
    "lord": ("Welcome to my grand house!", "Büyük evime hoş geldiniz!"),
    "queen": ("Magic mirror, who is the fairest of all?", "Sihirli ayna, söyle bana, en güzel kim?"),
    "stepmother": ("Work, work, work! There is much to do!", "Çalış, çalış, çalış! Yapılacak çok iş var!"),
    "stepsister": ("That dress is mine! It is mine!", "O elbise benim! Benim!"),
    "witch": ("Ha, ha, ha! Take a bite of my apple, my dear.", "Ha, ha, ha! Elmamdan bir ısır bakalım canım."),
    "fairy": ("Do not cry. I am your fairy godmother.", "Ağlama. Ben senin peri annenim."),
    "mirror": ("You are the fairest of them all.", "Sen hepsinden daha güzelsin."),
    "dwarf": ("Look! We found a little house in the woods!", "Bak! Ormanda küçük bir ev bulduk!"),
    "elf": ("Snip, snap! We will make the shoes!", "Çıt çıt! Ayakkabıları biz yapacağız!"),
    "elfgirl": ("Snip, snap! What a lovely little shoe!", "Çıt çıt! Ne güzel küçük bir ayakkabı!"),
    "troll": ("Who is that trip-trapping over my bridge?", "Köprümün üstünde tıp tıp yürüyen kim?"),
    "giant": ("Fee, fi, fo, fum! I smell a boy!", "Fii, fay, fo, fam! Bir çocuk kokusu alıyorum!"),
    "pig": ("Not by the hair of my chinny chin chin!", "Asla! Çenemdeki tüylere yemin olsun!"),
    "wolf": ("I will huff, and I will puff, and I will blow your house down!", "Üfleyeceğim, püfleyeceğim, evinizi yıkacağım!"),
    "hare": ("I am the fastest animal in the whole wide world!", "Ben dünyanın en hızlı hayvanıyım!"),
    "tortoise": ("Slow and steady wins the race.", "Yavaş ve sağlam, yarışı kazanır."),
    "bear": ("Somebody has been eating my porridge!", "Biri benim yulaf lapamı yemiş!"),
    "mamabear": ("Somebody has been sitting in my chair!", "Biri benim sandalyemde oturmuş!"),
    "goat_little": ("Trip, trap, trip, trap! May I cross the bridge?", "Tıp tıp, tıp tıp! Köprüden geçebilir miyim?"),
    "goat_mid": ("Trip, trap, trip, trap! Please let me cross!", "Tıp tıp, tıp tıp! Lütfen geçmeme izin ver!"),
    "goat_big": ("I am the big billy goat! Out of my way!", "Ben koca keçiyim! Çekil yolumdan!"),
    "hen": ("Who will help me plant the wheat?", "Buğdayı ekmeme kim yardım edecek?"),
    "fox": ("Hello, friends. May I have a taste of your soup?", "Merhaba dostlar. Çorbanızdan tadabilir miyim?"),
    "tiny": ("I am very small, but I can help you!", "Çok küçüğüm ama sana yardım edebilirim!"),
    "lion": ("Roar! Who dares to wake the king of the jungle?", "Hırrr! Ormanın kralını kim uyandırmaya cesaret eder?"),
}
VOICE_NAMES = {
    "nar": ("Narrator", "Anlatıcı"), "girl": ("Girl", "Kız çocuğu"), "teen": ("Young woman", "Genç kız"), "boy": ("Boy", "Erkek çocuğu"), "baby": ("Baby", "Bebek"),
    "woman": ("Mother", "Anne"), "granny": ("Granny", "Nine"), "fakegranny": ("The wolf as granny", "Nine kılığındaki kurt"),
    "man": ("Man", "Adam"), "grandpa": ("Grandpa", "Dede"), "prince": ("Prince", "Prens"), "king": ("King", "Kral"), "lord": ("Lord", "Lord"),
    "queen": ("Queen", "Kraliçe"), "stepmother": ("Stepmother", "Üvey anne"), "stepsister": ("Stepsister", "Üvey kız kardeş"), "witch": ("Witch", "Cadı"),
    "fairy": ("Fairy", "Peri"), "mirror": ("Magic mirror", "Sihirli ayna"), "dwarf": ("Dwarf", "Cüce"), "elf": ("Elf", "Elf"), "elfgirl": ("Elf girl", "Elf kız"),
    "troll": ("Troll", "Trol"), "giant": ("Giant", "Dev"), "pig": ("Pig", "Domuz"), "wolf": ("Wolf", "Kurt"), "hare": ("Hare", "Tavşan"),
    "tortoise": ("Tortoise", "Kaplumbağa"), "bear": ("Papa bear", "Baba ayı"), "mamabear": ("Mama bear", "Anne ayı"), "goat_little": ("Little goat", "Küçük keçi"),
    "goat_mid": ("Middle goat", "Orta keçi"), "goat_big": ("Big goat", "Büyük keçi"), "hen": ("Hen", "Tavuk"), "fox": ("Fox", "Tilki"), "tiny": ("Mouse", "Fare"),
    "lion": ("Lion", "Aslan"),
}


def _f0(y, sr=44100):
    """Pitch track (Hz) of the voiced frames of a clip: normalized autocorrelation by FFT, on a copy at a third of the sample rate."""
    import numpy as np
    n3 = len(y) // 3 * 3
    y = y[:n3].reshape(-1, 3).mean(axis=1)
    sr //= 3
    fl, hop = int(0.04 * sr), int(0.01 * sr)
    lo, hi = int(sr / 520), int(sr / 70)
    if len(y) < fl + hop * 4:
        return np.array([])
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
    return np.array(out)


def _voices_table(a, ffmpeg, rows, base):
    """rows: [(type, name, item, label_item)]: writes <base>.txt (a table of the pitch and loudness of every clip) and <base>.mp3 to listen to
    (the narrator says the name, then the character says its line)."""
    import wave
    import numpy as np
    from bibi_buzz import voice as VO
    clips = {}
    for it in sorted({it for row in rows for it in row[2:]}):
        try:
            clips.update(VO.synth_items([it], ffmpeg, a.cache))
        except BaseException as e:                                             # (a voice that does not exist must not stop the others)
            print("FAILED:", it, repr(e)[:160], flush=True)
    sr = VO.SR
    gap1, gap2 = np.zeros(int(0.35 * sr)), np.zeros(int(1.0 * sr))
    lines, parts = [], []
    lines.append("%-12s %-34s %-5s %-6s %-30s %5s  %6s %6s %6s %7s %5s" % ("type", "voice", "rate", "pitch", "effect", "sec", "F0 med", "p10", "p90", "rms dB", "peak"))
    n = 0
    for typ, name, item, lab in rows:
        if item not in clips:
            lines.append("%-12s %-34s %-5s %-6s %-30s  FAILED" % (typ, item[1], item[2], item[3], item[4] or "-"))
            continue
        y = clips[item]
        f = _f0(y, sr)
        rms = 20 * math.log10(float(np.sqrt(np.mean(y ** 2))) + 1e-9)
        if len(f) >= 8:
            fs = "%6.1f %6.1f %6.1f" % (np.median(f), np.percentile(f, 10), np.percentile(f, 90))
        else:
            fs = "%6s %6s %6s" % ("-", "-", "-")
        lines.append("%-12s %-34s %-5s %-6s %-30s %5.1f  %s %7.1f %5.2f" % (typ, item[1], item[2], item[3], item[4] or "-", len(y) / sr, fs, rms, float(np.max(np.abs(y)))))
        if lab in clips:
            parts += [clips[lab], gap1]
        parts += [y, gap2]
        n += 1
    y = np.concatenate(parts) if parts else np.zeros(sr)
    with wave.open(base + ".wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    r = subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", base + ".wav", "-c:a", "libmp3lame", "-b:a", "128k", base + ".mp3"], capture_output=True, text=True)
    if r.returncode:
        print("mp3 failed:", r.stderr[:300], flush=True)
    else:
        os.remove(base + ".wav")
    lines.append("")
    lines.append("%d voices, %.0f seconds" % (n, len(y) / sr))
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)


def test_voices(a, ffmpeg):
    """Every character type of tales.TYPES says a line with its voice and effect; a table of the pitch and loudness and one mp3 to listen to."""
    i = 0 if a.lang == "en" else 1
    nar = tuple(TL.TYPES["nar"][i])
    rows = []
    for typ, spec in TL.TYPES.items():
        if typ in VOICE_LINES:
            v, r, p, fx = spec[i]
            rows.append((typ, VOICE_NAMES[typ][i], (VOICE_LINES[typ][i], v, r, p, fx), (VOICE_NAMES[typ][i],) + nar))
    _voices_table(a, ffmpeg, rows, os.path.join(a.out, "voices-" + a.lang))


def test_lab(a, ffmpeg, spec):
    """A voice laboratory: spec = 'type:voice|rate|pitch|effect;type:voice|rate|pitch|effect;...' (the type picks the sentence that is said,
    in the language a.lang; the effect may be left out) -> voices-lab-<lang>.txt / .mp3, to compare voices and settings by ear and by pitch."""
    i = 0 if a.lang == "en" else 1
    nar = tuple(TL.TYPES["nar"][i])
    rows = []
    for ent in [e.strip() for e in spec.split(";") if e.strip()]:
        typ, _, rest = ent.partition(":")
        v, r, p, fx = (rest.split("|") + ["", "", "", ""])[:4]
        name = "%s %s %s %s" % (v.split("-")[-1].replace("Neural", ""), r, p, fx)
        rows.append((typ, name, (VOICE_LINES[typ][i], v, r, p, fx), (name,) + nar))
    _voices_table(a, ffmpeg, rows, os.path.join(a.out, "voices-lab-" + a.lang))


def test_voice_list(a):
    """Which text-to-speech voices the machine offers for English and Turkish (and the multilingual ones): voices-list.txt."""
    import asyncio
    import edge_tts
    vs = asyncio.run(edge_tts.list_voices())
    keep = [v for v in vs if v["Locale"].startswith(("en-", "tr-")) or "Multilingual" in v["ShortName"]]
    lines = []
    for v in sorted(keep, key=lambda v: v["ShortName"]):
        tag = v.get("VoiceTag", {}) or {}
        lines.append("%-42s %-7s %-7s %s | %s" % (v["ShortName"], v["Gender"], v["Locale"], ",".join(tag.get("ContentCategories", [])),
                                                  ",".join(tag.get("VoicePersonalities", []))))
    lines.append("")
    lines.append("%d voices of %d" % (len(keep), len(vs)))
    with open(os.path.join(a.out, "voices-list.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)


def render_lesson_range(les, clips, path, ffmpeg, t0, t1):
    """A piece (t0..t1 seconds) of a lesson with its real sound: only those frames are drawn."""
    from bibi_buzz import music as MU
    from bibi_buzz import stage as ST
    from bibi_buzz import voice as VO
    mix = MU.mix(les, clips)
    wav = path + ".wav"
    MU.write_wav(wav, mix[int(t0 * VO.SR):int(t1 * VO.SR)])
    L = ST.layout(les.fmt)
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{L.w}x{L.h}", "-r", str(ST.FPS), "-i", "-",
           "-i", wav, "-map", "0:v", "-map", "1:a", "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
           "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "160k", "-t", "%.3f" % (t1 - t0), "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(t0 * ST.FPS), int(math.ceil(t1 * ST.FPS))):
        proc.stdin.write(ST.render_frame(les, i / ST.FPS).tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed for " + path)
    os.remove(wav)


def test_lesson(a, ffmpeg, lid):
    from bibi_buzz import emoji as E
    from bibi_buzz import pipeline as PL
    day = int(lid[1:4])
    les = next((l for l in CU.plan(day) if l.id == lid), None)
    if les is None:
        sys.exit("no lesson %s on day %d (ids: %s)" % (lid, day, ", ".join(l.id for l in CU.plan(day))))
    D.set_language("en")
    base = os.path.join(a.out, lid)
    clips = PL.prepare(les, ffmpeg, a.cache)                                # the real voice
    problems, st = PL.sync_report(les)
    print(lid, les.title, "| sync problems:", problems or "none", "| duration %.1fs, bpm %s, voice %.1fs" % (st["duration"], les.bpm, st["voice_seconds"]), flush=True)
    missing = E.prefetch(les.codes())
    if missing:
        print("[emoji] could not download %d sprites: %s" % (len(missing), ", ".join(missing)), flush=True)
    try:
        PL.contact_sheet(les, base + "-sheet.png")
    except Exception as e:                                                  # (e.g. an emoji sprite that could not be downloaded)
        print("contact sheet failed:", repr(e), flush=True)
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write("%s  %s\nbpm %s  beat %.3f s  duration %.2f s\n" % (lid, les.title, les.bpm, les.beat, les.duration))
        for seg in les.segs:
            f.write("\n-- %s  %.2f .. %.2f s\n" % (seg.kind, seg.t0, seg.t1))
            for c in seg.cues:
                if c.text:
                    f.write("%7.2fs  %5.2fs  %s\n" % (c.t, c.dur, c.text))
    if a.tail > 0:
        render_lesson_range(les, clips, base + "-tail.mp4", ffmpeg, max(0.0, les.duration - a.tail), les.duration)
        print("tail clip:", lid + "-tail.mp4", "(the last %.0f s, with the real voice)" % a.tail, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("key", help="a tale key (%s), lesson ids like d003-L1,d003-L4, or 'voices' (every character type says a line)" % ", ".join(sorted(TL.TALES)))
    ap.add_argument("lang", nargs="?", default="en", choices=["en", "tr"], help="language of a tale")
    ap.add_argument("--out", default="out/test")
    ap.add_argument("--seconds", type=float, default=40.0, help="length of the clip with real voices (0 = no clip; tales only)")
    ap.add_argument("--tail", type=float, default=0.0, help="also render the LAST n seconds (the end card) with real voices (0 = no)")
    ap.add_argument("--cache", default=os.path.join("out", "tts-cache"))
    a = ap.parse_args()

    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg = "ffmpeg"
    os.makedirs(a.out, exist_ok=True)
    if a.key.startswith("lab="):                                               # the spec has commas and semicolons of its own
        test_lab(a, ffmpeg, a.key[4:])
        return
    for key in [k.strip() for k in a.key.split(",") if k.strip()]:
        if key == "voices":
            test_voices(a, ffmpeg)
        elif key == "voices-list":
            test_voice_list(a)
        elif key.startswith("song:"):
            test_song(a, ffmpeg, key[5:])
        elif key in TL.TALES:
            test_tale(a, ffmpeg, key)
        elif re.fullmatch(r"d\d{3}-[LS]\d+", key):
            test_lesson(a, ffmpeg, key)
        else:
            sys.exit("unknown key %r: use a tale (%s) or a lesson id like d003-L1" % (key, ", ".join(sorted(TL.TALES))))


if __name__ == "__main__":
    main()
