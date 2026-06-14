# Usta — Yayın Hazırlık Kılavuzu

Uygulama **build'e hazır.** APK çıkar → telefonuna kur → gerçek araçta dene
(validation). Sonra mağaza yayını.

## ✅ Hazır olanlar (kod tarafı)
- `app.json`: isim/slug/scheme/sürüm (1.0.0), koyu tema, **icon 1024²**, splash,
  bundle id `com.usta.app`, EAS projectId, owner.
- İzinler: **kamera** (iOS NSCameraUsageDescription + Android CAMERA), **mikrofon**
  (iOS NSMicrophoneUsageDescription + Android RECORD_AUDIO — canlı sesli mod için).
- `eas.json`: `preview` (APK) + `production` profilleri; ikisi de
  `EXPO_PUBLIC_API_URL=https://usta-backend.onrender.com` → build otomatik canlı
  backend'e bağlanır.
- Backend canlı (Render), 154 test, /privacy ekranı (gizlilik metni) uygulamada var.

## 1) APK çıkar (validation için — Android, Mac gerekmez)
```bash
cd mobile
npm install -g eas-cli        # yoksa
eas login                     # Expo hesabınla (owner: ahyazgan)
eas build -p android --profile preview
```
→ Bitince EAS bir **APK indirme linki** verir. Telefonuna indir + kur (Android
"bilinmeyen kaynak"a izin ver). Uygulama doğrudan canlı backend'i kullanır.

> Not: Canlı sesli mod bu APK'da **sessiz** çalışır (native ses modülü bağlı değil
> — bkz. LIVE_SETUP.md). Teşhis / rehber / fiyat / katalog **tam çalışır** —
> validation için bunlar yeterli.

## 2) Gerçek araçta dene (asıl amaç — KANIT)
- Kendi aracını ekle → teşhis (kamera + ses) → **AI doğru mu okuyor?**
- Bir bakım rehberini aç → **akış garajda oturuyor mu?**
- Fiyat tahminlerine bak → **makul mü?**
- Notlarını al; prompt/UX'i veriye göre iyileştiririz.

## 3) iOS (Mac gerekmez — EAS bulutta derler)
```bash
eas build -p ios --profile preview     # gerektiğinde
```
- **Apple Developer** hesabı gerekir ($99/yıl). EAS kimlik bilgilerini ister.
- Camera/Microphone izin metinleri zaten app.json'da → Info.plist'e otomatik geçer.

## 4) Mağaza yayını için kalanlar (SENİN sağlayacakların)
| Gerek | Durum |
|---|---|
| Google Play geliştirici hesabı ($25 tek sefer) | senin |
| Apple Developer ($99/yıl, iOS için) | senin |
| **Hosted gizlilik politikası URL'i** (mağaza zorunlu) | gerekli — /privacy'yi bir web sayfasına da koy |
| Mağaza görselleri (ekran görüntüleri, feature grafik) | gerekli |
| Mağaza açıklaması (TR + EN) | gerekli |
| App Store gizlilik etiketi (veri beyanı) | KVKK altyapımız kolaylaştırır |
| Teşhis sorumluluk reddi ("kesin tavsiye değil") | ✅ uygulamada var (Apple lehine) |

## 5) Mağaza gönderimi (hazır olunca)
```bash
eas submit -p android --latest    # Play
eas submit -p ios --latest        # App Store
```
(Önce `eas.json` → `submit.production`'a hesap/credential bilgilerini ekle.)

---

## Önerilen sıra
1. **APK çıkar + kendi aracında dene** (bu hafta) → en yüksek değerli adım
2. Buluntulara göre prompt/UX düzelt
3. Mağaza görselleri + gizlilik URL'i hazırla
4. Play'e gönder (en hızlı), sonra App Store
5. İlk 100 kullanıcı taktikleri (FB grupları + fiyat-şeffaflık içeriği)

> En kritik: **özellik eklemeyi bırak, telefona/araca götür.** Wedge, gelir
> kanalları, canlı mod hazır — şimdi gerçekte işe yaradıklarını gör.
