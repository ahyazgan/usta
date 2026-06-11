# Usta — Canlıya Çıkış Rehberi (Deploy)

Amaç: backend'i bir public URL'e koymak ve mobil uygulamayı (APK) telefonda
çalıştırmak. Hepsi bulut üzerinden yapılır, laptop gerekmez.

> 🔐 **API anahtarı asla repoya/sohbete girmez.** Yalnızca aşağıdaki host
> panellerine **environment değişkeni** olarak yapıştırılır.

---

## 1) Backend → Render (ücretsiz)

1. https://render.com → GitHub ile giriş yap, bu repoyu bağla.
2. **New → Blueprint** → repodaki `render.yaml` otomatik bulunur → **Apply**.
   - Bu, bir **web servisi** (Docker, `backend/Dockerfile`) + **ücretsiz Postgres** oluşturur.
3. Servis oluştuktan sonra **Environment** sekmesinde:
   - `USTA_ANTHROPIC_API_KEY` → **Claude anahtarını buraya yapıştır** (repoda yok).
   - `USTA_JWT_SECRET` ve `USTA_DATABASE_URL` otomatik dolar (elleme).
4. İlk deploy bitince servis URL'in olur: `https://usta-backend-XXXX.onrender.com`.
5. Test: tarayıcıda `…onrender.com/health` → `{"status":"ok","database":"ok"}`.
6. (İsteğe bağlı) Demo veri: Render **Shell**'de `python -m app.seed`.

**Ortam değişkenleri**

| Değişken | Değer | Not |
|---|---|---|
| `USTA_ANTHROPIC_API_KEY` | `sk-ant-…` | **Elle gir** (panelde) |
| `USTA_JWT_SECRET` | (otomatik) | Render üretir |
| `USTA_DATABASE_URL` | (otomatik) | Postgres'ten bağlanır; kod `asyncpg`'ye normalize eder |
| `USTA_DEBUG` | `false` | Prod |

> 💳 Gerçek AI çağrısı için Claude Console'da **küçük bir kredi** gerekir
> (Add funds). Hedef maliyet teşhis başına < $0.05.

> ℹ️ Ücretsiz Render servisi boştayken uyur; ilk istek birkaç saniye gecikir.
> Ücretsiz Postgres'in süre sınırı vardır (geliştirme için yeterli).

Alternatifler: `Procfile` ile Railway/Heroku-tarzı da çalışır; Fly.io için
`fly launch` Dockerfile'ı kullanır.

---

## 2) Mobil → EAS Build (APK, bulutta derlenir)

Bilgisayar gerekmez; derleme Expo sunucularında olur, çıktıyı telefona kurarsın.

1. `mobile/eas.json` içindeki `EXPO_PUBLIC_API_URL`'i **Render URL'inle** değiştir
   (`preview` profili) — örn. `https://usta-backend-XXXX.onrender.com`.
2. Bir Expo hesabı aç (https://expo.dev). Sonra (bir terminalde / bulutta):
   ```bash
   cd mobile
   npm install -g eas-cli       # ilk sefer
   eas login
   eas init                     # app.json'a projectId ekler
   eas build -p android --profile preview
   ```
3. Derleme bitince Expo bir **APK indirme linki/QR** verir → telefonda aç, kur.
4. Uygulama açılır → Kayıt ol / Giriş yap → araç ekle → kamerayla teşhis.

> iOS için `eas build -p ios --profile preview` (Apple geliştirici hesabı gerekir).
> Android APK en hızlı yoldur.

---

## 3) Uçtan uca akış (anahtar girildikten sonra)
1. Render backend ayakta (`/health` ok) + `USTA_ANTHROPIC_API_KEY` dolu + kredi var.
2. APK telefonda kurulu, `EXPO_PUBLIC_API_URL` Render'a bakıyor.
3. Kayıt → araç ekle (spec katalogdan otomatik) → görev seç → kamerayla "doğru yer mi"
   doğrulaması (gerçek `claude-sonnet-4-5`) → ses tarifi analizi → bakım geçmişi.

## Üretim öncesi kontrol
- [ ] `USTA_DEBUG=false` (CORS prod alanına kısıtlı; native uygulamada CORS sorunu olmaz)
- [ ] `USTA_JWT_SECRET` güçlü ve rastgele (Render üretir)
- [ ] Postgres bağlı, `/health` `database: ok`
- [ ] Claude anahtarı yalnızca panelde; repoda/sohbette değil; kredi tanımlı
