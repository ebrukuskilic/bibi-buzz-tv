"""The fairy tales (public-domain classics) as story scripts, told in short, simple sentences for ages 2-6."""
from .story import Tale

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


TALES = {"three-little-pigs": three_little_pigs, "tortoise-and-hare": tortoise_and_hare, "goldilocks": goldilocks}


def build(key, lang="en"):
    """A fresh Tale of TALES[key] in `lang` ("en", or "tr" = the Turkish lines, voices, title and description of tales_tr.py)."""
    t = TALES[key](lang)
    if lang != "en":
        from . import tales_tr
        tales_tr.localize(t, key)
    return t
