"""The songs of the song videos (song.py): nursery rhymes and little songs, every one in English and in Turkish.

A song is written like sheet music, a spec (dict) with the notes, the chords and the words of every line (see song.py for the format),
plus a recipe that dresses its sections with pictures: backdrops, the four friends dancing and singing, the big star, confetti.

  build("twinkle", "en") -> a Song (it renders like a tale: story.render / story.make_cover)
"""
from .song import Song

FAMILY = ("bibi", "pip", "mo", "lila")
ALL4 = ("bibi", "pip", "mo", "lila")


# ================================================================================================ helpers for the recipes
def _friends(sc, xs=(235, 500, 785, 1050), y=556, k=1.6, dy=(-6, 4, 4, -6)):
    """The four friends in a row (the lyrics sit below them at y = 640: their feet stay above y = 560)."""
    for w, x, d in zip(FAMILY, xs, dy):
        sc.actor(w, w, x, y + d, k)


def _star(s, sec, x=640, y=172, r=100, words=None, every=None, tint="#FFD21F"):
    """The big star with a face: it swells on the key words of the lines, or every `every` beats."""
    pulses = []
    if words:
        for it in sec["items"]:
            pulses += [a for w, a, b in s.word_spans(sec, it) if w in words]
    if every:
        pulses += s.beat_times(sec, every)
    return ("fx", "star_face", x, y, {"at": 0.0, "dur": sec["dur"], "r": r, "pulses": sorted(pulses), "tint": tint, "sfx": False})


def _fx(kind, x, y, at, dur, **kw):
    return ("fx", kind, x, y, dict(kw, at=at, dur=dur, sfx=False))


def _bar_pumps(s, sec, bars=2.0, amount=0.045):
    """A little 'pump' of the camera on the first beat of every `bars` bars (dancing sections)."""
    out = []
    for t in s.beat_times(sec, step=bars * s.nbeats):
        if t + 0.8 < sec["dur"] - 0.2:
            out.append(("cam", 640, 360, 1.0 + amount, {"at": t, "dur": 0.2}))
            out.append(("cam", 640, 360, 1.0, {"at": t + 0.2, "dur": 0.5}))
    return out


# ================================================================================================ Twinkle, twinkle, little star
_A = dict(notes="C4 C4 G4 G4 A4 A4 G4:2", tr_notes="C4 C4 G4 G4 A4 A4 G4 G4", chords="C:4 F:2 C:2")
_B = dict(notes="F4 F4 E4 E4 D4 D4 C4:2", tr_notes="F4 F4 E4 E4 D4 D4 C4 C4", chords="F:2 C:2 G:2 C:2")
_C = dict(notes="G4 G4 F4 F4 E4 E4 D4:2", tr_notes="G4 G4 F4 F4 E4 E4 D4 D4", chords="C:2 F:2 C:2 G:2")

_SING = dict(lead="xylo", lead_gain=0.20, chords="strum", chord_gain=1.0, bass_gain=0.7, drums="light")
_SOFT = dict(lead="box", lead_gain=0.22, chords="lull", chord_gain=1.0, bass_gain=0.8, drums="none")
_TOGETHER = dict(lead="flute", lead_gain=0.22, chords="strum", chord_gain=1.05, bass_gain=0.8, drums="clap", drum_gain=0.9)
_DANCE = dict(lead="xylo", lead_gain=0.45, chords="oompah", chord_gain=1.1, bass_gain=0.9, drums="party", drum_gain=1.0)

TWINKLE = dict(
    id="twinkle",
    title={"en": "Twinkle Twinkle Little Star | Kids Song & Nursery Rhyme | Bibi Buzz TV", "tr": "Parla Parla Küçük Yıldız | Çocuk Şarkısı | Bibi Buzz TV"},
    blurb={
        "en": "Sing along with Bibi, Pip, Mo and Lila! Twinkle Twinkle Little Star, the lullaby every child knows, with the words "
              "lighting up as we sing. A cheerful nursery rhyme for babies, toddlers and preschoolers.",
        "tr": "Bibi, Pip, Mo ve Lila ile birlikte söyleyelim! Parla Parla Küçük Yıldız: sözleri şarkı söylenirken ekranda yanan, "
              "neşeli bir çocuk şarkısı. Bebekler, küçük çocuklar ve okul öncesi minikler için.",
    },
    tags={
        "en": ["twinkle twinkle little star", "nursery rhymes", "kids songs", "sing along", "lullaby", "songs for kids", "baby songs",
               "toddler songs", "children songs", "Bibi Buzz TV"],
        "tr": ["parla parla küçük yıldız", "çocuk şarkıları", "bebek şarkıları", "ninni", "çocuk şarkısı", "birlikte söyleyelim",
               "okul öncesi şarkılar", "Bibi Buzz TV", "türkçe çocuk şarkıları"],
    },
    bpm=100, beats=4, shift={"en": -2, "tr": -5},
    lines={
        "A": dict(en="Twin-kle twin-kle lit-tle star", tr="Par-la par-la kü-çük yıl-dız", **_A),
        "B": dict(en="How I won-der what you are", tr="Ge-ce-yi ay-dın-lat bi-raz", **_B),
        "C": dict(en="Up a-bove the world so high", tr="Yük-sek-te-ki gök-yü-zün-de", **_C),
        "D": dict(en="Like a dia-mond in the sky", tr="El-mas gi-bi ı-şıl ı-şıl", **_C),
        "A2": dict(en="When the blaz-ing sun is gone", tr="Gün ba-tın-ca gök ka-ra-rır", **_A),
        "B2": dict(en="When he no-thing shines up-on", tr="Sen par-lar-sın göz kır-pa-rak", **_B),
        "C2": dict(en="Then you show your lit-tle light", tr="Her ge-ce se-ni gö-rü-rüm", **_C),
        "D2": dict(en="Twin-kle twin-kle all the night", tr="Ben de sa-na gü-lü-yo-rum", **_C),
    },
    form=[
        dict(name="Intro", mode="inst", lines=["A"], style=dict(lead="glock", lead_gain=0.5, chords="lull", chord_gain=1.0, drums="none")),
        dict(name="Verse 1a", lines=["A", "B"], style=_SING),
        dict(name="Verse 1b", lines=["C", "D"], style=_SING),
        dict(name="Verse 1c", lines=["A", "B"], style=_SING),
        dict(name="Dance a", mode="inst", lines=["C", "D"], style=_DANCE),
        dict(name="Dance b", mode="inst", lines=["A", "B"], style=_DANCE),
        dict(name="Verse 2a", lines=["A2", "B2"], style=_SOFT),
        dict(name="Verse 2b", lines=["C2", "D2"], style=_SOFT),
        dict(name="Verse 2c", lines=["A", "B"], style=_SOFT),
        dict(name="Verse 3a", lines=["A", "B"], style=_TOGETHER),
        dict(name="Verse 3b", lines=["C", "D"], style=_TOGETHER),
        dict(name="Verse 3c", lines=["A", "B"], style=_TOGETHER),
        dict(name="Outro", mode="inst", lines=["B"], post=4, style=dict(lead="glock", lead_gain=0.5, chords="pad", chord_gain=1.0, drums="none")),
    ],
    cover={
        "en": dict(bg="garden_night", title=("TWINKLE TWINKLE", "LITTLE STAR"), size=104, gap=106, sub="Sing along with Bibi Buzz TV",
                   actors=[("bibi", "bibi", 175, 706, 1.7, 1, "idle", {}), ("pip", "pip", 405, 712, 1.55, 1, "idle", {}),
                           ("mo", "mo", 905, 712, 1.55, -1, "idle", {}), ("lila", "lila", 1110, 706, 1.7, -1, "idle", {})],
                   fx=[("star_face", 640, 478, {"r": 128})]),
        "tr": dict(bg="garden_night", title=("PARLA PARLA", "KÜÇÜK YILDIZ"), size=108, gap=108, sub="Bibi Buzz TV ile şarkı söyle",
                   actors=[("bibi", "bibi", 175, 706, 1.7, 1, "idle", {}), ("pip", "pip", 405, 712, 1.55, 1, "idle", {}),
                           ("mo", "mo", 905, 712, 1.55, -1, "idle", {}), ("lila", "lila", 1110, 706, 1.7, -1, "idle", {})],
                   fx=[("star_face", 640, 478, {"r": 128})]),
    },
)

STAR_WORDS = {
    "en": {"twinkle", "star", "diamond", "sky", "light", "night", "high", "sun"},
    "tr": {"parla", "yıldız", "elmas", "ışıl", "gökyüzünde", "parlarsın", "gece", "güneş"},
}


def _twinkle(s):
    """The pictures of 'Twinkle, twinkle, little star', one scene for every section of the form."""
    sw = STAR_WORDS[s.lang]
    S = s.sections
    en = s.lang == "en"

    # ---- intro: the title card, two little stars at its sides, the friends hopping
    sc = s.scene_for(0, "garden_night", mood="title", drift=0.0, clouds=False)
    sc.actor("bibi", "bibi", 250, 612, 1.2).actor("pip", "pip", 510, 620, 1.1).actor("mo", "mo", 780, 620, 1.1).actor("lila", "lila", 1040, 612, 1.2)
    sec = S[0]
    title = ("TWINKLE TWINKLE", "LITTLE STAR") if en else ("PARLA PARLA", "KÜÇÜK YILDIZ")
    sub = "Sing along with Bibi Buzz TV" if en else "Bibi Buzz TV ile şarkı söyle"
    s.finish_scene(sc, dancers=ALL4, hop=1.0, hop_mode="wave", extra=[
        ("fx", "title", 0, 0, {"at": 0.0, "dur": sec["dur"], "lines": title, "sub": sub, "top": 84, "size": 108, "gap": 112, "pill": 38, "sfx": False}),
        ("fx", "star_face", 84, 74, {"at": 0.2, "dur": sec["dur"], "r": 42, "pulses": s.beat_times(sec, 2.0, 0.0), "sfx": False}),
        ("fx", "star_face", 1196, 74, {"at": 0.35, "dur": sec["dur"], "r": 42, "pulses": s.beat_times(sec, 2.0, 1.0), "sfx": False}),
        _fx("sparkle", 640, 440, 0.4, sec["dur"], r=330),
        _fx("notes", 120, 560, 0.0, sec["dur"]), _fx("notes", 1130, 560, 0.7, sec["dur"]),
        ("sfx", "sparkle", {"at": 0.3}), ("sfx", "tada", {"at": 0.0})])

    # ---- verse 1: the garden at night, the castle, a golden evening
    sc = s.scene_for(1, "garden_night", drift=0.04)
    _friends(sc)
    s.finish_scene(sc, singers=("bibi", "pip"), dancers=ALL4, hop=1.0, hop_mode="wave", cam=(640, 340, 1.1), extra=[
        _star(s, S[1], 640, 172, 100, words=sw), _fx("notes", 130, 520, 0.0, S[1]["dur"]), _fx("notes", 1150, 520, 1.0, S[1]["dur"])])

    sc = s.scene_for(2, "castle_night", drift=0.0)
    _friends(sc, xs=(190, 450, 830, 1090))
    s.finish_scene(sc, singers=("mo", "lila"), dancers=ALL4, hop=1.0, hop_mode="wave", cam=(640, 330, 1.08), extra=[
        _star(s, S[2], 640, 190, 112, words=sw), _fx("sparkle", 640, 200, 0.0, S[2]["dur"], r=260)])

    sc = s.scene_for(3, "meadow_dusk", drift=0.04)
    _friends(sc)
    s.finish_scene(sc, singers=(("bibi", "pip"), ("mo", "lila")), dancers=ALL4, hop=2.0, hop_mode="all", side=34, cam=(640, 350, 1.1), extra=[
        _star(s, S[3], 940, 160, 92, words=sw), _fx("hearts", 360, 330, 0.5, S[3]["dur"])])

    # ---- the dance: everybody hops, the camera pumps, the star beats like a heart
    sc = s.scene_for(4, "ballroom", drift=0.0, clouds=False)
    _friends(sc, y=562, k=1.65)
    s.finish_scene(sc, dancers=ALL4, hop=1.0, hop_mode="all", side=40, extra=_bar_pumps(s, S[4]) + [
        _star(s, S[4], 640, 175, 96, every=2.0), _fx("confetti", 0, 0, 0.0, S[4]["dur"]), ("sfx", "cheer", {"at": 0.0})])

    sc = s.scene_for(5, "meadow_open", drift=0.0)
    _friends(sc, xs=(290, 530, 750, 990), y=562, k=1.65)
    s.finish_scene(sc, dancers=ALL4, hop=1.0, hop_mode="wave", side=50, extra=_bar_pumps(s, S[5]) + [
        _star(s, S[5], 640, 160, 96, every=2.0), _fx("sparkle", 640, 300, 0.0, S[5]["dur"], r=420),
        _fx("notes", 110, 540, 0.0, S[5]["dur"]), _fx("notes", 1160, 540, 0.9, S[5]["dur"])])

    # ---- verse 2: a softer verse in the bedroom, the castle and the garden
    sc = s.scene_for(6, "sunset", drift=0.04)
    _friends(sc)
    s.finish_scene(sc, singers=("pip", "bibi"), dancers=ALL4, hop=2.0, hop_mode="wave", cam=(640, 340, 1.08), extra=[
        _star(s, S[6], 640, 176, 96, words=sw, tint="#FFE88A")])

    sc = s.scene_for(7, "forest_dusk", drift=0.0)
    _friends(sc, xs=(190, 450, 830, 1090))
    s.finish_scene(sc, singers=("lila", "mo"), dancers=ALL4, hop=2.0, hop_mode="wave", cam=(640, 330, 1.08), extra=[
        _star(s, S[7], 640, 190, 110, words=sw), _fx("sparkle", 640, 220, 0.0, S[7]["dur"], r=300)])

    sc = s.scene_for(8, "garden_night", drift=0.04)
    _friends(sc, xs=(330, 560, 720, 950))
    s.finish_scene(sc, singers=(("bibi", "lila"), ("pip", "mo")), dancers=ALL4, hop=2.0, hop_mode="all", cam=(640, 345, 1.1), extra=[
        _star(s, S[8], 640, 172, 100, words=sw), _fx("hearts", 220, 330, 0.5, S[8]["dur"]), _fx("hearts", 1060, 330, 1.2, S[8]["dur"])])

    # ---- verse 3: everybody sings together, brighter and bouncier
    sc = s.scene_for(9, "ballroom_day", drift=0.0, clouds=False)
    _friends(sc, y=556, k=1.65)
    s.finish_scene(sc, singers=(ALL4,), dancers=ALL4, hop=1.0, hop_mode="all", side=30, cam=(640, 335, 1.1), extra=[
        _star(s, S[9], 640, 180, 108, words=sw), _fx("sparkle", 640, 300, 0.0, S[9]["dur"], r=420)])

    sc = s.scene_for(10, "river", drift=0.0)
    _friends(sc, xs=(205, 480, 805, 1075), y=556, k=1.65)
    s.finish_scene(sc, singers=(ALL4,), dancers=ALL4, hop=1.0, hop_mode="wave", side=40, cam=(640, 345, 1.08), extra=[
        _star(s, S[10], 640, 165, 100, words=sw), _fx("notes", 120, 520, 0.0, S[10]["dur"]), _fx("notes", 1150, 520, 0.8, S[10]["dur"])])

    sc = s.scene_for(11, "meadow_dawn", drift=0.0)
    _friends(sc, y=556, k=1.65)
    s.finish_scene(sc, singers=(ALL4,), dancers=ALL4, hop=1.0, hop_mode="all", side=40, extra=_bar_pumps(s, S[11], amount=0.035) + [
        _star(s, S[11], 640, 160, 104, words=sw), _fx("confetti", 0, 0, 0.0, S[11]["dur"]), ("sfx", "cheer", {"at": 0.0})])

    # ---- outro: thank you, like and subscribe
    sc = s.scene_for(12, "meadow_open", drift=0.0)
    sc.actor("bibi", "bibi", 230, 606, 1.15).actor("pip", "pip", 520, 612, 1.05).actor("mo", "mo", 800, 614, 1.05).actor("lila", "lila", 1060, 606, 1.15)
    sec = S[12]
    like, sub_t = 1.7, 3.0
    caption = "Like and subscribe for more songs!" if en else "Daha fazla şarkı için beğen ve abone ol!"
    s.finish_scene(sc, dancers=ALL4, hop=2.0, hop_mode="all", extra=[
        _fx("confetti", 0, 0, sub_t, sec["dur"]), ("fx", "cta", 640, 215, {"at": 0.0, "dur": sec["dur"], "like": like, "sub": sub_t, "sfx": False}),
        _fx("caption", 0, 0, 0.3, sec["dur"], text=caption), _fx("hearts", 300, 380, 1.0, sec["dur"]), _fx("hearts", 980, 380, 1.4, sec["dur"]),
        ("sfx", "pop", {"at": 0.05}), ("sfx", "pop", {"at": 0.3}), ("sfx", "ding", {"at": like + 0.05}), ("sfx", "pop", {"at": like}),
        ("sfx", "ding", {"at": sub_t + 0.05}), ("sfx", "pop", {"at": sub_t}), ("sfx", "sparkle", {"at": sub_t + 0.1})])


# ================================================================================================ the shelf
SPECS = {"twinkle": TWINKLE}
RECIPES = {"twinkle": _twinkle}
QUEUE = ["twinkle"]                      # the order in which the songs come out (one a day: curriculum.py)


def build(key, lang="en"):
    """The song `key` in `lang` as a Song (voice, band and pictures are made from its spec)."""
    s = Song(SPECS[key], lang)
    RECIPES[key](s)
    return s
