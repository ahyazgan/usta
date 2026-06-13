# Canlı Sesli Rehber — Kurulum & Bağlama (dev-build)

Canlı mod (Gemini Live: görüntülü konuş, sesle rehberlik) **Expo Go'da çalışmaz** —
gerçek-zamanlı PCM ses yakalama/oynatma **native modül + dev-build** ister.
Ekran, oturum, kamera, WS protokolü, metering **hazır**; tek eksik **native ses
köprüsü** ve birkaç **doğrulama**.

## Mimari (hatırlatma)
```
Mobil → backend /v1/live/session → ephemeral token
Mobil → DOĞRUDAN Gemini Live (WS) → ses↔ses + kamera kare
Bitince → backend /v1/live/session/{id}/end (dakika sayacı)
```
`system_instruction` (güvenlik + araç + görev) backend'de token'a bağlanır,
istemciye sızmaz.

## 1) Backend'i aç
`.env` (Render ortam değişkeni — anahtarı ASLA koda/git'e yazma):
```
USTA_GEMINI_API_KEY=...        # Google AI Studio'dan
USTA_GEMINI_LIVE_MODEL=gemini-3.1-flash-live-preview   # API ile doğrulandı (mevcut)
USTA_GEMINI_DEFAULT_VOICE=Puck
USTA_FREE_LIVE_SECONDS_PER_MONTH=600
```
Anahtar boşsa `/v1/live/session` **503** döner (canlı mod kapalı).

> ✅ Doğrulandı (canlı API testi): anahtar `?key=` ile çalışıyor; canlı model
> `gemini-3.1-flash-live-preview` mevcut; ephemeral token ucu `v1alpha/auth_tokens`
> 200 + `{"name": ...}` döndürüyor (kodumuz bu alanı okuyor). Kalan tek belirsiz:
> `liveConnectConstraints` config-bağlama şeklinin tam alanları (güvenlik config'i
> token'a bağlar) — Render'da ilk gerçek oturumda teyit et.

## 2) Dev-build oluştur
```
cd mobile
npx expo install expo-dev-client
npx expo prebuild          # native projeleri üretir (Expo Go'dan çıkar)
npx expo run:android       # veya: eas build --profile development
```

## 3) Native ses köprüsünü bağla
`lib/live/audioBridge.ts` içindeki `AudioBridge` arayüzünü implemente et:
- `startMic(onChunk)` — mikrofonu **PCM16 16kHz mono** yakala, her parçayı
  base64 olarak `onChunk`'a ver
- `playChunk(base64)` — Gemini'den gelen **PCM16 24kHz mono** parçayı çal
- `stop()` — durdur/bırak

Uygulama başlangıcında (örn. `app/_layout.tsx`) kaydet:
```ts
import { setAudioBridge } from '@/lib/live/audioBridge';
setAudioBridge(new MyNativeAudioBridge());
```
Bağlanana kadar görüntü çalışır, ses sessizdir (ekranda uyarı gösterilir).

> Öneri: gerçek-zamanlı PCM için bir native ses kütüphanesi (örn. Web Audio API
> tabanlı RN modülü) veya küçük bir Expo native modülü değerlendir. Kayıt-dosyası
> odaklı `expo-av`/`expo-audio` akış için yetmez.

## 4) Gemini Live protokolünü DOĞRULA
`lib/live/engine.ts` içinde `⚠️ DOĞRULA` işaretli yerler:
- WS uç'u (`LIVE_WS_BASE`)
- ephemeral token'ın nasıl iletildiği (query param mı, header mı)
- `realtimeInput` / `serverContent` / `toolCall` mesaj şekilleri

Google Live API hızlı evriliyor; güncel dokümana göre bu şekilleri teyit et.
Mantık akışı (bağlan → gönder → al → tool) sağlam; sadece tel-formatı.

## 5) AI Studio ön-doğrulaması (kod yazmadan, bedava)
1. **TR/EN ses** doğal mı?
2. **Vision** gerçek motor parçalarını doğru görüyor mu?
3. **Tool calling** (function declarations) çalışıyor mu?
4. **Güncel dakika fiyatı** (ai.google.dev/pricing)

## Akış kontrol listesi (bağlandıktan sonra)
- [ ] `/v1/live/session` token döndürüyor (key set)
- [ ] WS açılıyor, "live" durumu
- [ ] Mikrofon → ses gidiyor, Gemini sesi geliyor (köprü bağlı)
- [ ] Kamera karesi 2sn'de bir gidiyor
- [ ] `fiyat_tahmini` tool çağrısı backend'e düşüp dönüyor
- [ ] Bitişte `/end` süreyi yazıyor, aylık limit çalışıyor (402)
