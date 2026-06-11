# Usta — Proje Kuralları (CLAUDE.md)

Usta, araç sahipleri için bir **AI bakım asistanı** mobil uygulamasıdır. Kullanıcı
aracını tanıtır (marka/model/yıl/motor kodu/yakıt), bir bakım görevi seçer (yağ
değişimi, buji, filtre...), uygulama o araca **özel** adım adım rehberlik eder.
Kamera ile "doğru yeri buldun ✓" doğrulaması ve motor sesi **tarif** analizi yapar.

**Rakip:** MECH AI (mechai.app). **Farkımız:** canlı rehberli kamera, Türkiye
odağı (TR araç parkı, LPG farkındalığı), çift dil (TR/EN).

---

## STACK
- `mobile/` → Expo (React Native) + TypeScript + expo-router + expo-camera + zustand + i18n-js
- `backend/` → FastAPI (Python 3.12) + SQLAlchemy async + Claude API (`anthropic>=0.40`)
- **Celery / Redis / pgvector / S3 KULLANMA** — MVP'de yok.

---

## KATMAN MİMARİSİ (atlama YASAK)
- Backend: `api/` → `services/` → `domain/`. Üst katman alt katmanı çağırır; alt
  katman üstü import etmez. Rotalar yalnızca servis çağırır; iş mantığı serviste,
  saf kurallar/şema/model `domain/` içinde.
- Mobile: `screens (app/)` → `components` → `hooks` → `lib`.

## ULUSLARARASILAŞTIRMA
- **Tüm UI metinleri** `mobile/locales/tr.json` + `en.json` içinde. **Hardcoded
  string YASAK.** `tr` ve `en` anahtar kümeleri birebir aynı olmalı.

## AI PROMPT'LARI
- Tüm prompt'lar `backend/prompts/` altında ayrı `.md` dosyalarında. Kod içine
  gömülü prompt yazma. Vision prompt'ları `prompts/vision/`, ses `prompts/audio/`.

## HER ENDPOINT
- JWT zorunlu + **kullanıcı-bazlı rate limit** + **30s timeout** + **tenacity
  retry(2)** (geçici hatalarda, toplam 3 deneme).

---

## GÜVENLİK (EN YÜKSEK ÖNCELİK)
1. AI yanıtlarında **kesin teşhis dili YASAK**; **"büyük ihtimalle"** zorunlu.
2. Sıcak motor / kriko / akü / yakıt / soğutma basıncı / fren / LPG geçen **her**
   yanıtta `guvenlik_uyarisi` **zorunlu**.
3. **LPG sistemine müdahale tarifi YASAK** — yetkili LPG servisine yönlendir.
4. Her görevde **"vazgeç, tamirciye git"** çıkış noktası bulunur; risk/şüphe
   varsa `tamirciye_git_onerisi=true`.

Bu kurallar `backend/app/domain/safety.py` içinde son katman olarak ZORLANIR ve
`safety-auditor` subagent'ı ile prompt/rehberlere karşı denetlenir.

## MALİYET
- **Vision = `claude-sonnet-4-5`** (Opus YASAK). Ses analizi de sonnet.
- Frame **max 1024px**, **JPEG 0.7**.
- Token sayıları (`tokens_in`/`tokens_out`) `AISession`'a loglanır.
- Hedef: **teşhis başına < $0.05**.

---

## AI YANIT ŞEMASI (her görsel teşhis)
```json
{
  "tespit": "string (büyük ihtimalle ...)",
  "guven": "yuksek | orta | dusuk",
  "konum_tarifi": "sol-ust|orta-ust|sag-ust|sol-orta|merkez|sag-orta|sol-alt|orta-alt|sag-alt|null",
  "dogru_yer_mi": "bool | null",
  "sonraki_adim": "string",
  "guvenlik_uyarisi": "string | null",
  "tamirciye_git_onerisi": "bool"
}
```
`konum_tarifi` = kameranın 3x3 ızgarasında ilgili parçanın hücresi.

## SES ANALİZİ
- **Whisper / transkripsiyon KULLANMA** — motor sesi transkribe edilemez.
- Girdi: kullanıcı **tarifi** + **kayıt koşulu** (`rolanti | gazda | soguk_motor |
  seyirde`) + araç verisi → Claude **metin** analizi.
- Kategoriler: `tikirti | kayis_sesi | metalik_vuruntu | islik | egzoz_patlamasi |
  normal | belirsiz`. `metalik_vuruntu` → **her zaman acil + tamirci**.

---

## TASARIM — "Gece Garajı"
| Token | Değer |
|---|---|
| zemin | `#16181D` |
| yüzey | `#1D2026` |
| border | `#2A2D34` |
| vurgu (amber) | `#FF8A00` |
| ✓ başarı | `#22C55E` |
| ✗ hata | `#EF4444` |
| uyarı | `#EAB308` |
| metin | `#F2F3F5` / `#8B8E96` |

- Başlık fontu: **Barlow Condensed**, gövde: **Inter**.
- Koyu tema **varsayılan**. Dokunma hedefi **min 56dp** (eldivenli el).
- **Yeşil yalnızca doğrulama durumunda** kullanılır (başka yerde değil).

---

## ARAÇLAR (`.claude/`)
- **Subagent'lar:** `safety-auditor`, `test-writer`, `cost-guard`, `i18n-checker`,
  `vision-prompt-engineer`, `mobile-expert`.
- **Komutlar:** `/new-task-guide`, `/add-endpoint`, `/safety-audit`,
  `/generate-tests`, `/i18n-sync`.

## TEST
- Claude API **her zaman mock** (gerçek ağ yok). Her endpoint için
  happy + 401 + 429 + 422; güvenlik uyarısı senaryoları assert edilir.
- Çalıştır: `cd backend && python -m pytest`.
