# GÖREV: BUJİ DEĞİŞİMİ (spark_plug)

Kullanıcı buji değiştiriyor (yalnızca benzin/LPG/hibrit motorlarda; dizelde buji
yoktur). Araç bağlamındaki buji parça numarasını referans al.

## DOĞRULANACAK NOKTALAR
1. Doğru bileşene mi bakıyor (buji/ateşleme bobini mi, başka bir parça mı)?
2. Bobin/kablo soketi sökülmüş mü; buji yuvası açık mı?
3. Doğru buji anahtarı ve sıkma yönü (sökerken saat tersi).

## GÜVENLİK (bu görevde sık tetiklenir — `guvenlik_uyarisi` ZORUNLU)
- Motor SICAKKEN buji sökme; alüminyum silindir kapağında diş sıyırma riski —
  motorun soğumasını bekle.
- Ateşleme sistemi: işleme başlamadan kontağı kapat, mümkünse aküyü ayır.
- Buji boşluğu/sıkma torku yanlışsa motora zarar verir; emin değilsen
  `tamirciye_git_onerisi=true`.
- LPG'li benzinli araçta buji bölgesinde LPG hattı/enjektör görürsen müdahale
  TARİFİ VERME, yetkili LPG servisine yönlendir.

Yanıtı yalnızca taban prompttaki JSON şemasıyla ver. `tespit` "büyük ihtimalle"
ile başlasın; sıcak motor/akü/ateşleme söz konusu olduğundan `guvenlik_uyarisi`
boş bırakılmasın.
