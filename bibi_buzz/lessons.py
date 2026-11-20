"""Lesson templates: vocabulary -> Lesson (segments + spoken cues). Pure data, nothing is drawn here.

Segment kinds (drawn by stage.py): title, card, count, number, color, letter, shape, pair, phrase, review,
quiz, cta, outro.  Icon references used by review / quiz options: an emoji code ("1f34e"), "#rrggbb" (colour dot),
"n:5" (number), "L:A" (letter), "S:circle" (shape).
"""
import random

from . import vocab as V
from .schedule import Cue, Seg, Lesson

BRAND = "Bibi Buzz TV"
RINGS = ["#FF6FAE", "#3E8EDE", "#FFB400", "#3DB54A", "#9B59D0", "#FF8A1F", "#00B8D4", "#E8383D"]
THEME_NAMES = ["park", "sunset", "ocean", "night", "candy"]
BASE_TAGS = ["kids learning", "learning videos for kids", "toddler learning", "preschool", "educational videos for kids",
             "english for kids", "Bibi Buzz TV"]

INTROS = [
    "Hi friends! I am Bibi the bee. Today we will learn about {topic}!",
    "Hello, little buddies! Bibi is here. Let's learn about {topic} together!",
    "Buzz buzz! Hi friends! Are you ready to learn about {topic}?",
    "Hello hello! It is me, Bibi! Today we are going to learn about {topic}!",
]
OUTROS = [
    "Great job, friends! You learned so much today. See you next time. Bye bye!",
    "Wow, you did it! Give yourself a big clap. Bye bye, see you soon!",
    "Hooray! You are so smart. Thank you for learning with me. Bye bye!",
]
SINGULAR = {"apples": "apple", "stars": "star", "balloons": "balloon", "ducks": "duck", "fish": "fish",
            "flowers": "flower", "butterflies": "butterfly", "strawberries": "strawberry", "cars": "car",
            "bees": "bee", "cookies": "cookie", "frogs": "frog"}


# ------------------------------------------------------------------------------ helpers
def is_code(ref):
    return not ref.startswith(("#", "n:", "L:", "S:"))


def Cap(s):
    return V.cap(s)


def sentence(cat_key, word):
    tpl = V.CATS[cat_key]["sentence"]
    return (tpl.replace("{This}", V.this(word)).replace("{a}", V.art(word))
            .replace("{my}", "my " + word).replace("{w}", word))


def verb_for(cat_key):
    return "goes" if cat_key == "vehicles" else "says"


def ident_q(cat_key, word):
    if cat_key == "feelings":
        return f"Which face is {word}?", f"Yes! This face is {word}!"
    if word in V.PLURAL:
        return f"Which ones are {word}?", f"Yes! These are {word}!"
    return f"Which one is {V.art(word)}?", f"Yes! This is {V.art(word)}!"


def title_words(words, n=3):
    ws = [Cap(w) for w in words[:n]]
    return ", ".join(ws)


def mk_title(head, words, n=3, suffix=True):
    s = f"{head} | {title_words(words, n)} & More" if words else head
    full = s + (f" | {BRAND}" if suffix else "")
    while len(full) > 98 and n > 1:
        n -= 1
        s = f"{head} | {title_words(words, n)} & More"
        full = s + (f" | {BRAND}" if suffix else "")
    return full if len(full) <= 98 else full[:98]


# -------------------------------------------------------------------------------- segments
def title_seg(title, sub, codes, rng, topic):
    intro = rng.choice(INTROS).format(topic=topic)
    return Seg("title", dict(title=title, sub=sub, codes=codes[:5]), [Cue(intro, "intro")], codes=codes[:5])


def outro_seg(rng):
    return Seg("outro", {}, [Cue(rng.choice(OUTROS), "outro")], chapter="Goodbye")


# YouTube switches the comments, end screens and the subscribe watermark off for videos made for kids, so every long video carries
# its own reminder: a "Like / Subscribe" card (buttons drawn by stage.r_cta, a pointer presses them) right before the goodbye.
CTA_LINE = "Please like and subscribe, so you never miss a video!"


def cta_segs(rng):
    """The end of every long video: the Like / Subscribe card, then the goodbye. (Draws no random numbers of its own.)"""
    return [Seg("cta", {}, [Cue(CTA_LINE, "outro", min_beats=8)]), outro_seg(rng)]


def card_seg(cat_key, item, ring, chapter=None):
    word, code, extra, sound = item
    cues = [Cue(Cap(word) + "!", "reveal", cap=""), Cue(sentence(cat_key, word), "say")]
    if extra:
        cues.append(Cue(extra, "fact"))
    if sound:
        cues.append(Cue(f"The {word} {verb_for(cat_key)} {sound}!", "sound"))
    return Seg("card", dict(code=code, word=word, ring=ring, sound=sound), cues, chapter=chapter, codes=[code])


def card_seg_short(cat_key, item, ring):
    """Shorts: word + sentence (+ sound), no long fun fact."""
    word, code, extra, sound = item
    cues = [Cue(Cap(word) + "!", "reveal", cap=""), Cue(sentence(cat_key, word), "say")]
    if sound:
        cues.append(Cue(f"The {word} {verb_for(cat_key)} {sound}!", "sound"))
    elif extra:
        cues.append(Cue(extra, "fact"))
    return Seg("card", dict(code=code, word=word, ring=ring, sound=sound), cues, codes=[code])


def review_seg(entries, chapter="Let's say them together"):
    """entries: [(label, ref, spoken)]"""
    cues = [Cue("Let's say them together!", "say")]
    for k, (label, ref, spoken) in enumerate(entries):
        cues.append(Cue(spoken, "item", i=k, cap="", gap=0.20, min_beats=2))
    return Seg("review", dict(items=[(l, r) for l, r, _ in entries]), cues, chapter=chapter,
               codes=[r for _, r, _ in entries if is_code(r)])


def quiz_seg(q, options, answer, ans_text, rng, show=None, chapter=None):
    order = list(range(len(options)))
    rng.shuffle(order)
    opts = [options[i] for i in order]
    a = order.index(answer)
    cues = [Cue(q, "q"), Cue("", "think", min_beats=3), Cue(ans_text, "answer")]
    refs = [r for _, r in opts if is_code(r)] + ([show["code"]] if show else [])
    return Seg("quiz", dict(options=opts, answer=a, show=show), cues, chapter=chapter, codes=refs)


def quiz_ident(cat_key, items, rng, chapter=None):
    it = rng.choice(items)
    others = rng.sample([x for x in items if x[0] != it[0]], 2)
    q, a = ident_q(cat_key, it[0])
    return quiz_seg(q, [(w, c) for w, c, *_ in [it] + others], 0, a, rng, chapter=chapter)


def quiz_sound(cat_key, items, rng, chapter=None):
    snd = [x for x in items if x[3]]
    it = rng.choice(snd)
    others = rng.sample([x for x in items if x[0] != it[0]], 2)
    verb = verb_for(cat_key)
    q = f"Who {verb} {it[3]}?" if verb == "says" else f"Which one {verb} {it[3]}?"
    return quiz_seg(q, [(w, c) for w, c, *_ in [it] + others], 0, f"Yes! The {it[0]} {verb} {it[3]}!", rng,
                    chapter=chapter)


def quiz_color(rng, chapter=None, color=None):
    names = list(V.COLORS)
    cn = color or rng.choice(names)
    right = rng.choice(V.COLORS[cn][1])
    others = []
    for o in rng.sample([n for n in names if n != cn], 2):
        others.append(rng.choice(V.COLORS[o][1]))
    word = right[0]
    return quiz_seg(f"Which one is {cn}?", [right, others[0], others[1]], 0,
                    f"Yes! The {word} {V.be(word)} {cn}!", rng, chapter=chapter)


def quiz_count(rng, chapter=None, nmax=8):
    code, name = rng.choice(V.COUNT_OBJECTS)
    n = rng.randint(2, nmax)
    pool = [x for x in range(1, 11) if x != n]
    wrong = rng.sample(pool, 2)
    opts = [(str(n), f"n:{n}"), (str(wrong[0]), f"n:{wrong[0]}"), (str(wrong[1]), f"n:{wrong[1]}")]
    return quiz_seg(f"How many {name} can you see?", opts, 0, f"Yes! {Cap(V.NUMBER_WORDS[n])} {name}!", rng,
                    show=dict(code=code, n=n), chapter=chapter)


def quiz_letter(rng, chapter=None, letters=None):
    ls = list(letters or V.LETTERS)
    L = rng.choice(ls)
    spoken, _, word, code = V.LETTERS[L]
    others = rng.sample([x for x in V.LETTERS if x != L and V.LETTERS[x][2] != word], 2)
    opts = [(word, code)] + [(V.LETTERS[o][2], V.LETTERS[o][3]) for o in others]
    return quiz_seg(f"Which one starts with the letter {L}?", opts, 0,
                    f"Yes! {Cap(word)} starts with {spoken}!", rng, chapter=chapter)


def quiz_shape(rng, chapter=None, shapes=None):
    names = list(shapes or V.SHAPES)
    s = rng.choice(names)
    others = rng.sample([x for x in V.SHAPES if x != s], 2)
    opts = [(n, "S:" + n) for n in [s] + others]
    return quiz_seg(f"Which one is {V.art(s)}?", opts, 0, f"Yes! This is {V.art(s)}!", rng, chapter=chapter)


def count_seg(n, obj):
    code, name = obj
    cues = [Cue(Cap(V.NUMBER_WORDS[i]) + "!", "count", i=i, cap="", gap=0.12, min_beats=1) for i in range(1, n + 1)]
    cues.append(Cue(f"{Cap(V.NUMBER_WORDS[n])} {name}!", "total", min_beats=2))
    return Seg("count", dict(n=n, code=code, name=name), cues, codes=[code])


def number_seg(n, obj):
    code, name = obj
    w = V.NUMBER_WORDS[n]
    nm = SINGULAR.get(name, name) if n == 1 else name
    cues = [Cue(Cap(w) + "!", "reveal", cap=""), Cue(f"{Cap(w)} {nm}.", "say")]
    return Seg("number", dict(n=n, code=code, name=nm), cues, codes=[code])


def color_seg(name, rng, chapter=None):
    hexc, items = V.COLORS[name]
    cues = [Cue(Cap(name) + "!", "reveal", cap="")]
    for k, (w, code) in enumerate(items):
        cues.append(Cue(f"{Cap(name)} {w}.", "item", i=k, gap=0.25, min_beats=2))
    return Seg("color", dict(name=name, hex=hexc, items=items), cues, chapter=chapter, codes=[c for _, c in items])


def letter_seg(L, chapter=None):
    spoken, phon, word, code = V.LETTERS[L]
    cues = [Cue(Cap(spoken) + "!", "letter", cap=""), Cue(Cap(word) + "!", "reveal", cap=""),
            Cue(f"{Cap(spoken)} is for {word}.", "say", cap=f"{L} is for {word}.")]
    return Seg("letter", dict(L=L, word=word, code=code), cues, chapter=chapter, codes=[code])


def shape_seg(name, chapter=None):
    hexc, l1, l2, ex = V.SHAPES[name]
    cues = [Cue(Cap(name) + "!", "reveal", cap=""), Cue(l1, "say"), Cue(l2, "say")]
    for k, (w, code) in enumerate(ex):
        cues.append(Cue(f"Look! {Cap(V.art(w))}.", "item", i=k, gap=0.25, min_beats=2))
    return Seg("shape", dict(name=name, hex=hexc, items=ex), cues, chapter=chapter, codes=[c for _, c in ex])


def pair_seg(pr, chapter=None):
    a, ca, b, cb, size = pr
    cues = [Cue(Cap(a) + "!", "a", cap=""), Cue(Cap(b) + "!", "b", cap=""),
            Cue(f"{Cap(a)} and {b} are opposites!", "say")]
    return Seg("pair", dict(a=a, ca=ca, b=b, cb=cb, size=size), cues, chapter=chapter, codes=[ca, cb])


def phrase_seg(item, chapter=None):
    text, code, expl = item
    cues = [Cue(expl, "say"), Cue(text, "phrase"), Cue("Now you say it!", "say"),
            Cue("", "think", cap="Your turn!", min_beats=3), Cue(text, "phrase")]
    return Seg("phrase", dict(text=text, code=code), cues, chapter=chapter, codes=[code])


# -------------------------------------------------------------------------------- lessons
def _lesson(id, fmt, title, topic, tags, seed, segs, items, blurb, theme=None, bpm=None):
    rng = random.Random(seed)
    return Lesson(id, fmt, title, topic, list(tags) + BASE_TAGS, theme or rng.choice(THEME_NAMES),
                  bpm or rng.choice([92, 96, 100, 104, 108]), seed, segs, items=items, blurb=blurb)


def _quiz_set(cat_key, items, rng, n):
    segs = []
    pool = list(items)
    rng.shuffle(pool)
    have_sound = [x for x in items if x[3]]
    for k in range(n):
        if k == 1 and len(have_sound) >= 2:
            segs.append(quiz_sound(cat_key, items, rng))
        else:
            sub = pool[k:k + 3] if len(pool) - k >= 3 else pool
            segs.append(quiz_ident(cat_key, sub if len(sub) >= 3 else items, rng))
    segs[0].chapter = "Quiz time"
    return segs


def cat_lesson(id, cat_key, items, seed, part=None, fmt="long"):
    rng = random.Random(seed)
    cat = V.CATS[cat_key]
    head = cat["title"] + (f" Part {part}" if part else "")
    words = [i[0] for i in items]
    ring0 = rng.randrange(len(RINGS))
    segs = [title_seg(head, "Learn with Bibi", [i[1] for i in items], rng, cat["topic"])]
    for k, it in enumerate(items):
        segs.append(card_seg(cat_key, it, RINGS[(ring0 + k) % len(RINGS)], chapter=f"Let's learn {cat['title']}" if k == 0 else None))
    segs.append(review_seg([(Cap(w), c, Cap(w) + "!") for w, c, *_ in items]))
    segs += _quiz_set(cat_key, items, rng, 3)
    segs += cta_segs(rng)
    title = mk_title(f"Learn {head} for Kids", words)
    blurb = f"Let's learn about {cat['topic']} with Bibi the bee! Kids will see each picture, hear the word and a simple sentence, and then play a fun quiz."
    return _lesson(id, fmt, title, cat["topic"], cat["tags"], seed, segs, [Cap(w) for w in words], blurb,
                   theme=_theme_for(cat_key, rng))


def _theme_for(cat_key, rng):
    return {"sea": "ocean", "space": "night", "weather": "park", "fruits": "sunset", "vegetables": "park",
            "toys": "candy", "food": "sunset", "farm": "park"}.get(cat_key) or rng.choice(THEME_NAMES)


def numbers_lesson(id, lo, hi, seed, fmt="long"):
    rng = random.Random(seed)
    objs = rng.sample(V.COUNT_OBJECTS, 3)
    topic = f"counting from {V.NUMBER_WORDS[lo]} to {V.NUMBER_WORDS[hi]}"
    segs = [title_seg(f"Numbers {lo} to {hi}", "Let's count!", [o[0] for o in objs], rng, topic)]
    first = count_seg(hi - lo + 1 if lo == 1 else hi, objs[0])
    first.chapter = "Let's count"
    segs.append(first)
    for n in range(lo, hi + 1):
        s = number_seg(n, objs[1 + n % 2])
        if n == lo:
            s.chapter = "Meet the numbers"
        segs.append(s)
    segs.append(review_seg([(str(n), f"n:{n}", Cap(V.NUMBER_WORDS[n]) + "!") for n in range(lo, hi + 1)],
                           chapter="Count together"))
    q = [quiz_count(rng, nmax=hi) for _ in range(3)]
    q[0].chapter = "Quiz time"
    segs += q
    segs += cta_segs(rng)
    title = f"Learn to Count {lo} to {hi} | Numbers for Kids | {BRAND}"
    blurb = f"Let's count from {lo} to {hi} with Bibi the bee! Kids count fun objects, see each number, and play a counting quiz."
    return _lesson(id, fmt, title, topic, ["counting", "numbers", f"count to {hi}", "math for kids"], seed, segs,
                   [str(n) for n in range(lo, hi + 1)], blurb)


def colors_lesson(id, names, seed, fmt="long"):
    rng = random.Random(seed)
    segs = [title_seg("Colors", "Learn with Bibi", [V.COLORS[n][1][0][1] for n in names], rng, "colors")]
    for k, n in enumerate(names):
        segs.append(color_seg(n, rng, chapter="Let's learn colors" if k == 0 else None))
    segs.append(review_seg([(Cap(n), V.COLORS[n][0], Cap(n) + "!") for n in names]))
    q = [quiz_color(rng, color=names[i % len(names)]) for i in range(5)]
    q[0].chapter = "Quiz time"
    segs += q
    segs += cta_segs(rng)
    cn = ", ".join(Cap(n) for n in names[:4]) + (" & More" if len(names) > 4 else "")
    title = f"Learn Colors for Kids | {cn} | {BRAND}"
    blurb = "Let's learn colors with Bibi the bee! Kids see each color on fun everyday things and play a color quiz."
    return _lesson(id, fmt, title, "colors", ["colors", "learn colors", "color names"], seed, segs,
                   [Cap(n) for n in names], blurb)


def letters_lesson(id, letters, seed, fmt="long"):
    rng = random.Random(seed)
    first, last = letters[0], letters[-1]
    segs = [title_seg(f"Letters {first} to {last}", "ABC with Bibi", [V.LETTERS[L][3] for L in letters], rng,
                      f"the letters {first} to {last}")]
    for k, L in enumerate(letters):
        segs.append(letter_seg(L, chapter="Let's learn the letters" if k == 0 else None))
    segs.append(review_seg([(f"{L}  {Cap(V.LETTERS[L][2])}", V.LETTERS[L][3],
                             f"{Cap(V.LETTERS[L][0])}. {Cap(V.LETTERS[L][2])}!") for L in letters]))
    q = [quiz_letter(rng, letters=letters) for _ in range(5)]
    q[0].chapter = "Quiz time"
    segs += q
    segs += cta_segs(rng)
    title = f"ABC Letters {first} to {last} | Learn the Alphabet for Kids | {BRAND}"
    blurb = f"Let's learn the alphabet with Bibi the bee! Today: letters {first} to {last}. Kids see each letter, hear its name and a word that starts with it."
    return _lesson(id, fmt, title, f"the letters {first} to {last}", ["alphabet", "abc", "letters", "phonics"], seed,
                   segs, [f"{L} is for {Cap(V.LETTERS[L][2])}" for L in letters], blurb)


def letters_game(id, seed, fmt="long", rounds=9):
    """Quiz-only ABC game."""
    rng = random.Random(seed)
    segs = [title_seg("ABC Quiz", "Find the letter", [V.LETTERS[L][3] for L in "ABCDE"], rng, "a fun ABC guessing game")]
    for k in range(rounds):
        segs.append(quiz_letter(rng, chapter="Let's play" if k == 0 else None))
    segs += cta_segs(rng)
    title = f"ABC Quiz for Kids | Which Letter Does It Start With | {BRAND}"
    blurb = "Let's play an ABC guessing game with Bibi the bee! Which picture starts with the letter?"
    return _lesson(id, fmt, title, "a fun ABC guessing game", ["alphabet", "abc quiz", "letters", "phonics"], seed, segs,
                   [], blurb)


def shapes_lesson(id, names, seed, fmt="long"):
    rng = random.Random(seed)
    segs = [title_seg("Shapes", "Learn with Bibi", [V.SHAPES[n][3][0][1] for n in names], rng, "shapes")]
    for k, n in enumerate(names):
        segs.append(shape_seg(n, chapter="Let's learn shapes" if k == 0 else None))
    segs.append(review_seg([(Cap(n), "S:" + n, Cap(n) + "!") for n in names]))
    q = [quiz_shape(rng, shapes=names) for _ in range(4)]
    q[0].chapter = "Quiz time"
    segs += q
    segs += cta_segs(rng)
    sn = ", ".join(Cap(n) for n in names[:4]) + (" & More" if len(names) > 4 else "")
    title = f"Learn Shapes for Kids | {sn} | {BRAND}"
    blurb = "Let's learn shapes with Bibi the bee! Kids see each shape, count its sides and find it in the real world."
    return _lesson(id, fmt, title, "shapes", ["shapes", "learn shapes", "shape names", "geometry for kids"], seed, segs,
                   [Cap(n) for n in names], blurb)


def opposites_lesson(id, pairs, seed, fmt="long"):
    rng = random.Random(seed)
    segs = [title_seg("Opposites", "Learn with Bibi", [p[1] for p in pairs], rng, "opposites")]
    for k, p in enumerate(pairs):
        segs.append(pair_seg(p, chapter="Let's learn opposites" if k == 0 else None))
    entries = []
    for p in pairs:
        entries += [(Cap(p[0]), p[1], Cap(p[0]) + "!"), (Cap(p[2]), p[3], Cap(p[2]) + "!")]
    segs.append(review_seg(entries[:8]))
    allitems = [(p[0], p[1], None, None) for p in pairs] + [(p[2], p[3], None, None) for p in pairs]
    for k in range(3):
        p = rng.choice(pairs)
        word, code = (p[0], p[1]) if rng.random() < 0.5 else (p[2], p[3])
        others = rng.sample([x for x in allitems if x[0] not in (p[0], p[2])], 2)
        segs.append(quiz_seg(f"Which one shows {word}?", [(word, code)] + [(w, c) for w, c, *_ in others], 0,
                             f"Yes! This is {word}!", rng, chapter="Quiz time" if k == 0 else None))
    segs += cta_segs(rng)
    words = [p[0] for p in pairs] + [p[2] for p in pairs]
    title = mk_title("Learn Opposites for Kids", words, n=4)
    blurb = "Let's learn opposites with Bibi the bee! Big and small, hot and cold, and more."
    return _lesson(id, fmt, title, "opposites", ["opposites", "learn opposites", "antonyms for kids"], seed, segs,
                   [f"{Cap(p[0])} and {p[2]}" for p in pairs], blurb)


def phrases_lesson(id, key, items, seed, fmt="long"):
    rng = random.Random(seed)
    ph = V.PHRASES[key]
    segs = [title_seg(ph["title"], "Speak with Bibi", [i[1] for i in items], rng, ph["topic"])]
    for k, it in enumerate(items):
        segs.append(phrase_seg(it, chapter="Let's practice speaking" if k == 0 else None))
    segs.append(review_seg([(i[0].rstrip("!."), i[1], i[0]) for i in items][:8], chapter="Say them all"))
    segs += cta_segs(rng)
    title = f"{ph['title']} | English Speaking for Kids | {BRAND}"
    blurb = f"Let's practice speaking English with Bibi the bee! Today: {ph['topic']}. Kids listen, then say each sentence out loud."
    return _lesson(id, fmt, title, ph["topic"], ph["tags"], seed, segs, [i[0] for i in items], blurb)


def game_lesson(id, seed, fmt="long", rounds=10):
    """A pure quiz game (animals, food, colors, counting, letters, shapes mixed)."""
    rng = random.Random(seed)
    segs = [title_seg("Quiz Time", "Can you guess?", [V.CATS["farm"]["items"][0][1], V.CATS["wild"]["items"][0][1],
                                                        V.CATS["fruits"]["items"][0][1]], rng, "a super fun guessing game")]
    kinds = ["sound", "ident", "color", "count", "letter", "shape", "ident", "sound", "color", "count"]
    rng.shuffle(kinds)
    for k in range(rounds):
        kind = kinds[k % len(kinds)]
        ch = "Let's play" if k == 0 else None
        if kind == "sound":
            cat = rng.choice(["farm", "wild"])
            segs.append(quiz_sound(cat, V.CATS[cat]["items"], rng, chapter=ch))
        elif kind == "ident":
            cat = rng.choice(["fruits", "vegetables", "farm", "wild", "sea", "food", "vehicles", "toys"])
            segs.append(quiz_ident(cat, V.CATS[cat]["items"], rng, chapter=ch))
        elif kind == "color":
            segs.append(quiz_color(rng, chapter=ch))
        elif kind == "count":
            segs.append(quiz_count(rng, chapter=ch))
        elif kind == "letter":
            segs.append(quiz_letter(rng, chapter=ch))
        else:
            segs.append(quiz_shape(rng, chapter=ch))
    segs += cta_segs(rng)
    title = f"Quiz Game for Kids | Animals, Colors, Numbers & More | {BRAND}"
    blurb = "Let's play a guessing game with Bibi the bee! Animal sounds, colors, counting, letters and shapes."
    return _lesson(id, fmt, title, "a super fun guessing game", ["quiz for kids", "guessing game", "kids quiz",
                   "animal sounds", "learn colors", "counting"], seed, segs, [], blurb)


# --------------------------------------------------------------------------------- shorts
# Every Short also ends with a few seconds of the Like / Subscribe card (see CTA_LINE above): the buttons are baked into the picture
# because YouTube has no subscribe watermark for videos made for kids. Draws no random numbers.
SHORT_CTA_LINE = "Like and subscribe for more!"


def _short(id, title_head, topic, tags, seed, segs, items, blurb, theme=None):
    segs = list(segs) + [Seg("cta", {}, [Cue(SHORT_CTA_LINE, "outro", min_beats=8)])]
    title = f"{title_head} | {BRAND} #Shorts"
    if len(title) > 98:
        title = f"{title_head} #Shorts"
    les = _lesson(id, "short", title, topic, list(tags) + ["shorts"], seed, segs, items, blurb, theme=theme,
                  bpm=random.Random(seed).choice([100, 104, 108, 112]))
    return les


def short_trio(id, cat_key, items3, seed):
    rng = random.Random(seed)
    cat = V.CATS[cat_key]
    ring0 = rng.randrange(len(RINGS))
    segs = [card_seg_short(cat_key, it, RINGS[(ring0 + k) % len(RINGS)]) for k, it in enumerate(items3)]
    segs.append(quiz_sound(cat_key, items3, rng) if sum(1 for x in items3 if x[3]) >= 1 and cat_key in ("farm", "wild", "birds", "insects", "vehicles")
                else quiz_ident(cat_key, items3, rng))
    words = [i[0] for i in items3]
    head = f"{cat['title']} for Kids: {', '.join(Cap(w) for w in words)}"
    blurb = f"Learn {cat['topic']} with Bibi the bee in under a minute!"
    return _short(id, head, cat["topic"], cat["tags"], seed, segs, [Cap(w) for w in words], blurb,
                  theme=_theme_for(cat_key, rng))


def short_count(id, n, obj, seed):
    rng = random.Random(seed)
    segs = [count_seg(n, obj), quiz_count(rng, nmax=max(3, n))]
    head = f"Count to {n} with {Cap(obj[1])}"
    return _short(id, head, f"counting to {V.NUMBER_WORDS[n]}", ["counting", "numbers", "math for kids"], seed, segs,
                  [str(i) for i in range(1, n + 1)], f"Count from 1 to {n} with Bibi the bee!")


def short_color(id, name, seed):
    rng = random.Random(seed)
    segs = [color_seg(name, rng), quiz_color(rng, color=name)]
    head = f"Learn the Color {Cap(name)} for Kids"
    return _short(id, head, f"the color {name}", ["colors", "learn colors", name], seed, segs, [Cap(name)],
                  f"Learn the color {name} with Bibi the bee!")


def short_quiz(id, seed, n=3):
    rng = random.Random(seed)
    segs = []
    kinds = ["sound", "ident", "color", "count", "letter", "shape"]
    rng.shuffle(kinds)
    for kind in kinds[:n]:
        if kind == "sound":
            cat = rng.choice(["farm", "wild"])
            segs.append(quiz_sound(cat, V.CATS[cat]["items"], rng))
        elif kind == "ident":
            cat = rng.choice(["fruits", "vegetables", "sea", "food", "vehicles", "toys"])
            segs.append(quiz_ident(cat, V.CATS[cat]["items"], rng))
        elif kind == "color":
            segs.append(quiz_color(rng))
        elif kind == "count":
            segs.append(quiz_count(rng))
        elif kind == "letter":
            segs.append(quiz_letter(rng))
        else:
            segs.append(quiz_shape(rng))
    names = {"sound": "Animal Sounds", "ident": "Pictures", "color": "Colors", "count": "Counting", "letter": "Letters",
             "shape": "Shapes"}
    head = "Quick Quiz for Kids: " + ", ".join(names[k] for k in kinds[:n])
    return _short(id, head, "a quick guessing game",
                  ["quiz for kids", "guessing game", "kids quiz"], seed, segs, [], "A quick guessing game with Bibi the bee!")


def short_letter(id, L, seed):
    rng = random.Random(seed)
    segs = [letter_seg(L), quiz_letter(rng, letters=[L])]
    spoken, _, word, _ = V.LETTERS[L]
    return _short(id, f"Letter {L} for Kids: {L} is for {Cap(word)}", f"the letter {L}", ["alphabet", "abc", f"letter {L}"],
                  seed, segs, [f"{L} is for {Cap(word)}"], f"Learn the letter {L} with Bibi the bee!")


def short_shape(id, name, seed):
    rng = random.Random(seed)
    segs = [shape_seg(name), quiz_shape(rng)]
    return _short(id, f"Learn the {Cap(name)} Shape for Kids", f"the {name} shape", ["shapes", "learn shapes", name], seed,
                  segs, [Cap(name)], f"Learn the {name} shape with Bibi the bee!")


def short_phrase(id, key, item, seed):
    ph = V.PHRASES[key]
    segs = [phrase_seg(item)]
    return _short(id, f"Say It: {item[0]} | English for Kids", ph["topic"], ph["tags"], seed, segs, [item[0]],
                  f"Practice speaking English with Bibi the bee! Today: {item[0]}")


def short_opposites(id, pair, seed):
    rng = random.Random(seed)
    segs = [pair_seg(pair)]
    a, ca, b, cb, _ = pair
    return _short(id, f"Opposites for Kids: {Cap(a)} and {Cap(b)}", "opposites", ["opposites", "learn opposites"], seed,
                  segs, [f"{Cap(a)} and {b}"], f"Learn the opposites {a} and {b} with Bibi the bee!")
