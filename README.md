# 🐝 Bibi Buzz TV – Bölüm 1: "Bibi and the Colorful Flowers"

2-6 yaş çocuklar için, tamamen **kodla üretilen** 2 dakika 30 saniyelik animasyon videosu.
Karakterler (Bibi, Pip, Mo, Lila), arka plan, müzik ve ses efektleri hazır görsel/ses dosyası
olmadan, Python ile çizilir ve sentezlenir. Telif sorunu yoktur, her şey özgündür.

- Çıktı: `out/bibi_buzz_ep01.mp4` (1280x720, 30 fps, H.264 + AAC)
- Kapak görseli: `out/thumbnail.png`
- İçerik: tanıtım şarkısı, kırmızı/mavi/sarı renkleri öğrenme, renk karıştırma (kırmızı + sarı = turuncu),
  1'den 5'e sayma, gökkuşağı ve buket, veda

## Yöntem 1: GitHub Actions (bilgisayara bir şey kurmadan, önerilen)

1. GitHub'da yeni bir repo açın (örn. `bibi-buzz-tv`, gizli de olabilir).
2. Bu klasörün tüm içeriğini yükleyin. Gizli `.github` klasörünün de yüklendiğinden emin olun.
   Web arayüzünde "uploading an existing file" bağlantısı ile klasörü sürükleyebilirsiniz.
   Terminalden yüklemek isterseniz:
   ```bash
   git init -b main && git add . && git commit -m "Bibi Buzz TV episode 1"
   git remote add origin https://github.com/KULLANICI_ADINIZ/bibi-buzz-tv.git
   git push -u origin main
   ```
3. Repoda **Actions** sekmesine gidin, **Render Bibi Buzz TV episode** iş akışını seçin.
4. **Run workflow** düğmesine basın. **voice** kutusu varsayılan olarak işaretlidir: videoya çocuk sesiyle
   anlatım eklenir (istemezseniz işareti kaldırın). Ses üretilemezse iş hata verir, sessiz video çıkarmaz.
5. İş bitince (birkaç dakika) reponun sağındaki **Releases** bölümünden `bibi_buzz_ep01.mp4`
   dosyasını doğrudan indirin (zip gerekmez). Aynı dosyalar çalıştırma sayfasının altındaki
   **Artifacts** bölümünde de vardır.

## Yöntem 2: GitHub Codespaces

1. Repoda **Code > Codespaces > Create codespace** seçin (ortam otomatik kurulur).
2. Terminalde `python render.py` çalıştırın.
3. `out/` klasöründen dosyaları indirin (sağ tık > Download).

## Yöntem 3: Kendi bilgisayarınız

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python render.py
```

FFmpeg ayrıca kurmanız gerekmez, `imageio-ffmpeg` paketi onu getirir.

## Komutlar

| Komut | Ne yapar |
|---|---|
| `python render.py` | Tüm bölümü render eder |
| `python render.py --voice` | Çocuk sesli anlatım ekler (`pip install -r requirements-voice.txt` ve internet gerekir). Uzun satırlar kendi süresine sığacak kadar hızlandırılır, ses üretilemezse hata verir |
| `python render.py --resume` | Yarım kalan render'a devam eder, var olan sahne dosyalarını atlar |
| `python render.py --scenes color_red,bye` | Sadece bu sahneleri yeniden render eder ve videoyu yeniden birleştirir |
| `python render.py --stills` | Önemli anlardan PNG önizlemeleri üretir (`out/stills/`) |
| `python render.py --stills --at 12,47` | İstediğiniz saniyelerden önizleme üretir |
| `python render.py --thumbnail` | YouTube kapak görselini üretir |
| `python render.py --workers 4` | Kaç işlemci çekirdeği kullanılacağını belirler |

Sahne adları: `logo`, `intro`, `color_red`, `color_blue`, `color_yellow`, `mix`, `count`, `bouquet`, `bye`.

Süre: 2 çekirdekte yaklaşık 1 dakika (4500 kare), tek çekirdekte yaklaşık 2 dakika.
Her sahne `out/scenes/` içinde ayrı bir videoya kodlanır, sonra tek dosyada birleşir. Bu yüzden bir
sahneyi değiştirirseniz yalnızca onu yeniden render etmeniz yeterlidir.

## Dosya yapısı

```
render.py                 komut satırı arayüzü, sahneleri kodlar, birleştirir, sesi ekler
bibi_buzz/draw.py         çizim araçları + Bibi, Pip, Mo, Lila, çiçekler, güneş, bulutlar
bibi_buzz/scenes.py       7 bölüm (logo, tanıtım, renkler, karıştırma, sayma, buket, veda)
bibi_buzz/timeline.py     süreler, şarkı sözleri, ses efekti ve anlatım zamanları
bibi_buzz/audio.py        müzik ve ses efekti sentezi, isteğe bağlı sesli anlatım
bibi_buzz/thumbnail.py    YouTube kapak görseli
.github/workflows/        GitHub Actions render iş akışı
.devcontainer/            Codespaces ayarı
```

## Özelleştirme

- **Yazılar ve şarkı sözleri:** `bibi_buzz/timeline.py` içindeki `INTRO_LINES` ve `COLOR_SEGS`.
- **Renkler ve süreler:** yine `timeline.py`. Sahnelerin süresini değiştirirseniz `DURATION` ve
  sahne aralıklarını (`S_LOGO` ... `S_BYE`) birlikte güncelleyin.
- **Müzik:** `bibi_buzz/audio.py` içindeki `MELODY` (nota listesi) ve `CHORDS`.
- **Yazı tipi:** daha sevimli bir görünüm için `assets/Fredoka-Bold.ttf` dosyasını ekleyin
  (Google Fonts'tan ücretsiz indirilebilir). Kod otomatik olarak onu kullanır.
- **Yeni bölüm:** `scenes.py` ve `timeline.py` dosyalarını kopyalayıp yeni bir konu için
  (örn. "Hayvan Sesleri") düzenleyin.

## YouTube'a yüklerken

- Videoyu **"Çocuklara özel" (Made for Kids)** olarak işaretleyin.
- YouTube'un "değiştirilmiş/sentetik içerik" sorusunu dürüstçe yanıtlayın. Bu video çizgi film tarzıdır
  ve gerçekçi bir kişi, yer ya da olayı taklit etmez.
- Başlık, açıklama, bölümler (chapters) ve etiketler için `BIBI_KIT.md` dosyasına bakın.

## Masallar (hikâyeli uzun videolar)

`bibi_buzz/story*.py` ve `bibi_buzz/tales.py`: çocuk masallarını sahne sahne yazıp animasyonlu, çok sesli videoya çeviren motor.

- Her masal `tales.py` içinde bir fonksiyondur: `Tale(...)`, `tale.scene(ad, arka_plan)`, `sc.actor(...)`, `sc.prop(...)`,
  `sc.nar("anlatıcı metni", *eylemler)`, `sc.say("karakter", "replik", *eylemler)`. Her cümlenin süresi sesin uzunluğundan çıkar
  (hiçbir şey hızlandırılmaz), böylece ses, hareket ve müzik hep birlikte kalır.
- Eylemler: `walk`, `pose`, `face`, `hold`, `fx`, `sfx`, `cam`, `follow`, `set`, `show` / `hide`. Poz adlarına `sit@84`
  (gövdeyi 84 piksel yukarı al, ayaklar sarksın) ve `sit+sad` (aynı poz, başka yüz ifadesi) eklenebilir.
- Kadro: domuz, kurt, ayı, tavşan, kaplumbağa, kız ve Bibi, Pip, Mo, Lila. Yeni karakter ve dekorlar `storyart.py`,
  `storyart2.py`, `storyprops.py` içindedir.
- Günlük plan: `curriculum.TALE_QUEUE` listesindeki masallar 2. günden itibaren sırayla 5. uzun dersin yerine geçer
  (video kimliği `dNNN-T1`). Yeni masal eklemek için fonksiyonu yazıp `tales.TALES` ve `TALE_QUEUE` listelerine ekleyin.
- Deneme: `python make_batch.py --day 2 --only d002-T1 --sheet --out out/test` (kapak: `out/test/d002-T1.jpg`).
- Türkçe sürümler: her masalın Türkçe versiyonu bir gün sonra yayınlanır (`dNNN-T2`): aynı çizimler, Türkçe sesler (Emel, Ahmet),
  metinler, başlık ve açıklama. Türkçe satırlar `bibi_buzz/tales_tr.py` içindedir; yeni masalda her İngilizce satırın karşılığı `TR`
  sözlüğüne eklenmelidir (eksik çeviri hata verir, yarım çevrilmiş video asla üretilmez). Türkçe yazılar Baloo 2 ile çizilir
  (Fredoka'da ğ, ş, İ yoktur).
- Bitiş kartı: videolar "çocuklara özel" olduğu için YouTube yorumları, bitiş ekranlarını ve abone ol filigranını kapatır. Bu yüzden her
  uzun dersin ve masalın sonuna "Beğen / Abone ol" düğmeleri çizilir, bir fare imleci önce Beğen'e sonra Abone ol'a basar
  (`draw.cta`; derslerde `cta` bölümü, masallarda son sahne). Açıklamaların başına tıklanabilir abone ol bağlantısı eklenir
  (`curriculum.SUBSCRIBE_URL`).
- Deneme (gerçek yazı tipi ve gerçek seslerle): Actions → "test-render" → Run workflow (masal, dil, saniye). Kapak, sahne sayfası,
  satır listesi ve kısa bir klip `test-output` dalına yazılır; günlük videolara dokunmaz.
