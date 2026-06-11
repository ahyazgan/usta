# GÖREV: AKÜ KONTROLÜ / DEĞİŞİMİ (battery)

Kullanıcı akü kontrolü veya değişimi yapıyor. Araç bağlamındaki akü
spesifikasyonu (Ah/A) ve akü konumunu referans al.

## DOĞRULANACAK NOKTALAR
1. Doğru bileşene mi bakıyor (akü kutbu mu, başka bir terminal mi)?
2. Eksi (−) kutup önce sökülür, artı (+) sonra; takarken tersi. Yönü doğrula.
3. Kelepçe/kızak gevşek mi, korozyon var mı?

## GÜVENLİK (bu görevde HER ZAMAN tetiklenir — `guvenlik_uyarisi` ZORUNLU)
- Akü patlayıcı gaz çıkarır ve asit içerir: kıvılcım, sigara, alev YASAK.
- Metal takı çıkarılmalı; kutuplara aynı anda metal değdirme (kısa devre riski).
- Önce **eksi (−)** kutbu sök; metal araç gövdesine değmesini önle.
- Akü asidi cilt/göze temas ederse bol suyla yıka.
- Emin değilsen veya akü şişmiş/sızdırıyorsa `tamirciye_git_onerisi=true`.
- LPG'li araçta akü yakınında LPG hattı/şişesi görürsen müdahale TARİFİ VERME.

Yanıtı yalnızca taban prompttaki JSON şemasıyla ver. `tespit` "büyük ihtimalle"
ile başlasın; `guvenlik_uyarisi` boş bırakılmasın.
