"""Synthesises the soundtrack with numpy only (no sample files needed).

Music: gentle ukulele/xylophone nursery-rhyme loop at 100 BPM in C major (original melody).
Sound effects are synced to timeline.build_events().
Optional: --voice adds a child-friendly text-to-speech voice-over using the `edge-tts` package.
"""
import asyncio
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np

from . import timeline as T

SR = 44100
BPM = 100
BEAT = 60.0 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def tone(freq, dur, harm=(1, 0.5, 0.25, 0.12), decay=5.0, attack=0.004):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for i, a in enumerate(harm, 1):
        if a:
            y += a * np.sin(2 * np.pi * freq * i * t) * np.exp(-t * decay * (1 + 0.4 * (i - 1)))
    return y * np.minimum(1.0, t / attack)


def add(buf, t0, sig, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf) or i < 0:
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def xylo(m, dur=0.7):
    return tone(hz(m), dur, harm=(1, 0, 0.18, 0, 0.08), decay=6.0)


def uke(m, dur=0.9):
    return tone(hz(m), dur, harm=(1, 0.5, 0.3, 0.15), decay=3.6)


def bass(m, dur=0.55):
    return tone(hz(m), dur, harm=(1, 0.3), decay=4.5)


def shaker(dur=0.09):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = np.diff(np.random.default_rng(1).standard_normal(n + 1))
    return noise * np.exp(-t * 55)


def woodblock():
    return tone(880, 0.08, harm=(1, 0.5), decay=40)


def pop_sfx():
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    f = 280 + 700 * (t / 0.16)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18)


def ding(m):
    return tone(hz(m), 1.1, harm=(1, 0.4, 0.2), decay=4.0)


def sparkle(buf, t0):
    for i, m in enumerate((88, 91, 95, 100, 96, 103)):
        add(buf, t0 + i * 0.06, tone(hz(m), 0.5, harm=(1, 0.3), decay=7), 0.22)


# chord roots / triads (MIDI) for C - G - Am - F
CHORDS = [((36, 48), (60, 64, 67)), ((43, 55), (59, 62, 67)), ((45, 57), (60, 64, 69)), ((41, 53), (60, 65, 69))]
# 8-bar melody, 4 notes per bar (C major pentatonic)
MELODY = [76, 79, 76, 72,  74, 76, 74, 67,  76, 81, 79, 76,  79, 76, 74, 72,
          72, 76, 79, 81,  79, 76, 74, 76,  81, 79, 76, 74,  72, 74, 76, 72]


def section_gain(t):
    if t < 6:
        return 0.55
    if t < 20:
        return 1.0
    if t < 100:
        return 0.85
    if t < 125:
        return 0.7
    return 0.9


def music(total):
    buf = np.zeros(int(total * SR) + SR * 3)
    bars = int(total / (4 * BEAT)) + 1
    for bar in range(bars):
        t0 = bar * 4 * BEAT
        (b1, b2), triad = CHORDS[bar % 4]
        g = section_gain(t0)
        add(buf, t0, bass(b1), 0.38 * g)
        add(buf, t0 + 2 * BEAT, bass(b2), 0.30 * g)
        for e in range(8):  # strummed eighth-note arpeggio
            add(buf, t0 + e * BEAT / 2, uke(triad[(0, 1, 2, 1, 0, 1, 2, 1)[e]]), 0.17 * g)
        for b in range(4):  # melody
            add(buf, t0 + b * BEAT, xylo(MELODY[((bar % 8) * 4) + b]), 0.30 * g)
        for e in (1, 3, 5, 7):  # offbeat shaker
            add(buf, t0 + e * BEAT / 2, shaker(), 0.10 * g)
        for b in (1, 3):  # woodblock on beats 2 and 4
            add(buf, t0 + b * BEAT, woodblock(), 0.07 * g)
    # warm final chord
    end = total - 3.0
    for m in (48, 52, 55, 60, 64):
        add(buf, end, tone(hz(m), 3.0, harm=(1, 0.4), decay=1.2), 0.12)
    return buf


def sfx(buf):
    for t, kind, arg in T.build_events():
        if kind == "pop":
            add(buf, t, pop_sfx(), 0.30)
        elif kind == "ding":
            add(buf, t, ding(arg), 0.28)
        elif kind == "sparkle":
            sparkle(buf, t)


def _read_wav_mono(path):
    with wave.open(path, "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)
    return data


def _fit(ffmpeg, mp3, wav, slot):
    """Converts one TTS clip to mono wav. If it is longer than its time slot it is sped up
    (pitch is kept) so that it ends before the next line starts."""
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", mp3, "-ar", str(SR), "-ac", "1", wav], check=True)
    y = _read_wav_mono(wav)
    dur = len(y) / SR
    if slot > 0.4 and dur > slot:
        tempo = min(1.6, dur / slot)
        fast = wav[:-4] + "_fit.wav"
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", wav, "-filter:a", "atempo=%.3f" % tempo,
                        "-ar", str(SR), "-ac", "1", fast], check=True)
        return _read_wav_mono(fast), tempo
    return y, 1.0


def voice_track(buf, ffmpeg, voice="en-US-AnaNeural"):
    """Adds a TTS voice-over (edge-tts, needs internet). Exits with an error when the voice cannot be
    produced, so a silent video is never made by accident."""
    try:
        import edge_tts
    except ImportError:
        sys.exit("[voice] edge-tts is not installed: run `pip install -r requirements-voice.txt`")
    cues = sorted(T.build_voice_cues())
    tmp = tempfile.mkdtemp()

    async def gen():
        for i, (_, text) in enumerate(cues):
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(text, voice, rate="-8%", pitch="+8Hz").save(os.path.join(tmp, f"{i}.mp3"))
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(2)

    try:
        asyncio.run(gen())
    except Exception as e:  # no internet, voice service unavailable, ...
        sys.exit(f"[voice] text-to-speech failed ({e}). Check the internet connection and try again.")
    sped = 0
    for i, (t, _) in enumerate(cues):
        nxt = cues[i + 1][0] if i + 1 < len(cues) else min(T.DURATION - 1.0, t + 4.0)
        y, tempo = _fit(ffmpeg, os.path.join(tmp, f"{i}.mp3"), os.path.join(tmp, f"{i}.wav"), nxt - t - 0.12)
        sped += tempo > 1.0
        add(buf, t, y, 0.9)
    print(f"[voice] added {len(cues)} voice lines ({voice}), {sped} sped up to fit their time slot")


def build_wav(path, ffmpeg, with_voice=False, total=T.DURATION):
    buf = music(total)
    sfx(buf)
    if with_voice:
        buf *= 0.75  # leave room for the voice
        voice_track(buf, ffmpeg)
    buf = buf[: int(total * SR)]
    fade = int(2.0 * SR)
    buf[-fade:] *= np.linspace(1, 0, fade)
    buf /= max(1e-9, np.max(np.abs(buf))) / 0.85
    pcm = (buf * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path
