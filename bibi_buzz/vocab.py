"""Teaching content: word lists (with Noto emoji codes), fun facts, sounds, phrases.

Item tuple: (word, emoji_code, extra_line_or_None, sound_or_None)
- extra_line is spoken after the basic sentence (a fun fact or a short sentence)
- sound is what the animal / vehicle says (used by the sound lessons)
Plural words (grapes, socks...) and uncountable words (milk, bread...) are listed in PLURAL / MASS.
"""

PLURAL = {"grapes", "cherries", "blueberries", "socks", "gloves", "pants", "shoes", "glasses", "blocks", "eyes",
          "ears", "hands", "feet", "legs", "teeth"}
MASS = {"milk", "bread", "cheese", "rice", "broccoli", "corn", "popcorn", "soup", "ice cream", "snow", "rain", "wind",
        "water", "juice", "lightning", "pasta"}
A_EXCEPT = {"unicorn": "a", "uniform": "a", "hour": "an", "x-ray": "an", "ice cream": "an", "yo-yo": "a"}


def art(word):
    """'an apple', 'a banana', 'grapes' (plural / uncountable words get no article)."""
    if word in PLURAL or word in MASS:
        return word
    a = A_EXCEPT.get(word) or ("an" if word[0] in "aeiou" else "a")
    return a + " " + word


def cap(s):
    return s[0].upper() + s[1:]


def be(word):
    return "are" if word in PLURAL else "is"


def this(word):
    return "These are" if word in PLURAL else "This is"


# ------------------------------------------------------------------ categories
CATS = {
    "fruits": dict(
        title="Fruits", topic="yummy fruits", sentence="{This} {a}.", tags=["fruits", "fruit names"],
        items=[
            ("apple", "1f34e", "Apples can be red, green, or yellow.", None),
            ("banana", "1f34c", "Bananas are yellow and sweet.", None),
            ("orange", "1f34a", "Oranges are round and juicy.", None),
            ("grapes", "1f347", "Grapes grow in bunches.", None),
            ("strawberry", "1f353", "Strawberries are red with tiny seeds.", None),
            ("watermelon", "1f349", "Watermelons are big, green, and juicy.", None),
            ("pineapple", "1f34d", "Pineapples are spiky outside and sweet inside.", None),
            ("cherries", "1f352", "Cherries are small and red.", None),
            ("peach", "1f351", "Peaches are soft and fuzzy.", None),
            ("pear", "1f350", "Pears are sweet and juicy.", None),
            ("lemon", "1f34b", "Lemons are yellow and sour.", None),
            ("mango", "1f96d", "Mangoes are sweet and orange inside.", None),
            ("kiwi", "1f95d", "Kiwis are green inside, with tiny black seeds.", None),
            ("coconut", "1f965", "Coconuts have sweet water inside.", None),
            ("melon", "1f348", "Melons are sweet and juicy.", None),
            ("blueberries", "1fad0", "Blueberries are small and blue.", None),
        ]),
    "vegetables": dict(
        title="Vegetables", topic="healthy vegetables", sentence="{This} {a}.", tags=["vegetables", "healthy food"],
        items=[
            ("carrot", "1f955", "Carrots are orange and crunchy.", None),
            ("tomato", "1f345", "Tomatoes are red and juicy.", None),
            ("corn", "1f33d", "Corn is yellow and sweet.", None),
            ("broccoli", "1f966", "Broccoli looks like a tiny tree.", None),
            ("potato", "1f954", "Potatoes grow under the ground.", None),
            ("cucumber", "1f952", "Cucumbers are green and cool.", None),
            ("eggplant", "1f346", "Eggplants are shiny and purple.", None),
            ("onion", "1f9c5", "Onions have many layers.", None),
            ("garlic", "1f9c4", "Garlic has a strong smell.", None),
            ("mushroom", "1f344", "Mushrooms grow in the forest.", None),
            ("lettuce", "1f96c", "Lettuce is green and crispy.", None),
        ]),
    "farm": dict(
        title="Farm Animals", topic="farm animals and the sounds they make", sentence="{This} {a}.",
        tags=["farm animals", "animal sounds"], sound_mode=True,
        items=[
            ("cow", "1f42e", "Cows give us milk.", "moo"),
            ("pig", "1f437", "Pigs love to roll in the mud.", "oink oink"),
            ("sheep", "1f411", "Sheep have soft, fluffy wool.", "baa baa"),
            ("duck", "1f986", "Ducks love to swim.", "quack quack"),
            ("chicken", "1f414", "Chickens lay eggs.", "cluck cluck"),
            ("horse", "1f434", "Horses can run very fast.", "neigh"),
            ("goat", "1f410", "Goats like to climb.", "maa maa"),
            ("rooster", "1f413", "Roosters wake up the farm in the morning.", "cock-a-doodle-doo"),
            ("dog", "1f436", "Dogs are our best friends.", "woof woof"),
            ("cat", "1f431", "Cats love to purr.", "meow"),
            ("rabbit", "1f430", "Rabbits hop, hop, hop!", None),
        ]),
    "wild": dict(
        title="Wild Animals", topic="wild animals and the sounds they make", sentence="{This} {a}.",
        tags=["wild animals", "zoo animals", "animal sounds"], sound_mode=True,
        items=[
            ("lion", "1f981", "Lions are big cats with a mane.", "roar"),
            ("tiger", "1f42f", "Tigers have orange fur with black stripes.", "grrr"),
            ("elephant", "1f418", "Elephants have a very long trunk.", "toot toot"),
            ("monkey", "1f435", "Monkeys love bananas.", "ooh ooh ah ah"),
            ("bear", "1f43b", "Bears love honey.", "grrr"),
            ("wolf", "1f43a", "Wolves howl at the moon.", "awoo"),
            ("frog", "1f438", "Frogs jump and swim.", "ribbit"),
            ("owl", "1f989", "Owls are awake at night.", "hoo hoo"),
            ("snake", "1f40d", "Snakes slide on the ground.", "sss"),
            ("giraffe", "1f992", "Giraffes have very long necks.", None),
            ("zebra", "1f993", "Zebras have black and white stripes.", None),
            ("panda", "1f43c", "Pandas love to eat bamboo.", None),
            ("koala", "1f428", "Koalas sleep in trees.", None),
            ("fox", "1f98a", "Foxes have fluffy tails.", None),
            ("hippo", "1f99b", "Hippos love to stay in the water.", None),
            ("kangaroo", "1f998", "Kangaroos hop with their strong legs.", None),
            ("crocodile", "1f40a", "Crocodiles have big teeth.", None),
            ("penguin", "1f427", "Penguins waddle on the ice.", None),
            ("parrot", "1f99c", "Parrots can copy words.", "hello"),
            ("deer", "1f98c", "Deer are gentle forest animals.", None),
        ]),
    "sea": dict(
        title="Sea Animals", topic="animals that live in the sea", sentence="{This} {a}.",
        tags=["sea animals", "ocean animals"],
        items=[
            ("fish", "1f41f", "Fish swim with their fins.", None),
            ("whale", "1f433", "Whales are the biggest animals in the sea.", None),
            ("dolphin", "1f42c", "Dolphins are smart and playful.", None),
            ("octopus", "1f419", "Octopuses have eight arms.", None),
            ("crab", "1f980", "Crabs walk sideways.", None),
            ("shark", "1f988", "Sharks have sharp teeth.", None),
            ("turtle", "1f422", "Turtles carry their shell on their back.", None),
            ("shrimp", "1f990", "Shrimp are tiny and pink.", None),
            ("seal", "1f9ad", "Seals love to splash in the water.", None),
            ("shell", "1f41a", "Shells wash up on the beach.", None),
        ]),
    "insects": dict(
        title="Bugs and Insects", topic="little bugs and insects", sentence="{This} {a}.",
        tags=["insects", "bugs"],
        items=[
            ("butterfly", "1f98b", "Butterflies have colorful wings.", None),
            ("ladybug", "1f41e", "Ladybugs are red with black dots.", None),
            ("bee", "1f41d", "Bees make honey.", "buzz buzz"),
            ("ant", "1f41c", "Ants work together.", None),
            ("snail", "1f40c", "Snails move very slowly.", None),
            ("caterpillar", "1f41b", "Caterpillars turn into butterflies.", None),
            ("cricket", "1f997", "Crickets sing at night.", "chirp chirp"),
            ("spider", "1f577", "Spiders have eight legs.", None),
        ]),
    "birds": dict(
        title="Birds", topic="birds that fly and swim", sentence="{This} {a}.", tags=["birds"],
        items=[
            ("bird", "1f426", "Birds can fly high in the sky.", "tweet tweet"),
            ("duck", "1f986", "Ducks love to swim.", "quack quack"),
            ("owl", "1f989", "Owls are awake at night.", "hoo hoo"),
            ("penguin", "1f427", "Penguins cannot fly, but they swim very well.", None),
            ("parrot", "1f99c", "Parrots have bright, colorful feathers.", None),
            ("swan", "1f9a2", "Swans are graceful and white.", None),
            ("flamingo", "1f9a9", "Flamingos are pink and stand on one leg.", None),
            ("peacock", "1f99a", "Peacocks have beautiful tail feathers.", None),
            ("eagle", "1f985", "Eagles fly very high.", None),
            ("chick", "1f424", "Chicks are small and fluffy.", "peep peep"),
        ]),
    "vehicles": dict(
        title="Vehicles", topic="cars, trucks, and things that go", sentence="{This} {a}.",
        tags=["vehicles", "cars and trucks", "transportation"],
        items=[
            ("car", "1f697", "Cars take us to many places.", "beep beep"),
            ("bus", "1f68c", "A bus carries lots of people.", "beep beep"),
            ("taxi", "1f695", "A taxi is yellow.", "honk honk"),
            ("fire truck", "1f692", "Fire trucks help put out fires.", "wee-oo wee-oo"),
            ("ambulance", "1f691", "An ambulance helps sick people.", "wee-oo wee-oo"),
            ("police car", "1f693", "Police cars keep us safe.", "wee-oo wee-oo"),
            ("truck", "1f69a", "Trucks carry big, heavy things.", "vroom"),
            ("tractor", "1f69c", "Tractors work on the farm.", "chug chug"),
            ("bicycle", "1f6b2", "You pedal a bicycle with your feet.", "ring ring"),
            ("train", "1f686", "Trains go along the tracks.", "choo choo"),
            ("airplane", "2708", "Airplanes fly in the sky.", "whoosh"),
            ("helicopter", "1f681", "Helicopters have spinning blades.", "whirr"),
            ("rocket", "1f680", "Rockets fly to space.", "whoosh"),
            ("ship", "1f6a2", "Ships sail on the sea.", "toot toot"),
            ("motorcycle", "1f3cd", "Motorcycles have two wheels.", "vroom vroom"),
        ]),
    "body": dict(
        title="My Body", topic="the parts of my body", sentence="{This} {my}.", tags=["body parts", "my body"],
        items=[
            ("eyes", "1f441", "I see with my eyes.", None),
            ("ears", "1f442", "I hear with my ears.", None),
            ("nose", "1f443", "I smell with my nose.", None),
            ("mouth", "1f444", "I eat and talk with my mouth.", None),
            ("tongue", "1f445", "I taste with my tongue.", None),
            ("hand", "270b", "I clap with my hands.", None),
            ("foot", "1f9b6", "I walk with my feet.", None),
            ("leg", "1f9b5", "I jump with my legs.", None),
            ("tooth", "1f9b7", "I brush my teeth every day.", None),
            ("arm", "1f4aa", "My arms are strong.", None),
        ]),
    "clothes": dict(
        title="Clothes", topic="clothes we wear", sentence="{This} {a}.", tags=["clothes", "what to wear"],
        items=[
            ("shirt", "1f455", "I wear a shirt on my body.", None),
            ("pants", "1f456", "I wear pants on my legs.", None),
            ("dress", "1f457", "A dress is nice for a party.", None),
            ("shoes", "1f45f", "I wear shoes on my feet.", None),
            ("hat", "1f452", "A hat keeps the sun off my head.", None),
            ("socks", "1f9e6", "Socks keep my feet warm.", None),
            ("gloves", "1f9e4", "Gloves keep my hands warm.", None),
            ("scarf", "1f9e3", "A scarf keeps my neck warm.", None),
            ("coat", "1f9e5", "I wear a coat when it is cold.", None),
            ("backpack", "1f392", "I carry my things in a backpack.", None),
            ("glasses", "1f453", "Glasses help people see clearly.", None),
        ]),
    "food": dict(
        title="Yummy Food", topic="yummy food and drinks", sentence="{This} {a}.", tags=["food", "yummy food"],
        items=[
            ("bread", "1f35e", "Bread is soft and tasty.", None),
            ("cheese", "1f9c0", "Cheese is made from milk.", None),
            ("egg", "1f95a", "Eggs come from chickens.", None),
            ("milk", "1f95b", "Milk makes our bones strong.", None),
            ("pizza", "1f355", "Pizza has cheese on top.", None),
            ("cake", "1f382", "We eat cake on birthdays.", None),
            ("ice cream", "1f368", "Ice cream is cold and sweet.", None),
            ("cookie", "1f36a", "Cookies are crunchy and sweet.", None),
            ("burger", "1f354", "A burger has a bun.", None),
            ("rice", "1f35a", "Rice is small and white.", None),
            ("cupcake", "1f9c1", "A cupcake is a little cake.", None),
            ("popcorn", "1f37f", "Popcorn goes pop, pop, pop!", None),
            ("sandwich", "1f96a", "A sandwich has two slices of bread.", None),
            ("soup", "1f372", "Soup is warm and tasty.", None),
        ]),
    "weather": dict(
        title="Weather", topic="the weather outside", sentence="{This} {a}.", tags=["weather", "seasons"],
        items=[
            ("sun", "2600", "It is sunny and warm.", None),
            ("cloud", "2601", "Clouds float in the sky.", None),
            ("rain", "1f327", "Rain makes the flowers grow.", None),
            ("snow", "2744", "Snow is white and cold.", None),
            ("rainbow", "1f308", "A rainbow has many colors.", None),
            ("lightning", "26a1", "Lightning is bright and fast.", None),
            ("wind", "1f32c", "The wind blows the leaves.", None),
            ("umbrella", "2602", "An umbrella keeps us dry in the rain.", None),
        ]),
    "nature": dict(
        title="Nature", topic="plants and nature around us", sentence="{This} {a}.", tags=["nature", "plants"],
        items=[
            ("tree", "1f333", "Trees give us shade.", None),
            ("flower", "1f33b", "Flowers smell nice.", None),
            ("rose", "1f339", "Roses are red and pretty.", None),
            ("tulip", "1f337", "Tulips bloom in spring.", None),
            ("cactus", "1f335", "A cactus grows in the desert.", None),
            ("mountain", "26f0", "Mountains are very tall.", None),
            ("volcano", "1f30b", "A volcano can erupt.", None),
            ("leaf", "1f343", "Leaves are green.", None),
            ("star", "2b50", "Stars shine at night.", None),
            ("moon", "1f319", "The moon glows in the night sky.", None),
            ("earth", "1f30d", "Earth is our home.", None),
        ]),
    "feelings": dict(
        title="Feelings", topic="how we feel", sentence="I feel {w}.", tags=["feelings", "emotions"],
        items=[
            ("happy", "1f604", "When I am happy, I smile.", None),
            ("sad", "1f622", "When I am sad, I can ask for a hug.", None),
            ("angry", "1f620", "When I am angry, I take a deep breath.", None),
            ("surprised", "1f62e", "Wow! Surprise!", None),
            ("sleepy", "1f634", "When I am sleepy, it is time for bed.", None),
            ("scared", "1f628", "When I am scared, I can tell a grown-up.", None),
            ("silly", "1f61c", "I like to be silly and laugh.", None),
            ("loved", "1f60d", "I feel loved when I get a hug.", None),
        ]),
    "school": dict(
        title="At School", topic="things we use at school", sentence="{This} {a}.", tags=["school", "back to school"],
        items=[
            ("book", "1f4d6", "We read a book.", None),
            ("pencil", "270f", "We write with a pencil.", None),
            ("crayon", "1f58d", "We color with crayons.", None),
            ("scissors", "2702", "Scissors cut paper.", None),
            ("ruler", "1f4cf", "A ruler helps us measure.", None),
            ("clock", "23f0", "A clock tells the time.", None),
            ("bell", "1f514", "The bell rings, ding dong!", None),
            ("paint", "1f3a8", "We paint with bright colors.", None),
            ("globe", "1f30e", "A globe shows the whole world.", None),
        ]),
    "toys": dict(
        title="Toys", topic="fun toys to play with", sentence="{This} {a}.", tags=["toys", "playtime"],
        items=[
            ("ball", "26bd", "We kick the ball.", None),
            ("teddy bear", "1f9f8", "A teddy bear is soft and cuddly.", None),
            ("kite", "1fa81", "A kite flies high in the wind.", None),
            ("blocks", "1f9f1", "We build towers with blocks.", None),
            ("balloon", "1f388", "A balloon floats in the air.", None),
            ("puzzle", "1f9e9", "A puzzle has many pieces.", None),
            ("drum", "1f941", "A drum goes boom, boom, boom!", None),
            ("guitar", "1f3b8", "We strum a guitar.", None),
            ("trumpet", "1f3ba", "A trumpet goes toot toot!", None),
            ("piano", "1f3b9", "A piano has black and white keys.", None),
            ("violin", "1f3bb", "A violin has strings.", None),
        ]),
    "home": dict(
        title="At Home", topic="things in our home", sentence="{This} {a}.", tags=["home", "household"],
        items=[
            ("bed", "1f6cf", "I sleep in my bed.", None),
            ("chair", "1fa91", "I sit on a chair.", None),
            ("door", "1f6aa", "I open the door.", None),
            ("key", "1f511", "A key opens the door.", None),
            ("light bulb", "1f4a1", "A light bulb makes light.", None),
            ("toothbrush", "1faa5", "I brush my teeth with a toothbrush.", None),
            ("soap", "1f9fc", "I wash my hands with soap.", None),
            ("cup", "1f964", "I drink from a cup.", None),
        ]),
    "family": dict(
        title="My Family", topic="the people in a family", sentence="{This} {a}.", tags=["family", "people"],
        items=[
            ("baby", "1f476", "A baby is very little.", None),
            ("girl", "1f467", "A girl can play and learn.", None),
            ("boy", "1f466", "A boy can play and learn.", None),
            ("woman", "1f469", "A woman can be a mom or an aunt.", None),
            ("man", "1f468", "A man can be a dad or an uncle.", None),
            ("grandpa", "1f474", "Grandpa tells great stories.", None),
            ("grandma", "1f475", "Grandma gives the best hugs.", None),
        ]),
    "space": dict(
        title="Space", topic="the sun, the moon, and the stars", sentence="{This} {a}.", tags=["space", "planets"],
        items=[
            ("sun", "1f31e", "The sun gives us light and heat.", None),
            ("moon", "1f319", "The moon shines at night.", None),
            ("star", "2b50", "Stars twinkle in the night sky.", None),
            ("earth", "1f30d", "We live on planet Earth.", None),
            ("rocket", "1f680", "A rocket flies to space.", None),
            ("planet", "1fa90", "A planet goes around the sun.", None),
            ("comet", "2604", "A comet has a long, glowing tail.", None),
            ("alien", "1f47d", "Some people imagine friendly aliens.", None),
        ]),
}

# ---------------------------------------------------------------------- colours
# name, hex, spoken examples: [(word, emoji_code)]
COLORS = {
    "red": ("#E8383D", [("apple", "1f34e"), ("strawberry", "1f353"), ("fire truck", "1f692"), ("ladybug", "1f41e")]),
    "blue": ("#3E7BEA", [("whale", "1f433"), ("blueberries", "1fad0"), ("blue heart", "1f499"), ("ocean wave", "1f30a")]),
    "yellow": ("#FFC81E", [("banana", "1f34c"), ("sun", "1f31e"), ("lemon", "1f34b"), ("chick", "1f424")]),
    "green": ("#3DB54A", [("frog", "1f438"), ("broccoli", "1f966"), ("leaf", "1f343"), ("turtle", "1f422")]),
    "orange": ("#FF8A1F", [("orange", "1f34a"), ("carrot", "1f955"), ("fox", "1f98a"), ("pumpkin", "1f383")]),
    "purple": ("#9B59D0", [("grapes", "1f347"), ("eggplant", "1f346"), ("purple heart", "1f49c"), ("octopus", "1f419")]),
    "pink": ("#FF6FAE", [("pig", "1f437"), ("flamingo", "1f9a9"), ("flower", "1f338"), ("ice cream", "1f368")]),
    "brown": ("#9A6A3A", [("bear", "1f43b"), ("monkey", "1f435"), ("cookie", "1f36a"), ("tree", "1f333")]),
    "white": ("#BFC9D6", [("cloud", "2601"), ("snowman", "26c4"), ("egg", "1f95a"), ("sheep", "1f411")]),
    "gray": ("#8892A0", [("elephant", "1f418"), ("mouse", "1f42d"), ("wolf", "1f43a"), ("rhino", "1f98f")]),
}

# --------------------------------------------------------------------- alphabet
# letter: (spoken name, phonics sound, word, emoji)
LETTERS = {
    "A": ("ay", "ah", "apple", "1f34e"), "B": ("bee", "buh", "ball", "26bd"), "C": ("see", "kuh", "cat", "1f431"),
    "D": ("dee", "duh", "dog", "1f436"), "E": ("ee", "eh", "elephant", "1f418"), "F": ("eff", "fff", "fish", "1f41f"),
    "G": ("jee", "guh", "grapes", "1f347"), "H": ("aitch", "huh", "hat", "1f452"), "I": ("eye", "ih", "ice cream", "1f368"),
    "J": ("jay", "juh", "juice", "1f9c3"), "K": ("kay", "kuh", "kite", "1fa81"), "L": ("ell", "lll", "lion", "1f981"),
    "M": ("em", "mmm", "moon", "1f319"), "N": ("en", "nnn", "nose", "1f443"), "O": ("oh", "aw", "orange", "1f34a"),
    "P": ("pee", "puh", "pizza", "1f355"), "Q": ("cue", "kwuh", "queen", "1f478"), "R": ("ar", "rrr", "rainbow", "1f308"),
    "S": ("ess", "sss", "sun", "2600"), "T": ("tee", "tuh", "tree", "1f333"), "U": ("you", "uh", "umbrella", "2602"),
    "V": ("vee", "vvv", "violin", "1f3bb"), "W": ("double you", "wuh", "whale", "1f433"), "X": ("ex", "ks", "x-ray", "1fa7b"),
    "Y": ("why", "yuh", "yo-yo", "1fa80"), "Z": ("zee", "zzz", "zebra", "1f993"),
}

NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
                "nineteen", "twenty"]

COUNT_OBJECTS = [  # emoji used to count, spoken name (plural)
    ("1f34e", "apples"), ("2b50", "stars"), ("1f388", "balloons"), ("1f986", "ducks"), ("1f41f", "fish"),
    ("1f33b", "flowers"), ("1f98b", "butterflies"), ("1f353", "strawberries"), ("1f697", "cars"), ("1f41d", "bees"),
    ("1f36a", "cookies"), ("1f438", "frogs"),
]

# ---------------------------------------------------------------------- phrases
# (phrase shown+spoken, emoji, explanation spoken first)
PHRASES = {
    "greetings": dict(title="Say Hello!", topic="how to say hello and goodbye", tags=["greetings", "speaking", "english for kids"],
                      items=[("Hello!", "1f44b", "We say hello when we meet someone."),
                             ("Good morning!", "1f305", "We say good morning when the sun comes up."),
                             ("Good afternoon!", "1f31e", "We say good afternoon after lunch."),
                             ("Good night!", "1f319", "We say good night before we go to sleep."),
                             ("How are you?", "1f642", "We ask this to find out how someone feels."),
                             ("I am fine, thank you!", "1f60a", "This is a nice way to answer."),
                             ("Goodbye!", "1f44b", "We say goodbye when we leave.")]),
    "manners": dict(title="Magic Words", topic="polite magic words", tags=["manners", "speaking", "english for kids"],
                    items=[("Please!", "1f64f", "We say please when we ask for something."),
                           ("Thank you!", "1f917", "We say thank you when someone helps us."),
                           ("You are welcome!", "1f60a", "We say this after someone says thank you."),
                           ("Sorry!", "1f614", "We say sorry when we make a mistake."),
                           ("Excuse me!", "1f64b", "We say excuse me to get someone's attention."),
                           ("Yes, please!", "1f44d", "This means we would like it."),
                           ("No, thank you!", "1f44e", "This means we do not want it.")]),
    "talk": dict(title="Let's Talk", topic="easy sentences to practice talking", tags=["speaking", "english for kids", "first sentences"],
                 items=[("My name is Bibi.", "1f41d", "Say your name like this."),
                        ("I am happy!", "1f604", "Tell us how you feel."),
                        ("I like apples.", "1f34e", "Tell us what you like."),
                        ("I love my family.", "2764", "Tell us who you love."),
                        ("Let's play!", "1f388", "Invite a friend to play."),
                        ("I can jump!", "1f938", "Tell us what you can do."),
                        ("It is a sunny day.", "2600", "Tell us about the weather.")]),
}

# -------------------------------------------------------------------- opposites
# (word_a, emoji_a, word_b, emoji_b, size_pair)
OPPOSITES = [
    ("big", "1f418", "small", "1f42d", True),
    ("hot", "1f525", "cold", "1f9ca", False),
    ("day", "1f31e", "night", "1f319", False),
    ("happy", "1f604", "sad", "1f622", False),
    ("fast", "1f407", "slow", "1f422", False),
    ("tall", "1f992", "short", "1f401", True),
    ("up", "2b06", "down", "2b07", False),
    ("heavy", "1faa8", "light", "1fab6", False),
    ("wet", "1f4a7", "dry", "1f3dc", False),
    ("open", "1f4d6", "closed", "1f4d5", False),
]

SHAPES = {
    "circle": ("#FF5C8A", "A circle is round.", "It has no corners.", [("ball", "26bd"), ("clock", "23f0"), ("cookie", "1f36a")]),
    "square": ("#3E8EDE", "A square has four equal sides.", "It has four corners.", [("window", "1fa9f"), ("gift", "1f381"), ("dice", "1f3b2")]),
    "triangle": ("#FFB400", "A triangle has three sides.", "It has three corners.", [("pizza", "1f355"), ("sailboat", "26f5"), ("mountain", "26f0")]),
    "rectangle": ("#3DB54A", "A rectangle has two long sides and two short sides.", "It has four corners.", [("door", "1f6aa"), ("book", "1f4d5"), ("phone", "1f4f1")]),
    "star": ("#FFC81E", "A star has five points.", "Stars twinkle at night.", [("star", "2b50"), ("sparkle", "2728"), ("glowing star", "1f31f")]),
    "heart": ("#E8383D", "A heart is a shape of love.", "It has a round top and a pointy bottom.", [("heart", "2764"), ("gift", "1f381"), ("rose", "1f339")]),
    "oval": ("#9B59D0", "An oval is like a stretched circle.", "It has no corners.", [("egg", "1f95a"), ("lemon", "1f34b"), ("mirror", "1fa9e")]),
    "diamond": ("#00B8D4", "A diamond has four equal sides.", "It looks like a kite.", [("kite", "1fa81"), ("gem", "1f48e"), ("card", "2666")]),
}


def all_codes():
    codes = set()
    for c in CATS.values():
        codes.update(i[1] for i in c["items"])
    for name, (hexc, items) in COLORS.items():
        codes.update(i[1] for i in items)
    for v in LETTERS.values():
        codes.add(v[3])
    for code, _ in COUNT_OBJECTS:
        codes.add(code)
    for p in PHRASES.values():
        codes.update(i[1] for i in p["items"])
    for a in OPPOSITES:
        codes.update([a[1], a[3]])
    for s in SHAPES.values():
        codes.update(i[1] for i in s[3])
    return sorted(codes)
