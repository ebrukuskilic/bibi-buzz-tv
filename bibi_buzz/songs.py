"""The songs of the song videos (song.py): nursery rhymes and little songs, every one in English and in Turkish.

A song is written like sheet music, a spec (dict) with the notes, the chords and the words of every line (see song.py for the format),
plus a recipe that dresses its sections with pictures: backdrops, the four friends dancing and singing, the big star, confetti.

  build("twinkle", "en") -> a Song (it renders like a tale: story.render / story.make_cover)
"""
import re

from . import draw as D
from . import songart  # noqa: F401  (registers the farm and lake backdrops in storyart2.BACKDROPS and the props of the rainbow sheep, the boat and the animals of the lake)
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


# ================================================================================================ Baa baa rainbow sheep / Mee mee gökkuşağı koyunu
# C major, 4/4, the old tune of 'Baa baa black sheep' (it is the tune of 'Twinkle twinkle' too).  The wool of the sheep takes a new colour in every verse:
#   Verse a   'Baa baa red sheep, have you any wool?'  (at the colour word the wool turns red)  /  'Yes sir, yes sir, four bags full!' (four sacks pop up)
#   Verse b   'One for Bibi, one for Pip, one for Mo and one for Lila!'  (a sack for each friend, at his name; the friends take turns to be first)
# After the six colours comes the rainbow: rainbow wool, six sacks, and the six colours are named in the order of the rainbow.
# Every line is made below: the colour word has one, two (or, in Turkish, three or four) syllables, so the notes of its line are made to fit.
WOOLS = [      # the colour of the wool, the sky of its verse, and the colour word in English and Turkish ('-' = syllable breaks)
    dict(wool=songart.RAINBOW6[0], bg="farm_dawn", en="red", tr="kır-mı-zı"),
    dict(wool=songart.RAINBOW6[1], bg="sunset", en="or-ange", tr="tu-run-cu"),
    dict(wool=songart.RAINBOW6[2], bg="farm_open", en="yel-low", tr="sa-rı"),
    dict(wool=songart.RAINBOW6[3], bg="meadow", en="green", tr="ye-şil"),
    dict(wool=songart.RAINBOW6[4], bg="river", en="blue", tr="ma-vi"),
    dict(wool=songart.RAINBOW6[5], bg="meadow_dusk", en="pur-ple", tr="mor"),
]
RAINBOW_WORD = dict(en="rain-bow", tr="gök-ku-şa-ğı")
NAMES = {"bibi": dict(en="Bi-bi", tr="Bi-bi'-ye"), "pip": dict(en="Pip", tr="Pip'-e"),             # (in Turkish: 'for Bibi' = Bibi'ye)
         "mo": dict(en="Mo", tr="Mo'-ya"), "lila": dict(en="Li-la", tr="Li-la'-ya")}
ORDERS = [("bibi", "pip", "mo", "lila"), ("lila", "mo", "pip", "bibi"), ("bibi", "mo", "pip", "lila"),     # who gets the 1st, 2nd, 3rd and 4th sack in every verse
          ("lila", "pip", "mo", "bibi"), ("pip", "bibi", "lila", "mo"), ("mo", "lila", "bibi", "pip")]       # (a pair is always a long name and a short one: the lines keep their syllables)

_N_B = "F4 F4 E4 E4 D4 D4 C4:2"
_N_C7 = "G4 G4 F4 F4 E4 E4 D4:2"
_N_C8 = "G4 G4 F4 F4 E4 E4 D4 D4"
_CH_Q, _CH_B, _CH_C = "C:4 F:2 C:2", "F:2 C:2 G:2 C:2", "C:2 F:2 C:2 G:2"
_SLOT_EN = {1: (1.0,), 2: (0.5, 0.5)}
_SLOT_TR = {1: (2.0,), 2: (1.0, 1.0), 3: (0.5, 0.5, 1.0), 4: (0.5, 0.5, 0.5, 0.5)}


def _slot(pitch, beats):
    return " ".join("%s:%g" % (pitch, d) for d in beats)


def _q_en(nc):
    """'Baa baa [red] sheep, have you any wool?': the colour word sits on the third beat, split into nc notes."""
    return "C4 C4 %s G4 A4:0.5 A4:0.5 A4:0.5 A4:0.5 G4:2" % _slot("G4", _SLOT_EN[nc])


def _q_tr(nc):
    """'Mee mee [mavi] koyun, yünün var mı?': the colour word has two beats."""
    return "C4 C4 %s G4:0.5 G4:0.5 A4:0.5 A4:0.5 G4 G4" % _slot("G4", _SLOT_TR[nc])


def _n_syl(word):
    return len(word.split("-"))


def _plain(text):
    return re.sub(r"[^\w]", "", text.replace("-", "")).lower()


def _up(text, lang):
    """A word in capitals (the Turkish i has a dot: 'mavi' = MAVİ)."""
    t = text.replace("-", "")
    return (t.replace("i", "İ") if lang == "tr" else t).upper()


def _rs_lines():
    L = {}
    for k, w in enumerate(WOOLS):
        L["Q%d" % k] = dict(en="Baa baa %s sheep, have you a-ny wool?" % w["en"], tr="Mee mee %s ko-yun, yü-nün var mı?" % w["tr"],
                            notes=_q_en(_n_syl(w["en"])), tr_notes=_q_tr(_n_syl(w["tr"])), chords=_CH_Q)
        a, b, c_, d = ORDERS[k]
        L["P%d" % k] = dict(en="One for %s, one for %s," % (NAMES[a]["en"], NAMES[b]["en"]), tr="%s bir, %s bir," % (NAMES[a]["tr"], NAMES[b]["tr"]),
                            notes=_N_C7, chords=_CH_C)
        L["S%d" % k] = dict(en="One for %s and one for %s!" % (NAMES[c_]["en"], NAMES[d]["en"]), tr="%s bir, %s bir!" % (NAMES[c_]["tr"], NAMES[d]["tr"]),
                            notes=_N_C8, tr_notes=_N_C7, chords=_CH_C)
    L["QR"] = dict(en="Baa baa %s sheep, have you a-ny wool?" % RAINBOW_WORD["en"], tr="Mee mee %s ko-yun, yü-nün var mı?" % RAINBOW_WORD["tr"],
                   notes=_q_en(2), tr_notes=_q_tr(4), chords=_CH_Q)
    L["A"] = dict(en="Yes sir, yes sir, four bags full!", tr="Var var, dört çu-val do-lu!", notes=_N_B, chords=_CH_B)
    L["AR"] = dict(en="Yes sir, yes sir, six bags full!", tr="Var var, al-tı çu-val do-lu!", notes=_N_B, tr_notes="F4 F4 E4 E4 D4 D4 C4 C4", chords=_CH_B)
    L["PR"] = dict(en="Red and or-ange, yel-low, green,", tr="Kır-mı-zı, tu-run-cu, sa-rı, ye-şil,", notes=_N_C7,
                   tr_notes="G4:0.5 G4:0.5 G4 F4:0.5 F4:0.5 F4 E4 E4 D4 D4", chords=_CH_C)
    L["SR"] = dict(en="Blue and pur-ple, what a scene!", tr="Ma-vi ve mor, ne gü-zel renk!", notes=_N_C7, tr_notes=_N_C8, chords=_CH_C)
    return L


_RS_SING = dict(lead="xylo", lead_gain=0.20, chords="strum", chord_gain=1.0, bass_gain=0.75, drums="light")
_RS_CLAP = dict(lead="xylo", lead_gain=0.20, chords="strum", chord_gain=1.05, bass_gain=0.8, drums="clap", drum_gain=0.85)
_RS_BOUNCE = dict(lead="flute", lead_gain=0.20, chords="oompah", chord_gain=1.1, bass_gain=0.9, drums="clap", drum_gain=0.9)
_RS_SOFT = dict(lead="box", lead_gain=0.22, chords="lull", chord_gain=1.0, bass_gain=0.8, drums="none")
_RS_FINAL = dict(lead="xylo", lead_gain=0.22, chords="oompah", chord_gain=1.15, bass_gain=1.0, drums="party", drum_gain=1.0)
_RS_DANCE = dict(lead="xylo", lead_gain=0.45, chords="oompah", chord_gain=1.1, bass_gain=0.9, drums="party", drum_gain=1.0)
_RS_STYLES = [_RS_SING, _RS_CLAP, _RS_BOUNCE, _RS_CLAP, _RS_SOFT, _RS_BOUNCE]                      # the six colour verses


def _rs_form():
    form = [dict(name="Intro", mode="inst", lines=["Q0"], style=_RS_DANCE)]
    for k in range(len(WOOLS)):
        form += [dict(name="Verse %d a" % (k + 1), lines=["Q%d" % k, "A"], style=_RS_STYLES[k]),
                 dict(name="Verse %d b" % (k + 1), lines=["P%d" % k, "S%d" % k], style=_RS_STYLES[k])]
        if k == 2:
            form.append(dict(name="Dance", mode="inst", lines=["P0", "S0"], style=_RS_DANCE))
    form += [dict(name="Final a", lines=["QR", "AR"], style=_RS_FINAL), dict(name="Final b", lines=["PR", "SR"], style=_RS_FINAL),
             dict(name="Outro", mode="inst", lines=["A"], post=4, style=dict(lead="xylo", lead_gain=0.5, chords="oompah", chord_gain=1.1, bass_gain=0.9,
                                                                          drums="clap", drum_gain=0.9))]
    return form


def _rs_cover(lang):
    en = lang == "en"
    rb = songart.RAINBOW6
    return dict(bg="meadow_open", title=("BAA BAA", "RAINBOW SHEEP") if en else ("MEE MEE", "GÖKKUŞAĞI KOYUNU"), size=104 if en else 92, gap=106 if en else 98,
                sub="Sing along with Bibi Buzz TV" if en else "Bibi Buzz TV ile şarkı söyle",
                props=[("rb", "rainbow", 640, 600, 1.0, dict(grow=1.0, r=300.0, band=15.0)),
                       ("b1", "wool_bag", 440, 706, 0.95, dict(wool=rb[0], n=0)), ("b2", "wool_bag", 840, 706, 0.95, dict(wool=rb[4], n=0))],
                actors=[("bibi", "bibi", 130, 708, 1.55, 1, "idle", {}), ("pip", "pip", 320, 714, 1.4, 1, "idle", {}),
                        ("mo", "mo", 960, 714, 1.4, -1, "idle", {}), ("lila", "lila", 1150, 708, 1.55, -1, "idle", {}),
                        ("sheep", "sheep", 640, 716, 1.85, 1, "happy", dict(wool=rb))],
                fx=[])


RAINBOWSHEEP = dict(
    id="rainbowsheep",
    title={"en": "Baa Baa Rainbow Sheep | Learn Colors | Kids Song & Nursery Rhyme | Bibi Buzz TV",
           "tr": "Mee Mee Gökkuşağı Koyunu | Renkleri Öğreniyoruz | Çocuk Şarkısı | Bibi Buzz TV"},
    blurb={
        "en": "Sing along with Bibi, Pip, Mo and Lila! Baa baa rainbow sheep, have you any wool? Yes sir, yes sir, bags full of red, orange, yellow, green, blue "
              "and purple wool! Learn the colors of the rainbow and count the sacks of wool, with the words lighting up as we sing. "
              "A cheerful nursery rhyme for babies, toddlers and preschoolers.",
        "tr": "Bibi, Pip, Mo ve Lila ile birlikte söyleyelim! Mee mee gökkuşağı koyunu, yünün var mı? Var var, kırmızı, turuncu, sarı, yeşil, mavi ve mor yün dolu çuvallar! "
              "Gökkuşağının renklerini öğreniyor ve yün çuvallarını sayıyoruz; sözler şarkı söylenirken ekranda yanıyor. "
              "Bebekler, küçük çocuklar ve okul öncesi minikler için neşeli bir çocuk şarkısı.",
    },
    tags={
        "en": ["baa baa black sheep", "baa baa rainbow sheep", "learn colors", "colors song", "rainbow colors", "nursery rhymes", "kids songs", "sing along",
               "songs for kids", "toddler songs", "baby songs", "children songs", "Bibi Buzz TV"],
        "tr": ["mee mee koyun", "gökkuşağı koyunu", "renkleri öğreniyorum", "renkler şarkısı", "gökkuşağı renkleri", "çocuk şarkıları", "bebek şarkıları",
               "çocuk şarkısı", "birlikte söyleyelim", "okul öncesi şarkılar", "türkçe çocuk şarkıları", "Bibi Buzz TV"],
    },
    bpm=100, beats=4, shift={"en": -2, "tr": -5},
    lines=_rs_lines(),
    form=_rs_form(),
    cover={"en": _rs_cover("en"), "tr": _rs_cover("tr")},
)

_RB_X = {"bibi": 150, "pip": 345, "mo": 935, "lila": 1130}          # where the friends stand beside the sheep
RB6 = songart.RAINBOW6


def _rainbowsheep(s):
    """The pictures of 'Baa baa rainbow sheep': the intro (the wool of the sheep turns through all the colours), six colour verses (the wool turns, four sacks
    pop up, a sack for every friend), a dance, the rainbow verse, and the outro."""
    S, lg, en, beat = s.sections, s.lang, s.lang == "en", s.beat
    at = {sec["name"]: sec["index"] for sec in S}
    movers = ALL4 + ("sheep",)

    def flank(sc, k=1.35, y=566):
        for w, f, d in zip(FAMILY, (1, 1, -1, -1), (-6, 4, 4, -6)):
            sc.actor(w, w, _RB_X[w], y + d, k, face=f)

    def sheep(sc, wool, x=640, y=566, k=2.0):
        sc.actor("sheep", "sheep", x, y, k, face=1, wool=wool)

    def turn(col, t, y=410, stars=170):
        """The wool of the sheep turns into `col` at the time t: a puff of wool, a ring of stars (radius `stars`, 0 = none) and a hop."""
        out = [("look", "sheep", "wool", col, {"at": t}), ("hop", "sheep", {"at": t}), ("sfx", "sparkle", {"at": t}), _fx("wool_burst", 640, y, t, 1.5, color=col)]
        if stars:
            out.append(_fx("sparkle", 640, y, t, 1.2, r=stars, n=9))
        return out

    def bag(sc, pid, x, y, k, wool, n, show=False):
        sc.prop(pid, "wool_bag", x, y, k, show=show, wool=wool, n=n)

    def pop(pid, t):
        return ("show", pid, {"at": max(0.0, t)})

    def notes_fx(sec):
        return [_fx("notes", 90, 520, 0.0, sec["dur"]), _fx("notes", 1190, 520, 0.7, sec["dur"])]

    # ---- intro: the title card; the white sheep turns red, orange, yellow, green, blue, purple, and last rainbow-coloured
    sec = S[0]
    sc = s.scene_for(0, "meadow_open", mood="title", drift=0.0, clouds=False)
    for w, x, d in zip(FAMILY, (150, 395, 885, 1130), (-8, 2, 2, -8)):
        sc.actor(w, w, x, 612 + d, 1.2)
    sheep(sc, "#FFFFFF", 640, 626, 1.12)
    acts = []
    for i, w in enumerate(WOOLS):
        acts += turn(w["wool"], (1 + i) * beat, y=470, stars=0)
    acts += turn(RB6, 7 * beat, y=470, stars=0)
    title = ("BAA BAA", "RAINBOW SHEEP") if en else ("MEE MEE", "GÖKKUŞAĞI KOYUNU")
    sub = "Sing along with Bibi Buzz TV" if en else "Bibi Buzz TV ile şarkı söyle"
    s.finish_scene(sc, dancers=ALL4, hop=1.0, hop_mode="wave", extra=acts + [
        ("fx", "title", 0, 0, {"at": 0.0, "dur": sec["dur"], "lines": title, "sub": sub, "top": 84, "size": 104 if en else 92, "gap": 108 if en else 98,
                               "pill": 38, "sfx": False}),
        _fx("sparkle", 640, 440, 0.4, sec["dur"], r=330), _fx("notes", 120, 560, 0.0, sec["dur"]), _fx("notes", 1130, 560, 0.7, sec["dur"]),
        ("sfx", "tada", {"at": 0.0})])

    # ---- the six colour verses
    prev = "#FFFFFF"
    for k, w in enumerate(WOOLS):
        if k == 3:                                                                                # (the dance comes after the third colour)
            secD = S[at["Dance"]]
            sc = s.scene_for(at["Dance"], "ballroom_day", drift=0.0, clouds=False)
            flank(sc, 1.4, 562)
            sheep(sc, prev, 640, 562, 1.9)
            seq = [RB6[0], RB6[1], RB6[3], RB6[4], RB6[5], RB6[0], RB6[1], RB6[2]]              # (it ends on yellow again: the next verse starts from there)
            acts = []
            for i, col in enumerate(seq):
                acts += turn(col, i * 2 * beat, stars=0)
            s.finish_scene(sc, dancers=movers, hop=1.0, hop_mode="all", side=40, extra=_bar_pumps(s, secD) + acts + [
                _fx("confetti", 0, 0, 0.0, secD["dur"]), ("sfx", "cheer", {"at": 0.0})])
            prev = seq[-1]
        secA, secB = S[at["Verse %d a" % (k + 1)]], S[at["Verse %d b" % (k + 1)]]
        # -- a: 'Baa baa red sheep, have you any wool?' (the wool turns at the colour word) 'Yes sir, yes sir, four bags full!' (four sacks pop up)
        sc = s.scene_for(at["Verse %d a" % (k + 1)], w["bg"], drift=0.03)
        flank(sc)
        sheep(sc, prev)
        t_col = s.word_spans(secA, secA["items"][0])[2][1]
        extra = turn(w["wool"], max(0.0, t_col - 0.05))
        for j, bx in enumerate((455, 560, 720, 825)):
            bag(sc, "bag%d" % j, bx, 580, 0.95, w["wool"], j + 1)
            extra += [pop("bag%d" % j, (12 + j) * beat - 0.05)]
        extra += notes_fx(secA) + [_fx("sparkle", 640, 300, 12 * beat, secA["dur"], r=260)]
        s.finish_scene(sc, singers=(ALL4, ("sheep",)), dancers=movers, hop=1.0, hop_mode="wave", cam=(640, 350, 1.06), size=48, extra=extra)
        # -- b: 'One for Bibi, one for Pip, one for Mo and one for Lila!' (a sack pops up at the feet of every friend, at his name)
        sc = s.scene_for(at["Verse %d b" % (k + 1)], w["bg"], drift=0.0)
        flank(sc)
        sheep(sc, w["wool"])
        extra = []
        order = ORDERS[k]
        for it, pair, off in zip(secB["items"], (order[:2], order[2:]), (0, 2)):
            spans = s.word_spans(secB, it)
            for j, who in enumerate(pair):
                n = off + j + 1
                t_n = next(a for (pl, a, b) in spans if pl == _plain(NAMES[who][lg]))
                bx = _RB_X[who] + (62 if _RB_X[who] < 640 else -62)
                bag(sc, "bag%d" % n, bx, 580, 0.95, w["wool"], n)
                extra += [pop("bag%d" % n, t_n - 0.05), ("hop", who, {"at": t_n}), ("sfx", "ding", {"at": t_n}), _fx("sparkle", bx, 520, t_n, 0.9, r=70)]
        extra += notes_fx(secB) + [_fx("hearts", 470, 400, 0.5, secB["dur"]), _fx("hearts", 810, 400, 1.1, secB["dur"])]
        s.finish_scene(sc, singers=(ALL4,), dancers=movers, hop=2.0, hop_mode="all", cam=(640, 346, 1.04), extra=extra)
        prev = w["wool"]

    # ---- the rainbow verse
    secA, secB = S[at["Final a"]], S[at["Final b"]]
    RB_BAGS = [400 + 96 * j for j in range(6)]
    sc = s.scene_for(at["Final a"], "farm_open", drift=0.03)
    sc.prop("rb", "rainbow", 640, 478, 1.0, grow=0.0, r=370.0, band=19.0)
    flank(sc)
    sheep(sc, prev)
    t_col = s.word_spans(secA, secA["items"][0])[2][1]
    t_r = max(0.0, t_col - 0.05)
    extra = turn(RB6, t_r) + [("set", "rb", "grow", 1.0, {"at": t_r, "dur": min(1.9, secA["dur"] - t_r - 0.4)}), ("sfx", "tada", {"at": t_r})]
    for j, bx in enumerate(RB_BAGS):
        bag(sc, "bag%d" % j, bx, 580, 0.72, RB6[j], j + 1)
        extra += [pop("bag%d" % j, (10 + j) * beat - 0.05)]
    extra += notes_fx(secA) + [_fx("confetti", 0, 0, t_r + 0.3, secA["dur"])]
    s.finish_scene(sc, singers=(ALL4, ("sheep",)), dancers=movers, hop=1.0, hop_mode="wave", cam=(640, 350, 1.04), size=44, extra=extra)

    sc = s.scene_for(at["Final b"], "farm_open", drift=0.0)
    sc.prop("rb", "rainbow", 640, 478, 1.0, grow=1.0, r=370.0, band=19.0)
    flank(sc)
    sheep(sc, RB6)
    for j, bx in enumerate(RB_BAGS):
        bag(sc, "bag%d" % j, bx, 580, 0.72, RB6[j], j + 1, show=True)
    extra = []
    named = []
    for it in secB["items"]:
        for (pl, a, b) in s.word_spans(secB, it):
            for j, w in enumerate(WOOLS):
                if pl == _plain(w["en"] if en else w["tr"]):
                    named.append((a, b, j))
    named.sort()
    for i, (a, b, j) in enumerate(named):
        nxt = named[i + 1][0] if i + 1 < len(named) else secB["dur"]
        hold = max(0.5, min(1.4, nxt - a - 0.15))
        extra += [("fx", "word_pop", 640, 58, {"at": a, "dur": hold + 0.3, "text": _up(WOOLS[j]["en"] if en else WOOLS[j]["tr"], lg), "color": WOOLS[j]["wool"],
                                                 "hold": hold, "size": 1.0, "sfx": False}),
                  ("sfx", "ding", {"at": a})]
    extra += notes_fx(secB) + _bar_pumps(s, secB, amount=0.03) + [_fx("confetti", 0, 0, 0.0, secB["dur"]), ("sfx", "cheer", {"at": 0.0})]
    s.finish_scene(sc, singers=(ALL4,), dancers=movers, hop=1.0, hop_mode="all", side=24, extra=extra)

    # ---- outro: thank you, like and subscribe
    sc = s.scene_for(len(S) - 1, "meadow_dawn", drift=0.0)
    sc.prop("rb", "rainbow", 640, 600, 1.0, grow=1.0, r=300.0, band=15.0)
    for w, x, f, d in zip(FAMILY, (210, 470, 810, 1070), (1, 1, -1, -1), (-6, 4, 4, -6)):
        sc.actor(w, w, x, 612 + d, 1.05, face=f)
    sheep(sc, RB6, 640, 618, 1.2)
    sec = S[-1]
    like, sub_t = 1.7, 3.0
    caption = "Like and subscribe for more songs!" if en else "Daha fazla şarkı için beğen ve abone ol!"
    s.finish_scene(sc, dancers=movers, hop=2.0, hop_mode="all", extra=[
        _fx("confetti", 0, 0, sub_t, sec["dur"]), ("fx", "cta", 640, 215, {"at": 0.0, "dur": sec["dur"], "like": like, "sub": sub_t, "sfx": False}),
        _fx("caption", 0, 0, 0.3, sec["dur"], text=caption), _fx("hearts", 330, 380, 1.0, sec["dur"]), _fx("hearts", 950, 380, 1.4, sec["dur"]),
        ("sfx", "pop", {"at": 0.05}), ("sfx", "pop", {"at": 0.3}), ("sfx", "ding", {"at": like + 0.05}), ("sfx", "pop", {"at": like}),
        ("sfx", "ding", {"at": sub_t + 0.05}), ("sfx", "pop", {"at": sub_t}), ("sfx", "sparkle", {"at": sub_t + 0.1})])


# ================================================================================================ Row, row, row your boat / Kürek çek, kürek çek
# C major, 6/8, written with the dotted quarter as the beat (60 to the minute, two beats to a bar).  A verse is eight bars:
#   a  'Row, row, row your boat, gently down the stream.'      b  'Merrily, merrily, merrily, merrily, life is but a dream.'
# The first verse (sunrise) and the last one (starry night, a lullaby) are the song as it is.  In the four verses between, an animal of the lake comes by:
# the third line becomes its sound (eight half beats: quack quack ...) and the fourth greets it ('Hello little duck!').
_T1, _T2 = "%.10g" % (1 / 3), "%.10g" % (2 / 3)          # a third of a beat and two thirds of a beat (an eighth and a quarter in 6/8)
_RW_N1 = "C4 C4 C4:%s D4:%s E4" % (_T2, _T1)
_RW_N1_TR = "C4:0.5 C4:0.5 C4 C4:%s D4:%s E4" % (_T2, _T1)                                  # 'Kü-rek çek, kü-rek çek': six syllables
_RW_N2 = "E4:%s D4:%s E4:%s F4:%s G4:2" % (_T2, _T1, _T2, _T1)
_RW_N3 = " ".join("%s:%s" % (p, _T1) for p in "C5 C5 C5 G4 G4 G4 E4 E4 E4 C4 C4 C4".split())
_RW_N4 = "G4:%s F4:%s E4:%s D4:%s C4:2" % (_T2, _T1, _T2, _T1)
_RW_N4_6 = "G4:%s G4:%s F4:%s E4:%s D4:%s C4:2" % (_T1, _T1, _T1, _T2, _T1)                 # 'Mer-ha-ba kur-ba-ğa': six syllables
_RW_NS = "C5:0.5 C5:0.5 G4:0.5 G4:0.5 E4:0.5 E4:0.5 C4:0.5 C4:0.5"                         # the sound of an animal: eight half beats down the chord

RW_ANIMALS = [      # who comes by, the sound it makes (the plain lower-case word of the sound line), the big sound word, the colour of its burst, its line 3 and its greeting
    dict(key="duck", color="#F2A71B", snd=dict(en="quack", tr="vak"), big=dict(en="QUACK!", tr="VAK!"),
         sound=dict(en=" ".join(["Quack"] * 8) + "!", tr=" ".join(["Vak"] * 8) + "!"),
         hello=dict(en="Hel-lo lit-tle duck!", tr="Mer-ha-ba ör-dek!")),
    dict(key="frog", color="#3FAE49", snd=dict(en="ribbit", tr="vrak"), big=dict(en="RIBBIT!", tr="VRAK!"),
         sound=dict(en=" ".join(["Rib-bit"] * 4) + "!", tr=" ".join(["Vrak"] * 8) + "!"),
         hello=dict(en="Hel-lo lit-tle frog!", tr="Mer-ha-ba kur-ba-ğa!")),
    dict(key="fish", color="#FF7A1F", snd=dict(en="blub", tr="blup"), big=dict(en="BLUB!", tr="BLUP!"),
         sound=dict(en=" ".join(["Blub"] * 8) + "!", tr=" ".join(["Blup"] * 8) + "!"),
         hello=dict(en="Hel-lo lit-tle fish!", tr="Mer-ha-ba ba-lık!")),
    dict(key="bird", color="#4A8FE7", snd=dict(en="tweet", tr="cik"), big=dict(en="TWEET!", tr="CİK!"),
         sound=dict(en=" ".join(["Tweet"] * 8) + "!", tr=" ".join(["Cik"] * 8) + "!"),
         hello=dict(en="Hel-lo lit-tle bird!", tr="Mer-ha-ba ku-şum!")),
]


def _rw_lines():
    L = {
        "L1": dict(en="Row, row, row your boat,", tr="Kü-rek çek, kü-rek çek,", notes=_RW_N1, tr_notes=_RW_N1_TR, chords="C:4"),
        "L2": dict(en="Gent-ly down the stream.", tr="Su-da u-sul-ca.", notes=_RW_N2, chords="C:2 G:2"),
        "L3": dict(en="Mer-ri-ly, mer-ri-ly, mer-ri-ly, mer-ri-ly,", tr="Ne-şey-le ne-şey-le ne-şey-le ne-şey-le,", notes=_RW_N3, chords="C:4"),
        "L4": dict(en="Life is but a dream.", tr="Ha-yat bir rü-ya.", notes=_RW_N4, chords="G7:2 C:2"),
    }
    for i, a in enumerate(RW_ANIMALS):
        L["S%d" % i] = dict(en=a["sound"]["en"], tr=a["sound"]["tr"], notes=_RW_NS, chords="C:4")
        L["H%d" % i] = dict(en=a["hello"]["en"], tr=a["hello"]["tr"], notes=_RW_N4, chords="G7:2 C:2")
        if a["key"] == "frog":
            L["H%d" % i]["tr_notes"] = _RW_N4_6
    return L


_RW_SOFT = dict(lead="box", lead_gain=0.22, chords="rollbox", chord_gain=1.0, bass_gain=0.8, drums="none")
_RW_SING = dict(lead="xylo", lead_gain=0.20, chords="roll", chord_gain=1.0, bass_gain=0.75, drums="sway")
_RW_CLAP = dict(lead="xylo", lead_gain=0.20, chords="roll", chord_gain=1.05, bass_gain=0.8, drums="sway_clap", drum_gain=0.85)
_RW_SOUND = dict(lead="flute", lead_gain=0.20, chords="roll", chord_gain=1.1, bass_gain=0.9, drums="sway_clap", drum_gain=0.9)
_RW_PARTY = dict(lead="xylo", lead_gain=0.45, chords="roll", chord_gain=1.1, bass_gain=0.9, drums="sway_party", drum_gain=1.0)
_RW_OUTRO = dict(lead="xylo", lead_gain=0.5, chords="roll", chord_gain=1.1, bass_gain=0.9, drums="sway_clap", drum_gain=0.9)


def _rw_form():
    form = [dict(name="Intro", mode="inst", lines=["L1"], style=_RW_PARTY)]

    def verse(n, sa, sb, l3="L3", l4="L4"):
        return [dict(name="Verse %d a" % n, lines=["L1", "L2"], style=sa), dict(name="Verse %d b" % n, lines=[l3, l4], style=sb)]

    form += verse(1, _RW_SOFT, _RW_SING)
    form += verse(2, _RW_SING, _RW_SOUND, "S0", "H0")
    form += verse(3, _RW_CLAP, _RW_SOUND, "S1", "H1")
    form += verse(4, _RW_SING, _RW_SOUND, "S2", "H2")
    form += verse(5, _RW_CLAP, _RW_SOUND, "S3", "H3")
    form.append(dict(name="Dance", mode="inst", lines=["L1", "L2", "L3", "L4"], style=_RW_PARTY))
    form += verse(6, _RW_SOFT, _RW_SOFT)
    form.append(dict(name="Outro", mode="inst", lines=["L4"], post=4, style=_RW_OUTRO))
    return form


def _rw_cover(lang):
    en = lang == "en"
    tint = songart.LAKE_MOODS["day"]["tint"]
    return dict(bg="lake", title=("ROW ROW ROW", "YOUR BOAT") if en else ("KÜREK ÇEK,", "KÜREK ÇEK!"), size=110, gap=112,
                sub="Sing along with Bibi Buzz TV" if en else "Bibi Buzz TV ile şarkı söyle",
                props=[("water", "lake_water", 640, 420, 1.0, dict(mood="day")),
                       ("boat_b", "boat_back", 620, 480, 1.0, dict(wl=534, bar=2.0)),
                       ("boat_f", "boat_front", 620, 540, 1.0, dict(wl=534, bar=2.0, water=tint)),
                       ("duck", "duck", 905, 566, 0.95, dict(face=1, water=tint, talk=[(0.6, 1.5)], seed=0.3)),
                       ("kid0", "duck", 770, 569, 0.42, dict(face=1, water=tint, talk=[(0.75, 1.5)], seed=1.1)),
                       ("kid1", "duck", 712, 570, 0.4, dict(face=1, water=tint, talk=[(0.85, 1.5)], seed=2.1)),
                       ("frog", "frog_pad", 290, 578, 0.62, dict(face=1, water=tint, croak=[(0.6, 1.5)])),
                       ("fish", "fish", 500, 566, 0.9, dict(water=tint, jumps=[(0.3, 1.4, 170, 190)], seed=0.7)),
                       ("bird", "songbird", 1100, 345, 1.0, dict(face=-1, talk=[(0.6, 1.5)]))],
                actors=[("bibi", "bibi", 320, 498, 1.075, 1, "idle", {}), ("pip", "pip", 500, 500, 1.079, 1, "idle", {}),
                        ("mo", "mo", 680, 500, 1.079, -1, "idle", {}), ("lila", "lila", 860, 496, 1.071, -1, "idle", {})],
                fx=[])


ROWBOAT = dict(
    id="rowboat",
    title={"en": "Row Row Row Your Boat | Kids Song & Nursery Rhyme | Bibi Buzz TV",
           "tr": "Kürek Çek, Kürek Çek | Çocuk Şarkısı | Bibi Buzz TV"},
    blurb={
        "en": "Sing along with Bibi, Pip, Mo and Lila! Row, row, row your boat gently down the stream, and say hello to a duck, a frog, a fish and a little bird along the way. "
              "Watch the day go by from sunrise to a starry night, with the words lighting up as we sing. A cheerful, gentle nursery rhyme for babies, toddlers and preschoolers.",
        "tr": "Bibi, Pip, Mo ve Lila ile birlikte söyleyelim! Kürek çek, kürek çek, suda usulca; yolda bir ördeğe, bir kurbağaya, bir balığa ve küçük bir kuşa merhaba diyoruz. "
              "Gün doğumundan yıldızlı geceye uzanan yolculukta sözler şarkı söylenirken ekranda yanıyor. Bebekler, küçük çocuklar ve okul öncesi minikler için neşeli, sakin bir çocuk şarkısı.",
    },
    tags={
        "en": ["row row row your boat", "row your boat", "nursery rhymes", "kids songs", "animal sounds", "sing along", "songs for kids", "toddler songs",
               "baby songs", "children songs", "lullaby", "Bibi Buzz TV"],
        "tr": ["kürek çek", "row row row your boat türkçe", "çocuk şarkıları", "hayvan sesleri", "bebek şarkıları", "çocuk şarkısı", "ninni",
               "birlikte söyleyelim", "okul öncesi şarkılar", "türkçe çocuk şarkıları", "Bibi Buzz TV"],
    },
    bpm=60, beats=2, shift={"en": -3, "tr": -6},
    lines=_rw_lines(),
    form=_rw_form(),
    cover={"en": _rw_cover("en"), "tr": _rw_cover("tr")},
)

RW_FRIENDS = (("bibi", 320, 498), ("pip", 500, 500), ("mo", 680, 500), ("lila", 860, 496))      # where the friends sit in the boat
RW_DUCK, RW_FROG, RW_FISH, RW_BIRD = (905, 566, 0.95), (290, 578, 0.76), (500, 566, 0.9), (1100, 345, 1.0)
RW_KIDS = ((770, 569, 0.42), (712, 570, 0.4))                                                  # the ducklings behind their mother
RW_MOOD = {"lake": "day", "lake_dawn": "dawn", "lake_dusk": "dusk", "lake_night": "night"}
RW_LANTERN = {"lake": 0.0, "lake_dawn": 0.0, "lake_dusk": 0.45, "lake_night": 1.0}
RW_IDS = {"duck": ("duck", "kid0", "kid1"), "frog": ("frog",), "fish": ("fish",), "bird": ("bird",)}
RW_HEAD = {"duck": (950, 485), "frog": (300, 500), "fish": (500, 470), "bird": (1105, 275)}       # (above) where its hearts go
RW_ZZZ = {"duck": (962, 440), "frog": (228, 520), "bird": (1118, 232)}                                # where an animal sleeps (the fish is out of sight)
RW_BURST = {"duck": ((760, 262), (990, 238)), "frog": ((300, 262), (500, 238)), "fish": ((420, 262), (640, 238)), "bird": ((760, 200), (980, 176))}


def _rw_size(s, sec):
    """The biggest size (up to 62) at which the longest line of a section fits in one row of the lyrics pill (about 1090 px)."""
    D.set_language(s.lang)
    for size in range(62, 35, -2):
        widest = 0.0
        for it in sec["items"]:
            ws = ["".join(w["syl"]) for w in it["words"]]
            if ws:
                widest = max(widest, sum(D.font(size).getlength(w) / D.SS for w in ws) + 0.28 * size * (len(ws) - 1))
        if widest <= 1090:
            return size
    return 36


def _rowboat(s):
    """The pictures of 'Row, row, row your boat': the four friends row a boat over a lake while the day goes by (dawn, day, dusk, night).  Four animals come by
    one after the other (a duck, a frog, a fish, a little bird), make their sound with the song and are greeted; at the end they all fall asleep."""
    S, lg, en, beat = s.sections, s.lang, s.lang == "en", s.beat
    at = {sec["name"]: sec["index"] for sec in S}
    bar = 2.0 * beat                                                  # one stroke of the oar for every bar
    A = {a["key"]: a for a in RW_ANIMALS}

    def stage(sc, bg, rowing=True, speed=1.0):
        """The lake, the boat and the four friends in it (between the far wall and the near wall of the boat)."""
        tint = songart.LAKE_MOODS[RW_MOOD[bg]]["tint"]
        sc.prop("water", "lake_water", 640, 420, 1.0, mood=RW_MOOD[bg], speed=speed)
        sc.prop("boat_b", "boat_back", 620, 480, 1.0, wl=534, bar=bar if rowing else 0.0)
        for w, x, y in RW_FRIENDS:
            sc.actor(w, w, x, y, 1.3)
        sc.prop("boat_f", "boat_front", 620, 540, 1.0, wl=534, bar=bar if rowing else 0.0, water=tint, lantern=RW_LANTERN[bg])
        return tint

    def critter(sc, key, tint, show=True, sleep=0, talk=(), croak=(), hops=(), jumps=()):
        """An animal of the lake: talk / croak / hops / jumps are the times (seconds in the scene) at which it sings, croaks, hops, leaps."""
        if key == "duck":
            x, y, k = RW_DUCK
            sc.prop("duck", "duck", x, y, k, show=show, face=1, water=tint, talk=list(talk), sleep=sleep, seed=0.3)
            for i, (kx, ky, kk) in enumerate(RW_KIDS):
                d = 0.14 + 0.08 * i
                sc.prop("kid%d" % i, "duck", kx, ky, kk, show=show, face=1, water=tint, talk=[(a + d, b + d) for a, b in talk], sleep=sleep, seed=1.1 + i)
        elif key == "frog":
            x, y, k = RW_FROG
            sc.prop("frog", "frog_pad", x, y, k, show=show, face=1, water=tint, croak=list(croak), hops=list(hops), sleep=sleep)
        elif key == "fish":
            x, y, k = RW_FISH
            sc.prop("fish", "fish", x, y, k, show=show, water=tint, jumps=list(jumps), sleep=sleep, seed=0.7)
        else:
            x, y, k = RW_BIRD
            sc.prop("bird", "songbird", x, y, k, show=show, face=-1, talk=list(talk), sleep=sleep)

    def appear(key, t):
        """The animal pops in at the time t (a splash for the water animals, a few sparkles for the bird)."""
        out = [("show", pid, {"at": max(0.0, t + 0.12 * i)}) for i, pid in enumerate(RW_IDS[key])]
        if key == "bird":
            out.append(_fx("sparkle", RW_BIRD[0], 300, t, 1.2, r=100, n=8))
        else:
            x, y, _k = {"duck": RW_DUCK, "frog": RW_FROG, "fish": RW_FISH}[key]
            out += [_fx("ripples", x, y, t, 1.8, r=110), _fx("droplets", x, y, t, 1.1, n=12)]
        return out

    def notes_fx(sec):
        return [_fx("notes", 90, 520, 0.0, sec["dur"]), _fx("notes", 1190, 520, 0.7, sec["dur"])]

    def wins(sec, word, item=0):
        """[(start, end)] of every sung `word` (plain lower case) in the item of the section."""
        return [(a, b) for pl, a, b in s.word_spans(sec, sec["items"][item]) if pl == word]

    def splash_at(x, y, t):
        return [_fx("droplets", x, y, t, 1.1, n=10, power=0.9), _fx("ripples", x, y, t, 1.8, r=90, n=2)]

    # ---- intro: the title card; the four animals pop in one after the other
    sec = S[0]
    sc = s.scene_for(0, "lake", mood="title", drift=0.0, clouds=False)
    tint = stage(sc, "lake")
    for key in ("duck", "frog", "fish", "bird"):
        critter(sc, key, tint, show=False)
    acts = []
    for i, key in enumerate(("duck", "frog", "fish", "bird")):
        acts += appear(key, 0.5 + 0.8 * i)
    title = ("ROW ROW ROW", "YOUR BOAT") if en else ("KÜREK ÇEK,", "KÜREK ÇEK!")
    sub = "Sing along with Bibi Buzz TV" if en else "Bibi Buzz TV ile şarkı söyle"
    s.finish_scene(sc, dancers=ALL4, hop=1.0, hop_mode="wave", extra=acts + [
        ("fx", "title", 0, 0, {"at": 0.0, "dur": sec["dur"], "lines": title, "sub": sub, "top": 52, "size": 100, "gap": 100, "pill": 38, "sfx": False}),
        _fx("notes", 90, 520, 0.0, sec["dur"]), _fx("notes", 1190, 520, 0.7, sec["dur"]), ("sfx", "tada", {"at": 0.0})])

    present = []                                                       # the animals that have come by
    for n in range(1, 7):
        if n == 6:                                                     # (the dance comes after the bird's verse)
            secD = S[at["Dance"]]
            sc = s.scene_for(at["Dance"], "lake_dusk", drift=0.0, clouds=False)
            tint = stage(sc, "lake_dusk")
            bt = [i * bar for i in range(int(secD["beats"] // 2))]       # the first beat of every bar
            talk = {k: [] for k in A}
            extra, jumps = [], []
            for i, t in enumerate(bt):
                key = RW_ANIMALS[i % 4]["key"]
                a = A[key]
                bx, by = RW_BURST[key][(i // 4) % 2]
                extra.append(("fx", "burst", bx, by, {"at": t, "dur": 0.9, "text": a["big"][lg], "color": a["color"], "size": 0.85, "sfx": False}))
                talk[key].append((t, t + 0.8))
                if key == "fish":
                    sgn = 1 if (i // 4) % 2 == 0 else -1
                    jumps.append((t - 0.1, 1.2, sgn * 170, 200))
                    extra += splash_at(RW_FISH[0] - sgn * 85, RW_FISH[1], t - 0.1) + splash_at(RW_FISH[0] + sgn * 85, RW_FISH[1], t + 1.1)
            critter(sc, "duck", tint, talk=talk["duck"])
            critter(sc, "frog", tint, croak=talk["frog"], hops=[a for a, b in talk["frog"]])
            critter(sc, "fish", tint, jumps=jumps)
            critter(sc, "bird", tint, talk=talk["bird"])
            s.finish_scene(sc, dancers=ALL4, hop=1.0, hop_mode="all", extra=_bar_pumps(s, secD, amount=0.03) + extra + [
                _fx("confetti", 0, 0, 0.0, secD["dur"]), ("sfx", "cheer", {"at": 0.0}), _fx("notes", 90, 520, 0.0, secD["dur"]), _fx("notes", 1190, 520, 0.7, secD["dur"])])
        secA, secB = S[at["Verse %d a" % n]], S[at["Verse %d b" % n]]
        bg = {1: "lake_dawn", 2: "lake", 3: "lake", 4: "lake", 5: "lake_dusk", 6: "lake_night"}[n]
        key = {2: "duck", 3: "frog", 4: "fish", 5: "bird"}.get(n)
        asleep = 1 if n == 6 else 0

        # -- a: 'Row, row, row your boat, gently down the stream.' (the animal of the verse pops in during the long last note)
        sc = s.scene_for(at["Verse %d a" % n], bg, drift=0.03)
        tint = stage(sc, bg, rowing=(n != 6), speed=1.0 if n != 6 else 0.5)
        for k_ in present:
            critter(sc, k_, tint, sleep=asleep)
        extra = notes_fx(secA)
        if key:
            critter(sc, key, tint, show=False)
            extra += appear(key, secA["dur"] - 1.7)
        if n == 6:
            for k_ in RW_ZZZ:
                extra.append(_fx("zzz", RW_ZZZ[k_][0], RW_ZZZ[k_][1], 0.8 + 0.5 * list(RW_ZZZ).index(k_), secA["dur"]))
        s.finish_scene(sc, singers=(ALL4,), dancers=ALL4, hop=2.0, hop_mode="wave", cam=(640, 360, 1.04), size=_rw_size(s, secA), extra=extra)

        # -- b: the sound of the animal and the greeting (or: 'Merrily, merrily ...  Life is but a dream.')
        sc = s.scene_for(at["Verse %d b" % n], bg, drift=0.0)
        tint = stage(sc, bg, rowing=(n != 6), speed=1.0 if n != 6 else 0.5)
        extra = notes_fx(secB)
        if key is None:
            for k_ in present:
                critter(sc, k_, tint, sleep=asleep)
            for (pl, a, b) in s.word_spans(secB, secB["items"][0]):                  # a sparkle at every 'merrily'
                extra.append(_fx("sparkle", 640, 300, a, 1.0, r=220, n=7))
            t_dream = s.word_spans(secB, secB["items"][1])[-1][1]
            if n == 6:
                extra += [_fx("hearts", 640, 330, t_dream, 2.0), _fx("sparkle", 640, 250, t_dream, 2.0, r=320, n=12), ("sfx", "sparkle", {"at": t_dream})]
                for k_ in RW_ZZZ:
                    extra.append(_fx("zzz", RW_ZZZ[k_][0], RW_ZZZ[k_][1], 0.2 + 0.5 * list(RW_ZZZ).index(k_), secB["dur"]))
            else:
                extra += [_fx("hearts", 640, 330, t_dream, 2.0), ("sfx", "ding", {"at": t_dream})]
            s.finish_scene(sc, singers=(ALL4,), dancers=ALL4, hop=1.0, hop_mode="wave", size=_rw_size(s, secB), extra=extra)
        else:
            a = A[key]
            snd = wins(secB, a["snd"][lg], 0)
            words = s.word_spans(secB, secB["items"][1])
            t_name = words[-1][1]                                                    # when the animal's name is sung
            greet = [(t_name, t_name + 0.9)]
            for k_ in present:
                critter(sc, k_, tint)
            kw = {}
            if key in ("duck", "bird"):
                kw = dict(talk=snd + greet)
            elif key == "frog":
                kw = dict(croak=snd + greet, hops=[w[0] + 0.05 for i, w in enumerate(snd) if i % (1 if len(snd) <= 4 else 2) == 0] + [t_name])
            else:
                jumps, sgn = [], 1                                                     # a leap at every second sound, left to right and back again
                for t0, _t1 in snd[::2]:
                    ta = max(0.0, t0 - 0.1)
                    jumps.append((ta, 0.9, sgn * 170, 165))
                    extra += splash_at(RW_FISH[0] - sgn * 85, RW_FISH[1], ta) + splash_at(RW_FISH[0] + sgn * 85, RW_FISH[1], ta + 0.9)
                    sgn = -sgn
                ta = t_name - 0.5                                                      # and a high one over the name of the fish (it starts where the last one ended)
                jumps.append((ta, 1.6, sgn * 170, 230))
                extra += splash_at(RW_FISH[0] - sgn * 85, RW_FISH[1], ta) + splash_at(RW_FISH[0] + sgn * 85, RW_FISH[1], ta + 1.6)
                kw = dict(jumps=jumps)
            critter(sc, key, tint, **kw)
            for i, (t0, _t1) in enumerate(snd):                                       # the sound word bursts out at every sound
                bx, by = RW_BURST[key][i % 2]
                extra.append(("fx", "burst", bx, by + 14 * (i % 3), {"at": max(0.0, t0 - 0.05), "dur": 0.9, "text": a["big"][lg], "color": a["color"],
                                                                  "size": 0.8 if len(a["big"][lg]) <= 6 else 0.72, "sfx": False}))
            hx, hy = RW_HEAD[key]
            extra += [_fx("hearts", hx, hy, t_name, 2.0), ("sfx", "ding", {"at": t_name})]
            s.finish_scene(sc, singers=(ALL4,), dancers=ALL4, hop=1.0, hop_mode="all", size=_rw_size(s, secB), extra=extra)
            present.append(key)

    # ---- outro: thank you, like and subscribe (everybody is awake again)
    sc = s.scene_for(len(S) - 1, "lake", drift=0.0)
    tint = stage(sc, "lake")
    for k_ in ("duck", "frog", "fish", "bird"):
        critter(sc, k_, tint, talk=[(0.5, 1.2), (2.2, 2.9)], croak=[(0.5, 1.2), (2.2, 2.9)], hops=[0.5, 2.2],
                jumps=[(1.0, 1.3, 170, 190)] if k_ == "fish" else ())
    sec = S[-1]
    like, sub_t = 1.7, 3.0
    caption = "Like and subscribe for more songs!" if en else "Daha fazla şarkı için beğen ve abone ol!"
    s.finish_scene(sc, dancers=ALL4, hop=2.0, hop_mode="all", extra=[
        _fx("confetti", 0, 0, sub_t, sec["dur"]), ("fx", "cta", 640, 215, {"at": 0.0, "dur": sec["dur"], "like": like, "sub": sub_t, "sfx": False}),
        _fx("caption", 0, 0, 0.3, sec["dur"], text=caption), _fx("hearts", 330, 380, 1.0, sec["dur"]), _fx("hearts", 950, 380, 1.4, sec["dur"]),
        ("sfx", "pop", {"at": 0.05}), ("sfx", "pop", {"at": 0.3}), ("sfx", "ding", {"at": like + 0.05}), ("sfx", "pop", {"at": like}),
        ("sfx", "ding", {"at": sub_t + 0.05}), ("sfx", "pop", {"at": sub_t}), ("sfx", "sparkle", {"at": sub_t + 0.1})])


# ================================================================================================ the shelf
SPECS = {"twinkle": TWINKLE, "oldmac": OLDMAC, "rainbowsheep": RAINBOWSHEEP, "rowboat": ROWBOAT}
RECIPES = {"twinkle": _twinkle, "oldmac": _oldmac, "rainbowsheep": _rainbowsheep, "rowboat": _rowboat}
QUEUE = ["twinkle", "oldmac", "rainbowsheep", "rowboat"]            # the order in which the songs come out (one a day: curriculum.py)


def build(key, lang="en"):
    """The song `key` in `lang` as a Song (voice, band and pictures are made from its spec)."""
    s = Song(SPECS[key], lang)
    RECIPES[key](s)
    return s
