"""Shared timing for visuals and audio (seconds). Episode 1: 'Bibi and the Colorful Flowers'."""

FPS = 30
DURATION = 150.0

# scene windows (start, end)
S_LOGO = (0.0, 6.0)
S_INTRO = (6.0, 20.0)
S_COLORS = (20.0, 70.0)
S_MIX = (70.0, 100.0)
S_COUNT = (100.0, 125.0)
S_BOUQUET = (125.0, 140.0)
S_BYE = (140.0, 150.0)

# --- intro song: six lines, 2.2 s each, starting 0.8 s into the scene
INTRO_LINES = [
    "Bibi Buzz, Bibi Buzz,",
    "Sun is up, let's go and play!",
    "Bibi Buzz, Bibi Buzz,",
    "Friends are waiting, hip hip hooray!",
    "Buzz buzz buzz, here I come,",
    "Let's explore, it's gonna be fun!",
]
INTRO_LINE_START, INTRO_LINE_DUR = 0.8, 2.2

# --- colour segments: (word, hex colour, start, duration, flower x, lyric1, lyric2, note)
COLOR_SEGS = [
    ("RED", "#E8383D", 20.0, 16.0, 880, "Red, red, red, a flower so red,", "Pretty red flower on my head!", 72),
    ("BLUE", "#3E7BEA", 36.0, 16.0, 880, "Blue, blue, blue, a flower so blue,", "Blue is the sky and the water too!", 76),
    ("YELLOW", "#FFC81E", 52.0, 18.0, 880, "Yellow, yellow, shining so bright,", "Yellow like the sun, what a lovely sight!", 79),
]
SEG_FLOWER_POP = 1.8
SEG_LABEL_T = 3.0
SEG_L1 = (4.5, 4.0)    # start, duration (local seconds)
SEG_L2 = (8.5, 4.0)
SEG_HOP = 11.0

# --- mixing scene (local times)
MIX_LINES = [(9.0, 5.0, "Red and yellow, mix them up,"), (14.0, 5.0, "Look at that, it's orange, wow!")]
MIX_BLOBS_T, MIX_MERGE_T, MIX_ORANGE_T, MIX_TEXT_T, MIX_FLOWER_T = 4.0, 8.0, 11.0, 12.0, 19.0
ORANGE = "#FF8A1F"

# --- counting scene (local times)
COUNT_WORDS = ["ONE", "TWO", "THREE", "FOUR", "FIVE"]
COUNT_T0, COUNT_STEP = 3.0, 3.8
COUNT_COLORS = ["#E8383D", "#FF8A1F", "#FFC81E", "#3E7BEA", "#B058E8"]

# --- bouquet scene
BOUQ_T0, RAINBOW_T0, RAINBOW_T1, CONFETTI_T, PRAISE_T = 2.0, 3.0, 8.0, 9.0, 8.0

# --- goodbye scene
BYE_T, SOON_T, SUB_T = 0.8, 2.6, 4.5


def scene_list():
    """[(name, (start, end))] - every entry is encoded to its own video file."""
    segs = []
    for i, seg in enumerate(COLOR_SEGS):
        end = COLOR_SEGS[i + 1][2] if i + 1 < len(COLOR_SEGS) else S_COLORS[1]
        segs.append((f"color_{seg[0].lower()}", (seg[2], end)))
    return ([("logo", S_LOGO), ("intro", S_INTRO)] + segs +
            [("mix", S_MIX), ("count", S_COUNT), ("bouquet", S_BOUQUET), ("bye", S_BYE)])


def build_events():
    """Sound-effect events: (time, kind, arg)."""
    ev = [(0.4, "pop", 0), (0.7, "pop", 0), (1.0, "pop", 0), (1.9, "sparkle", 0)]
    for i in range(5):
        ev.append((S_INTRO[0] + 2.0 + 0.4 * i, "pop", 0))
    for word, col, st, dur, fx, l1, l2, note in COLOR_SEGS:
        ev += [(st + SEG_FLOWER_POP, "pop", 0), (st + SEG_LABEL_T, "ding", note),
               (st + SEG_HOP, "sparkle", 0)]
    b = S_MIX[0]
    ev += [(b + MIX_BLOBS_T, "pop", 0), (b + MIX_BLOBS_T + 0.4, "pop", 0), (b + MIX_ORANGE_T, "sparkle", 0),
           (b + MIX_ORANGE_T, "pop", 0), (b + MIX_TEXT_T, "ding", 84), (b + MIX_FLOWER_T, "pop", 0)]
    c0 = S_COUNT[0]
    for i in range(5):
        ev += [(c0 + COUNT_T0 + COUNT_STEP * i, "pop", 0), (c0 + COUNT_T0 + COUNT_STEP * i, "ding", 72 + 2 * i)]
    q = S_BOUQUET[0]
    for i in range(5):
        ev.append((q + BOUQ_T0 + 0.3 * i, "pop", 0))
    ev += [(q + RAINBOW_T0, "sparkle", 0), (q + CONFETTI_T, "sparkle", 0)]
    y = S_BYE[0]
    ev += [(y + BYE_T, "pop", 0), (y + SOON_T, "pop", 0), (y + SUB_T, "pop", 0), (y + SUB_T, "sparkle", 0)]
    return sorted(ev)


def build_voice_cues():
    """(time, text) lines for the optional text-to-speech voice-over."""
    cues = [(1.0, "Bibi Buzz T V!")]
    for i, line in enumerate(INTRO_LINES):
        cues.append((S_INTRO[0] + INTRO_LINE_START + INTRO_LINE_DUR * i + 0.1, line))
    for word, col, st, dur, fx, l1, l2, note in COLOR_SEGS:
        cues.append((st + SEG_LABEL_T, f"{word.title()}! {word.title()} flower!"))
        cues.append((st + SEG_L1[0], l1))
        cues.append((st + SEG_L2[0], l2))
    b = S_MIX[0]
    cues += [(b + 4.2, "Red! And yellow!"), (b + MIX_LINES[0][0], MIX_LINES[0][2]),
             (b + MIX_LINES[1][0], MIX_LINES[1][2]), (b + MIX_TEXT_T + 0.2, "Orange!")]
    c0 = S_COUNT[0]
    for i, w in enumerate(COUNT_WORDS):
        cues.append((c0 + COUNT_T0 + COUNT_STEP * i, w.title() + "!"))
    cues.append((c0 + 22.0, "Five beautiful flowers!"))
    cues.append((S_BOUQUET[0] + PRAISE_T, "Great job, friends!"))
    cues.append((S_BYE[0] + BYE_T + 0.1, "Bye bye, friends! See you soon!"))
    return cues
