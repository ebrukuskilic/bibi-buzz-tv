"""What gets made every day: 5 long lessons + 5 Shorts, each from a rotating queue (deterministic per day)."""
import datetime
import random
import string

from . import lessons as LS
from . import vocab as V

START_DATE = datetime.date(2026, 11, 20)          # day 1
COLOR_SETS = [["red", "blue", "yellow", "green", "orange"], ["purple", "pink", "brown", "white", "gray"]]
SHAPE_SETS = [["circle", "square", "triangle", "rectangle"], ["star", "heart", "oval", "diamond"]]
LETTER_SETS = ["ABCDE", "FGHIJ", "KLMNO", "PQRST", "UVWXYZ", "ABCDEFGHIJKLM", "NOPQRSTUVWXYZ"]

QUEUES = [
    # 1: animals and nature
    [("cat", "farm", 1, 1), ("cat", "wild", 1, 3), ("cat", "sea", 1, 1), ("cat", "wild", 2, 3), ("cat", "insects", 1, 1),
     ("cat", "birds", 1, 1), ("cat", "wild", 3, 3), ("game", 1), ("cat", "nature", 1, 1), ("cat", "weather", 1, 1),
     ("cat", "space", 1, 1), ("game", 2)],
    # 2: food and everyday things
    [("cat", "fruits", 1, 2), ("cat", "vegetables", 1, 1), ("cat", "fruits", 2, 2), ("cat", "food", 1, 2),
     ("cat", "clothes", 1, 2), ("cat", "food", 2, 2), ("cat", "toys", 1, 2), ("cat", "home", 1, 1),
     ("cat", "clothes", 2, 2), ("cat", "toys", 2, 2), ("cat", "school", 1, 1), ("cat", "family", 1, 1)],
    # 3: numbers, colors, shapes
    [("numbers", 1, 10), ("colors", 0), ("shapes", 0), ("numbers", 11, 20), ("colors", 1), ("shapes", 1),
     ("numbers", 1, 5), ("game", 3)],
    # 4: letters
    [("letters", 0), ("letters", 1), ("letters", 2), ("letters", 3), ("letters", 4), ("letters", 5), ("letters", 6),
     ("lgame", 1)],
    # 5: speaking, feelings, opposites, body, vehicles
    [("phr", "greetings"), ("cat", "feelings", 1, 1), ("opp", 0), ("phr", "manners"), ("cat", "body", 1, 2), ("opp", 1),
     ("phr", "talk"), ("cat", "vehicles", 1, 2), ("cat", "body", 2, 2), ("cat", "vehicles", 2, 2), ("game", 5)],
]


# One fairy tale per day replaces the 5th long lesson (the channel can only upload ~10 videos per day), one day after the other.
# The 5th lesson queue simply waits during those days and carries on afterwards. Append a key of tales.TALES to add more tales.
TALE_QUEUE = ["three-little-pigs", "tortoise-and-hare", "goldilocks", "red-riding-hood", "gingerbread-man", "three-billy-goats", "enormous-turnip", "stone-soup", "magic-porridge-pot", "cinderella", "snow-white", "elves-and-shoemaker", "princess-and-pea", "little-red-hen", "lion-and-mouse"]
TALE_FIRST_DAY = 2


def tale_key(day):
    i = day - TALE_FIRST_DAY
    return TALE_QUEUE[i] if 0 <= i < len(TALE_QUEUE) else None


# Every tale also gets a Turkish version (same pictures, Turkish voices, texts, title and description) ONE DAY AFTER its English
# premiere: the id dNNN-T2. Long videos per day: 4 lessons + the English tale + the Turkish tale; the channel can only upload
# ~10 videos per 24 hours, so a day with a Turkish tale has one Short fewer (see _raw_plan).
def tr_tale_key(day):
    return tale_key(day - 1)


# One song video a day replaces one Short: a song of songs.QUEUE in English on one day and the same song in Turkish on the next day, then the
# next song.  When the songs have run out the slot is a Short again.  Add a song: write its spec and recipe in songs.py and append its key to QUEUE.
SONG_FIRST_DAY = 3


def song_key(day):
    """(song key, language) of the day's song video, or None."""
    from . import songs as SS
    i = day - SONG_FIRST_DAY
    if i < 0 or i // 2 >= len(SS.QUEUE):
        return None
    return SS.QUEUE[i // 2], ("en" if i % 2 == 0 else "tr")


DAILY_UPLOADS = 10
# From day MIX_DAY on, the four lessons of a day are not uploaded one by one: they and the English tale become ONE 10-20 minute
# compilation (dNNN-C1, compilation.py), and the day has only MIX_SHORTS Shorts: about 6 uploads a day instead of 10 (long videos
# bring the watch hours and the money of a channel made for kids; many look-alike uploads a day keep a channel from earning).
MIX_DAY = 7
MIX_SHORTS = 2
SUBSCRIBE_URL = "https://www.youtube.com/channel/UCfiz1ZdIyjFtTYkzFOUqqWQ?sub_confirmation=1"      # opens the channel with the "Subscribe?" question


def day_number(date):
    return (date - START_DATE).days + 1


def _split(items, parts):
    n = len(items)
    out, a = [], 0
    for k in range(parts):
        b = a + (n - a + (parts - k) - 1) // (parts - k)
        out.append(items[a:b])
        a = b
    return out


def build_long(spec, id, seed, cycle):
    rng = random.Random(seed)
    kind = spec[0]
    if kind == "cat":
        _, key, part, parts = spec
        items = list(V.CATS[key]["items"])
        if cycle:
            rng.shuffle(items)
        chunk = _split(items, parts)[part - 1]
        pno = part + cycle * parts if (parts > 1 or cycle) else None
        return LS.cat_lesson(id, key, chunk, seed, part=pno)
    if kind == "numbers":
        return LS.numbers_lesson(id, spec[1], spec[2], seed)
    if kind == "colors":
        names = [n for st in COLOR_SETS for n in st]
        if cycle:
            rng.shuffle(names)
        return LS.colors_lesson(id, (names[:5], names[5:10])[spec[1]], seed)
    if kind == "shapes":
        names = [n for st in SHAPE_SETS for n in st]
        if cycle:
            rng.shuffle(names)
        return LS.shapes_lesson(id, (names[:4], names[4:8])[spec[1]], seed)
    if kind == "letters":
        return LS.letters_lesson(id, list(LETTER_SETS[spec[1]]), seed)
    if kind == "lgame":
        return LS.letters_game(id, seed)
    if kind == "opp":
        pairs = list(V.OPPOSITES)
        if cycle:
            rng.shuffle(pairs)
        return LS.opposites_lesson(id, (pairs[:5], pairs[5:10])[spec[1]], seed)
    if kind == "phr":
        items = list(V.PHRASES[spec[1]]["items"])
        return LS.phrases_lesson(id, spec[1], items, seed)
    if kind == "game":
        return LS.game_lesson(id, seed)
    raise ValueError(spec)


def build_short(slot, id, day, seed):
    """slot 0..4 -> five different kinds of Shorts; the content rotates with the day."""
    rng = random.Random(seed)
    cats = [k for k in V.CATS if k not in ("feelings", "weather", "body", "family")]
    if slot == 0:
        key = cats[(day * 2) % len(cats)]
        items = rng.sample(V.CATS[key]["items"], 3)
        return LS.short_trio(id, key, items, seed)
    if slot == 1:
        n = 3 + (day * 3) % 8
        return LS.short_count(id, n, V.COUNT_OBJECTS[day % len(V.COUNT_OBJECTS)], seed)
    if slot == 2:
        names = list(V.COLORS)
        return LS.short_color(id, names[(day - 1) % len(names)], seed)
    if slot == 3:
        return LS.short_quiz(id, seed)
    k = day % 4
    if k == 0:
        return LS.short_letter(id, string.ascii_uppercase[(day * 3) % 26], seed)
    if k == 1:
        names = list(V.SHAPES)
        return LS.short_shape(id, names[(day // 4) % len(names)], seed)
    if k == 2:
        key = ("greetings", "manners", "talk")[(day // 4) % 3]
        items = V.PHRASES[key]["items"]
        return LS.short_phrase(id, key, items[(day * 2) % len(items)], seed)
    pairs = V.OPPOSITES
    return LS.short_opposites(id, pairs[(day // 4) % len(pairs)], seed)


def _raw_plan(day):
    out = []
    tale = tale_key(day)
    for q, queue in enumerate(QUEUES):
        if q == len(QUEUES) - 1:
            if tale:                                            # today's 5th long video is a fairy tale
                from . import tales as TL
                t = TL.build(tale, "en")
                t.id = f"d{day:03d}-T1"
                out.append(t)
                continue
            idx = day - 1 - sum(1 for d in range(1, day) if tale_key(d))     # the lesson queue waited during the tale days
        else:
            idx = day - 1
        spec = queue[idx % len(queue)]
        out.append(build_long(spec, f"d{day:03d}-L{q + 1}", day * 100 + q, idx // len(queue)))
    tr = tr_tale_key(day)
    if tr:                                                      # the Turkish version of yesterday's tale
        from . import tales as TL
        t = TL.build(tr, "tr")
        t.id = f"d{day:03d}-T2"
        out.append(t)
    sk = song_key(day)
    if sk:                                                      # today's sing-along (dNNN-M1)
        try:
            from . import songs as SS
            m = SS.build(sk[0], sk[1])
            m.id = f"d{day:03d}-M1"
            out.append(m)
        except Exception as e:                                  # a song that cannot be built must never stop the day's other videos
            print(f"[song] {sk}: {e!r}", flush=True)
    n_shorts = DAILY_UPLOADS - len(out) if day < MIX_DAY else MIX_SHORTS
    for slot in range(n_shorts):                # the rest of the day's 10 uploads are Shorts (5, or fewer with a Turkish tale and a song)
        out.append(build_short(slot, f"d{day:03d}-S{slot + 1}", day, day * 100 + 50 + slot))
    return out


_titles = {}


def _day_titles(day):
    if day not in _titles:
        _titles[day] = [l.title for l in _raw_plan(day)]
    return _titles[day]


def _round_title(title, k):
    head, sep, tail = title.partition(f" | {LS.BRAND}")
    if sep:
        new = f"{head} - Round {k}{sep}{tail}"
    else:
        head, sep, tail = title.partition(" #Shorts")
        new = f"{head} - Round {k}{sep}{tail}"
    return new if len(new) <= 100 else new.replace(f" | {LS.BRAND}", "")


def plan(day):
    """Returns the list of 10 Lessons for a given day number (1-based). Titles are unique over the whole channel
    history (a repeated title gets ' - Round N'), because the uploader recognises finished uploads by title."""
    lessons = _raw_plan(day)
    seen = {}
    for d in range(1, day):
        for t in _day_titles(d):
            seen[t] = seen.get(t, 0) + 1
    for les in lessons:
        base = les.title
        n = seen.get(base, 0)
        if n:
            les.title = _round_title(base, n + 1)
        seen[base] = n + 1
    return lessons


def metadata(lesson, chapters_text=""):
    """Title / description / tags exactly as they will be typed into YouTube Studio."""
    short = lesson.fmt == "short"
    song = getattr(lesson, "song", False)
    tale = getattr(lesson, "kind", "") == "tale" and not song
    turkish = getattr(lesson, "lang", "en") == "tr"
    if turkish:
        from . import tales_tr as TT
    lines = [lesson.blurb, ""]
    # YouTube switches the subscribe watermark and the end screens off for videos made for kids: a link in the description does the job
    lines += [("Abone ol: " if turkish else "Subscribe to Bibi Buzz TV: ") + SUBSCRIBE_URL, ""]
    if song:                                                    # the words of the song, so that families can sing along
        lines += ["Şarkı sözleri:" if turkish else "Lyrics:", lesson.lyrics_text(), ""]
    if lesson.items and len(lesson.items) <= 30:
        lines.append("In this video: " + ", ".join(lesson.items) + ".")
        lines.append("")
    if chapters_text and not short and not song:
        lines += [TT.CHAPTERS if turkish else "Chapters", chapters_text, ""]
    if turkish:
        lines += (TT.SONG_FOOTER if song else TT.FOOTER) + [""]
    elif song:
        lines += ["New songs, fairy tales and learning videos for toddlers and preschoolers on Bibi Buzz TV!",
                  "Sung with text-to-speech voices. All the artwork and music were made for Bibi Buzz TV.", ""]
    elif tale:
        lines += ["New fairy tales and learning videos for toddlers and preschoolers on Bibi Buzz TV!",
                  "Narrated with text-to-speech voices. All the artwork and music were made for Bibi Buzz TV.", ""]
    else:
        lines += ["New learning videos for toddlers and preschoolers on Bibi Buzz TV!",
                  "Narrated with a text-to-speech voice. Emoji artwork: Google Noto Emoji (Apache License 2.0).", ""]
    tags_line = ((TT.SONG_HASHTAGS if song else TT.HASHTAGS) if turkish else "#nurseryrhymes #kidssongs #singalong #songsforkids #BibiBuzzTV" if song
                 else "#fairytales #storiesforkids #kidsstories #bedtimestories #BibiBuzzTV" if tale
                 else "#kidslearning #learnenglish #preschool #toddlers #BibiBuzzTV") + (" #Shorts" if short else "")
    lines.append(tags_line)
    desc = "\n".join(lines).replace("<", "").replace(">", "")
    seen, tags, total = set(), [], 0
    for t in lesson.tags:
        t = t.strip()
        if t and t.lower() not in seen and total + len(t) + 1 <= 450:
            seen.add(t.lower())
            tags.append(t)
            total += len(t) + 1
    title = lesson.title.replace("<", "").replace(">", "")
    return dict(title=title[:100], description=desc[:4900], tags=tags)
