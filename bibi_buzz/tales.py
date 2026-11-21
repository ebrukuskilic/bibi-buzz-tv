"""The fairy tales (public-domain classics) as story scripts, told in short, simple sentences for ages 2-6."""
import math

from .story import Tale, ease, HEAD

NAR = ("en-US-JennyNeural", "-6%", "+0Hz")
ANA = "en-US-AnaNeural"
GUY = "en-US-GuyNeural"
ARIA = "en-US-AriaNeural"

TAGS = ["fairy tale", "bedtime story", "kids story", "story for kids", "animated story", "story time", "cartoon for kids",
        "Bibi Buzz TV", "children stories", "toddler stories"]


def _intro(t, title_lines, line2, mood="title"):
    sc = t.scene("Welcome", "meadow_open", mood=mood, title="Intro", drift=0.0)
    sc.actor("bibi", "bibi", 250, 600, 1.15).actor("pip", "pip", 1030, 610, 1.05)
    sc.nar("Welcome to Bibi Buzz story time!", ("fx", "title", 0, 0, {"at": 0.0, "dur": 60.0, "lines": title_lines}), ("fx", "sparkle", 640, 420, {"at": 0.6, "dur": 3.0, "r": 330}))
    sc.nar(line2, ("fx", "sparkle", 640, 420, {"at": 0.2, "dur": 3.0, "r": 300}), tail=0.7)
    return sc


def _outro(t, moral, bye="The End. Thank you for watching!", bg="meadow_open", caption=None):
    sc = t.scene("The End", bg, mood="triumph", title="The End", drift=0.0)
    sc.actor("bibi", "bibi", 230, 600, 1.1).actor("pip", "pip", 520, 610, 1.0).actor("mo", "mo", 800, 612, 1.0).actor("lila", "lila", 1060, 604, 1.0)
    sc.nar(moral, ("fx", "caption", 0, 0, {"at": 0.4, "dur": 60.0, "text": caption or moral_caption(moral)}), ("fx", "sparkle", 640, 300, {"at": 0.3, "dur": 4.0, "r": 360}), tail=0.6)
    sc.nar(bye, ("fx", "the_end", 0, 0, {"at": 0.0, "dur": 60.0, "sub": "Bibi Buzz TV"}), ("fx", "confetti", 0, 0, {"at": 0.4, "dur": 60.0}), tail=1.2)
    _cta(t, bg)
    return sc


# YouTube switches the comments, end screens and the subscribe watermark off for videos made for kids, so every tale ends with its
# own "Like / Subscribe" card (buttons drawn by storyprops.cta; the pointer presses them while the narrator says the words).
CTA_LINE = "If you liked this story, please like and subscribe! See you at the next story. Bye bye!"
CTA_CAPTION = "Like and subscribe for more stories!"
# seconds after the scene's narration beat starts (the voice starts 0.25 s later): the pointer presses Like on the end of the word
# "like" / "beğen" and Subscribe on the end of "subscribe" / "abone ol" (measured on a test render with the real voices)
CTA_CLICKS = {"en": (1.95, 2.7), "tr": (2.05, 2.6)}


def _cta(t, bg):
    sc = t.scene("Like and subscribe", bg, mood="happy", drift=0.0)          # no title = no chapter of its own
    sc.actor("bibi", "bibi", 230, 600, 1.1).actor("pip", "pip", 520, 610, 1.0).actor("mo", "mo", 800, 612, 1.0).actor("lila", "lila", 1060, 604, 1.0)
    like, sub = CTA_CLICKS.get(t.lang, CTA_CLICKS["en"])
    sc.nar(CTA_LINE, ("fx", "confetti", 0, 0, {"at": sub, "dur": 60.0}),                      # (drawn first, so the buttons stay on top)
           ("fx", "cta", 640, 215, {"at": 0.0, "dur": 60.0, "like": like, "sub": sub}),
           ("fx", "caption", 0, 0, {"at": 0.3, "dur": 60.0, "text": CTA_CAPTION}),
           ("sfx", "pop", {"at": 0.05}), ("sfx", "pop", {"at": 0.3}), ("sfx", "ding", {"at": like + 0.05}), ("sfx", "pop", {"at": like}),
           ("sfx", "ding", {"at": sub + 0.05}), ("sfx", "pop", {"at": sub}), ("sfx", "sparkle", {"at": sub + 0.1}), tail=1.8)
    return sc


def moral_caption(moral):
    return moral if len(moral) <= 52 else moral.split(". ")[0].rstrip(".!") + "!"


# ================================================================================================ the three little pigs
PIG1 = dict(outfit="#E2574C", hat_kind="straw")
PIG2 = dict(outfit="#3E8EDE", hat_kind="cap", hat_color="#FFD21F")
PIG3 = dict(outfit="#3DB54A", hat_kind="helmet")
MAMA = dict(outfit="#FF8FB0", apron=True, hat_kind="bonnet", skin="#FFC1D2")
WOLF = dict(fur="#8E9AB0", scarf="#E2574C")


def three_little_pigs(lang="en"):
    t = Tale("tale-three-little-pigs", "The Three Little Pigs | Fairy Tale Story for Kids | Bibi Buzz TV",
             "Huff, puff, and a house that will not fall! Watch the classic fairy tale of The Three Little Pigs and the Big Bad Wolf: "
             "one pig builds with straw, one with sticks and one with strong bricks. A gentle, colorful animated story in simple English for toddlers and preschoolers.",
             TAGS + ["three little pigs", "the three little pigs", "big bad wolf", "huff and puff"],
             {"nar": NAR, "mama": (ARIA, "-4%", "+0Hz"), "pig1": (ANA, "-4%", "+18Hz"), "pig2": (ANA, "-4%", "+8Hz"),
              "pig3": (ANA, "-6%", "+0Hz"), "wolf": (GUY, "-10%", "-6Hz")}, lang=lang)
    t.bubble_tint = {"wolf": "#E8ECF6", "pig1": "#FFE3E0", "pig2": "#DDECFF", "pig3": "#DDF5DE", "mama": "#FFE9F2"}
    t.cover = dict(bg="meadow", title=("THE THREE", "LITTLE PIGS"), size=122, gap=122,
                   actors=[("p1", "pig", 170, 702, 1.45, 1, "surprised", PIG1), ("p2", "pig", 395, 708, 1.45, 1, "scared", PIG2),
                           ("p3", "pig", 620, 702, 1.45, 1, "cheer", PIG3), ("wolf", "wolf", 1040, 712, 1.4, -1, "blow", WOLF)])
    _intro(t, ("THE THREE", "LITTLE PIGS"), "Today's story is... The Three Little Pigs!")

    # ---------------------------------------------------------------- 1 mama pig
    s = t.scene("Mama Pig's house", "meadow", mood="happy", title="Mama Pig and her three little pigs")
    s.prop("home", "cottage", 330, 566, 0.95)
    s.actor("mama", "pig", 760, 612, 1.12, face=1, **MAMA)
    s.actor("pig1", "pig", 930, 628, 0.9, face=-1, **PIG1).actor("pig2", "pig", 1040, 636, 0.9, face=-1, **PIG2).actor("pig3", "pig", 1150, 628, 0.9, face=-1, **PIG3)
    s.nar("Once upon a time, a mama pig lived in a cozy little house, with her three little pigs.",
          ("pose", "pig1", "happy"), ("pose", "pig2", "happy"), ("pose", "pig3", "happy"))
    s.nar("The three little pigs grew bigger and bigger, until one day it was time to build houses of their own.",
          ("pose", "pig1", "idle"), ("pose", "pig2", "idle"), ("pose", "pig3", "idle"))
    s.say("mama", "My dear little pigs, it is time to build your own houses!", ("pose", "mama", "wave", {"at": "40%"}))
    s.say("mama", "Work hard, and stay safe. And watch out for the big bad wolf!",
          ("pose", "pig1", "scared", {"at": "75%"}), ("pose", "pig2", "scared", {"at": "75%"}), ("pose", "pig3", "scared", {"at": "75%"}))
    s.say("pig1", "Do not worry, Mama! I will build my house very fast!",
          ("pose", "pig1", "cheer"), ("pose", "pig2", "idle"), ("pose", "pig3", "idle"), ("pose", "mama", "idle"))
    s.nar("So the little pigs hugged their mama, and off they went, down the sunny road.",
          ("pose", "pig1", "idle"), ("pose", "mama", "wave", {"at": "30%"}),
          ("walk", "pig1", 1500, 600, {"at": 0.6, "speed": 135}), ("walk", "pig2", 1540, 610, {"at": 0.9, "speed": 135}), ("walk", "pig3", 1580, 600, {"at": 1.2, "speed": 135}))

    # ---------------------------------------------------------------- 2 straw house
    s = t.scene("The first pig builds a house of straw", "meadow_open", mood="happy", title="The straw house")
    s.prop("b1", "bundle", 420, 640, 1.0, kind="straw")
    s.prop("h1", "house", 930, 600, 1.0, kind="straw", build=0.0)
    s.actor("pig1", "pig", -160, 628, 0.95, **PIG1)
    s.nar("The first little pig walked and walked. Soon, he found a big pile of straw.", ("walk", "pig1", 540, 628, {"speed": 125}))
    s.say("pig1", "Straw is light and easy. I can build my house in no time!", ("pose", "pig1", "cheer"), ("fx", "sparkle", 420, 560, {"at": "30%", "dur": 2.5, "r": 90}))
    s.nar("So he stacked the straw, one bundle at a time, until he had built a little house.",
          ("pose", "pig1", "idle"), ("walk", "pig1", 760, 640, {"at": 0.4, "speed": 150}), ("hide", "b1", {"at": 1.0}),
          ("set", "h1", "build", 1.0, {"at": 1.0, "dur": 4.2}), ("fx", "dust", 930, 600, {"at": 4.6, "dur": 1.0, "size": 1.4}))
    s.nar("Pop! The straw house was ready.", ("pose", "pig1", "cheer"), ("hop", "pig1"), ("fx", "sparkle", 930, 430, {"dur": 2.5, "r": 190}))
    s.say("pig1", "Now I can play all day!", ("pose", "pig1", "jump"), ("fx", "notes", "pig1", 0, {"dur": 3.0}))

    # ---------------------------------------------------------------- 3 stick house
    s = t.scene("The second pig builds a house of sticks", "forest", mood="happy", title="The stick house")
    s.prop("b2", "bundle", 420, 650, 1.0, kind="sticks")
    s.prop("h2", "house", 930, 612, 1.0, kind="sticks", build=0.0)
    s.actor("pig2", "pig", -160, 636, 0.95, **PIG2)
    s.nar("The second little pig walked into the forest. There, he found a pile of sticks.", ("walk", "pig2", 540, 636, {"speed": 125}))
    s.say("pig2", "Sticks are strong, and quick to build with. I will make a house of sticks!", ("pose", "pig2", "cheer"))
    s.nar("Tap, tap, tap! He built his house of sticks.", ("pose", "pig2", "idle"), ("walk", "pig2", 780, 650, {"at": 0.3, "speed": 150}),
          ("hide", "b2", {"at": 0.8}), ("set", "h2", "build", 1.0, {"at": 0.8, "dur": 3.2}), ("fx", "dust", 930, 612, {"at": 3.6, "dur": 1.0, "size": 1.4}))
    s.say("pig2", "My house is done! Time to sing and dance!", ("pose", "pig2", "happy"), ("hop", "pig2", {"at": "50%"}), ("fx", "notes", "pig2", 0, {"dur": 3.5}))

    # ---------------------------------------------------------------- 4 brick house
    s = t.scene("The third pig builds a house of bricks", "meadow", mood="calm", title="The brick house")
    s.prop("b3", "bundle", 420, 640, 1.0, kind="bricks")
    s.prop("h3", "house", 930, 590, 1.0, kind="bricks", build=0.0)
    s.actor("pig3", "pig", -160, 628, 0.95, **PIG3).actor("pig1", "pig", -260, 640, 0.9, show=False, **PIG1).actor("pig2", "pig", -360, 640, 0.9, show=False, **PIG2)
    s.nar("The third little pig was very wise. He found a big pile of bricks.", ("walk", "pig3", 540, 628, {"speed": 125}))
    s.say("pig3", "Bricks are heavy, and this will take a long time. But a brick house is strong!", ("pose", "pig3", "think"))
    s.nar("So he worked, and worked, and worked. Brick by brick, he built his house.",
          ("pose", "pig3", "idle"), ("walk", "pig3", 760, 640, {"at": 0.4, "speed": 150}), ("hide", "b3", {"at": 1.0}),
          ("set", "h3", "build", 1.0, {"at": 1.0, "dur": 6.5}), ("fx", "sweat", "pig3", 0, {"at": 1.2, "dur": 6.0}), ("fx", "dust", 930, 590, {"at": 7.0, "dur": 1.0, "size": 1.4}))
    s.nar("His brothers came by, and they laughed.",
          ("show", "pig1"), ("show", "pig2"), ("walk", "pig1", 520, 640, {"speed": 140}), ("walk", "pig2", 380, 650, {"speed": 140}),
          ("pose", "pig1", "laugh", {"at": 2.2}), ("pose", "pig2", "laugh", {"at": 2.2}), ("pose", "pig3", "idle"))
    s.say("pig1", "Why are you working so hard? Come and play with us!", ("pose", "pig2", "happy"))
    s.say("pig3", "A strong house will keep me safe. I will play when I am done!", ("pose", "pig3", "proud"), ("pose", "pig1", "idle"), ("pose", "pig2", "idle"))
    s.nar("At last, the brick house was finished. It was strong, and warm, and cozy.",
          ("pose", "pig3", "cheer"), ("fx", "sparkle", 930, 430, {"at": 0.4, "dur": 3.5, "r": 200}),
          ("walk", "pig1", -300, 640, {"at": 1.5, "speed": 160}), ("walk", "pig2", -400, 650, {"at": 1.5, "speed": 160}))

    # ---------------------------------------------------------------- 5 the wolf comes: straw
    s = t.scene("The big bad wolf", "meadow_open", mood="sneaky", title="The big bad wolf")
    s.prop("h1", "house", 930, 600, 1.0, kind="straw", build=1.0)
    s.actor("pig1", "pig", 780, 636, 0.95, face=1, **PIG1).actor("wolf", "wolf", -280, 612, 0.88, **WOLF)
    s.nar("One day, a big bad wolf came walking down the road.", ("pose", "pig1", "happy"), ("walk", "wolf", 420, 612, {"speed": 125}), ("pose", "wolf", "sly", {"at": "60%"}))
    s.nar("He saw the little house of straw, and he had a sneaky plan.", ("pose", "pig1", "scared", {"at": "50%"}), ("walk", "wolf", 560, 612, {"speed": 110}))
    s.nar("Knock, knock, knock!", ("sfx", "knock", {"at": 0.15}), ("pose", "wolf", "knock"), ("pose", "pig1", "scared"))
    s.say("wolf", "Little pig, little pig, let me come in!", ("pose", "wolf", "sly"))
    s.say("pig1", "No, no, not by the hair of my chinny chin chin!", ("pose", "pig1", "scared"))
    s.say("wolf", "Then I will huff, and I will puff, and I will blow your house in!", ("pose", "wolf", "sly"), ("cam", 700, 380, 1.12, {"dur": 2.5}))
    s.nar("So the wolf took a big, deep breath. He huffed, and he puffed, and he blew the house down!",
          ("pose", "wolf", "blow", {"at": "25%"}), ("fx", "wind", "wolf", 50, {"at": "30%", "dur": 3.4, "dir": 1, "dx": 70}),
          ("set", "h1", "collapse", 1.0, {"at": "62%", "dur": 1.8, "dir": 1}), ("pose", "pig1", "scared", {"at": "60%"}), ("cam", 640, 360, 1.0, {"at": "75%", "dur": 1.5}), tail=0.8)
    s.say("pig1", "Help! Run, run, run! To my brother's house of sticks!", ("pose", "wolf", "laugh"), ("walk", "pig1", 1500, 628, {"at": 0.9, "speed": 380}))
    s.nar("The little pig ran and ran, as fast as his little legs could go.", ("pose", "wolf", "sly"), ("walk", "wolf", 1500, 612, {"at": 0.4, "speed": 150}))

    # ---------------------------------------------------------------- 6 the wolf comes: sticks
    s = t.scene("The house of sticks", "forest", mood="sneaky", title="The wolf at the stick house")
    s.prop("h2", "house", 930, 612, 1.0, kind="sticks", build=1.0)
    s.actor("pig2", "pig", 800, 650, 0.95, face=1, **PIG2).actor("pig1", "pig", -200, 640, 0.95, **PIG1).actor("wolf", "wolf", -300, 620, 0.88, **WOLF)
    s.nar("The first little pig ran into the forest, all the way to the house of sticks.", ("walk", "pig1", 650, 640, {"speed": 330}))
    s.say("pig1", "Brother, brother! The big bad wolf is coming!", ("pose", "pig1", "scared"), ("pose", "pig2", "surprised"))
    s.say("pig2", "Do not worry. My house is strong. Stay with me!", ("pose", "pig1", "scared"), ("pose", "pig2", "proud"))
    s.nar("But the big bad wolf had followed them.", ("walk", "wolf", 380, 620, {"speed": 125}), ("pose", "wolf", "sly", {"at": "50%"}), ("pose", "pig2", "scared"), ("pose", "pig1", "scared"))
    s.say("wolf", "Little pigs, little pigs, let me come in!", ("pose", "wolf", "sly"))
    s.say("pig2", "No, no, not by the hair of our chinny chin chins!", ("pose", "pig2", "scared"))
    s.say("wolf", "Then I will huff, and I will puff, and I will blow your house in!", ("cam", 700, 390, 1.12, {"dur": 2.5}))
    s.nar("The wolf huffed, and he puffed, and he blew... and the house of sticks fell down, too!",
          ("pose", "wolf", "blow", {"at": "20%"}), ("fx", "wind", "wolf", 50, {"at": "25%", "dur": 3.4, "dir": 1, "dx": 70}),
          ("set", "h2", "collapse", 1.0, {"at": "66%", "dur": 1.8, "dir": 1}), ("cam", 640, 360, 1.0, {"at": "78%", "dur": 1.5}), tail=0.7)
    s.say("pig2", "Quick! Run to our brother's house of bricks!", ("pose", "wolf", "laugh"), ("walk", "pig2", 1500, 650, {"at": 0.6, "speed": 380}), ("walk", "pig1", 1560, 640, {"at": 0.7, "speed": 380}))

    # ---------------------------------------------------------------- 7 the wolf comes: bricks
    s = t.scene("The house of bricks", "meadow", mood="sneaky", title="The wolf at the brick house")
    s.prop("h3", "house", 930, 590, 1.0, kind="bricks", build=1.0)
    s.actor("pig3", "pig", 760, 640, 0.95, face=-1, **PIG3).actor("pig1", "pig", -200, 640, 0.95, **PIG1).actor("pig2", "pig", -300, 650, 0.95, **PIG2)
    s.actor("wolf", "wolf", -300, 618, 0.88, zy=900, flat=True, **WOLF)
    s.nar("The two little pigs ran as fast as they could, all the way to the house of bricks.", ("walk", "pig1", 640, 640, {"speed": 330}), ("walk", "pig2", 540, 650, {"speed": 330}))
    s.say("pig3", "Come in, come in! Hurry!", ("pose", "pig1", "scared"), ("pose", "pig2", "scared"), ("set", "h3", "door", 1.0, {"dur": 0.8}), ("walk", "pig1", 930, 590, {"at": "40%", "speed": 220}), ("walk", "pig2", 930, 590, {"at": "50%", "speed": 220}))
    s.nar("They all ran inside, and they locked the door tight.",
          ("hide", "pig1", {"at": 0.1}), ("hide", "pig2", {"at": 0.4}), ("walk", "pig3", 930, 590, {"speed": 200}), ("hide", "pig3", {"at": 1.4}), ("set", "h3", "door", 0.0, {"at": 1.5, "dur": 0.6}))
    s.nar("Soon, the big bad wolf came to the brick house.", ("walk", "wolf", 470, 618, {"speed": 130}), ("pose", "wolf", "sly", {"at": "60%"}))
    s.say("wolf", "Little pigs, little pigs, let me come in!", ("pose", "wolf", "sly"), ("sfx", "knock", {"at": -0.3}))
    s.say("pig3", "No, no, not by the hair of our chinny chin chins!")
    s.say("wolf", "Then I will huff, and I will puff, and I will blow your house in!", ("cam", 700, 380, 1.12, {"dur": 2.5}))
    s.nar("So the wolf huffed, and he puffed. He huffed, and he puffed some more. But the brick house did not move at all!",
          ("pose", "wolf", "blow", {"at": "10%"}), ("fx", "wind", "wolf", 50, {"at": "12%", "dur": 6.0, "dir": 1, "dx": 70}),
          ("set", "h3", "shake", 1.0, {"at": "20%", "dur": 3.0}), ("set", "h3", "shake", 0.0, {"at": "75%", "dur": 0.1}),
          ("pose", "wolf", "dizzy", {"at": "85%"}), ("fx", "dizzy", "wolf", 0, {"at": "85%", "dur": 4.0}), tail=0.8)
    s.say("wolf", "Oh my! I am so tired. But I have a new plan. I will climb down the chimney!", ("pose", "wolf", "sly"), ("cam", 640, 360, 1.0, {"dur": 1.5}))
    s.nar("And the wolf climbed up, up, up, onto the roof of the brick house.", ("pose", "wolf", "jump", {"at": "20%"}), ("move", "wolf", 1034, 300, {"at": "20%", "dur": 1.6}), ("fx", "mark", "wolf", 0, {"at": "70%", "dur": 2.0, "text": "!"}))

    # ---------------------------------------------------------------- 8 inside
    s = t.scene("The clever pigs and the wolf", "room", mood="tense", title="The wolf in the chimney")
    s.prop("fire", "fireplace", 640, 640, 1.15)
    s.actor("pig1", "pig", 280, 640, 0.95, face=1, **PIG1).actor("pig2", "pig", 420, 650, 0.95, face=1, **PIG2).actor("pig3", "pig", 960, 640, 0.95, face=-1, **PIG3)
    s.actor("wolf", "wolf", 640, -330, 0.9, show=False, **WOLF)
    s.nar("Inside the house, the clever pigs heard a noise on the roof.", ("pose", "pig1", "surprised"), ("pose", "pig2", "surprised"), ("pose", "pig3", "surprised"))
    s.say("pig3", "Quick! He is coming down the chimney! Keep the pot of water bubbling!", ("pose", "pig3", "proud"))
    s.say("pig2", "The water is hot, hot, hot!", ("pose", "pig2", "cheer"), ("pose", "pig1", "cheer"), ("fx", "steam", 640, 440, {"dur": 8.0}))
    s.nar("Down, down, down the chimney slid the wolf... and splash! Right into the pot!",
          ("show", "wolf", {"at": "20%"}), ("pose", "wolf", "scared", {"at": "20%"}), ("move", "wolf", 640, 540, {"at": "30%", "dur": 0.9}), ("hide", "wolf", {"at": "55%"}),
          ("fx", "splash", 640, 545, {"at": "55%", "dur": 1.2}), ("fx", "burst", 640, 300, {"at": "55%", "dur": 2.0, "text": "SPLASH!"}), tail=0.6)
    s.say("wolf", "Yowwww! That is hot!", ("show", "wolf"), ("move", "wolf", 740, 640, {"dur": 0.5}), ("pose", "wolf", "scared"), ("fx", "sweat", "wolf", 0, {"dur": 2.5}), ("pose", "pig1", "laugh"), ("pose", "pig2", "laugh"))
    s.nar("The wolf jumped out of the pot, and he ran away, far over the hills. And he never came back again!",
          ("pose", "pig3", "cheer"), ("walk", "wolf", 1600, 640, {"at": 0.4, "speed": 520}), ("fx", "speed", "wolf", 0, {"at": 0.5, "dur": 2.2, "dir": 1}))

    # ---------------------------------------------------------------- 9 happy ending
    s = t.scene("Happily ever after", "meadow_dusk", mood="triumph", title="Happily ever after")
    s.prop("h3", "house", 930, 590, 1.0, kind="bricks", build=1.0)
    s.prop("pie", "pie", 520, 700, 1.3)
    s.actor("pig1", "pig", 360, 630, 0.95, face=1, **PIG1).actor("pig2", "pig", 560, 650, 0.95, face=1, **PIG2).actor("pig3", "pig", 760, 640, 0.95, face=-1, **PIG3)
    s.nar("The three little pigs were safe and sound. They had a big party in the strong brick house.", ("pose", "pig1", "cheer"), ("pose", "pig2", "cheer"), ("pose", "pig3", "cheer"), ("fx", "confetti", 0, 0, {"dur": 20.0}))
    s.say("pig1", "I am sorry I did not work hard, brother!", ("pose", "pig1", "sad"), ("pose", "pig2", "idle"), ("pose", "pig3", "idle"))
    s.say("pig3", "That is all right. Now we all have a strong, safe home!", ("pose", "pig3", "happy"), ("pose", "pig1", "happy"), ("fx", "hearts", "pig3", 0, {"dur": 3.5}))
    s.say("pig2", "Hooray for the brick house! Let us all have some pie!", ("pose", "pig2", "jump"), ("pose", "pig1", "jump"), ("pose", "pig3", "jump"))
    s.nar("And they all lived happily ever after.", ("pose", "pig1", "happy"), ("pose", "pig2", "happy"), ("pose", "pig3", "happy"), ("fx", "sparkle", 560, 460, {"dur": 4.0, "r": 330}), tail=0.8)

    _outro(t, "Remember, little ones: if you work hard and plan well, you can build something strong!", caption="Work hard, plan well, build strong!")
    return t


# ================================================================================================ the tortoise and the hare
BEAR_J = dict(fur="#8B5A2B", extra="tie", outfit="#E2574C", hat_kind="cap", hat_color="#3E8EDE")


def tortoise_and_hare(lang="en"):
    t = Tale("tale-tortoise-and-hare", "The Tortoise and the Hare | Fairy Tale Story for Kids | Bibi Buzz TV",
             "Slow and steady wins the race! Watch the classic fable of The Tortoise and the Hare: a speedy hare boasts that nobody can beat him, "
             "but a slow, kind tortoise has a plan. A colorful animated story in simple English for toddlers and preschoolers.",
             TAGS + ["tortoise and the hare", "the tortoise and the hare", "slow and steady wins the race", "aesop fables"],
             {"nar": NAR, "hare": ("en-US-EricNeural", "+2%", "+6Hz"), "tort": ("en-US-ChristopherNeural", "-16%", "-4Hz"),
              "bear": (GUY, "-8%", "-10Hz"), "pig1": (ANA, "-4%", "+18Hz"), "pig2": (ANA, "-4%", "+8Hz"), "pig3": (ANA, "-6%", "+0Hz")}, lang=lang)
    t.bubble_tint = {"hare": "#FFF0DC", "tort": "#E2F7DC", "bear": "#EADBC8", "pig1": "#FFE3E0", "pig2": "#DDECFF", "pig3": "#DDF5DE"}
    t.cover = dict(bg="race", title=("THE TORTOISE", "AND THE HARE"), size=106, gap=104,
                   props=[("fin", "finish_line", 900, 650, 0.9, {})],
                   actors=[("hare", "hare", 300, 708, 1.34, 1, "sly", {}), ("tort", "tortoise", 880, 706, 2.05, -1, "happy", {"hold": "medal"})])
    _intro(t, ("THE TORTOISE", "AND THE HARE"), "Today's story is... The Tortoise and the Hare!")

    # ---------------------------------------------------------------- 1 boastful hare
    s = t.scene("A boastful hare", "meadow_open", mood="happy", title="A boastful hare")
    s.actor("bear", "bear", 110, 618, 0.95, face=1, **BEAR_J).actor("pig1", "pig", 255, 636, 0.85, face=1, **PIG1).actor("pig2", "pig", 375, 644, 0.85, face=1, **PIG2)
    s.actor("hare", "hare", 600, 620, 1.0, face=-1).actor("tort", "tortoise", 1450, 640, 1.15, face=-1)
    s.nar("Once upon a time, in a sunny green meadow, there lived a very fast hare.", ("pose", "hare", "proud"))
    s.say("hare", "I am the fastest animal in the whole wide world!", ("pose", "hare", "cheer"), ("hop", "hare", {"at": "60%"}))
    s.say("hare", "Nobody can run as fast as me! Zoom, zoom, zoom!", ("walk", "hare", 420, 620, {"speed": 520, "keepface": True}), ("walk", "hare", 560, 620, {"speed": 520}), ("fx", "dust", 500, 620, {"at": 0.2, "dur": 1.0}))
    s.nar("In the same meadow, there lived a slow and gentle tortoise.", ("pose", "hare", "idle"), ("face", "hare", -1, {"at": 1.6}), ("walk", "tort", 1070, 640, {"fit": True, "pose": "walk"}))
    s.say("tort", "Hello, Hare. I may be slow, but I never give up.", ("pose", "tort", "happy"), ("pose", "hare", "sly"))
    s.say("hare", "Ha ha ha! You? Slow, slow tortoise! You could never beat me!", ("pose", "hare", "laugh"), ("pose", "pig1", "surprised"), ("pose", "pig2", "surprised"), ("pose", "tort", "idle"))
    s.say("tort", "Then let us have a race, and we will see.", ("pose", "tort", "proud"), ("pose", "hare", "idle"))
    s.say("hare", "A race? That is easy! I accept!", ("pose", "hare", "cheer"), ("hop", "hare", {"at": "50%"}))
    s.nar("All the animals came to watch the big race.", ("pose", "pig1", "cheer"), ("pose", "pig2", "cheer"), ("pose", "bear", "wave"), ("pose", "tort", "idle"), ("pose", "hare", "proud"))

    # ---------------------------------------------------------------- 2 ready set go
    s = t.scene("Ready, set, go!", "race", mood="happy", title="Ready, set, go!")
    s.prop("start", "start_line", 700, 640, 0.8)
    s.actor("bear", "bear", 280, 640, 0.9, face=1, hold="flag", **BEAR_J).actor("pig1", "pig", 120, 660, 0.8, face=1, **PIG1)
    s.actor("hare", "hare", 600, 646, 0.95, face=1).actor("tort", "tortoise", 700, 664, 1.1, face=1)
    s.nar("The race began at the starting line.", ("pose", "hare", "sly"), ("pose", "pig1", "cheer"))
    s.say("bear", "On your mark... get set...", ("sfx", "beep3", {"at": 0.0}), ("pose", "bear", "wave"), ("pose", "hare", "idle"))
    s.say("bear", "GO!", ("pose", "bear", "cheer"), ("fx", "burst", 640, 250, {"dur": 1.6, "text": "GO!", "color": "#3DB54A"}), tail=0.2)
    s.nar("Whoosh! The hare shot off like a rocket. And the tortoise? He took one slow step, and then another.",
          ("walk", "hare", 1600, 646, {"speed": 700}), ("fx", "dust", 640, 646, {"dur": 1.0}), ("fx", "speed", "hare", 0, {"dur": 1.2, "dir": 1}),
          ("walk", "tort", 900, 664, {"fit": True, "pose": "walk"}), ("pose", "bear", "cheer"))

    # ---------------------------------------------------------------- 3 hare dashes ahead
    s = t.scene("The hare dashes ahead", "race", world=2800, mood="chase", title="The hare dashes ahead", drift=0.0)
    s.actor("hare", "hare", 200, 646, 1.0, face=1)
    s.wait(0.1, ("follow", "hare", 260, 1.0, {"dur": 3600}))
    s.nar("The hare ran fast, faster, fastest! The wind blew his ears back.", ("walk", "hare", 1500, 646, {"fit": True, "pose": "run"}), ("fx", "speed", "hare", 0, {"dur": 9.0, "dir": 1}))
    s.nar("Soon, he was far, far ahead of the tortoise.", ("walk", "hare", 2300, 646, {"fit": True, "pose": "run"}), ("fx", "speed", "hare", 0, {"dur": 9.0, "dir": 1}))
    s.say("hare", "I am so far ahead! The tortoise is just a tiny dot!", ("face", "hare", -1), ("pose", "hare", "laugh"), ("fx", "dust", 2300, 646, {"dur": 1.0}))
    s.say("hare", "I have plenty of time for a little nap.", ("pose", "hare", "sly"), ("face", "hare", 1))

    # ---------------------------------------------------------------- 4 the nap
    s = t.scene("A little nap", "race", mood="calm", title="A little nap")
    s.prop("tree", "bigtree", 900, 620, 1.0)
    s.actor("hare", "hare", -150, 650, 1.0, face=1, zy=700)
    s.nar("The hare found a big, shady tree. He yawned a great big yawn.", ("walk", "hare", 790, 650, {"fit": True, "pose": "walk"}), ("sfx", "yawn", {"at": "60%"}))
    s.say("hare", "I will rest my eyes for just one little minute.", ("pose", "hare", "tired"), ("face", "hare", 1))
    s.nar("But the hare fell fast asleep. Zzzzz.", ("pose", "hare", "nap"), ("fx", "zzz", "hare", 0, {"dur": 8.0}), ("cam", 760, 420, 1.14, {"dur": 3.0}))
    s.wait(3.5, ("fx", "zzz", "hare", 0, {"dur": 6.0}), ("sfx", "snore", {"at": 0.2}))

    # ---------------------------------------------------------------- 5 slow and steady
    s = t.scene("Slow and steady", "race", world=3600, mood="calm", title="Slow and steady", drift=0.0)
    s.prop("tree", "bigtree", 1560, 620, 1.0)
    s.actor("hare", "hare", 1480, 650, 1.0, face=1, zy=640).actor("tort", "tortoise", 300, 668, 1.2, face=1)
    s.wait(0.1, ("pose", "hare", "nap"), ("follow", "tort", 220, 1.0, {"dur": 3600}), ("fx", "zzz", "hare", 0, {"dur": 90.0}))
    s.nar("Meanwhile, the tortoise kept on walking. Step, step, step.", ("walk", "tort", 700, 668, {"fit": True, "pose": "walk"}))
    s.say("tort", "Slow and steady. Slow and steady.", ("walk", "tort", 1000, 668, {"fit": True, "pose": "walk"}), ("pose", "tort", "happy"))
    s.nar("The sun was hot, and the road was long. But the tortoise did not stop.", ("walk", "tort", 1300, 668, {"fit": True, "pose": "walk"}), ("fx", "sweat", "tort", 0, {"dur": 6.0}))
    s.nar("Step by step, he came to the big tree. And there was the hare, fast asleep!", ("walk", "tort", 1400, 668, {"fit": True, "pose": "walk"}), ("sfx", "snore", {"at": "70%"}))
    s.say("tort", "Shh... Let us not wake him.", ("walk", "tort", 1580, 668, {"fit": True, "pose": "walk"}))
    s.nar("The tortoise tiptoed past the sleeping hare, and he kept going, and going, and going.", ("walk", "tort", 2300, 668, {"fit": True, "pose": "walk"}))
    s.nar("Far, far away, he could see the finish line.", ("walk", "tort", 2900, 668, {"fit": True, "pose": "walk"}), ("fx", "sparkle", 3300, 420, {"at": "30%", "dur": 4.0, "r": 120}))
    s.prop("fin", "finish_line", 3320, 690, 0.8)

    # ---------------------------------------------------------------- 6 hare wakes
    s = t.scene("The hare wakes up", "race", mood="tense", title="The hare wakes up")
    s.prop("tree", "bigtree", 900, 620, 1.0)
    s.actor("hare", "hare", 790, 650, 1.0, face=1, zy=700)
    s.nar("At last, the hare woke up. He stretched, and he rubbed his eyes.", ("pose", "hare", "nap"), ("pose", "hare", "idle", {"at": "50%"}), ("sfx", "yawn", {"at": 0.1}))
    s.say("hare", "Oh no! What time is it? Where is the tortoise?", ("pose", "hare", "surprised"), ("fx", "mark", "hare", 0, {"dur": 2.5, "text": "?"}))
    s.nar("The hare looked far down the road, and he saw the tortoise, almost at the finish line!", ("pose", "hare", "scared"), ("fx", "mark", "hare", 0, {"at": "50%", "dur": 2.5, "text": "!"}))
    s.say("hare", "I must run! Faster, faster, faster!", ("walk", "hare", 1700, 650, {"at": "72%", "speed": 800}), ("fx", "speed", "hare", 0, {"at": "72%", "dur": 2.0, "dir": 1}), ("fx", "dust", 790, 650, {"at": "72%", "dur": 1.0}))

    # ---------------------------------------------------------------- 7 finish line
    s = t.scene("The finish line", "race", mood="chase", title="The finish line")
    s.prop("fin", "finish_line", 620, 640, 0.8)
    s.actor("bear", "bear", 1010, 628, 0.9, face=-1, **BEAR_J).actor("pig1", "pig", 1110, 650, 0.85, face=-1, **PIG1).actor("pig2", "pig", 1195, 660, 0.85, face=-1, **PIG2)
    s.actor("tort", "tortoise", -200, 664, 1.1, face=1).actor("hare", "hare", -400, 650, 0.95, face=1)
    s.nar("Everybody cheered as the tortoise came closer to the finish line.", ("walk", "tort", 380, 664, {"fit": True, "pose": "walk"}), ("pose", "pig1", "cheer"), ("pose", "pig2", "cheer"), ("pose", "bear", "cheer"))
    s.say("pig1", "Go, Tortoise, go!", ("walk", "tort", 470, 664, {"fit": True, "pose": "walk"}))
    s.say("pig2", "You can do it!", ("walk", "tort", 540, 664, {"fit": True, "pose": "walk"}))
    s.nar("Just then, the hare came running, as fast as the wind!", ("walk", "hare", 330, 650, {"at": 0.2, "speed": 800, "pose": "run"}), ("walk", "tort", 590, 664, {"fit": True, "pose": "walk"}), ("pose", "pig1", "scared"), ("pose", "pig2", "scared"), ("fx", "speed", "hare", 0, {"at": 0.2, "dur": 1.5, "dir": 1}))
    s.nar("But it was too late! The tortoise crossed the finish line first!", ("walk", "tort", 800, 664, {"speed": 140}), ("set", "fin", "tape", 1.0, {"at": 0.9, "dur": 0.6}), ("fx", "confetti", 0, 0, {"at": 0.9, "dur": 30.0}), ("pose", "pig1", "cheer"), ("pose", "pig2", "cheer"), ("walk", "hare", 560, 650, {"speed": 300}))
    s.nar("The hare skidded to a stop. He had lost the race.", ("pose", "hare", "sad"), ("fx", "dust", "hare", 0, {"dur": 1.0}), ("pose", "tort", "cheer"), tail=0.8)

    # ---------------------------------------------------------------- 8 winner
    s = t.scene("The winner", "meadow_open", mood="triumph", title="The winner")
    s.actor("tort", "tortoise", 660, 650, 1.35, face=-1, hold="medal").actor("hare", "hare", 290, 630, 1.0, face=1)
    s.actor("bear", "bear", 960, 622, 0.95, face=-1, **BEAR_J).actor("pig1", "pig", 1090, 640, 0.85, face=-1, **PIG1).actor("pig2", "pig", 1190, 650, 0.85, face=-1, **PIG2)
    s.say("bear", "The winner of the race is... the tortoise!", ("pose", "tort", "cheer", {"at": "70%"}), ("pose", "hare", "sad"), ("fx", "sparkle", 660, 420, {"at": "70%", "dur": 4.0, "r": 200}), ("sfx", "tada", {"at": "70%"}))
    s.say("hare", "I am sorry I laughed at you, Tortoise. You are wonderful.", ("pose", "hare", "sad"), ("pose", "tort", "happy"), ("pose", "bear", "idle"))
    s.say("tort", "Thank you, Hare. Let us be friends.", ("pose", "tort", "proud"), ("pose", "hare", "happy"), ("fx", "hearts", "tort", 0, {"at": "50%", "dur": 4.0}))
    s.say("tort", "I just kept going, and I never gave up.", ("pose", "tort", "happy"), ("pose", "hare", "idle"))
    s.nar("From that day on, the hare never boasted again. And the two animals were the best of friends.", ("pose", "hare", "cheer"), ("pose", "tort", "happy"), ("pose", "pig1", "cheer"), ("pose", "pig2", "cheer"), ("fx", "sparkle", 660, 420, {"dur": 5.0, "r": 330}), tail=0.8)

    _outro(t, "Remember, little ones: slow and steady wins the race. Never give up!", caption="Slow and steady wins the race!")
    return t


# ================================================================================================ goldilocks and the three bears
PAPA = dict(fur="#7A4A25", extra="tie", outfit="#3E8EDE")
MAMA_B = dict(fur="#A8683A", hat_kind="bonnet")
BABY = dict(fur="#C98A52", hat_kind="cap", hat_color="#FFD21F")
GOLD = dict(dress="#6CB7FF", hair="#FFC83D")


def goldilocks(lang="en"):
    t = Tale("tale-goldilocks", "Goldilocks and the Three Bears | Fairy Tale Story for Kids | Bibi Buzz TV",
             "Too hot, too cold, just right! Watch the classic fairy tale of Goldilocks and the Three Bears: a curious little girl finds a cozy cottage, "
             "tries the porridge, the chairs and the beds, and meets Papa Bear, Mama Bear and Baby Bear. A colorful animated story in simple English for toddlers and preschoolers.",
             TAGS + ["goldilocks and the three bears", "goldilocks", "three bears", "too hot too cold just right"],
             {"nar": NAR, "gold": (ANA, "-4%", "+6Hz"), "papa": (GUY, "-10%", "-14Hz"), "mama": (ARIA, "-4%", "+0Hz"), "baby": (ANA, "-2%", "+22Hz")}, lang=lang)
    t.bubble_tint = {"gold": "#FFF5C8", "papa": "#DCE9FF", "mama": "#FFE3EE", "baby": "#FFF0C8"}
    t.cover = dict(bg="meadow", title=("GOLDILOCKS", "& THE 3 BEARS"), size=112, gap=112,
                   actors=[("gold", "girl", 300, 706, 1.6, 1, "surprised", dict(GOLD, hold="basket")), ("papa", "bear", 700, 710, 1.42, -1, "happy", PAPA),
                           ("mama", "bear", 915, 714, 1.28, -1, "happy", MAMA_B), ("baby", "bear", 1100, 716, 1.0, -1, "cheer", BABY)])
    _intro(t, ("GOLDILOCKS", "& THE 3 BEARS"), "Today's story is... Goldilocks and the Three Bears!")

    # ---------------------------------------------------------------- 1 the bears' cottage
    s = t.scene("The three bears", "meadow", mood="happy", title="The three bears")
    s.prop("home", "cottage", 340, 566, 1.0, wall="#FFE9C8", roof="#8E5A3A")
    s.actor("papa", "bear", 760, 620, 1.2, face=-1, **PAPA).actor("mama", "bear", 930, 630, 1.0, face=-1, **MAMA_B).actor("baby", "bear", 1080, 640, 0.72, face=-1, **BABY)
    s.nar("Once upon a time, three bears lived in a little house in the woods. There was Papa Bear, Mama Bear, and Baby Bear.",
          ("pose", "papa", "wave", {"at": "34%"}), ("pose", "papa", "idle", {"at": "50%"}), ("pose", "mama", "wave", {"at": "58%"}), ("pose", "mama", "idle", {"at": "74%"}), ("pose", "baby", "wave", {"at": "82%"}))
    s.say("mama", "Breakfast is ready, my dears!", ("pose", "mama", "happy"), ("pose", "baby", "idle"))
    s.say("papa", "Oh dear. This porridge is much too hot to eat!", ("pose", "papa", "blow"), ("fx", "steam", "papa", 0, {"dur": 4.0}))
    s.say("baby", "Let us go for a walk, while it cools down!", ("pose", "papa", "idle"), ("pose", "baby", "cheer"), ("hop", "baby", {"at": "50%"}))
    s.nar("So the three bears went for a walk in the woods.", ("pose", "baby", "idle"), ("walk", "papa", 1500, 620, {"at": 0.5, "speed": 130}), ("walk", "mama", 1500, 630, {"at": 0.7, "speed": 130}), ("walk", "baby", 1500, 640, {"at": 0.9, "speed": 130}))

    # ---------------------------------------------------------------- 2 goldilocks in the forest
    s = t.scene("Goldilocks", "forest", mood="calm", title="Goldilocks")
    s.actor("gold", "girl", -150, 636, 1.0, hold="basket", **GOLD)
    s.nar("Just then, a little girl named Goldilocks came walking through the forest.", ("walk", "gold", 540, 636, {"fit": True, "pose": "walk"}), ("fx", "leaves", 0, 0, {"dur": 60.0}))
    s.say("gold", "What a lovely day! I will pick some pretty flowers.", ("pose", "gold", "happy"), ("fx", "sparkle", "gold", 0, {"dur": 3.5, "r": 100}))
    s.nar("She walked and walked, until she saw a little house.", ("pose", "gold", "idle"), ("walk", "gold", 1250, 636, {"fit": True, "pose": "walk"}))

    # ---------------------------------------------------------------- 3 the door
    s = t.scene("A little house", "meadow", mood="calm", title="A little house")
    s.prop("home", "cottage", 900, 566, 1.05, wall="#FFE9C8", roof="#8E5A3A")
    s.actor("gold", "girl", -150, 628, 1.0, hold="basket", **GOLD)
    s.nar("Goldilocks went up to the little door. Knock, knock, knock!", ("walk", "gold", 835, 628, {"dur": 1.5}), ("sfx", "knock", {"at": "55%"}), ("pose", "gold", "knock", {"at": "55%"}))
    s.say("gold", "Hello? Is anybody home?", ("pose", "gold", "idle"))
    s.nar("But nobody answered. The door was open, just a little bit.", ("set", "home", "door", 1.0, {"at": "50%", "dur": 1.2}), ("pose", "gold", "think"))
    s.say("gold", "I will just take a tiny peek inside.", ("pose", "gold", "sly"), ("hold", "gold", None))
    s.nar("And she walked right in.", ("walk", "gold", 905, 606, {"dur": 0.9}), ("hide", "gold", {"at": 0.95}), ("set", "home", "door", 0.0, {"at": 1.4, "dur": 0.6}))

    # ---------------------------------------------------------------- 4 the porridge
    s = t.scene("Three bowls of porridge", "room", mood="happy", title="Three bowls of porridge")
    s.prop("tbl", "table", 700, 650, 1.0)
    s.actor("gold", "girl", -100, 660, 1.0, **GOLD)
    s.nar("Inside, there was a big table, and on the table, three bowls of porridge.", ("walk", "gold", 330, 660, {"fit": True, "pose": "walk"}), ("fx", "steam", 580, 520, {"dur": 40.0}), ("fx", "steam", 700, 520, {"dur": 40.0}), ("fx", "steam", 808, 520, {"dur": 40.0}))
    s.say("gold", "Yum! I am so hungry!", ("pose", "gold", "happy"), ("walk", "gold", 440, 660, {"at": "60%", "speed": 120}), ("hold", "gold", "spoon", {"at": "60%"}))
    s.nar("First, she tried the big bowl.", ("pose", "gold", "eat"), ("sfx", "munch", {"at": 0.5}))
    s.say("gold", "Ouch! This porridge is too hot!", ("pose", "gold", "scared"), ("fx", "sweat", "gold", 0, {"dur": 3.0}))
    s.nar("Then, she tried the middle bowl.", ("pose", "gold", "eat"), ("walk", "gold", 560, 660, {"speed": 150}), ("sfx", "munch", {"at": 1.2}))
    s.say("gold", "Brrr! This porridge is too cold!", ("pose", "gold", "sad"))
    s.nar("Then, she tried the little bowl.", ("pose", "gold", "eat"), ("walk", "gold", 660, 660, {"speed": 150}), ("sfx", "munch", {"at": 1.0}))
    s.say("gold", "Mmm! This porridge is just right!", ("pose", "gold", "happy"), ("fx", "sparkle", "gold", 0, {"dur": 3.0, "r": 110}))
    s.nar("And she ate it all up!", ("pose", "gold", "eat"), ("set", "tbl", "bowl3", 0.0, {"at": 0.4, "dur": 2.0}), ("sfx", "gulp", {"at": 2.0}), tail=0.6)

    # ---------------------------------------------------------------- 5 the chairs
    s = t.scene("Three chairs", "room", mood="happy", title="Three chairs")
    s.prop("c1", "chair", 380, 650, 1.0, size="big").prop("c2", "chair", 640, 650, 1.0, size="mid").prop("c3", "chair", 900, 650, 1.0, size="small", broken=0.0)
    s.actor("gold", "girl", -100, 676, 1.0, zy=800, **GOLD)
    s.nar("Next, Goldilocks saw three chairs by the window.", ("walk", "gold", 220, 676, {"fit": True, "pose": "walk"}))
    s.say("gold", "I am so tired. I think I will sit down.", ("pose", "gold", "tired"))
    s.nar("First, she sat in the big chair.", ("walk", "gold", 380, 668, {"dur": 1.0}), ("pose", "gold", "sit@117", {"at": "72%"}))
    s.say("gold", "Oh, this chair is too hard!", ("pose", "gold", "sit@117+sad"))
    s.nar("Then, she sat in the middle chair.", ("pose", "gold", "idle"), ("walk", "gold", 640, 668, {"at": 0.35, "dur": 1.2}), ("pose", "gold", "sit@84", {"at": "78%"}))
    s.say("gold", "Oh, this chair is too soft!", ("pose", "gold", "sit@84+sad"))
    s.nar("Then, she sat in the little chair.", ("pose", "gold", "idle"), ("walk", "gold", 900, 668, {"at": 0.35, "dur": 1.2}), ("pose", "gold", "sit@55", {"at": "78%"}))
    s.say("gold", "Ahh! This chair is just right!", ("pose", "gold", "sit@55+happy"))
    s.nar("But oh no! Crack! The little chair broke into pieces!", ("set", "c3", "broken", 1.0, {"at": "55%", "dur": 0.5}), ("fx", "burst", 930, 290, {"at": "55%", "dur": 2.0, "text": "CRACK!"}), ("pose", "gold", "dizzy", {"at": "62%"}), ("fx", "dizzy", "gold", 0, {"at": "62%", "dur": 3.0}))
    s.say("gold", "Oh dear! I am so sorry, little chair.", ("pose", "gold", "sad"), tail=0.6)

    # ---------------------------------------------------------------- 6 the beds
    s = t.scene("Three beds", "room_night", mood="night", title="Three beds")
    s.prop("b1", "bed", 280, 660, 1.0, size="big").prop("b2", "bed", 640, 660, 1.0, size="mid").prop("b3", "bed", 1010, 660, 1.0, size="small", girl=0.0)
    s.actor("gold", "girl", -100, 676, 1.0, zy=800, **GOLD)
    s.nar("Now Goldilocks was very sleepy. Upstairs, she found three beds.", ("walk", "gold", 200, 676, {"fit": True, "pose": "walk"}), ("pose", "gold", "tired", {"at": "70%"}))
    s.say("gold", "I will try the big bed first. Oh, it is too hard!", ("pose", "gold", "sad"), ("walk", "gold", 330, 676, {"speed": 100}))
    s.say("gold", "This one is too soft!", ("walk", "gold", 650, 676, {"speed": 200}), ("pose", "gold", "sad"))
    s.say("gold", "Ahh! This little bed is just right!", ("walk", "gold", 960, 676, {"speed": 220}), ("pose", "gold", "happy"))
    s.nar("She lay down, and she closed her eyes.", ("walk", "gold", 1000, 676, {"dur": 0.5}), ("hop", "gold", {"at": "30%"}), ("pose", "gold", "sleep", {"at": "45%"}), ("hide", "gold", {"at": "58%"}), ("set", "b3", "girl", 1.0, {"at": "58%", "dur": 0.1}), ("fx", "zzz", 990, 520, {"at": "62%", "dur": 12.0}), ("cam", 900, 440, 1.14, {"at": "40%", "dur": 3.0}))
    s.wait(3.5, ("sfx", "snore", {"at": 0.2}), ("fx", "zzz", 990, 520, {"dur": 6.0}))

    # ---------------------------------------------------------------- 7 the bears come home
    s = t.scene("Somebody has been eating my porridge", "room", mood="sneaky", title="Somebody has been eating my porridge")
    s.prop("tbl", "table", 640, 650, 1.0, bowl3=0.0)
    s.actor("papa", "bear", -200, 640, 1.2, **PAPA).actor("mama", "bear", -360, 650, 1.0, **MAMA_B).actor("baby", "bear", -480, 660, 0.72, **BABY)
    s.nar("Soon, the three bears came home from their walk.", ("walk", "papa", 360, 640, {"fit": True, "pose": "walk"}), ("walk", "mama", 190, 650, {"fit": True, "pose": "walk"}), ("walk", "baby", 880, 660, {"fit": True, "pose": "walk"}), ("face", "baby", -1, {"at": "90%"}))
    s.say("papa", "Somebody has been eating my porridge!", ("pose", "papa", "surprised"), ("face", "papa", 1))
    s.say("mama", "Somebody has been eating my porridge, too!", ("pose", "mama", "surprised"), ("face", "mama", 1), ("pose", "papa", "idle"))
    s.say("baby", "Somebody has been eating my porridge, and it is all gone!", ("pose", "baby", "sad"), ("pose", "mama", "idle"), ("fx", "sweat", "baby", 0, {"dur": 3.0}))

    # ---------------------------------------------------------------- 8 chairs again
    s = t.scene("Somebody has been sitting in my chair", "room", mood="sneaky", title="Somebody has been sitting in my chair")
    s.prop("c1", "chair", 440, 650, 1.0, size="big").prop("c2", "chair", 680, 650, 1.0, size="mid").prop("c3", "chair", 920, 650, 1.0, size="small", broken=1.0)
    s.actor("papa", "bear", 250, 640, 1.2, face=1, **PAPA).actor("mama", "bear", 815, 656, 1.0, face=1, **MAMA_B).actor("baby", "bear", 1120, 664, 0.72, face=-1, **BABY)
    s.say("papa", "Somebody has been sitting in my chair!", ("pose", "papa", "surprised"), ("fx", "mark", "papa", 0, {"dur": 2.0, "text": "!"}))
    s.say("mama", "Somebody has been sitting in my chair, too!", ("pose", "mama", "surprised"), ("pose", "papa", "idle"))
    s.say("baby", "Somebody has been sitting in my chair, and it is broken!", ("pose", "baby", "sad"), ("pose", "mama", "idle"), ("fx", "sweat", "baby", 0, {"dur": 3.0}))

    # ---------------------------------------------------------------- 9 beds again
    s = t.scene("Somebody has been sleeping in my bed", "room_night", mood="sneaky", title="Somebody has been sleeping in my bed")
    s.prop("b1", "bed", 280, 660, 1.0, size="big").prop("b2", "bed", 640, 660, 1.0, size="mid").prop("b3", "bed", 1010, 660, 1.0, size="small", girl=1.0)
    s.actor("papa", "bear", 160, 640, 1.2, face=1, zy=900, **PAPA).actor("mama", "bear", 520, 656, 1.0, face=1, zy=900, **MAMA_B).actor("baby", "bear", 860, 664, 0.72, face=1, zy=900, **BABY)
    s.actor("gold", "girl", 1010, 676, 1.0, show=False, zy=950, **GOLD)
    s.say("papa", "Somebody has been sleeping in my bed!", ("pose", "papa", "surprised"))
    s.say("mama", "Somebody has been sleeping in my bed, too!", ("pose", "mama", "surprised"), ("pose", "papa", "idle"))
    s.say("baby", "Somebody has been sleeping in my bed, and she is still there!", ("pose", "baby", "surprised"), ("pose", "mama", "idle"), ("fx", "mark", "baby", 0, {"at": "70%", "dur": 2.0, "text": "!"}), ("sfx", "snore", {"at": 0.2}))
    s.nar("Goldilocks woke up with a start. And she saw three bears!", ("set", "b3", "girl", 0.0, {"at": "45%", "dur": 0.1}), ("show", "gold", {"at": "45%"}), ("pose", "gold", "scared", {"at": "45%"}), ("hop", "gold", {"at": "45%"}), ("face", "gold", -1), ("pose", "baby", "surprised"))
    s.say("gold", "Oh my! Help! I am so sorry!", ("pose", "gold", "scared"), ("walk", "gold", 1500, 676, {"at": 1.0, "speed": 420}), ("pose", "papa", "surprised"), ("pose", "mama", "surprised"))

    # ---------------------------------------------------------------- 10 goodbye
    s = t.scene("Goodbye, Goldilocks", "meadow", mood="triumph", title="Goodbye, Goldilocks")
    s.prop("home", "cottage", 360, 566, 1.0, wall="#FFE9C8", roof="#8E5A3A")
    s.actor("papa", "bear", 760, 620, 1.2, face=1, **PAPA).actor("mama", "bear", 930, 630, 1.0, face=1, **MAMA_B).actor("baby", "bear", 1080, 640, 0.72, face=1, **BABY)
    s.actor("gold", "girl", 480, 636, 0.9, face=1, **GOLD)
    s.nar("Goldilocks ran out of the house, and all the way home. She never went into somebody's house without asking again.", ("walk", "gold", 1500, 636, {"speed": 330}), ("pose", "papa", "wave"), ("pose", "mama", "wave"), ("pose", "baby", "wave"))
    s.say("baby", "Come back and play with us one day!", ("pose", "baby", "cheer"), ("hop", "baby", {"at": "50%"}), ("pose", "papa", "happy"), ("pose", "mama", "happy"))
    s.nar("And the three bears had a new bowl of porridge, and they ate it up, just right.", ("pose", "papa", "eat"), ("pose", "mama", "eat"), ("pose", "baby", "eat"), ("fx", "hearts", "baby", 0, {"dur": 4.0}), tail=0.8)

    _outro(t, "Remember, little ones: always ask before you use someone else's things.", caption="Always ask before you use others' things!")
    return t


# ================================================================================================ little red riding hood
RED_C = dict(dress="#FFFFFF", hair="#7B4A2A", hood="#E2574C")
MAMA_R = dict(dress="#5BC27A", hair="#6B3E1E")
GRAN = dict(dress="#B58CFF", hair="#E4E4EC", granny="#FF9DB0")
WOODC = dict(fur="#8B5A2B", extra="tie", outfit="#3DB54A", hat_kind="cap", hat_color="#8B4F26")
NIGHTCAP = dict(fur="#8E9AB0", cap="#F3E9FF", glasses=True)
GRANNY_HOUSE = dict(wall="#EAF4FF", roof="#7B5EA7")


def red_riding_hood(lang="en"):
    t = Tale("tale-red-riding-hood", "Little Red Riding Hood | Fairy Tale Story for Kids | Bibi Buzz TV",
             "Stay on the path! Watch the classic fairy tale of Little Red Riding Hood and the big gray wolf: a little girl in a bright red hood takes a basket of cake "
             "to her grandma, and meets a sneaky wolf in the forest. A gentle, colorful animated story in simple English for toddlers and preschoolers.",
             TAGS + ["little red riding hood", "red riding hood", "big bad wolf", "grandma and the wolf"],
             {"nar": NAR, "red": (ANA, "-2%", "+12Hz"), "mama": (ARIA, "-4%", "+0Hz"), "granny": (ARIA, "-14%", "-16Hz"),
              "wolf": (GUY, "-10%", "-6Hz"), "wolfg": (GUY, "-2%", "+34Hz"), "wood": ("en-US-ChristopherNeural", "-6%", "-8Hz")}, lang=lang)
    t.bubble_tint = {"red": "#FFE0DC", "mama": "#DDF5E4", "granny": "#EDE3FF", "wolf": "#E8ECF6", "wolfb": "#E8ECF6", "wood": "#EADBC8"}
    t.cover = dict(bg="meadow", title=("LITTLE RED", "RIDING HOOD"), size=112, gap=110,
                   actors=[("red", "girl", 330, 706, 1.7, 1, "happy", dict(RED_C, hold="basket")), ("wolf", "wolf", 930, 712, 1.42, -1, "sly", WOLF)])
    _intro(t, ("LITTLE RED", "RIDING HOOD"), "Today's story is... Little Red Riding Hood!")

    # ---------------------------------------------------------------- 1 mama and little red
    s = t.scene("Little Red and Mama", "meadow", mood="happy", title="Little Red Riding Hood")
    s.prop("home", "cottage", 300, 566, 0.95)
    s.actor("mama", "girl", 650, 620, 1.2, face=-1, **MAMA_R).actor("red", "girl", 880, 636, 1.05, face=-1, **RED_C)
    s.nar("Once upon a time, a little girl lived in a small house, near a big green forest.", ("pose", "red", "happy"), ("pose", "mama", "happy"))
    s.nar("She always wore a bright red hood, so everybody called her Little Red Riding Hood.", ("pose", "red", "cheer"), ("hop", "red", {"at": "50%"}), ("fx", "sparkle", "red", 0, {"at": "40%", "dur": 3.0, "r": 110}))
    s.say("mama", "Little Red, Grandma is not feeling well today.", ("pose", "red", "idle"), ("pose", "mama", "sad"))
    s.say("mama", "Please take her this basket of cake and honey.", ("pose", "mama", "happy"), ("hold", "red", "basket", {"at": "30%"}), ("pose", "red", "happy", {"at": "30%"}))
    s.say("mama", "Walk straight along the path, and do not talk to strangers!", ("pose", "mama", "proud"), ("fx", "mark", "mama", 0, {"at": "30%", "dur": 2.2, "text": "!"}), ("pose", "red", "idle"))
    s.say("red", "I will, Mama! I will be very careful!", ("pose", "red", "cheer"), ("hop", "red", {"at": "40%"}), ("pose", "mama", "idle"))
    s.nar("So Little Red took her basket, and off she went, down the path.", ("pose", "mama", "wave", {"at": "30%"}), ("pose", "red", "idle"),
          ("walk", "red", 1500, 636, {"at": 0.4, "speed": 135}))

    # ---------------------------------------------------------------- 2 into the forest
    s = t.scene("Into the forest", "forest", mood="calm", title="Into the forest")
    s.prop("tree", "bigtree", 1120, 640, 1.0)
    s.actor("red", "girl", -150, 640, 1.0, hold="basket", **RED_C).actor("wolf", "wolf", 1030, 636, 0.9, face=-1, show=False, zy=600, **WOLF)
    s.nar("The forest was green and quiet. Little Red walked, and walked, and walked.", ("walk", "red", 470, 640, {"fit": True, "pose": "walk"}), ("fx", "leaves", 0, 0, {"dur": 60.0}))
    s.say("red", "La la la! What a lovely day for a walk!", ("pose", "red", "happy"), ("fx", "notes", "red", 0, {"dur": 3.5}))
    s.nar("But somebody was watching her, from behind a big tree.", ("pose", "red", "idle"), ("walk", "red", 640, 640, {"at": 0.3, "speed": 70}),
          ("show", "wolf", {"at": "35%"}), ("pose", "wolf", "sly", {"at": "35%"}), ("fx", "mark", "wolf", 0, {"at": "50%", "dur": 2.0, "text": "!"}), tail=0.7)

    # ---------------------------------------------------------------- 3 the wolf
    s = t.scene("The big gray wolf", "forest", mood="sneaky", title="The big gray wolf")
    s.actor("red", "girl", 400, 640, 1.05, face=1, hold="basket", **RED_C).actor("wolf", "wolf", -250, 626, 0.92, face=1, **WOLF)
    s.nar("Just then, a big gray wolf stepped out onto the path.", ("walk", "wolf", 820, 626, {"speed": 140}), ("pose", "red", "surprised", {"at": "60%"}), ("pose", "wolf", "sly", {"at": "70%"}))
    s.say("wolf", "Good morning, little girl. Where are you going, so early?", ("pose", "wolf", "sly"), ("pose", "red", "idle"))
    s.say("red", "Good morning, Mr. Wolf. I am going to my grandma's house.", ("pose", "red", "happy"), ("pose", "wolf", "idle"))
    s.say("red", "She is not feeling well, so I am bringing her some cake.", ("pose", "red", "happy"))
    s.say("wolf", "How nice! And where does your grandma live?", ("pose", "wolf", "sly"), ("cam", 760, 400, 1.1, {"dur": 2.5}))
    s.say("red", "In the little house, at the end of this path.", ("pose", "red", "idle"), ("pose", "wolf", "idle"))
    s.say("wolf", "I see... Why do you not pick some pretty flowers for her? She would love them!", ("pose", "wolf", "sly"), ("fx", "mark", "wolf", 0, {"at": "20%", "dur": 2.0, "text": "!"}))
    s.nar("And the wolf had a sneaky plan. He ran off through the trees, as fast as he could.", ("cam", 640, 360, 1.0, {"dur": 1.5}), ("pose", "wolf", "sly"),
          ("walk", "wolf", 1560, 626, {"at": 0.9, "speed": 460}), ("fx", "dust", "wolf", 0, {"at": 0.9, "dur": 1.0}), ("fx", "speed", "wolf", 0, {"at": 1.0, "dur": 2.0, "dir": 1}))
    s.say("red", "That is a good idea! Grandma loves flowers.", ("pose", "red", "cheer"), ("hop", "red", {"at": "40%"}), tail=0.5)

    # ---------------------------------------------------------------- 4 picking flowers
    s = t.scene("Picking flowers", "meadow_open", mood="happy", title="Picking flowers")
    s.prop("bsk", "basket", 360, 676, 1.0, show=False)
    s.actor("red", "girl", -150, 650, 1.05, hold="basket", **RED_C)
    s.nar("So Little Red left the path, and she found a meadow, full of flowers.", ("walk", "red", 520, 650, {"fit": True, "pose": "walk"}))
    s.say("red", "Red flowers, yellow flowers, and blue flowers! Grandma will love them!", ("hold", "red", "flowers", {"at": "10%"}), ("show", "bsk", {"at": "10%"}), ("pose", "red", "happy"), ("fx", "sparkle", "red", 0, {"dur": 3.5, "r": 110}))
    s.nar("She picked, and she picked, and she picked. She forgot all about the time.", ("walk", "red", 700, 660, {"at": 0.3, "speed": 60}), ("hop", "red", {"at": "40%"}), ("hop", "red", {"at": "75%"}), ("fx", "notes", "red", 0, {"dur": 4.0}))
    s.nar("At last, she picked up her basket, and she hurried to Grandma's house.", ("hold", "red", "basket", {"at": 0.2}), ("hide", "bsk", {"at": 0.2}), ("walk", "red", 1500, 650, {"at": 0.5, "speed": 190}), tail=0.6)

    # ---------------------------------------------------------------- 5 grandma's house: the wolf knocks
    s = t.scene("Grandma's little house", "meadow", mood="sneaky", title="Grandma's little house")
    s.prop("home", "cottage", 900, 566, 1.05, **GRANNY_HOUSE)
    s.actor("granny", "girl", 900, 604, 1.0, face=-1, show=False, **GRAN).actor("wolf", "wolf", -250, 620, 0.92, face=1, **WOLF)
    s.nar("Meanwhile, the wolf ran all the way to Grandma's little house.", ("walk", "wolf", 770, 620, {"speed": 400}), ("fx", "dust", "wolf", 0, {"at": 0.2, "dur": 1.0}), ("pose", "wolf", "sly", {"at": "80%"}))
    s.nar("Knock, knock, knock!", ("sfx", "knock", {"at": 0.15}), ("pose", "wolf", "knock"))
    s.say("granny", "Who is it?", ("pose", "wolf", "idle"))
    s.say("wolf", "It is me, Little Red Riding Hood! Please open the door!", ("pose", "wolf", "sly"), voice="wolfg")
    s.say("granny", "Oh my! That does not sound like my Little Red!", ("pose", "wolf", "sly"))
    s.nar("The wolf pushed the door open, and Grandma hid in the big wardrobe, quick as a flash!", ("set", "home", "door", 1.0, {"at": "20%", "dur": 1.0}), ("walk", "wolf", 890, 604, {"at": 1.2, "speed": 160}),
          ("hide", "wolf", {"at": 2.6}), ("fx", "mark", 900, 330, {"at": 0.6, "dur": 2.0, "text": "!"}), tail=0.6)

    # ---------------------------------------------------------------- 6 the wolf in grandma's bed
    s = t.scene("The wolf in Grandma's bed", "room", mood="sneaky", title="The wolf in Grandma's bed")
    s.prop("bed", "bed", 360, 650, 1.0, size="big").prop("wd", "wardrobe", 980, 640, 1.0, door=0.0)
    s.actor("wolf", "wolf", 1180, 640, 0.92, face=-1, **WOLF).actor("wolfb", "wolf", 290, 626, 0.86, face=1, show=False, zy=640, **NIGHTCAP)
    s.nar("Inside, the wolf found Grandma's nightcap, and her glasses.", ("walk", "wolf", 700, 640, {"at": 0.2, "speed": 150}), ("pose", "wolf", "sly", {"at": "60%"}))
    s.nar("He put them on, and he jumped into Grandma's bed. Hee, hee, hee!", ("walk", "wolf", 400, 640, {"at": 0.2, "speed": 220}), ("hide", "wolf", {"at": 1.4}), ("show", "wolfb", {"at": 1.4}),
          ("fx", "sparkle", 300, 500, {"at": 1.4, "dur": 2.5, "r": 120}), ("pose", "wolfb", "laugh", {"at": 1.8}), tail=0.6)
    s.nar("And he pulled the blanket up, and he waited for Little Red.", ("pose", "wolfb", "sly"), ("cam", 420, 470, 1.12, {"dur": 3.0}), tail=0.7)

    # ---------------------------------------------------------------- 7 little red arrives
    s = t.scene("At Grandma's door", "meadow", mood="calm", title="At Grandma's door")
    s.prop("home", "cottage", 900, 566, 1.05, **GRANNY_HOUSE)
    s.actor("red", "girl", -150, 628, 1.05, hold="basket", **RED_C)
    s.nar("At last, Little Red came to Grandma's house, with her basket full of cake and flowers.", ("walk", "red", 800, 628, {"fit": True, "pose": "walk"}))
    s.say("red", "That is strange. The door is open.", ("pose", "red", "think"), ("set", "home", "door", 1.0, {"at": 0.1, "dur": 1.0}))
    s.say("red", "Grandma? It is me, Little Red!", ("pose", "red", "idle"))
    s.nar("And she went inside.", ("walk", "red", 905, 606, {"dur": 1.0}), ("hide", "red", {"at": 1.05}), ("set", "home", "door", 0.0, {"at": 1.4, "dur": 0.6}))

    # ---------------------------------------------------------------- 8 what big ears, eyes, teeth
    s = t.scene("What big eyes you have", "room", mood="tense", title="What big eyes you have!")
    s.prop("bed", "bed", 360, 650, 1.0, size="big").prop("wd", "wardrobe", 980, 640, 1.0, door=0.0)
    s.actor("wolfb", "wolf", 290, 626, 0.86, face=1, zy=640, **NIGHTCAP).actor("wolf", "wolf", 300, 640, 0.92, face=1, show=False, **WOLF)
    s.actor("red", "girl", 1150, 650, 1.1, face=-1, hold="basket", **RED_C)
    s.nar("Little Red walked up to the bed. Grandma looked very strange!", ("walk", "red", 700, 650, {"fit": True, "pose": "walk"}), ("pose", "wolfb", "sly", {"at": "50%"}))
    s.say("red", "Grandma, what big ears you have!", ("pose", "red", "surprised"))
    s.say("wolfb", "All the better to hear you with, my dear!", ("pose", "wolfb", "sly"), ("pose", "red", "idle"), voice="wolfg")
    s.say("red", "Grandma, what big eyes you have!", ("pose", "red", "surprised"), ("walk", "red", 640, 650, {"speed": 60}))
    s.say("wolfb", "All the better to see you with, my dear!", ("pose", "wolfb", "sly"), ("pose", "red", "idle"), voice="wolfg", )
    s.say("red", "Grandma, what big teeth you have!", ("pose", "red", "scared"), ("fx", "mark", "red", 0, {"dur": 2.2, "text": "!"}), ("cam", 520, 470, 1.15, {"dur": 2.0}))
    s.say("wolfb", "All the better to...", ("pose", "wolfb", "sly"), ("pose", "red", "scared"), voice="wolfg")
    s.say("wolf", "GOBBLE you up!", ("hide", "wolfb", {"at": 0.0}), ("show", "wolf", {"at": 0.0}), ("pose", "wolf", "laugh", {"at": 0.0}), ("hop", "wolf", {"at": 0.05}),
          ("fx", "burst", 370, 205, {"at": 0.0, "dur": 2.0, "text": "GRRR!"}), ("cam", 640, 360, 1.0, {"at": 0.0, "dur": 1.2}), voice="wolf")
    s.nar("Little Red screamed, and she ran out of the house, as fast as she could!", ("pose", "red", "scared"), ("walk", "red", -300, 650, {"at": 0.2, "speed": 520}),
          ("pose", "wolf", "laugh", {"at": 0.2}), ("walk", "wolf", -400, 640, {"at": 1.0, "speed": 360}), tail=0.5)

    # ---------------------------------------------------------------- 9 the woodcutter
    s = t.scene("The kind woodcutter", "meadow", mood="chase", title="The kind woodcutter")
    s.prop("home", "cottage", 300, 566, 0.95, **GRANNY_HOUSE)
    s.actor("wood", "bear", 1120, 628, 1.0, face=-1, **WOODC)
    s.actor("red", "girl", 330, 612, 1.05, face=1, show=False, hold="basket", **RED_C).actor("wolf", "wolf", 300, 612, 0.92, face=1, show=False, **WOLF)
    s.nar("Little Red ran out of the house, and the big gray wolf ran after her!", ("show", "red", {"at": 0.1}), ("walk", "red", 780, 628, {"at": 0.2, "speed": 360}),
          ("show", "wolf", {"at": 0.9}), ("walk", "wolf", 560, 626, {"at": 1.0, "speed": 300}), ("pose", "wolf", "sly", {"at": 2.0}))
    s.say("red", "Help! Help! A wolf!", ("pose", "red", "scared"), ("hop", "red"), ("fx", "sweat", "red", 0, {"dur": 2.5}))
    s.nar("A kind woodcutter was working nearby, and he heard her cry.", ("pose", "wood", "surprised"), ("walk", "wood", 940, 628, {"at": 0.4, "speed": 150}), ("fx", "mark", "wood", 0, {"at": 0.3, "dur": 2.0, "text": "!"}))
    s.say("wood", "Stop right there, you big gray wolf!", ("pose", "wood", "proud"), ("pose", "wolf", "scared"), ("fx", "burst", 900, 300, {"dur": 1.8, "text": "STOP!", "color": "#3DB54A"}))
    s.say("wood", "Leave Little Red alone! Go away, and never come back!", ("pose", "wood", "proud"), ("cam", 760, 400, 1.1, {"dur": 2.0}))
    s.nar("The wolf was so scared, he ran away over the hills. And he never came back again!", ("cam", 640, 360, 1.0, {"dur": 1.5}), ("pose", "wolf", "scared"), ("face", "wolf", -1, {"at": 0.2}),
          ("walk", "wolf", -400, 626, {"at": 0.3, "speed": 560}), ("fx", "speed", "wolf", 0, {"at": 0.4, "dur": 2.2, "dir": -1}), ("pose", "red", "cheer", {"at": 1.0}), ("pose", "wood", "happy", {"at": 1.0}), tail=0.6)

    # ---------------------------------------------------------------- 10 grandma is safe
    s = t.scene("Grandma is safe", "room", mood="happy", title="Grandma is safe")
    s.prop("bed", "bed", 360, 650, 1.0, size="big").prop("wd", "wardrobe", 980, 640, 1.0, door=0.0)
    s.actor("granny", "girl", 980, 628, 1.0, face=-1, show=False, zy=700, **GRAN)                      # zy: drawn in front of the wardrobe she steps out of
    s.actor("red", "girl", -150, 650, 1.05, face=1, hold="basket", **RED_C).actor("wood", "bear", -330, 646, 1.0, face=1, zy=700, **WOODC)
    s.nar("Little Red and the woodcutter went back inside. But where was Grandma?", ("walk", "red", 740, 650, {"fit": True, "pose": "walk"}), ("walk", "wood", 600, 646, {"fit": True, "pose": "walk"}), ("pose", "red", "sad", {"at": "80%"}))
    s.say("red", "Grandma? Grandma, where are you?", ("pose", "red", "sad"), ("pose", "wood", "think"))
    s.nar("Then they heard a little noise, from the wardrobe. Knock, knock, knock!", ("sfx", "knock", {"at": "70%"}), ("fx", "mark", 980, 300, {"at": "70%", "dur": 2.0, "text": "?"}),
          ("pose", "red", "surprised", {"at": "70%"}), ("pose", "wood", "surprised", {"at": "70%"}))
    s.nar("Little Red opened the big wardrobe, and there was Grandma, safe and sound!", ("walk", "red", 790, 650, {"at": 0.8, "speed": 100}), ("set", "wd", "door", 1.0, {"at": 1.8, "dur": 1.0}),
          ("show", "granny", {"at": 2.8}), ("pose", "granny", "happy", {"at": 2.8}), ("fx", "sparkle", 980, 400, {"at": 2.8, "dur": 3.0, "r": 150}), ("pose", "wood", "happy", {"at": 2.8}))
    s.say("granny", "Oh, my dear Little Red! I was so scared!", ("walk", "granny", 940, 640, {"speed": 90}), ("pose", "granny", "scared"), ("pose", "red", "happy"),
          ("walk", "red", 850, 650, {"speed": 60}), ("walk", "wood", 700, 646, {"speed": 100}))
    s.say("red", "Grandma! I am so glad that you are safe!", ("pose", "red", "cheer"), ("hop", "red", {"at": "40%"}), ("pose", "granny", "happy"), ("pose", "wood", "happy"),
          ("fx", "hearts", "red", 0, {"at": "40%", "dur": 4.0}))

    # ---------------------------------------------------------------- 11 happy ending
    s = t.scene("Happily ever after", "meadow_dusk", mood="triumph", title="Happily ever after")
    s.prop("home", "cottage", 300, 566, 0.95, **GRANNY_HOUSE).prop("cake", "pie", 700, 700, 1.3)
    s.actor("red", "girl", 560, 640, 1.05, face=1, **RED_C).actor("granny", "girl", 860, 640, 1.0, face=-1, **GRAN).actor("wood", "bear", 1080, 636, 1.0, face=-1, **WOODC)
    s.nar("Then they all sat down together, and they ate the cake, and the honey. Yum, yum, yum!", ("pose", "red", "eat"), ("pose", "granny", "eat"), ("pose", "wood", "eat"), ("fx", "confetti", 0, 0, {"dur": 20.0}))
    s.say("red", "I am sorry that I talked to a stranger, and that I left the path.", ("pose", "red", "sad"), ("pose", "granny", "idle"), ("pose", "wood", "idle"))
    s.say("granny", "That is all right, my dear. Now you know what to do.", ("pose", "granny", "happy"), ("pose", "red", "idle"), ("fx", "hearts", "granny", 0, {"dur": 3.5}))
    s.say("wood", "And remember, if a stranger talks to you, tell a grown-up right away!", ("pose", "wood", "proud"), ("pose", "granny", "idle"))
    s.say("red", "I will, I promise!", ("pose", "red", "cheer"), ("hop", "red", {"at": "40%"}), ("pose", "wood", "happy"), ("pose", "granny", "happy"))
    s.nar("And Little Red Riding Hood never forgot. And they all lived happily ever after.", ("pose", "red", "happy"), ("fx", "sparkle", 700, 460, {"dur": 4.0, "r": 330}), tail=0.8)

    _outro(t, "Remember, little ones: stay on the path, and never talk to strangers.", caption="Stay on the path, and stay safe!")
    return t


# ================================================================================================ the gingerbread man
OLD_W = dict(dress="#7BC67B", hair="#E4E4EC", granny="#FFD27A")
OLD_M = dict(gramps="#8C6BC8", hair="#E4E4EC")
FARM_PIG = dict(outfit="#F2B632", hat_kind="straw")
BERRY_BEAR = dict(fur="#7A4A25", extra="bib", outfit="#3E8EDE", hold="basket")
FOX = dict(fur="#E8893A")
GM_COTTAGE = dict(wall="#FFF1D0", roof="#5FA8D3")
REFRAIN = "Run, run, as fast as you can! You cannot catch me, I am the Gingerbread Man!"


def gingerbread_man(lang="en"):
    t = Tale("tale-gingerbread-man", "The Gingerbread Man | Fairy Tale Story for Kids | Bibi Buzz TV",
             "Run, run, as fast as you can! Watch the classic fairy tale of The Gingerbread Man: a little cookie jumps out of the oven and runs away from an old woman, "
             "an old man, a pig and a bear, until he meets a sly fox at the river. A gentle, colorful animated story in simple English for toddlers and preschoolers.",
             TAGS + ["gingerbread man", "the gingerbread man", "run run as fast as you can", "gingerbread man story"],
             {"nar": NAR, "gm": ("en-US-EricNeural", "+2%", "+20Hz"), "woman": (ARIA, "-12%", "-10Hz"), "man": ("en-US-ChristopherNeural", "-10%", "-14Hz"),
              "pig": (ARIA, "+2%", "+18Hz"), "bear": (GUY, "-14%", "-22Hz"), "fox": (GUY, "-4%", "+12Hz")}, lang=lang)
    t.bubble_tint = {"gm": "#FFE9C8", "woman": "#E4F6E4", "man": "#EADBC8", "pig": "#FFE3EE", "bear": "#EADBC8", "fox": "#FFE4CC"}
    t.cover = dict(bg="meadow", title=("THE GINGERBREAD", "MAN"), size=104, gap=108,
                   actors=[("old", "girl", 170, 704, 1.3, 1, "surprised", OLD_W), ("gm", "ginger", 520, 712, 1.65, 1, "cheer", {}),
                           ("fox", "wolf", 1010, 712, 1.32, -1, "sly", FOX)])
    _intro(t, ("THE GINGERBREAD", "MAN"), "Today's story is... The Gingerbread Man!")

    # ---------------------------------------------------------------- 1 the old woman and the old man
    s = t.scene("A little cottage", "meadow", mood="happy", title="The old woman and the old man")
    s.prop("home", "cottage", 300, 566, 0.95, **GM_COTTAGE)
    s.actor("woman", "girl", 700, 622, 1.1, face=1, **OLD_W).actor("man", "girl", 900, 632, 1.12, face=-1, **OLD_M)
    s.nar("Once upon a time, a kind old woman and a kind old man lived in a little cottage.", ("pose", "woman", "happy"), ("pose", "man", "happy"))
    s.say("woman", "Oh, how I wish we had a little child to play with!", ("pose", "woman", "sad"), ("pose", "man", "idle"))
    s.say("man", "I have an idea! Let us bake a gingerbread man!", ("pose", "man", "cheer"), ("hop", "man", {"at": "40%"}), ("pose", "woman", "surprised"))
    s.say("woman", "What a wonderful idea! Let us go to the kitchen!", ("pose", "woman", "cheer"), ("hop", "woman", {"at": "40%"}), ("pose", "man", "happy"))
    s.nar("So the old woman and the old man went into the cottage, to bake.", ("pose", "woman", "idle"), ("pose", "man", "idle"), ("set", "home", "door", 1.0, {"at": 0.2, "dur": 0.9}),
          ("walk", "woman", 305, 606, {"at": 0.4, "speed": 190}), ("hide", "woman", {"at": 2.7}), ("walk", "man", 305, 612, {"at": 0.9, "speed": 190}), ("hide", "man", {"at": 4.2}),
          ("set", "home", "door", 0.0, {"at": 4.4, "dur": 0.6}), tail=0.5)

    # ---------------------------------------------------------------- 2 baking
    s = t.scene("The kitchen", "room", mood="happy", title="Baking a gingerbread man")
    s.prop("oven", "oven", 290, 650, 1.35, door=0.0).prop("cnt", "counter", 960, 650, 1.0)
    s.actor("woman", "girl", -150, 664, 1.1, face=1, **OLD_W).actor("man", "girl", -330, 668, 1.12, face=1, **OLD_M)
    s.actor("dough", "ginger", 945, 504, 0.42, face=-1, show=False, flat=True, zy=900)
    s.actor("gm", "ginger", 290, 624, 0.55, face=1, show=False, flat=True, zy=900)
    s.nar("In the kitchen, the old woman mixed the flour, and the sugar, and the ginger.",
          ("walk", "woman", 770, 664, {"fit": True, "pose": "walk"}), ("walk", "man", 560, 668, {"fit": True, "pose": "walk"}), ("fx", "dust", 880, 500, {"at": 3.4, "dur": 1.0, "size": 1.2}))
    s.nar("Then she rolled out the dough, and she cut out a little man. She gave him two eyes, a big smile, and three sweet buttons.",
          ("show", "dough", {"at": "35%"}), ("pose", "dough", "sleep", {"at": "35%"}), ("fx", "sparkle", 945, 440, {"at": "35%", "dur": 3.0, "r": 90}), ("pose", "woman", "happy", {"at": "40%"}), ("pose", "man", "think", {"at": "40%"}))
    s.say("woman", "There you go, my little gingerbread man!", ("pose", "woman", "happy"), ("pose", "man", "happy"))
    s.nar("Into the oven he went! The old woman closed the door, and they waited.",
          ("hide", "dough", {"at": 0.3}), ("set", "oven", "door", 1.0, {"at": 0.3, "dur": 0.7}), ("show", "gm", {"at": 1.1}), ("pose", "gm", "sleep", {"at": 1.1}),
          ("set", "oven", "door", 0.0, {"at": 3.0, "dur": 0.6}), ("hide", "gm", {"at": 3.0}), ("pose", "woman", "idle"), ("pose", "man", "idle"), tail=0.4)
    s.nar("Soon, the whole kitchen smelled so good. Mmm! Yum!", ("fx", "steam", 340, 440, {"dur": 6.0}), ("pose", "woman", "eat", {"at": "40%"}), ("pose", "man", "eat", {"at": "40%"}))
    s.nar("Ding! The oven was ready. The old man opened the oven door, and... pop!",
          ("sfx", "ding", {"at": 0.2}), ("set", "oven", "door", 1.0, {"at": 2.6, "dur": 0.4}), ("show", "gm", {"at": 3.2}), ("pose", "gm", "cheer", {"at": 3.2}),
          ("fx", "burst", 300, 330, {"at": 3.2, "dur": 1.6, "text": "POP!"}), ("pose", "woman", "surprised", {"at": 3.2}), ("pose", "man", "surprised", {"at": 3.2}))
    s.say("gm", REFRAIN, ("scale", "gm", 1.4, {"at": 0.0, "dur": 0.5}), ("hop", "gm", {"at": 0.05}), ("walk", "gm", 440, 690, {"at": 0.05, "dur": 0.5}), ("pose", "gm", "laugh", {"at": 0.6}),
          ("hop", "gm", {"at": "50%"}), ("pose", "woman", "surprised"), ("pose", "man", "surprised"))
    s.say("woman", "Oh my! Stop, little gingerbread man!", ("walk", "gm", 1500, 690, {"at": 0.15, "speed": 430}), ("pose", "woman", "wave"), ("pose", "man", "wave"), tail=0.4)

    # ---------------------------------------------------------------- 3 the chase begins
    s = t.scene("The chase begins", "meadow", mood="chase", title="Run, run, as fast as you can!")
    s.prop("home", "cottage", 260, 566, 0.95, **GM_COTTAGE)
    s.actor("gm", "ginger", 262, 612, 0.75, face=1, show=False, zy=900)
    s.actor("woman", "girl", 262, 606, 1.1, face=1, show=False, **OLD_W).actor("man", "girl", 262, 612, 1.12, face=1, show=False, **OLD_M)
    s.nar("Out of the cottage door he ran, and down the road! The old woman and the old man ran after him.",
          ("set", "home", "door", 1.0, {"at": 0.1, "dur": 0.6}), ("show", "gm", {"at": 0.5}), ("walk", "gm", 900, 650, {"at": 0.6, "speed": 360}),
          ("show", "woman", {"at": 1.3}), ("walk", "woman", 560, 640, {"at": 1.4, "speed": 300}), ("show", "man", {"at": 1.9}), ("walk", "man", 430, 644, {"at": 2.0, "speed": 280}),
          ("set", "home", "door", 0.0, {"at": 3.0, "dur": 0.6}), ("fx", "dust", 300, 620, {"at": 0.7, "dur": 1.0}))
    s.say("woman", "Stop, stop! Come back, little one!", ("pose", "woman", "wave"), ("pose", "man", "idle"), ("pose", "gm", "idle"))
    s.say("man", "Come back! It is not safe to run away!", ("pose", "man", "wave"), ("pose", "woman", "idle"))
    s.say("gm", REFRAIN, ("face", "gm", -1), ("pose", "gm", "laugh"), ("hop", "gm", {"at": "50%"}), ("pose", "woman", "scared"), ("pose", "man", "scared"))
    s.nar("But the gingerbread man ran, and ran, and ran. The old woman and the old man could not catch him.",
          ("walk", "gm", 1500, 650, {"at": 0.1, "speed": 430}), ("pose", "woman", "tired", {"at": 0.6}), ("pose", "man", "tired", {"at": 0.6}),
          ("fx", "sweat", "woman", 0, {"at": 0.6, "dur": 4.0}), ("fx", "sweat", "man", 0, {"at": 0.6, "dur": 4.0}), tail=0.5)

    # ---------------------------------------------------------------- 4 the pig
    s = t.scene("The little pig", "meadow", mood="chase", title="The little pig")
    s.actor("pig", "pig", 860, 640, 1.0, face=-1, **FARM_PIG).actor("gm", "ginger", -200, 650, 0.75, face=1, zy=900)
    s.nar("The gingerbread man ran past a little farm. A little pig was playing in the yard.", ("pose", "pig", "happy"), ("hop", "pig", {"at": "60%"}))
    s.nar("Along came the gingerbread man, running as fast as the wind!", ("walk", "gm", 520, 650, {"speed": 400}), ("fx", "dust", "gm", 0, {"at": 1.0, "dur": 1.0}), ("pose", "pig", "surprised", {"at": "60%"}))
    s.say("gm", REFRAIN, ("face", "gm", 1), ("pose", "gm", "laugh"), ("hop", "gm", {"at": "50%"}), ("pose", "pig", "surprised"))
    s.say("pig", "Oh my! Stop, little cookie! The old woman is looking for you!", ("walk", "gm", 1500, 650, {"at": 0.1, "speed": 430}), ("pose", "pig", "wave"), ("walk", "pig", 1500, 644, {"at": "35%", "speed": 300}),
          ("fx", "mark", "pig", 0, {"dur": 2.0, "text": "!"}), tail=0.3)

    # ---------------------------------------------------------------- 5 the bear
    s = t.scene("The big bear", "forest", mood="chase", title="The big bear")
    s.actor("bear", "bear", 900, 640, 1.1, face=-1, **BERRY_BEAR).actor("gm", "ginger", -200, 650, 0.75, face=1, zy=900)
    s.nar("Deep in the forest, a big bear was picking berries.", ("pose", "bear", "happy"), ("fx", "leaves", 0, 0, {"dur": 60.0}))
    s.nar("Along came the gingerbread man, running past the trees.", ("walk", "gm", 520, 650, {"speed": 400}), ("fx", "dust", "gm", 0, {"at": 1.0, "dur": 1.0}), ("pose", "bear", "surprised", {"at": "60%"}))
    s.say("gm", REFRAIN, ("face", "gm", 1), ("pose", "gm", "laugh"), ("hop", "gm", {"at": "50%"}), ("pose", "bear", "surprised"))
    s.say("bear", "Stop, little cookie! It is not safe to run so far away!", ("walk", "gm", 1500, 650, {"at": 0.1, "speed": 430}), ("pose", "bear", "wave"), ("walk", "bear", 1500, 644, {"at": "35%", "speed": 280}),
          ("fx", "mark", "bear", 0, {"dur": 2.0, "text": "!"}), tail=0.3)

    # ---------------------------------------------------------------- 6 the river and the fox
    s = t.scene("The wide river", "river", mood="sneaky", title="The wide river")
    s.prop("wat", "water", 640, 700, 1.0)
    s.actor("gm", "ginger", -200, 650, 0.75, face=1, flat=True, zy=900)
    s.actor("fox", "wolf", 430, 650, 0.95, face=-1, show=False, **FOX)
    s.nar("The gingerbread man ran, and ran, until he came to a wide, blue river.", ("walk", "gm", 250, 650, {"speed": 330, "pose": "run"}), ("pose", "gm", "scared", {"at": 2.4}))
    s.say("gm", "Oh no! A river! I cannot swim. I will get all soggy!", ("pose", "gm", "scared"), ("fx", "sweat", "gm", 0, {"dur": 3.0}))
    s.nar("Just then, a sly fox stepped out from behind the reeds.", ("show", "fox", {"at": 0.9}), ("pose", "fox", "sly", {"at": 0.9}), ("fx", "mark", 430, 300, {"at": 1.0, "dur": 2.0, "text": "!"}), ("pose", "gm", "surprised", {"at": 1.0}))
    s.say("fox", "Hello, little gingerbread man. Why are you in such a hurry?", ("pose", "fox", "sly"), ("pose", "gm", "idle"))
    s.say("gm", "I ran away from an old woman, an old man, a pig, and a bear. And I can run away from you!", ("pose", "gm", "proud"), ("pose", "fox", "idle"))
    s.say("fox", "Oh, I do not want to chase you. I want to help you cross the river.", ("pose", "fox", "sly"), ("pose", "gm", "think"))
    s.say("fox", "Hop on my tail, and I will carry you across.", ("face", "fox", 1), ("pose", "fox", "sly"), ("fx", "sparkle", 430, 420, {"at": "50%", "dur": 2.5, "r": 100}))
    s.say("gm", "Hmm... All right! But please do not let me get wet!", ("pose", "gm", "happy"), ("walk", "gm", 348, 548, {"at": "55%", "dur": 0.6, "pose": "jump"}), ("hop", "gm", {"at": "55%"}), ("scale", "gm", 0.72, {"at": "55%", "dur": 0.5}), tail=0.4)

    # ---------------------------------------------------------------- 7 across the river
    s = t.scene("Across the river", "river", mood="sneaky", title="Across the river")
    s.prop("wat", "water", 640, 700, 1.0)
    s.actor("fox", "wolf", 430, 650, 0.95, face=1, **FOX)
    s.actor("gm", "ginger", 348, 548, 0.54, face=1, flat=True, zy=900)
    s.nar("So the gingerbread man sat on the fox's tail, and the fox began to swim.", ("walk", "fox", 510, 650, {"at": 0.3, "dur": 3.6}), ("walk", "gm", 428, 548, {"at": 0.3, "dur": 3.6, "pose": "idle"}),
          ("fx", "splash", 450, 640, {"at": 0.4, "dur": 1.0}), ("pose", "fox", "sly"), ("pose", "gm", "happy", {"at": 1.0}))
    s.say("fox", "The water is getting deeper! Hop on my head, so you do not get wet!", ("walk", "fox", 650, 650, {"at": 0.2, "dur": 4.0}), ("walk", "gm", 540, 392, {"at": 0.2, "dur": 2.0, "pose": "jump"}),
          ("walk", "gm", 650, 418, {"at": 2.2, "dur": 2.0, "pose": "jump"}), ("hop", "gm", {"at": 0.3}), ("hop", "gm", {"at": 2.3}), ("pose", "fox", "sly"))
    s.nar("Now the gingerbread man sat on top of the fox's head. The river was wide, and the other side was far away.", ("pose", "gm", "happy"), ("pose", "fox", "idle"), ("cam", 650, 470, 1.12, {"at": 1.0, "dur": 3.0}))
    s.say("fox", "Hmm. You are so small, and I am so hungry. And you smell so yummy!", ("pose", "fox", "laugh"), ("pose", "gm", "scared", {"at": "40%"}), ("fx", "mark", "gm", 0, {"at": "45%", "dur": 2.0, "text": "!"}), ("cam", 650, 440, 1.3, {"dur": 3.0}))
    s.say("gm", "Oh no! Help! Help!", ("pose", "gm", "scared"), ("hop", "gm", {"at": "20%"}), ("hop", "gm", {"at": "60%"}), ("fx", "sweat", "gm", 0, {"dur": 3.0}), tail=0.4)

    # ---------------------------------------------------------------- 8 just in time
    s = t.scene("Just in time", "river", mood="chase", title="Just in time")
    s.prop("wat", "water", 640, 700, 1.0)
    s.actor("fox", "wolf", 650, 650, 0.95, face=1, **FOX)
    s.actor("gm", "ginger", 650, 418, 0.54, face=1, flat=True, zy=900)
    s.actor("woman", "girl", -150, 650, 1.1, face=1, **OLD_W).actor("man", "girl", -300, 654, 1.12, face=1, **OLD_M)
    s.actor("pig", "pig", -450, 648, 1.0, face=1, **FARM_PIG).actor("bear", "bear", -600, 652, 1.1, face=1, **BERRY_BEAR)
    s.nar("Just then, the old woman, the old man, the pig, and the bear came running to the river!",
          ("pose", "fox", "sly"), ("pose", "gm", "scared"), ("walk", "woman", 380, 650, {"at": 0.3, "speed": 330}), ("walk", "man", 285, 654, {"at": 0.3, "speed": 330}),
          ("walk", "pig", 195, 648, {"at": 0.3, "speed": 330}), ("walk", "bear", 90, 652, {"at": 0.3, "speed": 330}), ("fx", "dust", 200, 660, {"at": 1.5, "dur": 1.0}))
    s.say("woman", "Stop, Mr. Fox! Please do not eat our gingerbread man!", ("pose", "woman", "scared"), ("pose", "man", "scared"), ("pose", "pig", "scared"), ("pose", "bear", "scared"),
          ("face", "fox", -1), ("pose", "fox", "surprised"), ("pose", "gm", "wave"))
    s.say("man", "Wait, Mr. Fox! You must be so hungry!", ("pose", "man", "think"), ("pose", "woman", "idle"), ("pose", "pig", "idle"), ("pose", "bear", "idle"))
    s.say("fox", "Oh... Yes, I am very, very hungry. I am sorry that I tried to trick him.", ("pose", "fox", "sad"), ("pose", "gm", "idle"), ("pose", "man", "idle"))
    s.say("woman", "Bring our gingerbread man back to us, and we will bake you a big apple pie!", ("pose", "woman", "happy"), ("pose", "fox", "idle"))
    s.say("fox", "Really? Oh, thank you! You are so kind!", ("pose", "fox", "happy"), ("fx", "hearts", "fox", 0, {"at": "30%", "dur": 3.0}), ("walk", "fox", 470, 650, {"at": "40%", "speed": 90}),
          ("walk", "gm", 470, 418, {"at": "40%", "speed": 90, "pose": "idle"}), ("pose", "gm", "happy"), ("pose", "woman", "happy"))
    s.nar("The fox carried the gingerbread man safely back across the river. And the gingerbread man hopped down, into the old woman's arms.",
          ("walk", "fox", 440, 650, {"at": 0.3, "dur": 1.2}), ("walk", "gm", 440, 418, {"at": 0.3, "dur": 1.2, "pose": "idle"}), ("walk", "gm", 392, 646, {"at": 2.2, "dur": 0.7, "pose": "jump"}), ("hop", "gm", {"at": 2.2}),
          ("scale", "gm", 1.39, {"at": 2.2, "dur": 0.6}), ("pose", "woman", "cheer", {"at": 3.0}), ("fx", "hearts", "woman", 0, {"at": 3.0, "dur": 4.0}), ("pose", "gm", "happy", {"at": 3.0}), tail=0.5)

    # ---------------------------------------------------------------- 9 pie for everyone
    s = t.scene("Pie for everyone", "meadow_dusk", mood="triumph", title="A pie for everyone")
    s.prop("home", "cottage", 230, 566, 0.9, **GM_COTTAGE).prop("pie", "pie", 740, 684, 1.6, show=False)
    s.actor("woman", "girl", 440, 636, 1.05, face=1, **OLD_W).actor("man", "girl", 330, 632, 1.05, face=1, **OLD_M).actor("gm", "ginger", 590, 654, 0.78, face=1)
    s.actor("fox", "wolf", 900, 640, 0.9, face=-1, **FOX).actor("pig", "pig", 1020, 648, 0.95, face=-1, **FARM_PIG).actor("bear", "bear", 1140, 636, 1.05, face=-1, **BERRY_BEAR)
    s.nar("Back at the cottage, the old woman baked a big, warm apple pie, for everyone.", ("show", "pie", {"at": 0.6}), ("fx", "sparkle", 740, 600, {"at": 0.6, "dur": 3.0, "r": 150}), ("fx", "steam", 740, 622, {"at": 1.0, "dur": 20.0}),
          ("pose", "gm", "happy"), ("pose", "woman", "happy"))
    s.say("gm", "I am sorry that I ran away. Home is the best place to be!", ("pose", "gm", "sad"), ("pose", "woman", "idle"))
    s.say("woman", "We love you, little one! We were so worried about you!", ("pose", "woman", "happy"), ("pose", "gm", "idle"), ("fx", "hearts", "woman", 0, {"dur": 3.5}))
    s.say("fox", "And I am sorry that I tried to trick you, little one.", ("pose", "fox", "sad"), ("pose", "woman", "idle"))
    s.say("gm", "That is all right, Mr. Fox. Let us share the pie!", ("pose", "gm", "cheer"), ("hop", "gm", {"at": "40%"}), ("pose", "fox", "happy"), ("fx", "confetti", 0, 0, {"dur": 30.0}))
    s.nar("And they all ate the yummy pie together. Yum, yum, yum!", ("pose", "gm", "eat"), ("pose", "woman", "eat"), ("pose", "man", "eat"), ("pose", "fox", "eat"), ("pose", "pig", "eat"), ("pose", "bear", "eat"))
    s.nar("And the gingerbread man never ran away again. And they all lived happily ever after.", ("pose", "gm", "happy"), ("pose", "woman", "happy"), ("pose", "man", "happy"), ("pose", "fox", "happy"),
          ("fx", "sparkle", 700, 460, {"dur": 4.0, "r": 330}), tail=0.8)

    _outro(t, "Remember, little ones: stay close to the people who love you.", caption="Stay close to the people who love you!")
    return t


# ================================================================================================ the three billy goats gruff
GOAT_S = dict(fur="#F7F1E3", scarf="#FF6B8B", horns=0.7)
GOAT_M = dict(fur="#E5C99C", scarf="#FFD23F", horns=1.0)
GOAT_B = dict(fur="#8F8179", scarf="#3E8EDE", horns=1.25, horn="#D9C98E")
TROLL = dict(hold="club")
K_S, K_M, K_B, K_T = 0.52, 0.72, 0.92, 0.80                  # (no depth scaling in the gorge scenes: everybody is "flat")
DECK, POOL, TROLL_X = 440, 688, 780                          # the goats' feet on the bridge, the troll's feet in the stream, where the troll lives
BIG_X, MID_X, LIT_X = 135, 245, 340                          # the three brothers on the dry hill (left bank)
RBIG_X, RMID_X, RLIT_X = 985, 1110, 1205                     # ... and on the green hill (right bank)
FIGHT_X, HIT_X, WIN_X = 460, 660, RBIG_X                     # where the big goat stops to talk to the troll, where his horns hit him, where he walks to afterwards
TROLL_UP = 800                                               # where the troll jumps up onto the bridge
TROLL_Q = "Who is that, tripping over my bridge?"
TROLL_EAT = "Grr! Now I am going to gobble you up!"


def _gorge(s):
    """The bridge over the gorge and the front of the stream (see-through: it hides the troll's feet)."""
    return s.prop("bridge", "bridge", 640, DECK, 1.0).prop("water", "gorge_water", 640, 700, 1.0)


def _steps(k, dist, dur, at=0.0, c0=0.0, gain=0.5, heavy=False):
    """The trip-trap of hooves: one sound for every step of a goat that walks `dist` px in `dur` s, starting at `at`, after it already
    walked `c0` px in this scene. It follows the gait of story._draw_actor (one step per 46 * k + 0.05 * speed px; the walk eases
    in and out a little), so every sound lands on a foot. heavy = a big goat: thuds."""
    stride = 46.0 * max(0.6, k) + 0.05 * dist / dur
    acts, n = [], int(c0 // stride) + 1
    while n * stride - c0 <= dist + 1e-6:
        want = (n * stride - c0) / dist
        lo, hi = 0.0, 1.0
        for _ in range(24):                                   # solve u * 0.86 + 0.14 * ease(u) = want
            u = (lo + hi) / 2
            if u * 0.86 + 0.14 * ease(u) < want:
                lo = u
            else:
                hi = u
        tt = at + dur * lo
        if heavy:
            acts.append(("sfx", "thud", {"at": tt, "gain": gain * 1.2}))
            acts.append(("sfx", ("hoof", "hoof2")[n % 2], {"at": tt, "gain": gain * 0.8}))
        else:
            acts.append(("sfx", ("hoof", "hoof2")[n % 2], {"at": tt, "gain": gain}))
        n += 1
    return acts


def _taps(n, at=0.0, gap=0.42, gain=0.45):
    """n hoof taps that are heard from far away (trip, trap ...)."""
    return [("sfx", ("hoof", "hoof2")[i % 2], {"at": at + i * gap, "gain": gain}) for i in range(n)]


def three_billy_goats(lang="en"):
    t = Tale("tale-three-billy-goats-gruff", "The Three Billy Goats Gruff | Fairy Tale Story for Kids | Bibi Buzz TV",
             "Trip, trap! Trip, trap! Watch the classic fairy tale of The Three Billy Goats Gruff: three hungry brothers want to cross the old wooden bridge, to eat the sweet green "
             "grass on the other side, but a big, grumpy troll lives under it. A gentle, colorful animated story in simple English for toddlers and preschoolers.",
             TAGS + ["three billy goats gruff", "billy goats gruff", "the three billy goats gruff", "troll under the bridge", "trip trap trip trap"],
             {"nar": NAR, "lit": (ANA, "+4%", "+24Hz"), "mid": ("en-US-EricNeural", "+0%", "+8Hz"), "big": (GUY, "-12%", "-14Hz"),
              "troll": ("en-US-ChristopherNeural", "-16%", "-26Hz")}, lang=lang)
    t.bubble_tint = {"lit": "#FFE3EE", "mid": "#FFF3C4", "big": "#DCEBFF", "troll": "#DDEFC8"}
    t.cover = dict(bg="meadow", title=("THE THREE BILLY", "GOATS GRUFF"), size=104, gap=108,
                   actors=[("lit", "goat", 140, 706, 1.12, 1, "happy", GOAT_S), ("mid", "goat", 375, 708, 1.3, 1, "cheer", GOAT_M),
                           ("big", "goat", 650, 712, 1.42, 1, "proud", GOAT_B), ("troll", "troll", 1070, 712, 1.4, -1, "sly", TROLL)])
    _intro(t, ("THE THREE BILLY", "GOATS GRUFF"), "Today's story is... The Three Billy Goats Gruff!")

    # ---------------------------------------------------------------- 1 three hungry goats
    s = t.scene("Three hungry goats", "meadow_gorge", mood="happy", title="Three hungry billy goats")
    _gorge(s)
    s.actor("big", "goat", -330, DECK, K_B, face=1, flat=True, **GOAT_B).actor("mid", "goat", -215, DECK, K_M, face=1, flat=True, **GOAT_M)
    s.actor("lit", "goat", -105, DECK, K_S, face=1, flat=True, **GOAT_S).actor("troll", "troll", TROLL_X, POOL, K_T, face=-1, show=False, flat=True, **TROLL)
    s.nar("Once upon a time, three billy goats lived on a dry, brown hill.",
          ("walk", "lit", LIT_X, DECK, {"fit": True}), ("walk", "mid", MID_X, DECK, {"fit": True}), ("walk", "big", BIG_X, DECK, {"fit": True}))
    s.nar("There was a little goat, a middle goat, and a big goat.", ("pose", "lit", "happy"), ("pose", "mid", "happy"), ("pose", "big", "happy"),
          ("hop", "lit", {"at": "30%"}), ("hop", "mid", {"at": "58%"}), ("hop", "big", {"at": "88%"}))
    s.nar("They were brothers, and they loved to eat green grass.", ("pose", "lit", "eat"), ("pose", "mid", "eat"), ("pose", "big", "eat"),
          ("sfx", "munch", {"at": "55%"}), ("sfx", "munch", {"at": "85%"}))
    s.say("lit", "Oh no! All the grass on our hill is gone!", ("pose", "lit", "sad"), ("pose", "mid", "sad"), ("pose", "big", "idle"))
    s.say("mid", "My tummy is rumbling. I am so hungry!", ("pose", "mid", "sad"), ("pose", "lit", "idle"))
    s.say("big", "Do not worry, brothers. Look across the bridge!", ("pose", "big", "wave"), ("pose", "mid", "idle"))
    s.nar("On the other side of the bridge, there was a hill full of sweet, green grass.",
          ("pose", "big", "idle"), ("pose", "lit", "surprised"), ("pose", "mid", "surprised"), ("fx", "sparkle", 1110, 330, {"at": 0.3, "dur": 4.5, "r": 190}))
    s.say("lit", "Yum! Let us go and eat it!", ("pose", "lit", "cheer"), ("hop", "lit", {"at": "35%"}), ("pose", "mid", "cheer"), ("pose", "big", "happy"))
    s.nar("But under the bridge, there lived a big, grumpy troll. He did not like anyone to cross his bridge!",
          ("show", "troll", {"at": "42%"}), ("pose", "troll", "sly", {"at": "42%"}), ("pose", "lit", "scared", {"at": "46%"}), ("pose", "mid", "scared", {"at": "46%"}),
          ("pose", "big", "surprised", {"at": "46%"}), ("fx", "mark", "lit", 0, {"at": "46%", "dur": 1.8, "text": "!"}),
          ("pose", "troll", "knock", {"at": "78%"}), ("sfx", "thud", {"at": "78%", "gain": 0.9}))
    s.say("big", "Do not be afraid. I have a plan!", ("pose", "big", "proud"), ("pose", "lit", "idle"), ("pose", "mid", "idle"), ("pose", "troll", "sly"))
    s.say("big", "Little brother, you go first.", ("pose", "big", "wave"), ("pose", "lit", "surprised"))
    s.say("big", "Then middle brother. Then me!", ("pose", "big", "idle"), ("pose", "lit", "idle"), ("pose", "mid", "happy"))
    s.say("lit", "Okay! Here I go!", ("pose", "lit", "cheer"), ("hop", "lit", {"at": "40%"}), ("pose", "mid", "happy"), ("pose", "big", "happy"), tail=0.5)

    # ---------------------------------------------------------------- 2 the grumpy troll
    s = t.scene("The grumpy troll", "meadow_gorge", mood="sneaky", title="The grumpy troll")
    _gorge(s)
    s.actor("troll", "troll", TROLL_X, POOL, K_T, face=-1, flat=True, **TROLL)
    s.nar("Under the bridge, the grumpy troll was waiting. His tummy was rumbling, too!", ("cam", 780, 520, 1.4, {"at": 0.0, "dur": 2.6}), ("pose", "troll", "sly"))
    s.say("troll", "Grr... I am so hungry! I hope something yummy comes along!", ("pose", "troll", "think"))
    s.nar("Just then, he heard a sound. Trip, trap! Trip, trap!", ("pose", "troll", "surprised", {"at": "20%"}), ("fx", "mark", "troll", 0, {"at": "20%", "dur": 1.8, "text": "!"}),
          *_taps(5, at=1.6), ("pose", "troll", "sly", {"at": -1.0}), ("hide", "troll", {"at": -0.45}), tail=0.3)

    # ---------------------------------------------------------------- 3 little billy goat gruff
    s = t.scene("Little Billy Goat Gruff", "meadow_gorge", mood="sneaky", title="Little Billy Goat Gruff")
    _gorge(s)
    s.actor("big", "goat", BIG_X, DECK, K_B, face=1, flat=True, **GOAT_B).actor("mid", "goat", MID_X, DECK, K_M, face=1, flat=True, **GOAT_M)
    s.actor("lit", "goat", LIT_X, DECK, K_S, face=1, flat=True, **GOAT_S).actor("troll", "troll", TROLL_X, POOL, K_T, face=-1, show=False, flat=True, **TROLL)
    s.nar("Little Billy Goat Gruff walked onto the bridge. Trip, trap! Trip, trap!", ("walk", "lit", 560, DECK, {"at": 0.3, "dur": 3.9}),
          *_steps(K_S, 560 - LIT_X, 3.9, at=0.3), ("pose", "mid", "scared"), ("pose", "big", "idle"))
    s.say("troll", TROLL_Q, ("show", "troll"), ("pose", "troll", "sly"), ("pose", "lit", "scared"), ("fx", "mark", "lit", 0, {"at": 0.3, "dur": 1.8, "text": "!"}))
    s.say("lit", "It is only me, Little Billy Goat Gruff.", ("pose", "lit", "shrug"), ("pose", "troll", "idle"))
    s.say("lit", "I am going to the green hill, to eat some grass.", ("pose", "lit", "happy"))
    s.say("troll", TROLL_EAT, ("pose", "troll", "knock"), ("sfx", "thud", {"at": 0.25, "gain": 0.9}), ("pose", "lit", "scared"), ("fx", "sweat", "lit", 0, {"at": "30%", "dur": 3.0}))
    s.say("lit", "Please do not eat me! I am only a little goat.", ("pose", "lit", "scared"), ("pose", "troll", "idle"))
    s.say("lit", "My brother is coming soon. He is much bigger!", ("pose", "lit", "wave"))
    s.say("troll", "Hmm... Bigger, you say? Off you go, then!", ("pose", "troll", "think"), ("pose", "lit", "idle"))
    s.nar("So Little Billy Goat Gruff skipped across the bridge, and up the green hill. Munch, munch, munch!", ("walk", "lit", RLIT_X, DECK, {"at": 0.3, "dur": 4.6}),
          *_steps(K_S, RLIT_X - 560, 4.6, at=0.3, c0=560 - LIT_X, gain=0.45), ("hide", "troll", {"at": 0.6}), ("pose", "mid", "happy"), ("pose", "big", "happy"),
          ("pose", "lit", "eat", {"at": -1.4}), ("sfx", "munch", {"at": -1.2}), ("sfx", "munch", {"at": -0.7}), ("sfx", "munch", {"at": -0.2}), tail=0.5)

    # ---------------------------------------------------------------- 4 middle billy goat gruff
    s = t.scene("Middle Billy Goat Gruff", "meadow_gorge", mood="sneaky", title="Middle Billy Goat Gruff")
    _gorge(s)
    s.actor("big", "goat", BIG_X, DECK, K_B, face=1, flat=True, **GOAT_B).actor("mid", "goat", MID_X, DECK, K_M, face=1, flat=True, **GOAT_M)
    s.actor("lit", "goat", RLIT_X, DECK, K_S, face=-1, flat=True, **GOAT_S).actor("troll", "troll", TROLL_X, POOL, K_T, face=-1, show=False, flat=True, **TROLL)
    s.nar("Next came Middle Billy Goat Gruff. Trip, trap! Trip, trap! Trip, trap!", ("walk", "mid", 560, DECK, {"at": 0.3, "dur": 4.4}),
          *_steps(K_M, 560 - MID_X, 4.4, at=0.3), ("pose", "lit", "eat"), ("pose", "big", "idle"), ("sfx", "munch", {"at": 0.8, "gain": 0.5}), ("sfx", "munch", {"at": 1.6, "gain": 0.5}))
    s.say("troll", TROLL_Q, ("show", "troll"), ("pose", "troll", "sly"), ("pose", "mid", "scared"), ("pose", "lit", "scared"), ("fx", "mark", "mid", 0, {"at": 0.3, "dur": 1.8, "text": "!"}))
    s.say("mid", "It is only me, Middle Billy Goat Gruff.", ("pose", "mid", "shrug"), ("pose", "troll", "idle"))
    s.say("mid", "I am going to the green hill, to eat some grass.", ("pose", "mid", "happy"))
    s.say("troll", TROLL_EAT, ("pose", "troll", "knock"), ("sfx", "thud", {"at": 0.25, "gain": 0.9}), ("pose", "mid", "scared"), ("fx", "sweat", "mid", 0, {"at": "30%", "dur": 3.0}))
    s.say("mid", "Please do not eat me! I am only a middle goat.", ("pose", "mid", "scared"), ("pose", "troll", "idle"))
    s.say("mid", "My big brother is coming soon. He is much bigger!", ("pose", "mid", "wave"))
    s.say("troll", "Even bigger? Hmm... I will wait! Off you go!", ("pose", "troll", "think"), ("pose", "mid", "idle"))
    s.nar("So Middle Billy Goat Gruff crossed the bridge, and joined his little brother. Munch, munch, munch!", ("walk", "mid", RMID_X, DECK, {"at": 0.3, "dur": 4.6}),
          *_steps(K_M, RMID_X - 560, 4.6, at=0.3, c0=560 - MID_X, gain=0.5), ("hide", "troll", {"at": 0.6}), ("pose", "big", "happy"), ("pose", "lit", "happy", {"at": -2.2}), ("hop", "lit", {"at": -2.2}),
          ("pose", "mid", "eat", {"at": -1.4}), ("pose", "lit", "eat", {"at": -1.4}), ("sfx", "munch", {"at": -1.2}), ("sfx", "munch", {"at": -0.7}), ("sfx", "munch", {"at": -0.2}), tail=0.5)

    # ---------------------------------------------------------------- 5 big billy goat gruff
    s = t.scene("Big Billy Goat Gruff", "meadow_gorge", mood="chase", title="Big Billy Goat Gruff")
    _gorge(s)
    s.actor("big", "goat", BIG_X, DECK, K_B, face=1, flat=True, **GOAT_B)
    s.actor("mid", "goat", RMID_X, DECK, K_M, face=-1, flat=True, **GOAT_M).actor("lit", "goat", RLIT_X, DECK, K_S, face=-1, flat=True, **GOAT_S)
    s.actor("troll", "troll", TROLL_X, POOL, K_T, face=-1, show=False, flat=True, **TROLL)
    s.nar("Last of all came Big Billy Goat Gruff. TRIP, TRAP! TRIP, TRAP! The old bridge shook and shook!", ("walk", "big", FIGHT_X, DECK, {"at": 0.3, "dur": 4.8}),
          *_steps(K_B, FIGHT_X - BIG_X, 4.8, at=0.3, heavy=True), ("set", "bridge", "shake", 1.0, {"at": 2.2, "dur": 0.4}), ("cam", 640, 380, 1.1, {"at": 1.0, "dur": 3.5}),
          ("pose", "lit", "scared", {"at": "55%"}), ("pose", "mid", "scared", {"at": "55%"}))
    s.say("troll", "WHO is that, stomping over MY bridge?", ("set", "bridge", "shake", 0.0, {"at": 0.0, "dur": 0.4}), ("show", "troll", {"at": 0.0}), ("cam", 640, 360, 1.0, {"at": 0.0, "dur": 0.9}),
          ("walk", "troll", TROLL_UP, DECK, {"at": 0.5, "dur": 0.7, "pose": "jump"}), ("hop", "troll", {"at": 0.5}), ("scale", "troll", 1.12, {"at": 0.5, "dur": 0.7}),
          ("fx", "dust", TROLL_UP, 452, {"at": 1.2, "dur": 1.0, "size": 1.3}), ("pose", "troll", "sly", {"at": 1.25}), lead=1.5)
    s.say("big", "It is I, Big Billy Goat Gruff!", ("pose", "big", "proud"))
    s.say("big", "I am going to cross your bridge!", ("pose", "big", "idle"))
    s.say("troll", TROLL_EAT, ("pose", "troll", "knock"), ("sfx", "thud", {"at": 0.25, "gain": 0.9}))
    s.say("big", "Oh no, you are not! I have big horns, and I am brave!", ("pose", "big", "sly"))
    s.say("lit", "Go, big brother, go!", ("pose", "lit", "cheer"), ("hop", "lit", {"at": "30%"}), ("pose", "mid", "cheer"))
    s.nar("Big Billy Goat Gruff lowered his horns, and ran at the troll!", ("pose", "troll", "scared", {"at": -1.2}), ("walk", "big", HIT_X, DECK, {"at": -1.0, "dur": 0.9, "pose": "run"}),
          *_steps(K_B, HIT_X - FIGHT_X, 0.9, at=-1.0, c0=FIGHT_X - BIG_X, heavy=True), ("cam", 700, 370, 1.12, {"at": -1.6, "dur": 1.4}))
    s.nar("BONK! Up, up, up went the troll, high into the air!", ("fx", "burst", HIT_X + 95, 300, {"at": 0.0, "dur": 1.4, "text": "BONK!", "size": 0.85}),
          ("set", "bridge", "shake", 1.0, {"at": 0.0, "dur": 0.1}), ("set", "bridge", "shake", 0.0, {"at": 0.8, "dur": 0.4}),
          ("walk", "troll", TROLL_UP + 110, -40, {"at": 0.05, "dur": 1.3, "pose": "scared"}), ("pose", "big", "proud", {"at": 0.3}), ("pose", "lit", "surprised", {"at": 0.3}),
          ("pose", "mid", "surprised", {"at": 0.3}), ("walk", "big", WIN_X, DECK, {"at": 0.9, "dur": 3.2, "pose": "walk"}),
          *_steps(K_B, WIN_X - HIT_X, 3.2, at=0.9, c0=HIT_X - BIG_X, heavy=True, gain=0.42))
    s.nar("And down, down, down he fell, SPLASH, into the water!", ("face", "big", -1, {"at": 0.0}), ("cam", 640, 360, 1.0, {"at": 0.0, "dur": 1.0}),
          ("walk", "troll", 790, POOL, {"at": -2.7, "dur": 0.9, "pose": "scared"}), ("scale", "troll", 1.0, {"at": -2.7, "dur": 0.9}),
          ("fx", "splash", 765, 672, {"at": -1.8, "dur": 1.2}), ("fx", "splash", 820, 672, {"at": -1.8, "dur": 1.2, "sfx": False}),
          ("fx", "burst", 790, 520, {"at": -1.8, "dur": 1.6, "text": "SPLASH!", "color": "#3E9BE8", "sfx": "splash"}), ("pose", "troll", "dizzy", {"at": -1.7}),
          ("fx", "dizzy", "troll", 0, {"at": -1.6, "dur": 3.0}), ("pose", "big", "idle", {"at": -1.7}), ("pose", "lit", "cheer", {"at": -1.0}), ("pose", "mid", "cheer", {"at": -1.0}))
    s.say("troll", "Ouch! I am sorry that I was so mean!", ("pose", "troll", "sad"), ("pose", "big", "idle"), ("pose", "lit", "idle"), ("pose", "mid", "idle"))
    s.say("big", "Be kind, and others will be kind to you!", ("pose", "big", "proud"))
    s.say("troll", "I will! I promise! Thank you!", ("pose", "troll", "happy"), ("fx", "hearts", "troll", 0, {"at": "30%", "dur": 3.0}), ("pose", "big", "happy"), ("pose", "lit", "happy"), ("pose", "mid", "happy"))
    s.nar("And the three brothers were together again!", ("pose", "troll", "wave", {"at": 0.3}), ("pose", "big", "cheer", {"at": "40%"}), ("hop", "big", {"at": "40%"}), ("pose", "mid", "cheer", {"at": "55%"}),
          ("hop", "mid", {"at": "55%"}), ("pose", "lit", "cheer", {"at": "70%"}), ("hop", "lit", {"at": "70%"}), ("fx", "hearts", "mid", 0, {"at": "60%", "dur": 3.0}), tail=0.5)

    # ---------------------------------------------------------------- 6 the green hill
    s = t.scene("The green hill", "meadow_gorge_dusk", mood="calm", title="The green hill")
    _gorge(s)
    s.actor("big", "goat", WIN_X, DECK, K_B, face=-1, flat=True, **GOAT_B).actor("mid", "goat", RMID_X, DECK, K_M, face=-1, flat=True, **GOAT_M)
    s.actor("lit", "goat", RLIT_X, DECK, K_S, face=-1, flat=True, **GOAT_S).actor("troll", "troll", TROLL_X, POOL, K_T, face=1, show=False, flat=True, **TROLL)
    s.nar("And on the sweet, green hill, the three billy goats ate, and ate, and ate, until their tummies were full.",
          ("pose", "lit", "eat"), ("pose", "mid", "eat"), ("pose", "big", "eat"), ("sfx", "munch", {"at": 0.8}), ("sfx", "munch", {"at": 1.8}), ("sfx", "munch", {"at": 2.8}),
          ("sfx", "munch", {"at": 3.8}), ("fx", "sparkle", 1090, 330, {"at": 0.4, "dur": 5.0, "r": 200}))
    s.say("lit", "Yum, yum! This grass is the best!", ("pose", "lit", "happy"), ("hop", "lit", {"at": "40%"}), ("pose", "mid", "eat"), ("pose", "big", "eat"))
    s.say("mid", "Thank you, big brother, for being so brave!", ("pose", "mid", "happy"), ("pose", "lit", "eat"))
    s.say("big", "We did it together, brothers!", ("pose", "big", "cheer"), ("hop", "big", {"at": "40%"}), ("pose", "mid", "eat"), ("fx", "hearts", "big", 0, {"at": "30%", "dur": 3.0}))
    s.nar("And the troll? He was never mean again. Now he says hello to everyone who crosses his bridge.", ("pose", "big", "happy"), ("pose", "mid", "happy"), ("pose", "lit", "happy"),
          ("show", "troll", {"at": "40%"}), ("pose", "troll", "wave", {"at": "40%"}), ("fx", "hearts", "troll", 0, {"at": "62%", "dur": 3.0}))
    s.say("troll", "Hello, friends! Have a nice day!", ("pose", "troll", "wave"), ("pose", "big", "wave"), ("pose", "mid", "wave"), ("pose", "lit", "wave"))
    s.nar("Snip, snap, snout, this tale is told out!", ("fx", "sparkle", 640, 300, {"at": 0.2, "dur": 4.0, "r": 400}), ("pose", "troll", "happy"), tail=0.8)

    _outro(t, "Remember, little ones: be kind to others, and be brave when you need to be.", caption="Be kind, and be brave!")
    return t


# ================================================================================================ the enormous turnip
KID = dict(dress="#FF8FA3", hair="#7B4A2A")                                   # the little girl
BEAR_T = dict(fur="#7A4A25", extra="bib", outfit="#3E8EDE")
TN_X, TN_Y, TN_K = 225, 636, 1.3                                              # the turnip's garden bed: the middle of the bed on the ground, and its size
# everybody who pulls, nearest to the turnip first: id, kind, feet x, size, style (they all face the turnip, face -1)
LINE = [("gpa", "girl", 500, 1.0, OLD_M), ("gma", "girl", 606, 0.95, OLD_W), ("kid", "girl", 698, 0.8, KID), ("pig", "pig", 792, 0.9, FARM_PIG),
        ("hare", "hare", 888, 0.95, {}), ("bear", "bear", 988, 1.0, BEAR_T), ("pip", "pip", 1105, 0.85, {"zy": 900})]
LINE_Y = {"gpa": 650, "gma": 650, "kid": 650, "pig": 650, "hare": 650, "bear": 654, "pip": 658}
HEAVE = "Heave-ho! Heave-ho!"
STUCK = "But the turnip was still stuck!"
SOUP_SEAT = {"gpa": 280, "gma": 395, "kid": 490, "pig": 790, "hare": 890, "bear": 1005, "pip": 1125}     # where everybody sits at the soup pot
ARRIVE = {"gma": (300, None), "kid": (300, None), "pig": (300, None), "hare": (230, "jump"), "bear": (200, None), "pip": (260, None)}     # speed, walking pose


def _come(new, slot):
    """The act that brings a friend from the right edge of the screen to their place in the line."""
    speed, pose = ARRIVE[new]
    return ("walk", new, slot, LINE_Y[new], dict(at=0.3, speed=speed, **({"pose": pose} if pose else {})))


def _hand(x, y, k, lean=11.0, arm=100.0):
    """Where the front hand of a girl-shaped puller (facing left) is in the "pull" pose (see storyart.pose_for and storyart.girl)."""
    a, ln = math.radians(arm), math.radians(lean)
    ex, ey = -(30.0 + math.sin(a) * 40.0), -134.0 + math.cos(a) * 40.0
    return x + (ex * math.cos(ln) - ey * math.sin(ln)) * k, y + (ex * math.sin(ln) + ey * math.cos(ln)) * k


def _grip(px, py, pk, tx=TN_X, ty=TN_Y, tk=TN_K):
    """The turnip's gx, gy (in its own units): its bunch of leaves ends in the front hand of the puller at (px, py), size pk."""
    hx, hy = _hand(px, py, pk)
    return (hx - tx) / tk, (hy - ty) / tk


def _turnip(s, grow=1.0, bend=0.0, **st):
    gx, gy = _grip(LINE[0][2], LINE_Y["gpa"], LINE[0][3])
    return s.prop("tn", "turnip", TN_X, TN_Y, TN_K, grow=grow, bend=bend, gx=gx, gy=gy, gsw=8.0, **st)


def _line(s, upto):
    """The pulling line on a scene: the first `upto` friends stand in their places, everybody else waits out of sight, on the right."""
    for j, (aid, kind, x, k, style) in enumerate(LINE):
        s.actor(aid, kind, x if j < upto else 1500 + 160 * (j - upto), LINE_Y[aid], k, face=-1, flat=True, **style)


def _poses(ids, pose, **o):
    return [("pose", i, pose, dict(o)) if o else ("pose", i, pose) for i in ids]


def _above(j):
    """How far above the middle of the head of LINE[j] a number sits."""
    _aid, kind, _x, k, _st = LINE[j]
    return -(0.22 * HEAD[kind] * k + 46.0)


def _round(s, j, call, came, shout, wob, stuck=True):
    """One more friend joins the line (LINE[j]): the friend before calls, the new friend comes (and a number tells how many pull now),
    they all heave, and the turnip is still stuck."""
    new, _kind, slot, _k, _st = LINE[j]
    ids = [a[0] for a in LINE[:j + 1]]
    s.say(LINE[j - 1][0], call, *_poses(ids[:-1], "grip"), tail=0.3)
    s.nar(came, _come(new, slot), ("fx", "mark", new, _above(j), {"at": "58%", "dur": 1.8, "text": str(j + 1)}), *_poses(ids[:-1], "grip"), tail=0.3)
    if shout:
        s.say(new, shout, *_poses(ids, "pull"), ("set", "tn", "wobble", wob, {"at": 0.0, "dur": 0.5}), ("sfx", "creak", {"at": "20%", "gain": 0.4}), ("sfx", "creak", {"at": "65%", "gain": 0.4}), tail=0.3)
    if stuck:
        s.nar(STUCK, *_poses(ids, "grip"), ("set", "tn", "wobble", 0.0, {"at": 0.0, "dur": 0.6}), ("fx", "sweat", new, 0, {"at": 0.2, "dur": 3.0}), tail=0.35)


def _cheer_scene(t, title):
    """The meadow after the turnip is out: the six friends in a row, Pip flying above them, the turnip lying next to its hole."""
    s = t.scene("Hooray, we did it!", "meadow_open", mood="triumph", title=title)
    _turnip(s, bend=0.0, out=1.0)
    cheer_x = {"gpa": 645, "gma": 740, "kid": 820, "pig": 905, "hare": 990, "bear": 1090}
    for aid, kind, x, k, style in LINE[:6]:
        s.actor(aid, kind, cheer_x[aid], LINE_Y[aid], k, face=-1, flat=True, **style)
    s.actor("pip", "pip", 1185, 350, 0.85, face=-1, flat=True, zy=900)                       # Pip flies above everybody
    return s


def enormous_turnip(lang="en"):
    t = Tale("tale-enormous-turnip", "The Enormous Turnip | Fairy Tale Story for Kids | Bibi Buzz TV",
             "Heave-ho! Heave-ho! Watch the classic fairy tale of The Enormous Turnip: a kind old grandpa plants a tiny seed, and it grows into the biggest turnip in the whole wide world. "
             "Grandma, a little girl, a pig, a hare, a big bear and a tiny ladybug come to help him pull. Can they pull it up, all together? A gentle, colorful animated story in simple "
             "English for toddlers and preschoolers.",
             TAGS + ["enormous turnip", "the enormous turnip", "giant turnip", "the giant turnip story", "heave ho", "teamwork story"],
             {"nar": NAR, "gpa": ("en-US-ChristopherNeural", "-8%", "-6Hz"), "gma": (ARIA, "-12%", "-6Hz"), "kid": (ANA, "+2%", "+18Hz"),
              "pig": (ARIA, "+4%", "+20Hz"), "hare": ("en-US-EricNeural", "+4%", "+10Hz"), "bear": (GUY, "-14%", "-22Hz"), "pip": (ANA, "+8%", "+34Hz")}, lang=lang)
    t.bubble_tint = {"gpa": "#E9DDFF", "gma": "#DFF4DF", "kid": "#FFE3EE", "pig": "#FFEFC4", "hare": "#FFF0DC", "bear": "#EADBC8", "pip": "#FFE0E0"}
    gx, gy = _grip(560, 712, 1.25, 250, 706, 1.45)
    t.cover = dict(bg="meadow_open", title=("THE ENORMOUS", "TURNIP"), size=104, gap=108,
                   props=[("tn", "turnip", 250, 706, 1.45, dict(grow=1.0, bend=1.0, gx=gx, gy=gy))],
                   actors=[("gpa", "girl", 560, 712, 1.25, -1, "pull", OLD_M), ("gma", "girl", 690, 712, 1.15, -1, "pull", OLD_W), ("kid", "girl", 800, 712, 0.95, -1, "pull", KID),
                           ("pig", "pig", 915, 712, 1.1, -1, "pull", FARM_PIG), ("hare", "hare", 1035, 712, 1.15, -1, "pull", {}), ("bear", "bear", 1165, 716, 1.2, -1, "pull", BEAR_T)])
    _intro(t, ("THE ENORMOUS", "TURNIP"), "Today's story is... The Enormous Turnip!")

    # ---------------------------------------------------------------- 1 grandpa plants a seed
    s = t.scene("Grandpa's garden", "meadow_open", mood="happy", title="Grandpa plants a seed")
    s.prop("tn", "turnip", TN_X, TN_Y, TN_K, grow=0.0)
    s.actor("gpa", "girl", 1180, 650, 1.0, face=-1, flat=True, **OLD_M)
    s.nar("Once upon a time, there lived a kind old grandpa. He had a big, beautiful garden.", ("walk", "gpa", 310, 650, {"fit": True}), ("pose", "gpa", "happy", {"at": "70%"}))
    s.nar("One sunny morning, Grandpa dug a little hole, and planted a tiny seed.", ("pose", "gpa", "plant"), ("fx", "dust", 250, 654, {"at": "45%", "dur": 1.0, "size": 0.7}))
    s.say("gpa", "Grow, little turnip, grow! Grow big and strong!", ("pose", "gpa", "plant"), ("set", "tn", "grow", 0.22, {"at": "55%", "dur": 1.2}),
          ("fx", "sparkle", TN_X, 590, {"at": "55%", "dur": 2.6, "r": 120}))
    s.nar("The sun shone, and the rain fell. And the little turnip grew, and grew.", ("pose", "gpa", "happy", {"at": 0.3}), ("set", "tn", "grow", 0.55, {"at": 0.4, "dur": 4.0}),
          ("fx", "sparkle", TN_X, 520, {"at": 0.5, "dur": 4.0, "r": 200}))
    s.nar("It grew, and grew, and GREW! It was the biggest turnip in the whole wide world!", ("pose", "gpa", "surprised", {"at": 0.4}), ("set", "tn", "grow", 1.0, {"at": 0.3, "dur": 4.4}),
          ("sfx", "whoosh", {"at": 0.3, "gain": 0.6}), ("fx", "sparkle", TN_X, 450, {"at": 0.3, "dur": 5.0, "r": 260}), ("walk", "gpa", 500, 650, {"at": 1.0, "dur": 3.6, "keepface": True}), tail=0.5)
    s.say("gpa", "Wow! What an enormous turnip! Let me pull it up!", ("pose", "gpa", "cheer"), ("hop", "gpa", {"at": "45%"}))

    # ---------------------------------------------------------------- 2 pull, pull, pull (grandpa, grandma, the little girl, the pig, the hare)
    s = t.scene("Pull, pull, pull!", "meadow_open", mood="happy", title="Pull, pull, pull!")
    _turnip(s)
    _line(s, 1)
    s.nar("So Grandpa took hold of the turnip's leaves. He pulled, and he pulled, and he pulled!", ("pose", "gpa", "grip"), ("set", "tn", "bend", 1.0, {"at": "20%", "dur": 0.7}),
          ("pose", "gpa", "pull", {"at": "50%"}), ("set", "tn", "wobble", 0.3, {"at": "50%", "dur": 0.6}), ("sfx", "creak", {"at": "55%", "gain": 0.4}))
    s.say("gpa", HEAVE, ("pose", "gpa", "pull"), ("set", "tn", "wobble", 0.35, {"at": 0.0, "dur": 0.4}), ("sfx", "creak", {"at": "20%", "gain": 0.4}), ("sfx", "creak", {"at": "65%", "gain": 0.4}), tail=0.3)
    s.nar("But the turnip did not move. It was stuck, stuck, stuck!", ("pose", "gpa", "grip"), ("set", "tn", "wobble", 0.0, {"at": 0.0, "dur": 0.6}), ("fx", "sweat", "gpa", 0, {"at": 0.2, "dur": 3.5}))
    _round(s, 1, "Grandma! Grandma! Please come and help me!", "Grandma came running. Now there were two friends pulling the turnip!", HEAVE, 0.45)
    _round(s, 2, "Little girl! Please come and help us!", "The little girl came running. Now there were three friends pulling the turnip!", HEAVE, 0.55)
    _round(s, 3, "Piggy! Piggy! Please come and help us!", "The pig came trotting. Now there were four friends pulling the turnip!", "Oink, oink! Heave-ho! Heave-ho!", 0.65)
    _round(s, 4, "Hare! Hare! Please come and help us!", "The hare came hopping. Now there were five friends pulling the turnip!", HEAVE, 0.75)

    # ---------------------------------------------------------------- 3 little Pip helps
    s = t.scene("Little Pip helps", "meadow_open", mood="chase", title="Little Pip helps")
    _turnip(s, bend=1.0)
    _line(s, 5)
    allp = [a[0] for a in LINE]
    s.say("hare", "Big Bear! Please come and help us!", *_poses(allp[:5], "grip"), tail=0.3)
    s.nar("The big bear came stomping. Now there were six friends pulling the turnip!", _come("bear", LINE[5][2]), ("fx", "mark", "bear", _above(5), {"at": "58%", "dur": 1.8, "text": "6"}),
          ("fx", "dust", 1260, 668, {"at": 1.5, "dur": 1.0, "size": 1.2}), ("fx", "dust", 1160, 668, {"at": 2.0, "dur": 1.0, "size": 1.2}),
          ("fx", "dust", 1060, 668, {"at": 2.5, "dur": 1.0, "size": 1.2}), *_poses(allp[:5], "grip"), tail=0.3)
    s.say("bear", HEAVE, *_poses(allp[:6], "pull"), ("set", "tn", "wobble", 0.85, {"at": 0.0, "dur": 0.5}), ("sfx", "creak", {"at": "20%", "gain": 0.45}), ("sfx", "creak", {"at": "65%", "gain": 0.45}), tail=0.3)
    s.nar("But the turnip was still stuck! It was stuck, stuck, stuck!", *_poses(allp[:6], "grip"), ("set", "tn", "wobble", 0.0, {"at": 0.0, "dur": 0.6}), ("fx", "sweat", "bear", 0, {"at": 0.2, "dur": 3.5}), tail=0.35)
    s.say("bear", "Little Pip! Please come and help us!", *_poses(allp[:6], "grip"), tail=0.3)
    s.nar("Little Pip came flying. Now there were seven friends pulling the turnip!", _come("pip", LINE[6][2]), ("hop", "pip", {"at": 1.0}), ("hop", "pip", {"at": 1.8}),
          ("fx", "mark", "pip", _above(6), {"at": "58%", "dur": 1.8, "text": "7"}), *_poses(allp[:6], "grip"), tail=0.3)
    s.say("pig", "Pip is so tiny. Can Pip really help?", *_poses(allp[:6], "grip"), ("pose", "pig", "think"), tail=0.3)
    s.say("pip", "Yes, I can! I am small, but I am strong!", *_poses(allp[:6], "grip"), ("hop", "pip", {"at": "35%"}), tail=0.3)
    s.nar("Now everyone held on tight, and they all pulled together!", *_poses(allp, "strain"), ("set", "tn", "wobble", 0.8, {"at": 0.3, "dur": 1.0}),
          ("cam", 620, 390, 1.06, {"at": 0.3, "dur": 3.2}), ("sfx", "creak", {"at": "50%", "gain": 0.5}))
    s.say("pip", "One, two, three... HEAVE-HO!", *_poses(allp, "strain"), ("set", "tn", "wobble", 1.0, {"at": 0.0, "dur": 0.6}), ("sfx", "creak", {"at": "30%", "gain": 0.5}),
          ("sfx", "creak", {"at": "75%", "gain": 0.55}), tail=0.3)
    s.nar("The turnip creaked, and it cracked. And then... POP!", *_poses(allp, "strain"), ("sfx", "creak", {"at": "15%", "gain": 0.5}), ("sfx", "creak", {"at": "42%", "gain": 0.55}),
          *_poses(allp[1:], "surprised", at="86%"), ("pose", "gpa", "surprised", {"at": "86%"}), ("set", "tn", "bend", 0.0, {"at": "86%", "dur": 0.12}),
          ("set", "tn", "out", 1.0, {"at": "86%", "dur": 1.2}), ("set", "tn", "wobble", 0.0, {"at": "86%", "dur": 0.2}),
          ("fx", "burst", TN_X + 40, 400, {"at": "86%", "dur": 1.5, "text": "POP!", "sfx": "pop"}), ("fx", "dust", TN_X, 664, {"at": "86%", "dur": 1.0, "size": 1.6, "sfx": False}),
          ("fx", "dust", TN_X + 195, 668, {"at": "86%+1.0", "dur": 1.0, "size": 1.3}), ("cam", 640, 360, 1.0, {"at": "86%", "dur": 0.8}), tail=0.2)
    falls = [("gpa", 80, "8%"), ("gma", 76, "22%"), ("kid", 84, "36%"), ("pig", 72, "50%"), ("hare", 86, "64%"), ("bear", 78, "78%")]
    acts = [("pose", "pip", "surprised"), ("hop", "pip", {"at": "10%"}), ("move", "pip", LINE[6][2], 500, {"at": "25%", "dur": 0.7})]
    for aid, deg, when in falls:                                            # everybody falls down like dominoes (the dust is silent: the thuds come with the bumps)
        _a, _kd, fx_, fk, _s = LINE[allp.index(aid)]
        acts += [("tilt", aid, deg, {"at": when, "dur": 0.4}), ("fx", "dust", fx_ + 140 * fk, 668, {"at": when + "+0.38", "dur": 1.0, "size": 0.8 + 0.3 * fk, "sfx": False})]
    s.nar("Out flew the turnip! And everybody fell down.", *acts, tail=0.3)
    acts = []
    for (aid, deg, _w), pct in zip(falls, (4, 21, 38, 55, 72, 88)):         # six "bump"s: one friend bounces on the ground with every word
        _a, _kd, fx_, fk, _s = LINE[allp.index(aid)]
        acts += [("tilt", aid, deg - 11, {"at": "%d%%-0.12" % pct, "dur": 0.12}), ("tilt", aid, deg, {"at": "%d%%" % pct, "dur": 0.16}),
                 ("fx", "dust", fx_ + 140 * fk, 668, {"at": "%d%%" % pct, "dur": 0.9, "size": 0.7 + 0.3 * fk})]
    s.nar("Bump, bump, bump, bump, bump, bump!", *acts, tail=0.3)
    s.nar("Nobody was hurt. They were just a little bit dizzy.", *_poses(allp[:6], "dizzy"), ("pose", "pip", "surprised"), tail=0.3)
    acts = [("move", "pip", LINE[6][2], LINE_Y["pip"], {"at": 0.9, "dur": 0.6}), ("hop", "pip", {"at": 1.5})]
    for aid, at in (("gpa", 0.0), ("gma", 0.2), ("kid", 0.4), ("pig", 0.6), ("hare", 0.8), ("bear", 1.0)):
        acts += [("tilt", aid, 0, {"at": at, "dur": 0.5}), ("pose", aid, "cheer", {"at": at + 0.3})]
    s.wait(1.8, *acts)
    s.say("bear", "Ha ha ha! We did it! We pulled up the enormous turnip!", *_poses(allp[:6], "laugh"), ("pose", "bear", "laugh"), tail=0.4)

    # ---------------------------------------------------------------- 4 hooray (and counting the friends)
    s = _cheer_scene(t, "Hooray, we did it!")
    s.say("pip", "Hooray! Even a tiny friend can help!", *_poses(allp[:6], "cheer"), ("hop", "pip", {"at": "30%"}), ("fx", "confetti", 0, 0, {"at": 0.3, "dur": 60.0}))
    s.nar("The tiniest friend had made a big difference!", *_poses(allp[:6], "happy"), ("fx", "sparkle", 640, 360, {"at": 0.2, "dur": 4.0, "r": 360}), ("fx", "hearts", "pip", 0, {"at": 0.4, "dur": 3.5}))
    s.nar("Let us count the friends who helped!", *_poses(allp[:6], "happy"), ("hop", "pip", {"at": "60%"}))
    for i, (aid, word) in enumerate(zip(allp, ("One!", "Two!", "Three!", "Four!", "Five!", "Six!", "Seven!"))):      # the numbers stay until the scene ends
        s.nar(word, ("hop", aid, {"at": 0.05}), ("fx", "mark", aid, _above(i) - (18 if aid == "pip" else 0), {"at": 0.0, "dur": 60.0, "text": str(i + 1)}), *_poses(allp[:6], "happy"), tail=0.32)
    s.nar("Seven good friends, and one enormous turnip!", *[("hop", aid, {"at": "%d%%" % (20 + 9 * j)}) for j, aid in enumerate(allp)], *_poses(allp[:6], "cheer"),
          ("fx", "sparkle", 640, 330, {"at": 0.2, "dur": 3.0, "r": 380}), tail=0.3)
    s = _cheer_scene(t, None)                                               # the same picture without the numbers (a scene change nobody notices)
    s.say("gma", "Thank you, my friends! Let us go home, and cook some turnip soup!", ("pose", "gma", "cheer"), ("hop", "gma", {"at": "40%"}), *_poses(["gpa", "kid", "pig", "hare", "bear"], "happy"),
          ("hop", "pip", {"at": "20%"}), ("fx", "confetti", 0, 0, {"at": 0.0, "dur": 60.0}), tail=0.5)

    # ---------------------------------------------------------------- 5 turnip soup
    s = t.scene("Turnip soup", "meadow_dusk", mood="triumph", title="Turnip soup for everyone")
    s.prop("pot", "pot", 640, 660, 1.05)
    for aid, kind, x, k, style in LINE:
        s.actor(aid, kind, SOUP_SEAT[aid], LINE_Y[aid] - 8, k, face=1 if SOUP_SEAT[aid] < 640 else -1, flat=True, **style)
    s.nar("That evening, Grandma cooked a big pot of yummy turnip soup.", ("fx", "steam", 640, 470, {"at": 0.0, "dur": 60.0}), ("pose", "gma", "happy"), ("fx", "sparkle", 640, 470, {"at": 0.4, "dur": 3.0, "r": 150}))
    names = ["gpa", "gma", "kid", "pig", "hare", "bear", "pip"]
    s.nar("There was enough for everyone: Grandpa, Grandma, the little girl, the pig, the hare, the big bear, and tiny Pip.",
          *[("hop", aid, {"at": "%d%%" % (18 + 10 * i)}) for i, aid in enumerate(names)], *_poses(names[:6], "happy"))
    s.say("kid", "Mmm! This turnip soup is so yummy!", *_poses(["gpa", "gma", "kid", "pig", "hare", "bear"], "eat"), ("sfx", "gulp", {"at": "80%", "gain": 0.6}))
    s.say("bear", "It is the best soup in the whole world!", ("pose", "bear", "eat"), ("sfx", "munch", {"at": "30%", "gain": 0.6}))
    s.nar("They all ate, and ate, and ate. Yum, yum, yum!", ("sfx", "munch", {"at": "35%", "gain": 0.6}), ("sfx", "munch", {"at": "55%", "gain": 0.6}), ("sfx", "gulp", {"at": "80%", "gain": 0.6}),
          ("fx", "hearts", "gma", 0, {"at": 0.3, "dur": 4.0}))
    s.nar("And from that day on, the friends always helped each other.", *_poses(names[:6], "happy"), ("fx", "sparkle", 640, 330, {"at": 0.2, "dur": 4.0, "r": 380}), ("hop", "pip", {"at": "50%"}), tail=0.8)

    _outro(t, "Remember, little ones: when we work together, even the biggest job becomes easy.", caption="Together, big jobs become easy!")
    return t


# ================================================================================================ stone soup
SS_X, SS_Y, SS_K = 640, 664, 1.0                 # the soup pot (the middle of its fire on the ground)
SS_FOX = 470                                     # the fox stands on the left of the pot
SS_GIVE = 840                                    # a friend stands here and throws a vegetable into the pot
SS_MOUTH = (SS_X - 10, SS_Y - 150 * SS_K)        # the middle of the soup, where the vegetables land
FOX_T = dict(fur="#E8893A", scarf="#3E8EDE")     # the hungry traveller
PIG_V = dict(outfit="#8A6BD6", hat_kind="cap", hat_color="#FF8A3D")
GOAT_V = dict(fur="#F7F1E3", scarf="#FF6B8B", horns=0.8)
# the friends who bring a vegetable: id, kind, size, style, how they walk in, the vegetable, and the six lines of their visit
SS_GUESTS = [
    dict(id="hare", kind="hare", k=0.95, style={}, how="jump", veg="carrot", cook=0.2,
         arrive="A hare came hopping by.", hello="Hello, Fox! What are you cooking?", offer="I am making stone soup! Would you like to help?",
         give="Yes, please! I have a carrot for your soup.", plop="Plop! In went a bright orange carrot.", taste="Mmm! It is getting yummy. Please come back for dinner!"),
    dict(id="pig", kind="pig", k=0.9, style=PIG_V, how=None, veg="potato", cook=0.4,
         arrive="A pig came trotting by.", hello="Hello, Fox! What smells so good?", offer="It is my stone soup! Would you like to help?",
         give="Oink, oink! I have a potato for your soup.", plop="Plop! In went a big brown potato.", taste="Mmm! It is getting yummier. Please come back for dinner!"),
    dict(id="goat", kind="goat", k=0.95, style=GOAT_V, how=None, veg="cabbage", cook=0.6,
         arrive="A goat came skipping by.", hello="Hello, Fox! Is that soup made from a stone?", offer="Yes, it is! Would you like to help?",
         give="Maa, maa! I have a cabbage for your soup.", plop="Plop! In went a big green cabbage.", taste="Mmm! It smells so good. Please come back for dinner!"),
    dict(id="gma", kind="girl", k=0.95, style=OLD_W, how=None, veg="onion", cook=0.8,
         arrive="Then Granny came walking by.", hello="Hello, Fox! Soup from a stone? How wonderful!", offer="Would you like to help, Granny?",
         give="Of course, dear! I have an onion for your soup.", plop="Plop! In went a round, golden onion.", taste="Mmm! It smells just like home. Please come back for dinner!"),
    dict(id="kid", kind="girl", k=0.8, style=KID, how=None, veg="tomato", cook=1.0,
         arrive="Last of all, a little girl came running by.", hello="Hello, Fox! Can I help, too?", offer="Yes, please! Every friend can help.",
         give="I have a tomato for your soup!", plop="Plop! In went a juicy red tomato.", taste="Mmm! The soup is ready! Please tell everybody!"),
]
SS_COUNT = [("stone", "One! A smooth grey stone."), ("carrot", "Two! A bright orange carrot."), ("potato", "Three! A big brown potato."),
            ("cabbage", "Four! A big green cabbage."), ("onion", "Five! A round, golden onion."), ("tomato", "Six! A juicy red tomato.")]
SS_SEAT = {"hare": 260, "pig": 365, "fox": 470, "goat": 810, "gma": 915, "kid": 1020}      # where everybody sits at dinner
SS_VEGS = ["carrot", "potato", "cabbage", "onion", "tomato"]


def _ss_pot(s, done, stone=1.0, **st):
    """The soup pot of the stone soup with the vegetables of the first `done` guests already in it."""
    have = {v: 1.0 for v in SS_VEGS[:done]}
    return s.prop("pot", "pot", SS_X, SS_Y, SS_K, kind="stone", water=1.0, stone=stone, stir=1.0, cook=(SS_GUESTS[done - 1]["cook"] if done else 0.0), **have, **st)


def _ss_village(s, done):
    """The village: two cottages behind, the pot (with the vegetables of the first `done` guests in it), the vegetables waiting to be thrown, and the fox next to the pot."""
    s.prop("c1", "cottage", 175, 606, 0.78, wall="#FFF1D0", roof="#5FA8D3")
    s.prop("c2", "cottage", 1135, 606, 0.82, wall="#EAF4FF", roof="#D9654F")
    if done:
        _ss_pot(s, done)
    else:
        s.prop("pot", "pot", SS_X, SS_Y, SS_K, kind="stone", water=0.0, stone=0.0, stir=0.0, cook=0.0)
    for g in SS_GUESTS:
        k = g["k"]
        sx, sy = SS_GIVE - 26 * k, 650 - 110 * k
        s.prop("v_" + g["id"], "veg", sx, sy, 1.0, kind=g["veg"], u=0.0, dx=SS_MOUTH[0] - sx, dy=SS_MOUTH[1] - sy, h=150.0, turns=1.5, size=0.8)
    s.actor("fox", "wolf", SS_FOX, 650, 0.95, face=1, flat=True, **FOX_T)


def _ss_visit(s, g, steam=True):
    """One friend comes to the pot and throws a vegetable in (six beats)."""
    gid, k = g["id"], g["k"]
    walk = dict(at=0.2, speed=230 if g["how"] else 190)
    if g["how"]:
        walk["pose"] = g["how"]
    s.actor(gid, g["kind"], 1500, 650, k, face=-1, flat=True, **g["style"])
    s.nar(g["arrive"], ("walk", gid, SS_GIVE, 650, walk), tail=0.3)
    s.say(gid, g["hello"], ("pose", gid, "happy"), tail=0.3)
    s.say("fox", g["offer"], ("pose", "fox", "cheer", {"at": "30%"}), ("hop", "fox", {"at": "30%"}), ("pose", "fox", "idle", {"at": "92%"}), tail=0.3)
    s.say(gid, g["give"], ("pose", gid, "cheer", {"at": "55%"}), tail=0.2)
    s.nar(g["plop"], ("set", "v_" + gid, "u", 1.0, {"at": 0.0, "dur": 0.6}), ("set", "pot", g["veg"], 1.0, {"at": 0.52, "dur": 0.3}),
          ("sfx", "splash", {"at": 0.55, "gain": 0.5}), ("pose", gid, "happy", {"at": 1.0}), ("pose", "fox", "happy", {"at": 0.5}),
          ("fx", "sparkle", SS_MOUTH[0], SS_MOUTH[1] - 20, {"at": 0.55, "dur": 2.0, "r": 120}), lead=0.5, tail=0.3)       # (the vegetable lands as "Plop!" begins)
    s.say("fox", g["taste"], ("pose", "fox", "eat"), ("set", "pot", "cook", g["cook"], {"at": 0.0, "dur": 1.4}), ("sfx", "gulp", {"at": "70%", "gain": 0.6}),
          ("pose", "fox", "happy", {"at": "80%"}), ("walk", gid, 1500, 650, {"at": 0.4, "speed": 200, "pose": "walk"}), tail=0.3)


def stone_soup(lang="en"):
    t = Tale("tale-stone-soup", "Stone Soup | Fairy Tale Story for Kids | Bibi Buzz TV",
             "A hungry little fox has nothing to eat except a smooth, round stone. So he decides to make stone soup! One by one, a hare, a pig, a goat, Granny and a little girl bring "
             "a carrot, a potato, a cabbage, an onion and a tomato. Can a stone make a yummy soup? Watch the classic folk tale about sharing, in a gentle, colorful animated story "
             "in simple English for toddlers and preschoolers. Count the ingredients and learn the names of the vegetables, too!",
             TAGS + ["stone soup", "stone soup story", "sharing story", "kindness story", "vegetables for kids", "learn vegetables", "counting story"],
             {"nar": NAR, "fox": (GUY, "-4%", "+12Hz"), "hare": ("en-US-EricNeural", "+4%", "+10Hz"), "pig": (ARIA, "+4%", "+20Hz"),
              "goat": ("en-US-ChristopherNeural", "+6%", "+16Hz"), "gma": (ARIA, "-12%", "-6Hz"), "kid": (ANA, "+2%", "+18Hz")}, lang=lang)
    t.bubble_tint = {"fox": "#FFE4CC", "hare": "#FFF0DC", "pig": "#EDE4FF", "goat": "#FFE8F0", "gma": "#DFF4DF", "kid": "#FFE3EE"}
    full = dict(kind="stone", water=1.0, stone=1.0, cook=1.0, stir=1.0, **{v: 1.0 for v in SS_VEGS})
    t.cover = dict(bg="meadow_dusk", title=("STONE", "SOUP"), size=118, gap=116,
                   props=[("pot", "pot", 330, 712, 1.55, full),
                          ("v1", "veg", 150, 335, 1.0, dict(kind="carrot", rest=1.0, size=0.95)), ("v2", "veg", 255, 285, 1.0, dict(kind="onion", rest=1.0, size=0.95)),
                          ("v3", "veg", 330, 350, 1.0, dict(kind="cabbage", rest=1.0, size=0.95)), ("v4", "veg", 70, 235, 1.0, dict(kind="tomato", rest=1.0, size=0.95))],
                   actors=[("fox", "wolf", 690, 712, 1.35, 1, "cheer", dict(FOX_T)), ("hare", "hare", 840, 712, 1.1, -1, "happy", {}), ("pig", "pig", 970, 712, 1.1, -1, "happy", PIG_V),
                           ("goat", "goat", 1080, 712, 1.1, -1, "happy", GOAT_V), ("gma", "girl", 1180, 712, 1.0, -1, "happy", OLD_W)])
    _intro(t, ("STONE", "SOUP"), "Today's story is... Stone Soup!")

    # ---------------------------------------------------------------- 1 a hungry fox finds a stone
    s = t.scene("The long road", "meadow_open", mood="calm", title="A hungry fox")
    s.prop("stone", "stone", 905, 656, 1.0, show=True)
    s.actor("fox", "wolf", -160, 650, 0.95, face=1, flat=True, **FOX_T)
    s.nar("Once upon a time, a little fox walked down a long, long road.", ("walk", "fox", 330, 650, {"fit": True}))
    s.nar("He had walked all day, and he was very, very hungry.", ("pose", "fox", "tired", {"at": 0.3}))
    s.nar("His tummy went rumble, rumble, rumble!", ("pose", "fox", "sad", {"at": 0.2}), ("sfx", "rumble", {"at": "38%", "gain": 0.9}), ("sfx", "rumble", {"at": "66%", "gain": 0.9}), tail=0.7)
    s.say("fox", "Oh dear! I am so hungry. But I have no food at all.", ("pose", "fox", "sad"))
    s.nar("Then he saw something on the road. It was a smooth, round stone.", ("walk", "fox", 640, 650, {"at": 0.4, "speed": 170}), ("pose", "fox", "surprised", {"at": "55%"}),
          ("fx", "mark", 905, 520, {"at": "50%", "dur": 1.8, "text": "!"}))
    s.say("fox", "A stone! I know what I will do. I will make stone soup!", ("walk", "fox", 800, 650, {"at": 0.0, "speed": 170}), ("pose", "fox", "plant", {"at": 0.9}),
          ("hide", "stone", {"at": 1.7}), ("hold", "fox", "stone", {"at": 1.7}), ("pose", "fox", "cheer", {"at": 2.1}), ("hop", "fox", {"at": 2.3}), ("fx", "sparkle", 840, 440, {"at": 2.0, "dur": 2.0, "r": 160}))
    s.nar("So off he went, to find a village with a big, warm fire.", ("walk", "fox", 1480, 650, {"at": 0.3, "speed": 150, "pose": "walk"}), tail=0.3)

    # ---------------------------------------------------------------- 2 the stone goes into the pot, the hare and the pig help
    s = t.scene("The village", "meadow", mood="happy", title="Stone in the pot")
    _ss_village(s, 0)
    s.actor("fox", "wolf", -160, 650, 0.95, face=1, flat=True, hold="stone", **FOX_T)           # (the fox walks in from the left, with the stone)
    s.nar("Soon, the fox came to a little village.", ("walk", "fox", SS_FOX, 650, {"fit": True}))
    s.nar("In the middle of the village, there was a big, empty pot.", ("fx", "sparkle", SS_X, 520, {"at": 0.6, "dur": 2.4, "r": 150}))
    s.say("fox", "Hello, everybody! I am going to make stone soup!", ("pose", "fox", "cheer", {"at": "20%"}), ("hop", "fox", {"at": "20%"}))
    s.nar("First, he filled the pot with water. Splash!", ("set", "pot", "water", 1.0, {"at": "66%", "dur": 1.0}), ("sfx", "splash", {"at": "84%", "gain": 0.7}),
          ("fx", "sparkle", SS_X, 520, {"at": "84%", "dur": 2.0, "r": 130}))
    s.nar("Then he popped in the stone. Plop!", ("pose", "fox", "cheer", {"at": 0.0}), ("set", "pot", "stone", 1.0, {"at": "60%", "dur": 0.55}), ("hold", "fox", None, {"at": "56%"}),
          ("sfx", "splash", {"at": "60%+0.45", "gain": 0.55}), ("pose", "fox", "happy", {"at": "92%"}))
    s.nar("Now the fox stirred, and stirred, and stirred.", ("set", "pot", "stir", 1.0, {"at": 0.2, "dur": 0.6}), ("fx", "steam", SS_X, 470, {"at": 0.4, "dur": 60.0}), ("pose", "fox", "talk", {"at": 0.3}))
    s.say("fox", "Mmm, stone soup! It will be good. But a little help would make it even better.", ("pose", "fox", "think"))
    for g in SS_GUESTS[:2]:
        _ss_visit(s, g)

    # ---------------------------------------------------------------- 3 the goat and Granny help
    s = t.scene("The village", "meadow", mood="happy", title="More friends help")
    _ss_village(s, 2)
    s.nar("The fox stirred the pot, and the soup smelled better and better.", ("fx", "steam", SS_X, 470, {"at": 0.0, "dur": 60.0}), ("pose", "fox", "happy", {"at": 0.3}))
    for g in SS_GUESTS[2:4]:
        _ss_visit(s, g)

    # ---------------------------------------------------------------- 4 the little girl brings the last vegetable
    s = t.scene("The village", "meadow", mood="happy", title="The last vegetable")
    _ss_village(s, 4)
    s.nar("The soup was almost ready. It smelled so good!", ("fx", "steam", SS_X, 470, {"at": 0.0, "dur": 60.0}), ("fx", "hearts", "fox", 0, {"at": 0.3, "dur": 3.0}), tail=0.3)
    _ss_visit(s, SS_GUESTS[4])

    # ---------------------------------------------------------------- 5 dinner time (and counting what is in the soup)
    s = t.scene("Dinner time", "meadow_dusk", mood="triumph", title="Dinner time")
    s.prop("pot", "pot", SS_X, SS_Y, SS_K, kind="stone", water=1.0, stone=1.0, stir=1.0, cook=1.0, **{v: 1.0 for v in SS_VEGS})
    for i, (v, _line) in enumerate(SS_COUNT):
        s.prop("n%d" % i, "veg", 280 + 144 * i, 262, 1.0, kind=v, rest=1.0, pop=0.0, size=1.15)
    s.actor("fox", "wolf", SS_FOX, 650, 0.95, face=1, flat=True, **FOX_T)
    others = [g for g in SS_GUESTS]
    for g in others:
        left = SS_SEAT[g["id"]] < SS_X
        s.actor(g["id"], g["kind"], -200 if left else 1500, 650, g["k"], face=1 if left else -1, flat=True, **g["style"])
    s.say("fox", "The soup is ready! Dinner time, my friends!", ("pose", "fox", "cheer"), ("hop", "fox", {"at": "40%"}), ("fx", "steam", SS_X, 470, {"at": 0.0, "dur": 60.0}),
          ("fx", "sparkle", SS_X, 480, {"at": 0.3, "dur": 3.0, "r": 200}))
    arrive = [("hare", 0.2), ("pig", 0.9), ("kid", 0.2), ("gma", 0.9), ("goat", 1.6)]
    acts = []
    for gid, at in arrive:
        left = SS_SEAT[gid] < SS_X
        acts.append(("walk", gid, SS_SEAT[gid], 650, {"at": at, "speed": 250, "pose": "walk"}))
    s.nar("All the friends came back, with their bowls and spoons.", *acts, ("pose", "fox", "happy"), tail=0.5)
    s.say("goat", "Maa, maa! It smells so good!", ("pose", "goat", "happy"), tail=0.3)
    s.say("pig", "Oink, oink! I am so hungry!", ("pose", "pig", "happy"), tail=0.3)
    allsay = ["fox", "hare", "pig", "goat", "gma", "kid"]
    s.nar("They all tasted the soup. Yum, yum, yum!", *[("pose", a, "eat") for a in allsay], ("sfx", "munch", {"at": "30%", "gain": 0.6}), ("sfx", "munch", {"at": "55%", "gain": 0.6}),
          ("sfx", "gulp", {"at": "85%", "gain": 0.6}), ("fx", "hearts", "gma", 0, {"at": 0.4, "dur": 3.5}))
    s.say("hare", "This is the best soup I have ever tasted!", *[("pose", a, "happy") for a in allsay], ("hop", "hare", {"at": "50%"}))
    s.say("gma", "And it is made from a stone!", ("pose", "gma", "laugh"))
    s.say("fox", "A stone made the soup, but you made it the best! Thank you for sharing, my friends.", ("pose", "fox", "happy"), ("fx", "hearts", "fox", 0, {"at": "40%", "dur": 3.5}))
    s.nar("Let us count what is in the stone soup!", *[("pose", a, "happy") for a in allsay], ("fx", "sparkle", SS_X, 300, {"at": 0.3, "dur": 3.0, "r": 320}))
    for i, (v, line) in enumerate(SS_COUNT):                                  # the numbers and the vegetables stay until the scene ends
        x = 280 + 144 * i
        s.nar(line, ("set", "n%d" % i, "pop", 1.0, {"at": 0.05, "dur": 0.4}), ("fx", "mark", x, 168, {"at": 0.05, "dur": 60.0, "text": str(i + 1)}), tail=0.3)
    s.nar("Six yummy things, and six happy friends!", *[("hop", a, {"at": "%d%%" % (15 + 11 * j)}) for j, a in enumerate(allsay)], *[("pose", a, "cheer") for a in allsay],
          ("fx", "sparkle", SS_X, 330, {"at": 0.2, "dur": 3.0, "r": 380}), ("fx", "confetti", 0, 0, {"at": 0.4, "dur": 60.0}), tail=0.8)

    _outro(t, "Remember, little ones: when we share, there is always enough for everyone.", caption="Sharing is caring!")
    return t


TALES = {"three-little-pigs": three_little_pigs, "tortoise-and-hare": tortoise_and_hare, "goldilocks": goldilocks,
         "red-riding-hood": red_riding_hood, "gingerbread-man": gingerbread_man, "three-billy-goats": three_billy_goats,
         "enormous-turnip": enormous_turnip, "stone-soup": stone_soup}


def build(key, lang="en"):
    """A fresh Tale of TALES[key] in `lang` ("en", or "tr" = the Turkish lines, voices, title and description of tales_tr.py)."""
    t = TALES[key](lang)
    if lang != "en":
        from . import tales_tr
        tales_tr.localize(t, key)
    return t
