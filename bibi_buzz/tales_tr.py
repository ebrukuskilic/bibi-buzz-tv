"""Turkish versions of the fairy tales.

The scripts in tales.py are written in English. A Turkish tale (Tale.lang == "tr") looks up every line - narration,
dialogue, chapter names, words that appear on the screen - here by its English text. Scenes, animations and sound cues
stay exactly the same, only the words, the voices, the font and the video text change. A line that is missing here
raises an error when the tale is built, so a half translated video can never be rendered.
"""

EMEL, AHMET = "tr-TR-EmelNeural", "tr-TR-AhmetNeural"          # the only two Turkish neural voices of edge-tts

# (voice, rate, pitch) per character: a warm female narrator, male voices for the male characters, and pitch changes for the rest
VOICES = {
    "three-little-pigs": {"nar": (EMEL, "-6%", "+0Hz"), "mama": (EMEL, "-8%", "-8Hz"), "pig1": (AHMET, "+4%", "+26Hz"),
                          "pig2": (AHMET, "+0%", "+17Hz"), "pig3": (AHMET, "-4%", "+8Hz"), "wolf": (AHMET, "-10%", "-14Hz")},
    "tortoise-and-hare": {"nar": (EMEL, "-6%", "+0Hz"), "hare": (AHMET, "+6%", "+14Hz"), "tort": (AHMET, "-18%", "-6Hz"),
                          "bear": (AHMET, "-8%", "-16Hz"), "pig1": (AHMET, "+4%", "+26Hz"), "pig2": (AHMET, "+0%", "+17Hz"),
                          "pig3": (AHMET, "-4%", "+8Hz")},
    "goldilocks": {"nar": (EMEL, "-6%", "+0Hz"), "gold": (EMEL, "-2%", "+14Hz"), "papa": (AHMET, "-10%", "-20Hz"),
                   "mama": (EMEL, "-8%", "-8Hz"), "baby": (EMEL, "+0%", "+30Hz")},
}

TAGS = ["masal", "çocuk masalları", "uyku masalları", "türkçe masal", "çizgi film masal", "masal dinle", "çocuklar için masal",
        "Bibi Buzz TV", "çocuk hikayeleri", "bebek masalları", "animasyon masal", "masal saati"]

_TAIL = " Türkçe seslendirmeli, renkli ve sevimli bir çizgi film masal. 2-6 yaş çocuklar için sade ve kısa cümlelerle anlatılır."

# title / description paragraph / extra tags of every tale (the video title must stay within 100 characters)
META = {
    "three-little-pigs": dict(
        title="Üç Küçük Domuz Masalı | Çocuklar İçin Türkçe Masal | Bibi Buzz TV",
        blurb="Üfle, püfle, yıkılmayan ev! Üç Küçük Domuz ile Koca Kötü Kurt'un klasik masalını izleyin: biri samandan, biri çubuktan, "
              "biri de sağlam tuğladan evini yapar." + _TAIL,
        tags=["üç küçük domuz", "üç küçük domuz masalı", "koca kötü kurt", "kurt ve üç domuz"]),
    "tortoise-and-hare": dict(
        title="Tavşan ile Kaplumbağa Masalı | Çocuklar İçin Türkçe Masal | Bibi Buzz TV",
        blurb="Yavaş ama durmadan giden kazanır! Tavşan ile Kaplumbağa'nın klasik masalını izleyin: kendini beğenmiş hızlı bir tavşan, "
              "yavaş ama kararlı bir kaplumbağa ve büyük bir yarış." + _TAIL,
        tags=["tavşan ile kaplumbağa", "tavşan ile kaplumbağa masalı", "kaplumbağa ve tavşan", "yavaş ama durmadan"]),
    "goldilocks": dict(
        title="Altın Saç ve Üç Ayı Masalı | Çocuklar İçin Türkçe Masal | Bibi Buzz TV",
        blurb="Çok sıcak, çok soğuk, tam kararında! Altın Saç ve Üç Ayı'nın klasik masalını izleyin: meraklı küçük bir kız sevimli bir "
              "kulübeye girer, lapayı, sandalyeleri ve yatakları dener, sonra Baba Ayı, Anne Ayı ve Bebek Ayı ile karşılaşır." + _TAIL,
        tags=["altın saç ve üç ayı", "altın saç", "üç ayı masalı", "altın saç masalı"]),
}

# the description footer and hashtags of a Turkish tale (see curriculum.metadata)
FOOTER = ["Bibi Buzz TV'de her gün yeni masallar ve öğretici videolar!",
          "Seslendirme için metin okuma (TTS) sesleri kullanılmıştır. Tüm çizimler ve müzikler Bibi Buzz TV için hazırlanmıştır."]
HASHTAGS = "#masal #çocukmasalları #uykumasalları #türkçemasal #BibiBuzzTV"
CHAPTERS = "Bölümler"
PLAYLIST = "Türkçe Masallar | Çocuklar için Masal Videoları | Bibi Buzz TV"

# English text -> Turkish text. Upper case words are written out in Turkish upper case (İ / ı), never with str.upper().
TR = {
    # ---- the shared intro and ending
    "Welcome to Bibi Buzz story time!": "Bibi Buzz masal saatine hoş geldiniz!",
    "The End. Thank you for watching!": "Son. İzlediğiniz için teşekkürler!",
    "If you liked this story, please like and subscribe! See you at the next story. Bye bye!": "Masalı sevdiysen, beğen ve abone ol! Bir sonraki masalda görüşürüz. Hoşça kalın!",
    "Like and subscribe for more stories!": "Daha çok masal için beğen ve abone ol!",
    "Story Time with Bibi Buzz TV": "BİBİ BUZZ TV İLE MASAL SAATİ",
    "The End": "Son",
    "Intro": "Giriş",
    "Bibi Buzz TV": "Bibi Buzz TV",

    # ---- the three little pigs
    "THE THREE": "ÜÇ KÜÇÜK",
    "LITTLE PIGS": "DOMUZ",
    "Today's story is... The Three Little Pigs!": "Bugünün masalı... Üç Küçük Domuz!",
    "Mama Pig and her three little pigs": "Anne Domuz ve üç küçük domuzu",
    "Once upon a time, a mama pig lived in a cozy little house, with her three little pigs.": "Bir varmış, bir yokmuş. Küçük ve sıcacık bir evde, üç yavru domuzuyla yaşayan bir anne domuz varmış.",
    "The three little pigs grew bigger and bigger, until one day it was time to build houses of their own.": "Üç küçük domuz büyüdükçe büyüdü. Bir gün, kendi evlerini yapma zamanı geldi.",
    "My dear little pigs, it is time to build your own houses!": "Benim tatlı yavrularım, kendi evlerinizi yapma zamanı geldi!",
    "Work hard, and stay safe. And watch out for the big bad wolf!": "Çok çalışın ve kendinizi koruyun. Koca kötü kurda da dikkat edin!",
    "Do not worry, Mama! I will build my house very fast!": "Merak etme anne! Ben evimi çok çabuk yapacağım!",
    "So the little pigs hugged their mama, and off they went, down the sunny road.": "Küçük domuzlar annelerine sarıldılar ve güneşli yolda yürümeye başladılar.",
    "The straw house": "Saman ev",
    "The first little pig walked and walked. Soon, he found a big pile of straw.": "Birinci küçük domuz yürüdü, yürüdü. Çok geçmeden büyük bir saman yığını buldu.",
    "Straw is light and easy. I can build my house in no time!": "Saman hafif ve kolay. Evimi hemen yapabilirim!",
    "So he stacked the straw, one bundle at a time, until he had built a little house.": "Samanları demet demet üst üste dizdi ve küçük bir ev yaptı.",
    "Pop! The straw house was ready.": "Pat! Saman ev hazırdı.",
    "Now I can play all day!": "Şimdi bütün gün oynayabilirim!",
    "The stick house": "Çubuk ev",
    "The second little pig walked into the forest. There, he found a pile of sticks.": "İkinci küçük domuz ormana yürüdü. Orada bir yığın çubuk buldu.",
    "Sticks are strong, and quick to build with. I will make a house of sticks!": "Çubuklar sağlam, ev de çabuk biter. Ben çubuklardan bir ev yapacağım!",
    "Tap, tap, tap! He built his house of sticks.": "Tak, tak, tak! Evini çubuklardan yaptı.",
    "My house is done! Time to sing and dance!": "Evim bitti! Şarkı söyleyip dans etme zamanı!",
    "The brick house": "Tuğla ev",
    "The third little pig was very wise. He found a big pile of bricks.": "Üçüncü küçük domuz çok akıllıydı. Büyük bir tuğla yığını buldu.",
    "Bricks are heavy, and this will take a long time. But a brick house is strong!": "Tuğlalar ağır ve bu uzun sürecek. Ama tuğla ev çok sağlam olur!",
    "So he worked, and worked, and worked. Brick by brick, he built his house.": "Çalıştı, çalıştı, çalıştı. Tuğla tuğla evini yaptı.",
    "His brothers came by, and they laughed.": "Kardeşleri yanına geldi ve ona güldüler.",
    "Why are you working so hard? Come and play with us!": "Neden bu kadar çok çalışıyorsun? Gel bizimle oyna!",
    "A strong house will keep me safe. I will play when I am done!": "Sağlam bir ev beni korur. İşim bitince oynarım!",
    "At last, the brick house was finished. It was strong, and warm, and cozy.": "Sonunda tuğla ev bitti. Sağlamdı, sıcacıktı ve rahattı.",
    "The big bad wolf": "Koca kötü kurt",
    "One day, a big bad wolf came walking down the road.": "Bir gün, koca kötü bir kurt yolda yürüyerek geldi.",
    "He saw the little house of straw, and he had a sneaky plan.": "Küçük saman evi gördü ve sinsi bir planı vardı.",
    "Knock, knock, knock!": "Tak, tak, tak!",
    "Little pig, little pig, let me come in!": "Küçük domuz, küçük domuz, kapıyı aç, içeri gireyim!",
    "No, no, not by the hair of my chinny chin chin!": "Olmaz, olmaz! Sakalımın teline yemin olsun, açmam!",
    "Then I will huff, and I will puff, and I will blow your house in!": "O zaman üfleyeceğim, püfleyeceğim ve evini yıkacağım!",
    "So the wolf took a big, deep breath. He huffed, and he puffed, and he blew the house down!": "Kurt büyük, derin bir nefes aldı. Üfledi, püfledi ve evi yıktı!",
    "Help! Run, run, run! To my brother's house of sticks!": "İmdat! Koş, koş, koş! Kardeşimin çubuk evine!",
    "The little pig ran and ran, as fast as his little legs could go.": "Küçük domuz küçücük bacaklarıyla olabildiğince hızlı koştu, koştu.",
    "The wolf at the stick house": "Kurt çubuk evde",
    "The first little pig ran into the forest, all the way to the house of sticks.": "Birinci küçük domuz ormana koştu ve çubuk eve kadar geldi.",
    "Brother, brother! The big bad wolf is coming!": "Kardeşim, kardeşim! Koca kötü kurt geliyor!",
    "Do not worry. My house is strong. Stay with me!": "Korkma. Evim sağlam. Benimle kal!",
    "But the big bad wolf had followed them.": "Ama koca kötü kurt onları takip etmişti.",
    "Little pigs, little pigs, let me come in!": "Küçük domuzlar, küçük domuzlar, kapıyı açın, içeri gireyim!",
    "No, no, not by the hair of our chinny chin chins!": "Olmaz, olmaz! Sakallarımızın teline yemin olsun, açmayız!",
    "The wolf huffed, and he puffed, and he blew... and the house of sticks fell down, too!": "Kurt üfledi, püfledi ve üfledi... Çubuk ev de yıkıldı!",
    "Quick! Run to our brother's house of bricks!": "Çabuk! Kardeşimizin tuğla evine koşalım!",
    "The wolf at the brick house": "Kurt tuğla evde",
    "The two little pigs ran as fast as they could, all the way to the house of bricks.": "İki küçük domuz olabildiğince hızlı koştu ve tuğla eve kadar geldi.",
    "Come in, come in! Hurry!": "Girin, girin! Çabuk olun!",
    "They all ran inside, and they locked the door tight.": "Hepsi içeri koştu ve kapıyı sıkıca kilitledi.",
    "Soon, the big bad wolf came to the brick house.": "Çok geçmeden koca kötü kurt tuğla eve geldi.",
    "So the wolf huffed, and he puffed. He huffed, and he puffed some more. But the brick house did not move at all!": "Kurt üfledi, püfledi. Biraz daha üfledi, püfledi. Ama tuğla ev hiç kıpırdamadı!",
    "Oh my! I am so tired. But I have a new plan. I will climb down the chimney!": "Ah! Çok yoruldum. Ama yeni bir planım var. Bacadan aşağı ineceğim!",
    "And the wolf climbed up, up, up, onto the roof of the brick house.": "Kurt yukarı, yukarı, yukarı tırmandı ve tuğla evin çatısına çıktı.",
    "The wolf in the chimney": "Kurt bacada",
    "Inside the house, the clever pigs heard a noise on the roof.": "Evin içinde akıllı domuzlar çatıdan bir ses duydu.",
    "Quick! He is coming down the chimney! Keep the pot of water bubbling!": "Çabuk! Bacadan iniyor! Tencerenin suyunu kaynatın!",
    "The water is hot, hot, hot!": "Su sıcak, sıcak, sıcak!",
    "Down, down, down the chimney slid the wolf... and splash! Right into the pot!": "Aşağı, aşağı, aşağı... Kurt bacadan kaydı ve şlap! Tam tencerenin içine düştü!",
    "Yowwww! That is hot!": "Ayyy! Çok sıcak!",
    "The wolf jumped out of the pot, and he ran away, far over the hills. And he never came back again!": "Kurt tencereden fırladı ve tepelerin ardına kadar kaçtı. Bir daha da hiç geri gelmedi!",
    "SPLASH!": "ŞLAP!",
    "Happily ever after": "Mutlu son",
    "The three little pigs were safe and sound. They had a big party in the strong brick house.": "Üç küçük domuz güvendeydi. Sağlam tuğla evde büyük bir parti yaptılar.",
    "I am sorry I did not work hard, brother!": "Çok çalışmadığım için özür dilerim kardeşim!",
    "That is all right. Now we all have a strong, safe home!": "Önemli değil. Artık hepimizin sağlam, güvenli bir evi var!",
    "Hooray for the brick house! Let us all have some pie!": "Yaşasın tuğla ev! Hadi hep birlikte turta yiyelim!",
    "And they all lived happily ever after.": "Ve hepsi mutlu mutlu yaşadılar.",
    "Remember, little ones: if you work hard and plan well, you can build something strong!": "Unutmayın küçükler: çok çalışır ve iyi plan yaparsanız, sağlam şeyler yapabilirsiniz!",
    "Work hard, plan well, build strong!": "Çok çalış, iyi plan yap, sağlam yap!",

    # ---- the tortoise and the hare
    "THE TORTOISE": "TAVŞAN İLE",
    "AND THE HARE": "KAPLUMBAĞA",
    "Today's story is... The Tortoise and the Hare!": "Bugünün masalı... Tavşan ile Kaplumbağa!",
    "A boastful hare": "Övüngen tavşan",
    "Once upon a time, in a sunny green meadow, there lived a very fast hare.": "Bir varmış, bir yokmuş. Güneşli, yemyeşil bir çayırda çok hızlı bir tavşan yaşarmış.",
    "I am the fastest animal in the whole wide world!": "Ben dünyanın en hızlı hayvanıyım!",
    "Nobody can run as fast as me! Zoom, zoom, zoom!": "Kimse benim kadar hızlı koşamaz! Vızz, vızz, vızz!",
    "In the same meadow, there lived a slow and gentle tortoise.": "Aynı çayırda yavaş ve nazik bir kaplumbağa da yaşarmış.",
    "Hello, Hare. I may be slow, but I never give up.": "Merhaba Tavşan. Yavaş olabilirim ama asla pes etmem.",
    "Ha ha ha! You? Slow, slow tortoise! You could never beat me!": "Ha ha ha! Sen mi? Yavaş, yavaş kaplumbağa! Beni asla yenemezsin!",
    "Then let us have a race, and we will see.": "O zaman bir yarış yapalım, bakalım kim kazanacak.",
    "A race? That is easy! I accept!": "Yarış mı? Çok kolay! Kabul ediyorum!",
    "All the animals came to watch the big race.": "Bütün hayvanlar büyük yarışı izlemeye geldi.",
    "Ready, set, go!": "Hazır olun, başla!",
    "The race began at the starting line.": "Yarış başlangıç çizgisinde başladı.",
    "On your mark... get set...": "Yerlerinizi alın... Hazır olun...",
    "GO!": "BAŞLA!",
    "Whoosh! The hare shot off like a rocket. And the tortoise? He took one slow step, and then another.": "Vuuuş! Tavşan roket gibi fırladı. Peki ya kaplumbağa? O yavaşça bir adım attı, sonra bir adım daha.",
    "The hare dashes ahead": "Tavşan öne geçti",
    "The hare ran fast, faster, fastest! The wind blew his ears back.": "Tavşan hızlı, daha hızlı, en hızlı koştu! Rüzgâr kulaklarını geriye savurdu.",
    "Soon, he was far, far ahead of the tortoise.": "Çok geçmeden kaplumbağanın çok ama çok önüne geçti.",
    "I am so far ahead! The tortoise is just a tiny dot!": "Çok ilerideyim! Kaplumbağa küçücük bir nokta gibi kaldı!",
    "I have plenty of time for a little nap.": "Küçük bir şekerleme için bolca zamanım var.",
    "A little nap": "Küçük bir şekerleme",
    "The hare found a big, shady tree. He yawned a great big yawn.": "Tavşan büyük, gölgeli bir ağaç buldu. Kocaman bir esnedi.",
    "I will rest my eyes for just one little minute.": "Gözlerimi sadece bir dakikalığına dinlendireceğim.",
    "But the hare fell fast asleep. Zzzzz.": "Ama tavşan derin bir uykuya daldı. Horr, horr, horr.",
    "Slow and steady": "Yavaş ama durmadan",
    "Meanwhile, the tortoise kept on walking. Step, step, step.": "Bu sırada kaplumbağa yürümeye devam etti. Adım, adım, adım.",
    "Slow and steady. Slow and steady.": "Yavaş ama durmadan. Yavaş ama durmadan.",
    "The sun was hot, and the road was long. But the tortoise did not stop.": "Güneş sıcaktı, yol uzundu. Ama kaplumbağa durmadı.",
    "Step by step, he came to the big tree. And there was the hare, fast asleep!": "Adım adım büyük ağaca geldi. Ve orada tavşan, deliksiz uyuyordu!",
    "Shh... Let us not wake him.": "Şşş... Onu uyandırmayalım.",
    "The tortoise tiptoed past the sleeping hare, and he kept going, and going, and going.": "Kaplumbağa uyuyan tavşanın yanından parmak uçlarında geçti ve yürüdü, yürüdü, yürüdü.",
    "Far, far away, he could see the finish line.": "Çok ama çok uzakta bitiş çizgisini görebiliyordu.",
    "The hare wakes up": "Tavşan uyandı",
    "At last, the hare woke up. He stretched, and he rubbed his eyes.": "Sonunda tavşan uyandı. Gerindi ve gözlerini ovuşturdu.",
    "Oh no! What time is it? Where is the tortoise?": "Eyvah! Saat kaç oldu? Kaplumbağa nerede?",
    "The hare looked far down the road, and he saw the tortoise, almost at the finish line!": "Tavşan yolun ilerisine baktı ve kaplumbağayı bitiş çizgisine çok yakın gördü!",
    "I must run! Faster, faster, faster!": "Koşmalıyım! Daha hızlı, daha hızlı, daha hızlı!",
    "The finish line": "Bitiş çizgisi",
    "Everybody cheered as the tortoise came closer to the finish line.": "Kaplumbağa bitiş çizgisine yaklaştıkça herkes alkışladı.",
    "Go, Tortoise, go!": "Haydi Kaplumbağa, haydi!",
    "You can do it!": "Yapabilirsin!",
    "Just then, the hare came running, as fast as the wind!": "Tam o sırada tavşan rüzgâr gibi koşarak geldi!",
    "But it was too late! The tortoise crossed the finish line first!": "Ama çok geçti! Kaplumbağa bitiş çizgisini ilk geçti!",
    "The hare skidded to a stop. He had lost the race.": "Tavşan kayarak durdu. Yarışı kaybetmişti.",
    "The winner": "Kazanan",
    "The winner of the race is... the tortoise!": "Yarışın kazananı... kaplumbağa!",
    "I am sorry I laughed at you, Tortoise. You are wonderful.": "Sana güldüğüm için özür dilerim Kaplumbağa. Sen harikasın.",
    "Thank you, Hare. Let us be friends.": "Teşekkür ederim Tavşan. Hadi arkadaş olalım.",
    "I just kept going, and I never gave up.": "Ben sadece yürümeye devam ettim ve asla pes etmedim.",
    "From that day on, the hare never boasted again. And the two animals were the best of friends.": "O günden sonra tavşan bir daha asla övünmedi. İki hayvan da en iyi arkadaş oldu.",
    "Remember, little ones: slow and steady wins the race. Never give up!": "Unutmayın küçükler: yavaş ama durmadan giden yarışı kazanır. Asla pes etmeyin!",
    "Slow and steady wins the race!": "Yavaş ama durmadan kazanır!",

    # ---- goldilocks and the three bears
    "GOLDILOCKS": "ALTIN SAÇ",
    "& THE 3 BEARS": "& ÜÇ AYI",
    "Today's story is... Goldilocks and the Three Bears!": "Bugünün masalı... Altın Saç ve Üç Ayı!",
    "The three bears": "Üç ayı",
    "Once upon a time, three bears lived in a little house in the woods. There was Papa Bear, Mama Bear, and Baby Bear.": "Bir varmış, bir yokmuş. Ormanda küçük bir evde üç ayı yaşarmış. Baba Ayı, Anne Ayı ve Bebek Ayı.",
    "Breakfast is ready, my dears!": "Kahvaltı hazır, canlarım!",
    "Oh dear. This porridge is much too hot to eat!": "Eyvah. Bu yulaf lapası yemek için çok sıcak!",
    "Let us go for a walk, while it cools down!": "Soğuyana kadar yürüyüşe çıkalım!",
    "So the three bears went for a walk in the woods.": "Üç ayı ormanda yürüyüşe çıktı.",
    "Goldilocks": "Altın Saç",
    "Just then, a little girl named Goldilocks came walking through the forest.": "Tam o sırada Altın Saç adında küçük bir kız ormanda yürüyerek geldi.",
    "What a lovely day! I will pick some pretty flowers.": "Ne güzel bir gün! Birkaç güzel çiçek toplayacağım.",
    "She walked and walked, until she saw a little house.": "Yürüdü, yürüdü ve küçük bir ev gördü.",
    "A little house": "Küçük bir ev",
    "Goldilocks went up to the little door. Knock, knock, knock!": "Altın Saç küçük kapıya yaklaştı. Tak, tak, tak!",
    "Hello? Is anybody home?": "Merhaba? Evde kimse var mı?",
    "But nobody answered. The door was open, just a little bit.": "Ama kimse cevap vermedi. Kapı azıcık açıktı.",
    "I will just take a tiny peek inside.": "Sadece içeri küçük bir göz atacağım.",
    "And she walked right in.": "Ve içeri girdi.",
    "Three bowls of porridge": "Üç kase yulaf lapası",
    "Inside, there was a big table, and on the table, three bowls of porridge.": "İçeride büyük bir masa vardı ve masanın üstünde üç kase yulaf lapası duruyordu.",
    "Yum! I am so hungry!": "Mmm! Çok acıktım!",
    "First, she tried the big bowl.": "Önce büyük kaseyi denedi.",
    "Ouch! This porridge is too hot!": "Ay! Bu lapa çok sıcak!",
    "Then, she tried the middle bowl.": "Sonra ortadaki kaseyi denedi.",
    "Brrr! This porridge is too cold!": "Üff! Bu lapa çok soğuk!",
    "Then, she tried the little bowl.": "Sonra küçük kaseyi denedi.",
    "Mmm! This porridge is just right!": "Mmm! Bu lapa tam kararında!",
    "And she ate it all up!": "Ve hepsini yedi!",
    "Three chairs": "Üç sandalye",
    "Next, Goldilocks saw three chairs by the window.": "Sonra Altın Saç pencerenin yanında üç sandalye gördü.",
    "I am so tired. I think I will sit down.": "Çok yoruldum. Sanırım oturacağım.",
    "First, she sat in the big chair.": "Önce büyük sandalyeye oturdu.",
    "Oh, this chair is too hard!": "Ah, bu sandalye çok sert!",
    "Then, she sat in the middle chair.": "Sonra ortadaki sandalyeye oturdu.",
    "Oh, this chair is too soft!": "Ah, bu sandalye çok yumuşak!",
    "Then, she sat in the little chair.": "Sonra küçük sandalyeye oturdu.",
    "Ahh! This chair is just right!": "Ahh! Bu sandalye tam kararında!",
    "But oh no! Crack! The little chair broke into pieces!": "Ama eyvah! Çat! Küçük sandalye paramparça oldu!",
    "Oh dear! I am so sorry, little chair.": "Eyvah! Çok özür dilerim küçük sandalye.",
    "CRACK!": "ÇAT!",
    "Three beds": "Üç yatak",
    "Now Goldilocks was very sleepy. Upstairs, she found three beds.": "Altın Saç'ın çok uykusu gelmişti. Üst katta üç yatak buldu.",
    "I will try the big bed first. Oh, it is too hard!": "Önce büyük yatağı deneyeceğim. Ah, çok sert!",
    "This one is too soft!": "Bu çok yumuşak!",
    "Ahh! This little bed is just right!": "Ahh! Bu küçük yatak tam kararında!",
    "She lay down, and she closed her eyes.": "Uzandı ve gözlerini kapadı.",
    "Somebody has been eating my porridge": "Biri lapamı yemiş",
    "Soon, the three bears came home from their walk.": "Çok geçmeden üç ayı yürüyüşten eve döndü.",
    "Somebody has been eating my porridge!": "Biri benim lapamı yemiş!",
    "Somebody has been eating my porridge, too!": "Biri benim lapamı da yemiş!",
    "Somebody has been eating my porridge, and it is all gone!": "Biri benim lapamı yemiş ve hepsi bitmiş!",
    "Somebody has been sitting in my chair": "Biri sandalyeme oturmuş",
    "Somebody has been sitting in my chair!": "Biri benim sandalyeme oturmuş!",
    "Somebody has been sitting in my chair, too!": "Biri benim sandalyeme de oturmuş!",
    "Somebody has been sitting in my chair, and it is broken!": "Biri benim sandalyeme oturmuş ve kırılmış!",
    "Somebody has been sleeping in my bed": "Biri yatağımda uyumuş",
    "Somebody has been sleeping in my bed!": "Biri benim yatağımda uyumuş!",
    "Somebody has been sleeping in my bed, too!": "Biri benim yatağımda da uyumuş!",
    "Somebody has been sleeping in my bed, and she is still there!": "Biri benim yatağımda uyumuş ve hâlâ orada!",
    "Goldilocks woke up with a start. And she saw three bears!": "Altın Saç korkuyla uyandı. Ve üç ayıyı gördü!",
    "Oh my! Help! I am so sorry!": "Eyvah! İmdat! Çok özür dilerim!",
    "Goodbye, Goldilocks": "Hoşça kal, Altın Saç",
    "Goldilocks ran out of the house, and all the way home. She never went into somebody's house without asking again.": "Altın Saç evden dışarı koştu ve eve kadar koştu. Bir daha asla izin almadan kimsenin evine girmedi.",
    "Come back and play with us one day!": "Bir gün geri gel ve bizimle oyna!",
    "And the three bears had a new bowl of porridge, and they ate it up, just right.": "Üç ayı yeni bir kase yulaf lapası hazırladı ve tam kararında afiyetle yedi.",
    "Remember, little ones: always ask before you use someone else's things.": "Unutmayın küçükler: başkasının eşyalarını kullanmadan önce her zaman izin isteyin.",
    "Always ask before you use others' things!": "Başkasının eşyasını izinsiz kullanma!",
}


def lookup(text):
    """The Turkish text of an English line; text without any letter (!, ?, ...) is language neutral."""
    if not any(ch.isalpha() for ch in text):
        return text
    try:
        return TR[text]
    except KeyError:
        raise KeyError("no Turkish translation for: %r" % (text,)) from None


def localize(tale, key):
    """Replaces the English title / description / tags / voices of a freshly created Tale by the Turkish ones."""
    m = META[key]
    tale.title, tale.blurb = m["title"], m["blurb"]
    tale.tags = TAGS + m["tags"]
    tale.voices = dict(VOICES[key])
    return tale
