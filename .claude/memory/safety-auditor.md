# safety-auditor — proje hafızası

Bu dosya, güvenlik denetimlerinin kalıcı kaydıdır. Her çalıştırmada önce oku,
sonra güncelle.

## Denetlenen kapsam
- `backend/prompts/vision/_base.md`
- `backend/prompts/vision/oil_change.md`
- `backend/prompts/vision/battery.md`
- `backend/prompts/vision/cabin_filter.md`
- `backend/prompts/audio/_base.md`
- Kod katmanı backstop: `backend/app/domain/safety.py` (enforce_image_safety / enforce_sound_safety)

## Son denetim (2026-06-11)
- KRİTİK: 0 · YÜKSEK: 0 · ORTA: 3 → **PASS (bloklama yok)**
- Doğrulanan güçlü noktalar:
  - LPG müdahale tarifi hiçbir dosyada YOK; tümü "müdahale TARİFİ VERME" diyor.
  - `metalik_vuruntu` → acil + tamirci hem audio promptunda hem kodda zorlanıyor.
  - "büyük ihtimalle" hedge'i base prompt'larda mevcut; kod backstop'u da var.
  - guvenlik_uyarisi tetikleyici kelime listesi kod tarafında (`SAFETY_TRIGGER_KEYWORDS`) ile eşleşiyor.

## Açık ORTA bulgular (takip)
1. `oil_change.md:19` — kapanışta hedge/uyarı pekiştirmesi yok (base'e güveniyor).
   Diğer görev rehberleriyle tutarlılık için eklenebilir.
2. `cabin_filter.md:13` — "gereksiz uyarı ekleme" ifadesi, beklenmedik tetikleyici
   içerikte uyarıyı bastırma riski taşır; kod backstop'u koruyor.
3. Görev rehberleri tam şemayı yeniden yazmıyor, base'e atıf yapıyor — kabul edilebilir,
   ancak base dosyası taşınırsa kırılganlık oluşur.

## Notlar
- Yeni görev rehberi eklendiğinde: hedge + tetikleyici güvenlik uyarısı + tamirciye-git
  çıkışı + JSON şema atfı zorunlu. LPG bölgesi geçiyorsa müdahale tarifi YASAK.

## Denetim (2026-06-12) — YENİ DOSYA: backend/app/domain/guides.py
Kapsam: backend/app/domain/guides.py (10 bakım görevi: oil_change, air_filter,
cabin_filter, battery, spark_plug, coolant, brake_check, tire, wiper, headlight).
Referans kurallar: domain/safety.py + guides.py modül docstring'i.

Sonuç: KRİTİK 0 · YÜKSEK 0 · ORTA 2 → PASS (bloklama yok).

Doğrulanan güçlü noktalar:
- brake_check ve coolant gözlem-odaklı; söküm/onarım tarifi YOK.
- battery rehberi kontrol-odaklı; söküm/elektrot temizliği tamirciye bırakılıyor (step 4).
- spark_plug içindeki LPG bağlamı yalnızca "dokunma + yetkili servise git"; müdahale tarifi YOK.
- Tüm görevlerde mechanic_note (vazgeç-tamirciye-git) dataclass default'undan geliyor.
- Tehlikeli bağlam uyarıları mevcut: kriko altına girme (oil_change s3), sıcak motor/yağ
  (oil_change s1, spark_plug s1), soğutma basıncı (coolant s1), akü patlayıcı gaz/asit
  (battery s1/s3), HID yüksek voltaj (headlight s1), halojen cam teması (headlight s4),
  silecek kolunun cama çarpması (wiper s1), lastik yan duvar balonu (tire s3).

Açık ORTA bulgular (takip):
1. guides.py:142 cabin_filter — tetikleyici kelime yok, uyarısız; kabul edilebilir ama
   torpido/elektrik bağlamında "kontak kapalı" vurgusu zaten var. Düşük risk.
2. guides.py:113 oil_change son adım — yeni yağ doldurma/çalıştırma adımında sıcak yüzey
   (egzoz manifoldu) hatırlatması yok; opsiyonel pekiştirme.
   Not: Bunlar bloklayıcı değil; sahibi (a.hakan_@hotmail.com) opsiyonel iyileştirme olarak
   değerlendirebilir.
