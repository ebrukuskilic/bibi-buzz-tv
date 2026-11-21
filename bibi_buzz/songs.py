"""The songs of the song videos (song.py): nursery rhymes and little songs, every one in English and in Turkish.

A song is written like sheet music, a spec (dict) with the notes, the chords and the words of every line (see song.py for the format),
plus a recipe that dresses its sections with pictures: backdrops, the four friends dancing and singing, the big star, confetti.

  build("twinkle", "en") -> a Song (it renders like a tale: story.render / story.make_cover)
"""
from . import songart  # noqa: F401  (registers the farm backdrops in storyart2.BACKDROPS)
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


# ================================================================================================ Old MacDonald had a farm / Dedenin Çiftliği
# C major, 4/4, the traditional tune.  A verse is 'And on his farm he had a cow, E-I-E-I-O' (the animal pops in), its sound ('With a moo moo here,
# and a moo moo there ...') and 'Old MacDonald had a farm, E-I-E-I-O' again (the animals that have come so far dance together).
# The 'O' of E-I-E-I-O lasts 3 beats where 'And ...' follows (it starts with a one-beat pickup: such a section has grid = 1, its first bar line is
# one beat later) and 4 beats where the next line starts on the downbeat.  All the animal lines are made in a loop below.
_OM = dict(notes="C4 C4 C4 G3 A3 A3 G3:2", chords="C:4 F:2 C:2")
_R3 = dict(notes="E4 E4 D4 D4 C4:3", chords="C:2 G:2 C:3")
_R4 = dict(notes="E4 E4 D4 D4 C4:4", chords="C:2 G:2 C:4")
_AN = dict(notes="G3 C4 C4 C4 G3 A3 A3 G3:2", chords="G:1 C:4 F:2 C:2")
_MO = dict(notes="G3:0.5 G3:0.5 C4 C4 C4", chords="C:4")
_MH = dict(notes="C4:0.5 C4:0.5 C4", chords="C:2")
_MF = dict(notes="C4:0.5 C4:0.5 C4", chords="F:2")
_ME = dict(notes="C4:0.5 C4:0.5 C4:0.5 C4:0.5 C4 C4", tr_notes="C4:0.5 C4:0.5 C4 C4 C4", chords="F:2 C:2")

_FARM_SING = dict(lead="xylo", lead_gain=0.20, chords="oompah", chord_gain=1.1, bass_gain=0.9, drums="clap", drum_gain=0.8)
_FARM_SOUNDS = dict(lead="flute", lead_gain=0.20, chords="oompah", chord_gain=1.15, bass_gain=1.0, drums="party", drum_gain=0.9)
_FARM_FINAL = dict(lead="xylo", lead_gain=0.22, chords="oompah", chord_gain=1.15, bass_gain=1.0, drums="party", drum_gain=1.0)
_FARM_INTRO = dict(lead="xylo", lead_gain=0.45, chords="oompah", chord_gain=1.1, bass_gain=0.9, drums="party", drum_gain=0.9)
_FARM_OUTRO = dict(lead="xylo", lead_gain=0.5, chords="oompah", chord_gain=1.1, bass_gain=0.9, drums="clap", drum_gain=0.9)

# the animals in the order they come: the look of the actor, the colour of the big sound word, and the words of both languages
# (name = the animal, art = 'a' / 'an' before the sound, snd = the sound that is sung, big = the sound written big on the screen)
ANIMALS = [
    dict(key="cow", kind="cow", look=dict(accent="#33343C"), color="#3E8EDE",
         en=dict(name="cow", art="a", snd="moo", big="MOO!"), tr=dict(name="i-nek", snd="möö", big="MÖÖ!")),
    dict(key="pig", kind="pig", look={}, color="#FF6FA5",
         en=dict(name="pig", art="an", snd="oink", big="OINK!"), tr=dict(name="do-muz", snd="hort", big="HORT!")),
    dict(key="sheep", kind="sheep", look={}, color="#8E6BE0",
         en=dict(name="sheep", art="a", snd="baa", big="BAA!"), tr=dict(name="ko-yun", snd="mee", big="MEE!")),
    dict(key="dog", kind="dog", look={}, color="#F28C28",
         en=dict(name="dog", art="a", snd="woof", big="WOOF!"), tr=dict(name="kö-pek", snd="hav", big="HAV!")),
    dict(key="hen", kind="hen", look=dict(feathers="#E4573D"), color="#E5533D",
         en=dict(name="hen", art="a", snd="cluck", big="CLUCK!"), tr=dict(name="ta-vuk", snd="gıt", big="GIT!")),
]
FARMER = dict(gramps="#4E8FD8", hair="#EEEEF4", hat_kind="straw", hat_color="#E9B949")


def _om_lines():
    """The lines of the song: the ones that come back (OM, R3, R4) and, for every animal k, its six lines AN / M1 .. M5."""
    L = {
        "OM": dict(en="Old Mac-Don-ald=MacDonald had a farm", tr="De-de çift-lik-te ya-şar", **_OM),
        "R3": dict(en="E+I+E+I+O=ee_eye_ee_eye_oh", tr="İ+ya+i+ya+o=i_ya_i_ya_o", **_R3),
        "R4": dict(en="E+I+E+I+O=ee_eye_ee_eye_oh", tr="İ+ya+i+ya+o=i_ya_i_ya_o", **_R4),
    }
    for k, a in enumerate(ANIMALS):
        n, art, snd = a["en"]["name"], a["en"]["art"], a["en"]["snd"]
        tn, ts = a["tr"]["name"], a["tr"]["snd"]
        L["AN%d" % k] = dict(en="And on his farm he had a %s" % n, tr="Bu çift-lik-te bir %s var" % tn, **_AN)
        L["M1_%d" % k] = dict(en="With %s %s %s here" % (art, snd, snd), tr="Bu-ra-da %s %s" % (ts, ts), **_MO)
        L["M2_%d" % k] = dict(en="And %s %s %s there" % (art, snd, snd), tr="Şu-ra-da=Şu_ra_da %s %s" % (ts, ts), **_MO)
        L["M3_%d" % k] = dict(en="Here %s %s" % (art, snd), tr="Bur-da %s" % ts, **_MH)
        L["M4_%d" % k] = dict(en="There %s %s" % (art, snd), tr="Şur-da %s" % ts, **_MF)
        L["M5_%d" % k] = dict(en="Eve-ry-where=everywhere %s %s %s" % (art, snd, snd), tr="Her-yer-de %s %s" % (ts, ts), **_ME)
    return L


def _om_form():
    n = len(ANIMALS)
    form = [dict(name="Intro", mode="inst", lines=["OM"], style=_FARM_INTRO),
            dict(name="Farm", lines=["OM", "R3"], style=_FARM_SING)]
    for k in range(n):
        last = k == n - 1
        form += [dict(name="Animal %d" % (k + 1), lines=["AN%d" % k, "R4"], grid=1, style=_FARM_SING),
                 dict(name="Sounds %d" % (k + 1), lines=["M1_%d" % k, "M2_%d" % k, "M3_%d" % k, "M4_%d" % k, "M5_%d" % k], style=_FARM_SOUNDS),
                 dict(name="Chorus %d" % (k + 1), lines=["OM", "R4" if last else "R3"], style=_FARM_FINAL if last else _FARM_SING)]
    form.append(dict(name="Outro", mode="inst", lines=["R4"], post=4, style=_FARM_OUTRO))
    return form


def _om_cover(lang):
    en = lang == "en"
    return dict(bg="farm_open", title=("OLD MACDONALD", "HAD A FARM") if en else ("DEDENİN", "ÇİFTLİĞİ"), size=104 if en else 112, gap=106 if en else 114,
                sub="Sing along with Bibi Buzz TV" if en else "Bibi Buzz TV ile şarkı söyle",
                actors=[("bibi", "bibi", 130, 708, 1.55, 1, "idle", {}), ("pip", "pip", 330, 714, 1.4, 1, "idle", {}),
                        ("mo", "mo", 950, 714, 1.4, -1, "idle", {}), ("lila", "lila", 1150, 708, 1.55, -1, "idle", {}),
                        ("dog", "dog", 470, 700, 1.15, 1, "happy", {}), ("sheep", "sheep", 810, 700, 1.15, -1, "happy", {}),
                        ("cow", "cow", 640, 716, 1.85, 1, "happy", dict(accent="#33343C"))],
                fx=[])


OLDMAC = dict(
    id="oldmac",
    title={"en": "Old MacDonald Had a Farm | Kids Song & Animal Sounds | Bibi Buzz TV", "tr": "Dedenin Çiftliği | Hayvan Sesleri | Çocuk Şarkısı | Bibi Buzz TV"},
    blurb={
        "en": "Sing along with Bibi, Pip, Mo and Lila! Old MacDonald had a farm, E-I-E-I-O, and on that farm he had a cow, a pig, a sheep, a dog and a hen. "
              "Learn the farm animals and their sounds, with the words lighting up as we sing. A cheerful nursery rhyme for babies, toddlers and preschoolers.",
        "tr": "Bibi, Pip, Mo ve Lila ile birlikte söyleyelim! Dedenin çiftliğinde bir inek, bir domuz, bir koyun, bir köpek ve bir tavuk var. "
              "Çiftlik hayvanlarını ve seslerini öğreniyoruz; sözler şarkı söylenirken ekranda yanıyor. Bebekler, küçük çocuklar ve okul öncesi minikler için neşeli bir çocuk şarkısı.",
    },
    tags={
        "en": ["old macdonald had a farm", "old macdonald", "nursery rhymes", "kids songs", "animal sounds", "farm animals", "sing along", "songs for kids",
               "toddler songs", "baby songs", "children songs", "Bibi Buzz TV"],
        "tr": ["dedenin çiftliği", "ali baba'nın çiftliği", "old macdonald türkçe", "çocuk şarkıları", "hayvan sesleri", "çiftlik hayvanları",
               "bebek şarkıları", "çocuk şarkısı", "birlikte söyleyelim", "okul öncesi şarkılar", "türkçe çocuk şarkıları", "Bibi Buzz TV"],
    },
    bpm=104, beats=4, shift={"en": 3, "tr": -3},
    lines=_om_lines(),
    form=_om_form(),
    cover={"en": _om_cover("en"), "tr": _om_cover("tr")},
)

BACKS = ("farm_dawn", "farm", "farm_open", "farm", "farm_dusk")             # the sky of the five verses: morning, day, day, day, evening


def _oldmac(s):
    """The pictures of 'Old MacDonald': the title, Grandpa Mac pops in, and for every animal three scenes (it pops in / it makes its sound / the dance)."""
    S, lg, en, beat = s.sections, s.lang, s.lang == "en", s.beat
    ids = [a["key"] for a in ANIMALS]
    slot_x = {"cow": 130, "pig": 385, "sheep": 640, "dog": 895, "hen": 1150}      # where an animal stands behind the friends in the dances

    def animal(sc, a, x, y, k, face=1, show=True):
        sc.actor(a["key"], a["kind"], x, y, k, face=face, show=show, **a["look"])

    def sides(sc, k=1.35, y=566, xs=(150, 345, 935, 1130)):
        for w, x, f, d in zip(FAMILY, xs, (1, 1, -1, -1), (-6, 4, 4, -6)):
            sc.actor(w, w, x, y + d, k, face=f)

    # ---- intro: the title card on the farm; the five animals pop in one after the other
    sc = s.scene_for(0, "farm_open", mood="title", drift=0.0, clouds=False)
    for w, x, d in zip(FAMILY, (230, 510, 780, 1040), (-8, 2, 2, -8)):
        sc.actor(w, w, x, 612 + d, 1.2)
    xs0 = {"dog": 100, "cow": 370, "pig": 645, "sheep": 910, "hen": 1180}
    for a in ANIMALS:
        animal(sc, a, xs0[a["key"]], 556, 0.95, face=1 if xs0[a["key"]] < 640 else -1, show=False)
    sec = S[0]
    title = ("OLD MACDONALD", "HAD A FARM") if en else ("DEDENİN", "ÇİFTLİĞİ")
    sub = "Sing along with Bibi Buzz TV" if en else "Bibi Buzz TV ile şarkı söyle"
    pops = [("show", a["key"], {"at": (1.0 + 1.5 * i) * beat}) for i, a in enumerate(ANIMALS)]
    s.finish_scene(sc, dancers=ALL4, hop=1.0, hop_mode="wave", extra=pops + [
        ("fx", "title", 0, 0, {"at": 0.0, "dur": sec["dur"], "lines": title, "sub": sub, "top": 84, "size": 104 if en else 112, "gap": 108 if en else 114,
                               "pill": 38, "sfx": False}),
        _fx("sparkle", 640, 440, 0.4, sec["dur"], r=330), _fx("notes", 120, 560, 0.0, sec["dur"]), _fx("notes", 1130, 560, 0.7, sec["dur"]),
        ("sfx", "tada", {"at": 0.0})])

    # ---- 'Old MacDonald had a farm, E-I-E-I-O': Grandpa Mac pops in at his name
    sc = s.scene_for(1, "farm", drift=0.03)
    sides(sc)
    sc.actor("farmer", "girl", 640, 566, 1.5, show=False, **FARMER)
    sec = S[1]
    t_mac = next(a for w, a, b in s.word_spans(sec, sec["items"][0]) if w == ("macdonald" if en else "dede"))
    s.finish_scene(sc, singers=(ALL4,), dancers=ALL4 + ("farmer",), hop=1.0, hop_mode="wave", side=30, cam=(640, 350, 1.06), extra=[
        ("show", "farmer", {"at": max(0.0, t_mac - 0.1)}), ("pose", "farmer", "wave", {"at": t_mac}),
        _fx("poof", 640, 440, max(0.0, t_mac - 0.1), 1.2, r=220),
        _fx("notes", 90, 520, 0.0, sec["dur"]), _fx("notes", 1190, 520, 0.8, sec["dur"])])

    # ---- the verses
    for k, a in enumerate(ANIMALS):
        iA, iB, iC = 2 + 3 * k, 3 + 3 * k, 4 + 3 * k
        key = a["key"]
        info = a[lg]
        plain = info["name"].replace("-", "").lower()
        snd = info["snd"].lower()
        last = k == len(ANIMALS) - 1

        # -- 'And on his farm he had a cow, E-I-E-I-O': the cow pops in at its name, then dances
        secA = S[iA]
        sc = s.scene_for(iA, BACKS[k], drift=0.03)
        sides(sc)
        animal(sc, a, 640, 566, 2.0, show=False)
        t_an = next(t0 for w, t0, t1 in s.word_spans(secA, secA["items"][0]) if w == plain)
        t_on = max(0.0, t_an - 0.08)
        nxt = t_an + 0.1
        dance = [("hop", key, {"at": t}) for t in [1.0 * beat + j * beat for j in range(int(secA["beats"]))] if t >= nxt and t < secA["dur"] - 0.6]
        s.finish_scene(sc, singers=(("bibi", "pip"), ("mo", "lila")), dancers=ALL4, hop=1.0, hop_from=1.0, hop_mode="wave", side=30, cam=(640, 350, 1.06),
                       extra=[("show", key, {"at": t_on}), ("pose", key, "happy", {"at": t_on}), _fx("poof", 640, 430, t_on, 1.2, r=240),
                              _fx("hearts", 90, 400, 0.6, secA["dur"]), _fx("notes", 1190, 520, 0.2, secA["dur"])] + dance)

        # -- its sound: 'With a moo moo here ...': everybody sings, the sound word bursts out on the screen
        secB = S[iB]
        sc = s.scene_for(iB, BACKS[k], drift=0.0)
        sides(sc)
        animal(sc, a, 640, 566, 2.0)
        bursts, nb = [], 0
        for it in secB["items"]:
            final = it["key"].startswith("M5")
            for w, t0, t1 in s.word_spans(secB, it):
                if w != snd:
                    continue
                bx = 640 + (-1 if nb % 2 == 0 else 1) * (300 if not final else 250)
                by = 250 + (nb % 3) * 24
                big = 0.82 if len(info["big"]) <= 5 else 0.95
                bursts.append(("fx", "burst", bx, by, {"at": max(0.0, t0 - 0.05), "dur": 0.9, "text": info["big"], "color": a["color"],
                               "size": big * (1.25 if final else 1.0), "sfx": False}))
                bursts.append(("hop", key, {"at": t0}))
                nb += 1
        s.finish_scene(sc, singers=(ALL4 + (key,),), dancers=ALL4, hop=1.0, hop_mode="all", side=36, extra=_bar_pumps(s, secB) + bursts + [
            _fx("notes", 90, 520, 0.0, secB["dur"]), _fx("notes", 1190, 520, 0.7, secB["dur"])])

        # -- 'Old MacDonald had a farm ...' again: all the animals that have come so far dance with the friends
        secC = S[iC]
        sc = s.scene_for(iC, BACKS[k], drift=0.03)
        for j in range(k + 1):                                                  # (the animals stand behind the friends, in the gaps between them)
            b = ANIMALS[j]
            animal(sc, b, slot_x[b["key"]], 520, 1.2, face=1 if slot_x[b["key"]] < 640 else -1)
        for w, x, f, d in zip(FAMILY, (258, 512, 768, 1022), (1, 1, -1, -1), (-6, 4, 4, -6)):
            sc.actor(w, w, x, 582 + d, 1.25, face=f)
        dancers = ALL4 + tuple(ids[:k + 1])
        extra = [_fx("notes", 70, 470, 0.0, secC["dur"]), _fx("notes", 1210, 470, 0.7, secC["dur"])]
        if last:
            extra += _bar_pumps(s, secC, amount=0.035) + [_fx("confetti", 0, 0, 0.0, secC["dur"]), ("sfx", "cheer", {"at": 0.0})]
        else:
            extra += [_fx("sparkle", 640, 300, 0.0, secC["dur"], r=420)]
        s.finish_scene(sc, singers=(ALL4,), dancers=dancers, hop=1.0, hop_mode="all", side=24, extra=extra)

    # ---- outro: thank you, like and subscribe
    sc = s.scene_for(len(S) - 1, "farm_dusk", drift=0.0)
    for w, x, f, d in zip(FAMILY, (210, 470, 810, 1070), (1, 1, -1, -1), (-6, 4, 4, -6)):
        sc.actor(w, w, x, 612 + d, 1.05, face=f)
    sc.actor("farmer", "girl", 640, 616, 1.15, **FARMER)
    sec = S[-1]
    like, sub_t = 1.7, 3.0
    caption = "Like and subscribe for more songs!" if en else "Daha fazla şarkı için beğen ve abone ol!"
    s.finish_scene(sc, dancers=ALL4 + ("farmer",), hop=2.0, hop_mode="all", extra=[
        _fx("confetti", 0, 0, sub_t, sec["dur"]), ("fx", "cta", 640, 215, {"at": 0.0, "dur": sec["dur"], "like": like, "sub": sub_t, "sfx": False}),
        _fx("caption", 0, 0, 0.3, sec["dur"], text=caption), _fx("hearts", 330, 380, 1.0, sec["dur"]), _fx("hearts", 950, 380, 1.4, sec["dur"]),
        ("pose", "farmer", "wave", {"at": 0.2}),
        ("sfx", "pop", {"at": 0.05}), ("sfx", "pop", {"at": 0.3}), ("sfx", "ding", {"at": like + 0.05}), ("sfx", "pop", {"at": like}),
        ("sfx", "ding", {"at": sub_t + 0.05}), ("sfx", "pop", {"at": sub_t}), ("sfx", "sparkle", {"at": sub_t + 0.1})])


# ================================================================================================ the shelf
SPECS = {"twinkle": TWINKLE, "oldmac": OLDMAC}
RECIPES = {"twinkle": _twinkle, "oldmac": _oldmac}
QUEUE = ["twinkle", "oldmac"]            # the order in which the songs come out (one a day: curriculum.py)


def build(key, lang="en"):
    """The song `key` in `lang` as a Song (voice, band and pictures are made from its spec)."""
    s = Song(SPECS[key], lang)
    RECIPES[key](s)
    return s
