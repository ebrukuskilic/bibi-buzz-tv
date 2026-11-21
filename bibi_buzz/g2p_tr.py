# The text-to-sounds module (Turkish spelling -> Kokoro phonemes) of the Kokoro Turkish voice model, https://huggingface.co/empiriolabsai/kokoro-turkish
# (g2p_tr.py there; Copyright 2026 EmpirioLabs.ai LLC; Apache License, Version 2.0, http://www.apache.org/licenses/LICENSE-2.0).
# It was read through and written into this repository by hand (consolidated and re-typed, so it is NOT guaranteed to be byte for byte the original) so that
# the workflows never download somebody else's code and run it: this file is plain Python (os, re, shutil, subprocess, unicodedata), it uses no network,
# writes no files, and the only program it starts is `espeak-ng` (voice `tr`).
from __future__ import annotations

"""EmpirioLabs G2P for the Kokoro Turkish model (one self-contained file).

    from g2p_tr import TurkishG2P
    phonemes, _ = TurkishG2P()(text)
"""

"""Shared pieces of the EmpirioLabs Kokoro G2P modules: the Kokoro-82M phoneme vocabulary, punctuation-aware
chunking, and an espeak-ng runner that calls the `espeak-ng` program (no library linking)."""

import os
import re
import shutil
import subprocess
import unicodedata

# The 114 symbols Kokoro-82M's config.json maps to ids (hexgrad/Kokoro-82M, vocab unchanged).
KOKORO_SYMBOLS = (
    ';:,.!?—…"()“” ̃ʣʥʦʨᵝꭧAIOQSTWYᵊ'
    'abcdefhijklmnopqrstuvwxyz'
    'ɑɐɒæβɔɕçɖðʤəɚɛɜɟɡ'
    'ɥɨɪʝɯɰŋɳɲɴøɸθœɹɾɻ'
    'ʁɽʂʃʈʧʊʋʌɣɤχʎʒʔˈˌ'
    'ːʰʲ↓→↗↘ᵻ'
)
VOCAB = frozenset(KOKORO_SYMBOLS)
assert len(VOCAB) == 114, len(VOCAB)

PUNCT_KEEP = ";:,.!?…"          # punctuation tokens we emit
EM = "—"                         # Kokoro's dash token

# Affricates written as two letters by espeak-ng; Kokoro has single-symbol ligatures for them.
AFFRICATES = (("t͡s", "ʦ"), ("d͡z", "ʣ"), ("t͡ʃ", "ʧ"),
              ("d͡ʒ", "ʤ"), ("t͡ɕ", "ʨ"), ("d͡ʑ", "ʥ"),
              ("ts", "ʦ"), ("dz", "ʣ"), ("tʃ", "ʧ"), ("dʒ", "ʤ"),
              ("tɕ", "ʨ"), ("dʑ", "ʥ"))

def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def keep_final_punct(original: str, normalized: str) -> str:
    """An abbreviation such as `r.` or a number such as `295.` can swallow the sentence-final period."""
    o, n = original.rstrip(), normalized.rstrip()
    if o and o[-1] in ".!?…" and n and n[-1] not in ".!?…":
        return n + o[-1]
    return n

def unify_punctuation(text: str) -> str:
    """Map typographic variants onto the small punctuation set the models were trained with."""
    text = text.replace("…", "...").replace(" ", " ").replace(" ", " ")
    text = re.sub(r"[‘’‚‛ʼ´`]", "'", text)
    text = re.sub(r"[“”„‟«»‹›\"]", '"', text)
    text = re.sub(r"\s[\-–—]+\s", " — ", text)       # spaced dash = pause
    text = re.sub(r"[–—]", " — ", text)
    text = re.sub(r"\.{3,}", "…", text)
    text = re.sub(r"[!?]{2,}", lambda m: m.group(0)[0], text)
    return clean_spaces(text)

_SPLIT = re.compile(r"([;:,.!?…—\"()\[\]{}¿¡]+)")

def chunk(text: str) -> list[tuple[str, str]]:
    """Split normalised text into (words, following punctuation) pairs. Quotes and brackets end a chunk but
    emit no token; ;:,.!?... and the dash are kept as Kokoro tokens."""
    out: list[tuple[str, str]] = []
    parts = _SPLIT.split(text)
    for i in range(0, len(parts), 2):
        words = parts[i].strip()
        punct = parts[i + 1] if i + 1 < len(parts) else ""
        kept = "".join(ch for ch in punct if ch in PUNCT_KEEP or ch == EM)
        if kept:
            # keep one mark: the strongest (sentence end beats clause marks)
            for strong in ("?", "!", "…", ".", ";", ":", EM, ","):
                if strong in kept:
                    kept = strong
                    break
        if words:
            out.append((words, kept))
        elif kept and out and not out[-1][1]:
            out[-1] = (out[-1][0], kept)
    return out

def join_chunks(phonemized: list[str], puncts: list[str]) -> str:
    pieces = []
    for ph, p in zip(phonemized, puncts):
        ph = ph.strip()
        if not ph:
            continue
        if p == EM:
            pieces.append(ph + " " + EM)
        else:
            pieces.append(ph + p)
    return clean_spaces(" ".join(pieces))

def map_symbols(ps: str, table: list[tuple[str, str]]) -> str:
    for a, b in table:
        ps = ps.replace(a, b)
    return ps

def to_vocab(ps: str) -> str:
    """Drop anything Kokoro cannot embed (it would be silently dropped by KModel anyway)."""
    return clean_spaces("".join(ch for ch in ps if ch in VOCAB))

class Espeak:
    """Runs the espeak-ng program once per call on newline-separated chunks (one output line per chunk).
    Set ESPEAK_NG_BIN to point at a specific binary."""

    def __init__(self, voice: str):
        self.voice = voice
        self.bin = os.environ.get("ESPEAK_NG_BIN") or shutil.which("espeak-ng") or shutil.which("espeak")
        if not self.bin:
            raise RuntimeError("espeak-ng not found: install it (apt-get install espeak-ng, brew install "
                               "espeak-ng, or the Windows installer) or set ESPEAK_NG_BIN")

    def _run(self, lines: list[str]) -> list[str]:
        r = subprocess.run([self.bin, "-q", "--ipa", "-v", self.voice, "-b", "1"],
                           input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8",
                           check=True)
        return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]

    def __call__(self, chunks: list[str]) -> list[str]:
        if not chunks:
            return []
        out = self._run(chunks)
        if len(out) == len(chunks):
            return out
        return [" ".join(self._run([c])) for c in chunks]   # a chunk split into clauses: do one at a time

def version_of_espeak() -> str:
    exe = os.environ.get("ESPEAK_NG_BIN") or shutil.which("espeak-ng") or "espeak-ng"
    try:
        return subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return "missing"

# ---- language module ----
"""Turkish G2P for the EmpirioLabs Kokoro Turkish model: plain text (numbers with suffixes such as 2024'te,
ordinals, dates, times, percentages written %15, money, units and common abbreviations) to Kokoro-82M phonemes,
through the espeak-ng program (voice `tr`).

    g2p = TurkishG2P()
    phonemes, _ = g2p("Toplantı 12 Mart 2025'te saat 14:30'da, bilet fiyatı %15 indirimle 250 TL.")
"""

import re

UNITS = ["sıfır", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
TENS = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım",
          "Aralık"]
LETTERS = {"a": "a", "b": "be", "c": "ce", "ç": "çe", "d": "de", "e": "e", "f": "fe", "g": "ge", "ğ": "yumuşak ge",
           "h": "he", "ı": "ı", "i": "i", "j": "je", "k": "ke", "l": "le", "m": "me", "n": "ne", "o": "o", "ö": "ö",
           "p": "pe", "q": "kü", "r": "re", "s": "se", "ş": "şe", "t": "te", "u": "u", "ü": "ü", "v": "ve",
           "w": "çift ve", "x": "iks", "y": "ye", "z": "ze"}
ABBREVIATIONS = [
    (r"\bvb\.", "ve benzeri"), (r"\bvs\.", "vesaire"), (r"\bvd\.", "ve diğerleri"), (r"\bDr\.", "Doktor"),
    (r"\bProf\.", "Profesör"), (r"\bDoç\.", "Doçent"), (r"\bOp\.", "Operatör"), (r"\bAv\.", "Avukat"),
    (r"\bSn\.", "Sayın"), (r"\börn\.", "örneğin"), (r"\bbkz\.", "bakınız"), (r"\bCad\.", "Caddesi"),
    (r"\bSok\.", "Sokağı"), (r"\bMah\.", "Mahallesi"), (r"\bBlv\.", "Bulvarı"), (r"\bNo\.?(?=\s?\d)", "numara"),
    (r"\byy\.", "yüzyıl"), (r"\bM\.Ö\.", "milattan önce"), (r"\bM\.S\.", "milattan sonra"), (r"\bMÖ\b", "milattan önce"),
    (r"\bMS\b", "milattan sonra"), (r"\bTel\.", "telefon"), (r"\bçev\.", "çeviren"), (r"\bhaz\.", "hazırlayan"),
    (r"\bAŞ\b", "anonim şirketi"), (r"\bA\.Ş\.", "anonim şirketi"), (r"\bLtd\.", "limitet"), (r"\bŞti\.", "şirketi"),
]
UNIT_WORDS = {"km/sa": "kilometre", "km": "kilometre", "cm": "santimetre", "mm": "milimetre", "m": "metre",
              "kg": "kilogram", "gr": "gram", "g": "gram", "mg": "miligram", "lt": "litre", "l": "litre",
              "ml": "mililitre", "°C": "derece", "°": "derece", "TL": "lira", "₺": "lira", "$": "dolar",
              "USD": "dolar", "€": "avro", "EUR": "avro", "£": "sterlin", "sa": "saat", "dk": "dakika",
              "sn": "saniye", "MB": "megabayt", "GB": "gigabayt"}
BACK, FRONT = set("aıou"), set("eiöü")
HARD = set("çfhkpsşt")

# espeak-ng `tr` symbols Kokoro lacks, mapped to the nearest symbol in Kokoro's vocabulary.
SYMBOL_MAP = AFFRICATES + (("ɫ", "l"), ("g", "ɡ"), ("ʎ", "l"), ("ɦ", "h"))

def tr_lower(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()

def _below_1000(n: int) -> list[str]:
    h, r = divmod(n, 100)
    words = []
    if h:
        words += (["yüz"] if h == 1 else [UNITS[h], "yüz"])
    t, u = divmod(r, 10)
    if t:
        words.append(TENS[t])
    if u:
        words.append(UNITS[u])
    return words

def int_words(n: int) -> str:
    if n < 0:
        return "eksi " + int_words(-n)
    if n == 0:
        return "sıfır"
    words: list[str] = []
    for value, word in ((10 ** 12, "trilyon"), (10 ** 9, "milyar"), (10 ** 6, "milyon"), (1000, "bin")):
        q, n = divmod(n, value)
        if q:
            words += ([word] if (q == 1 and word == "bin") else _below_1000(q) + [word])
    words += _below_1000(n)
    return " ".join(words)

def _last_vowel(word: str) -> str:
    for ch in reversed(tr_lower(word)):
        if ch in BACK | FRONT:
            return ch
    return "e"

def ordinal_words(n: int) -> str:
    w = int_words(n)
    last = w.split()[-1]
    v = _last_vowel(last)
    if last.endswith("t") and last in ("dört",):
        last_base = last[:-1] + "d"
    else:
        last_base = last
    suffix = {"a": "ıncı", "ı": "ıncı", "o": "uncu", "u": "uncu", "e": "inci", "i": "inci", "ö": "üncü",
              "ü": "üncü"}[v]
    if last_base[-1] in "aeıioöuü":
        suffix = suffix[1:]
    return " ".join(w.split()[:-1] + [last_base + suffix])

def attach_suffix(words: str, suffix: str) -> str:
    """'iki bin yirmi dört' + 'te' -> 'iki bin yirmi dörtte' (the writer already chose the harmony)."""
    return words + suffix if suffix else words

def _num(s: str) -> int:
    return int(s.replace(".", ""))

def _decimal(intpart: str, frac: str) -> str:
    fw = int_words(int(frac)) if not frac.startswith("0") else " ".join(UNITS[int(d)] for d in frac)
    return f"{int_words(_num(intpart))} virgül {fw}"

def _spell(word: str) -> str:
    return " ".join(LETTERS.get(ch, ch) for ch in tr_lower(word))

def normalize(text: str) -> str:
    t = unify_punctuation(nfc(text))
    for pat, rep in ABBREVIATIONS:
        t = re.sub(pat, rep, t)
    sfx = r"(?:'([a-zçğıöşüA-ZÇĞİÖŞÜ]+))?"
    # dates 12.03.2024 / 12/03/2024 (+ optional suffix)
    def dmy(m):
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (1 <= mo <= 12 and 1 <= d <= 31):
            return m.group(0)
        return attach_suffix(f"{int_words(d)} {MONTHS[mo - 1]} {int_words(y)}", m.group(4) or "")
    t = re.sub(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})" + sfx, dmy, t)
    t = re.sub(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b",
               lambda m: f"{int_words(int(m.group(3)))} {MONTHS[int(m.group(2)) - 1]} {int_words(int(m.group(1)))}"
               if 1 <= int(m.group(2)) <= 12 else m.group(0), t)
    # times 14:30 or 14.30 after "saat" (+ suffix)
    def hm(m):
        h, mi = int(m.group(1)), int(m.group(2))
        if h > 23 or mi > 59:
            return m.group(0)
        s = int_words(h)
        if mi:
            s += " " + (int_words(mi) if mi >= 10 else "sıfır " + UNITS[mi])
        return attach_suffix(s, m.group(3) or "")
    t = re.sub(r"\b(\d{1,2}):(\d{2})" + sfx, hm, t)
    t = re.sub(r"(?<=\bsaat )(\d{1,2})\.(\d{2})" + sfx, hm, t)
    # percent: %15, % 15, 15% (+ suffix)
    t = re.sub(r"%\s?(\d+(?:,\d+)?)" + sfx, lambda m: "yüzde " + attach_suffix(m.group(1), "'" + m.group(2)
                                                                                if m.group(2) else ""), t)
    t = re.sub(r"(\d+(?:,\d+)?)\s?%", lambda m: "yüzde " + m.group(1), t)
    # money and units
    t = re.sub(r"([₺$€£])\s?((?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{1,2})?)", lambda m: f"{m.group(2)} {UNIT_WORDS[m.group(1)]}", t)
    def amount_unit(m):
        num, frac, unit, suffix = m.group(1), m.group(2), m.group(3), m.group(4) or ""
        word = UNIT_WORDS[unit]
        if frac and word == "lira":
            s = f"{int_words(_num(num))} lira" + (f" {int_words(int(frac.ljust(2, '0')[:2]))} kuruş"
                                                    if int(frac) else "")
        elif frac:
            s = f"{_decimal(num, frac)} {word}"
        else:
            s = f"{int_words(_num(num))} {word}"
        return attach_suffix(s, suffix)
    units = "|".join(re.escape(u) for u in sorted(UNIT_WORDS, key=len, reverse=True))
    t = re.sub(r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?\s?(" + units + r")(?![\wçğıöşü])" + sfx, amount_unit, t)
    # ordinals "3." before a lowercase word, decimals, numbers with suffixes, plain numbers
    t = re.sub(r"\b(\d+)\.(?=\s+[a-zçğıöşü])", lambda m: ordinal_words(int(m.group(1))), t)
    t = re.sub(r"\b(\d+)'(?:inci|ıncı|uncu|üncü|nci|ncı|ncu|ncü)\b", lambda m: ordinal_words(int(m.group(1))), t)
    t = re.sub(r"\b(\d{1,3}(?:\.\d{3})+|\d+),(\d+)" + sfx,
               lambda m: attach_suffix(_decimal(m.group(1), m.group(2)), m.group(3) or ""), t)
    t = re.sub(r"\b(\d{1,3}(?:\.\d{3})+|\d+)" + sfx,
               lambda m: attach_suffix(int_words(_num(m.group(1))), m.group(2) or ""), t)
    t = t.replace("&", " ve ").replace("+", " artı ").replace("=", " eşittir ").replace("@", " et ")
    # acronyms are read letter by letter; a suffix after an apostrophe joins the last letter name
    t = re.sub(r"\b([A-ZÇĞİÖŞÜ]{2,5})(?:'([a-zçğıöşü]+))?(?![a-zçğıöşü])",
               lambda m: attach_suffix(_spell(m.group(1)), m.group(2) or "")
               if (len(m.group(1)) <= 3 or not re.search(r"[AEIİOÖUÜ]", m.group(1))) else
               tr_lower(m.group(1)) + (m.group(2) or ""), t)
    t = re.sub(r"(\w)'(\w)", r"\1\2", t)       # proper-noun apostrophes: Ankara'ya -> Ankaraya
    t = t.replace("/", " ")
    return keep_final_punct(text, clean_spaces(t))

class TurkishG2P:
    """Callable like the misaki G2P classes: returns (phonemes, None)."""

    lang = "tr"

    def __init__(self):
        self.espeak = Espeak("tr")

    def phonemize_normalized(self, text: str) -> str:
        pairs = chunk(text)
        if not pairs:
            return ""
        ph = self.espeak([tr_lower(w) for w, _ in pairs])
        ps = join_chunks(ph, [p for _, p in pairs])
        return to_vocab(map_symbols(ps, list(SYMBOL_MAP)))

    def __call__(self, text: str):
        return self.phonemize_normalized(normalize(text)), None
