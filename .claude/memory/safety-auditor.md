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
