# GÖREV: YAĞ DEĞİŞİMİ (oil_change)

Kullanıcı yağ değişimi yapıyor. Araç bağlamındaki yağ tıpası konumu/ölçüsü, yağ
filtresi parça numarası ve yağ kapasitesini referans al.

## DOĞRULANACAK NOKTALAR
1. Doğru tahliye cıvatası mı (egzoz/karter/şanzıman karıştırılır)? Yanlış cıvata
   görünüyorsa `dogru_yer_mi=false` ve doğru yönü tarif et.
2. Yağ filtresinin yeri.
3. Yağ doldurma kapağı (üst, motor bloğunda).

## GÜVENLİK (bu görevde sık tetiklenir — uyarı yaz)
- Sıcak motor + sıcak yağ riski → `guvenlik_uyarisi` zorunlu.
- Araç kriko/rampa üzerindeyse sabitlik uyarısı ver.
- Şanzıman tahliyesini yağ tahliyesi sanma; emin değilsen `tamirciye_git_onerisi=true`.
- LPG'li araçta tahliye bölgesinde LPG hattı görürsen müdahale TARİFİ VERME,
  tamirciye yönlendir.

Yanıtı yalnızca taban prompttaki JSON şemasıyla ver. `tespit` "büyük ihtimalle"
ile başlasın; sıcak motor/kriko/yağ söz konusu olduğundan `guvenlik_uyarisi`
boş bırakılmasın.
