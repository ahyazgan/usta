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

## Denetim (2026-06-13) — YENİ ÖZELLİK: Arıza kodu (OBD-II / DTC) açıklama
Kapsam: backend/prompts/dtc/_base.md, backend/app/domain/safety.py (enforce_dtc_safety),
backend/app/services/ai/dtc_service.py, backend/app/domain/schemas.py
(DtcDiagnoseRequest/DtcDiagnoseResponse).

Sonuç: KRİTİK 0 · YÜKSEK 1 · ORTA 3 → PASS (yayından önce 1 zorunlu düzeltme).

Doğrulanan güçlü noktalar:
- LPG müdahale tarifi YOK; enforce_dtc_safety (safety.py:241-243) LPG'yi yakalayıp
  LPG_SAFETY_WARNING + tamirciye_git=True ile geçersiz kılıyor. Prompt (_base.md:15) de yasaklıyor.
- surulebilir_mi is False VEYA aciliyet=yuksek => tamirci + uyarı zorunlu (safety.py:244) gerçekten
  zorlanıyor; `is False` ile None doğru ayrılıyor (None tamirci tetiklemez, prompt semantiğiyle uyumlu).
- enforce_dtc_safety dtc_service.py:70'te son katman olarak çağrılıyor; ham model dönmüyor.
- DtcDiagnoseResponse hem guvenlik_uyarisi hem tamirciye_git_onerisi içeriyor (şema bütünlüğü OK).

Bulgular (takip):
1. [YÜKSEK — ZORUNLU DÜZELTME] safety.py:28-42 SAFETY_TRIGGER_KEYWORDS — "hararet" ve "yağ basıncı"
   eksik. Prompt (_base.md:13) ve enforce_dtc_safety docstring'i (safety.py:223) bunları zorunlu
   uyarı konusu sayıyor ama keyword listesinde yok ("yağ basıncı" sadece generic "basınç" ile kısmen
   yakalanıyor, "hararet" hiç yakalanmıyor). hararet/yağ basıncı geçen DTC yanıtı guvenlik_uyarisi=null
   ile geçebilir. Fix: "hararet", "yağ basınc"/"yag basinc", muhtemelen "şarj"/"sarj" ekle + regresyon testi.
2. [ORTA] safety.py:94-106 _ensure_hedge — sadece DEFINITIVE_PHRASES literallerini değiştiriyor;
   "arıza şudur"/"sorun budur"/bare "kesin" yakalanmıyor. Hedge zaten varsa kısa devre (satır 104)
   karışık dilde kesin sözcükleri bırakabilir.
3. [ORTA] enforce_dtc_safety hedge yumuşatmayı yalnız `tespit`'e uyguluyor; kullanıcıya görünen
   `baslik` ve `olasi_nedenler` haystack'e giriyor ama _ensure_hedge'den geçmiyor
   (dashboard'da `anlam` geçiyor — tutarsızlık).
4. [ORTA/opsiyonel] schemas.py:360-363 DtcDiagnoseRequest.code pattern yok (sadece 2-10 uzunluk);
   prompt bilinmeyen kodu zarif ele alıyor, güvenlik hatası değil — opsiyonel sıkılaştırma.

Karar: surulebilir_mi=False ve kesin-dil yumuşatma çekirdeği zorlanıyor; tek bloklayıcı, koddaki
keyword listesinin docstring/prompt'un vaat ettiği hararet/yağ-basıncı uyarısını gerçekten
zorlamaması (bulgu 1).

## Denetim (2026-06-13) — YENİ ÖZELLİK: Belirti-bazlı serbest teşhis
Kapsam: backend/prompts/symptom/_base.md, backend/app/domain/safety.py (enforce_symptom_safety),
backend/app/services/ai/symptom_service.py, backend/app/domain/schemas.py
(SymptomDiagnoseRequest/Response).

Sonuç: KRİTİK 1 · YÜKSEK 2 · ORTA 2 → BLOCK (yayından önce zorunlu düzeltmeler).

Doğrulanan güçlü noktalar:
- enforce_symptom_safety servis akışında son katman olarak çağrılıyor (symptom_service.py:60).
- ariza_sistem=='fren' VEYA aciliyet=yuksek => tamirci + uyarı zorlanıyor (safety.py:286).
- LPG müdahale tarifi prompt'ta yasak (_base.md:14); kodda LPG_INTERVENTION yakalanırsa
  LPG_SAFETY_WARNING + tamirci zorlanıyor (safety.py:282).
- Şema hem guvenlik_uyarisi hem tamirciye_git_onerisi içeriyor (şema bütünlüğü OK).
- "büyük ihtimalle" hedge prompt'ta + kod backstop'unda (tespit) mevcut.

Bulgular:
1. [KRİTİK] safety.py:286 — Fren DIŞINDAKİ güvenlik-kritik belirtiler (direksiyon kilitlenmesi,
   duman/yangın, metalik vuruntu) enforce katmanında zorlanmıyor. Prompt bunları "yuksek aciliyet"
   olarak işaretlemeye GÜVENİYOR; model orta/dusuk verirse fren-dışı kritik belirti tamirci+uyarı
   ALMADAN geçer. SAFETY_TRIGGER_KEYWORDS'te "direksiyon", "duman", "yangın", "metalik" YOK.
2. [YÜKSEK] safety.py:269-291 — haystack guvenlik_uyarisi tetikleyicisi için yalnız tespit+
   sonraki_adim+context+olasi_nedenler tarıyor; aciliyet tetiklemiyorsa ve keyword yoksa fren-dışı
   ciddi belirtide uyarı boş kalır. Ayrıca _mentions_safety_topic'te yağ basıncı sadece generic
   "basınç" ile kısmen yakalanıyor (DTC bulgusuyla aynı kök).
3. [YÜKSEK] _ensure_hedge yalnız tespit'e uygulanıyor; olasi_nedenler ve sonraki_adim kullanıcıya
   görünüyor ama hedge/kesin-dil yumuşatmadan geçmiyor (image/sound/dtc ile aynı sınır).
4. [ORTA] _ensure_hedge "kesin"/"arıza şudur"/"sorun budur" literallerini yakalamıyor (DEFINITIVE_
   PHRASES eksik) — DTC denetimindeki açık bulgu burada da geçerli.
5. [ORTA] symptom_service.py:54-58 — ValidationError path'inde token loglanıyor ama güvenlik
   açısından nötr; not olarak: AIKind.sound + kategori='belirti' kayıt seçimi kasıtlı.

---

## 2026-06-13 — Dashboard (pano) denetiminden taşınan kabul edilmiş istisnalar
(İlk denetim backend/ cwd'sinde yapıldığı için ayrı konumda kalmıştı; buraya
birleştirildi. Bu istisnalar gelecekte YENİDEN UYARILMAMALI:)
- DEFAULT_SAFETY_WARNING / DASHBOARD_RED_WARNING / LPG_SAFETY_WARNING sabitleri
  tasarım gereği tetikleyici kelime (motor, fren, akü, kesinlikle...) içerir —
  sabit metinlerin KENDİSİ ihlal olarak işaretlenmez.
- Dashboard teşhisi AISession'a kind=AIKind.image + kategori='pano_uyari',
  DTC kind=AIKind.sound + kategori='ariza_kodu', belirti kind=AIKind.sound +
  kategori='belirti' olarak kasıtlı loglanır (AIKind native-enum riskinden
  kaçınmak için; güvenlik sorunu değil).
- Dashboard YÜKSEK bulguları (per-ışık `anlam` hedge, _ensure_hedge kesin-dil
  yumuşatma) DÜZELTİLDİ (commit a97ab4a).
