# Usta 🔧

**Araç sahipleri için AI bakım asistanı.** Kullanıcı aracını tanıtır, bir bakım
görevi seçer (yağ, buji, filtre, fren, soğutma, lastik, silecek, far…), Usta o
araca özel **adım adım** rehberlik eder — gerekli **alet ve tork** dahil.
Kamerayla **"doğru yeri buldun ✓"** doğrulaması ve motor sesi **tarif** analizi
yapar; her işten **tasarrufunu** ve teşhis geçmişini tutar.

> **Farkımız (rakip: [MECH AI](https://mechai.app)):** canlı rehberli kamera,
> Türkiye odağı (TR araç parkı, LPG farkındalığı), çift dil (TR/EN).

**Canlı backend:** `https://usta-backend.onrender.com` · sağlık: `/health` ·
API dokümanı: `/docs`

---

## Yapı

```
usta/
├── CLAUDE.md              # Proje kuralları (mimari, güvenlik, maliyet, tasarım)
├── .claude/
│   ├── agents/            # 6 subagent (safety-auditor, test-writer, cost-guard,
│   │                      #   i18n-checker, vision-prompt-engineer, mobile-expert)
│   └── commands/          # 5 komut (/new-task-guide, /add-endpoint, /safety-audit,
│                          #   /generate-tests, /i18n-sync)
├── backend/              # FastAPI + SQLAlchemy async + Claude API
│   ├── app/
│   │   ├── api/          # rotalar (auth, vehicles, tasks, maintenance, ai)
│   │   ├── services/     # iş mantığı (auth, vehicle, maintenance, ai/vision, ai/audio)
│   │   ├── domain/       # modeller, enum'lar, şemalar, görevler, rehberler, güvenlik
│   │   ├── core/         # security (bcrypt/JWT), rate limit, deps
│   │   ├── config.py · database.py (+ idempotent kolon migration) · main.py
│   ├── prompts/          # AI prompt'ları (vision/, audio/) — kod dışında
│   └── tests/            # pytest (Claude mock'lu) — 88 test
└── mobile/              # Expo + TypeScript + expo-router (alt tab bar)
    ├── app/             # ekranlar: index (Ana Sayfa), maintenance (Bakım),
    │                    #   guide (adım adım), camera, sound (Teşhis), history (Geçmiş)
    ├── components/      # BottomTabBar
    ├── lib/             # theme, i18n, api, store, nav, demoSession, taskIcons, hook'lar
    └── locales/         # tr.json + en.json (parite zorunlu)
```

## Mimari kuralı
`api/ → services/ → domain/` (atlama yasak) · `screens → components → hooks → lib`

## Güvenlik (en yüksek öncelik)
Kesin teşhis dili yasak ("büyük ihtimalle" zorunlu) · sıcak motor/kriko/akü/yakıt/
soğutma/fren/LPG yanıtlarında güvenlik uyarısı zorunlu · **LPG müdahale tarifi
yasak** · her görevde ve rehberde "tamirciye git" çıkışı. Kurallar
`domain/safety.py` içinde zorlanır; rehberler (`domain/guides.py`) safety-auditor
denetiminden geçer (fren/soğutma yalnızca gözlem, söküm tarifi yok).

## Maliyet
Vision = `claude-sonnet-4-5` (Opus yasak) · frame max 1024px JPEG 0.7 · token
loglama (`AISession`) · hedef teşhis başına **< $0.05**.

---

## Özellikler (özet)

- **10 bakım görevi** — araç yakıtına göre filtrelenir (dizelde buji yok,
  elektrikte yağ/soğutma yok).
- **Adım adım rehber** — her görevin TR+EN adımları; talimatlardaki
  `{yer_tutucu}`'lar araç spec'inden dolar (örn. "14mm lokma", "30 Nm"). İlerleme
  hatırlanır; bitişte bakım loglanır + "+₺X tasarruf" kutlaması.
- **Kamera doğrulama** — Claude Vision ile "doğru yer mi" + 3x3 konum; rehberdeki
  mevcut adım AI'ye iletilir.
- **Ses teşhisi** — transkripsiyon YOK; kullanıcı tarifi + koşul + araç verisiyle
  metin analizi, baloncuklu sohbet arayüzü.
- **Hatırlatıcılar** — 7 görev için km-bazlı "Yaklaşıyor / Zamanı geldi".
- **Tasarruf takibi** — loglardan tahmini DIY işçilik tasarrufu (`/summary`).
- **Teşhis geçmişi** — geçmiş AI teşhisleri (güvenlik-sonrası özet) `/diagnoses`.
- **Çift dil + açık tema** ("Gündüz Servisi": krem zemin, mürekkep birincil).

> Mobilde şu an **otomatik demo girişi** var (login ekranı kaldırıldı). Gerçek
> kayıt/giriş, yayın hazırlığı fazında geri gelecek.

---

## Backend — çalıştırma

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Geliştirme sunucusu
export USTA_ANTHROPIC_API_KEY=sk-ant-...   # gerçek AI çağrıları için
uvicorn app.main:app --reload --port 8080

# Testler (Claude mock'lu — API anahtarı gerekmez)
python -m pytest
```

Sağlık kontrolü: `GET /health` (DB ping'li). `create_all()` yeni tabloları açar
ve eksik kolonları idempotent `ADD COLUMN` ile ekler (alembic MVP dışı).

### Önemli endpoint'ler
| Method | Yol | Açıklama |
|---|---|---|
| POST | `/v1/auth/register` · `/login` · `/refresh` | bcrypt12, sha256 refresh token |
| GET/POST/PATCH/DELETE | `/v1/vehicles` | yalnızca kendi araçların (403); spec katalogdan dolar; plaka alanı |
| GET | `/v1/tasks` · `/v1/vehicles/{id}/tasks` | görev listesi (genel / araca özel, yakıt filtreli) |
| GET | `/v1/vehicles/{id}/tasks/{task}/guide` | araca özel adım adım rehber (alet/tork/uyarı) |
| GET | `/v1/vehicles/{id}/reminders` | km-bazlı bakım hatırlatıcıları |
| GET | `/v1/vehicles/{id}/summary` | kayıtlı bakım sayısı + tahmini tasarruf (TL) |
| GET/POST | `/v1/vehicles/{id}/logs` | bakım geçmişi kayıtları |
| GET | `/v1/vehicles/{id}/diagnoses` | son AI teşhisleri (görüntü + ses) |
| POST | `/v1/ai/diagnose/image` | görsel teşhis (3x3 konum şeması) |
| POST | `/v1/ai/diagnose/sound` | ses **tarifi** analizi (transkripsiyon yok) |

Her endpoint: JWT + kullanıcı-bazlı rate limit + 30s timeout + tenacity retry(2).

### Demo verisi ve maliyet denetimi
```bash
python -m app.seed                  # demo kullanıcı (demo@usta.app / demoparola1234)
                                    #   + 3 plakalı TR aracı (idempotent)

# Vision maliyet/şema harness'i (cost-guard):
python -m app.tools.eval_vision --offline                 # anahtarsız öz-denetim
```
Hedef: teşhis başına **< $0.05** (`domain/pricing.py`).

---

## Mobile — çalıştırma

```bash
cd mobile
npm install

# Telefonda (Expo Go) — canlı backend'e bağlan:
EXPO_PUBLIC_API_URL=https://usta-backend.onrender.com npx expo start
# Tarayıcı önizleme (kamera çalışmaz): npx expo start --web
```

- Tema **"Gündüz Servisi"** (açık), dokunma hedefi min 56dp.
- Tüm metinler `locales/tr.json` + `en.json` üzerinden (hardcoded string yok, parite zorunlu).
- Alt tab bar: **Ana Sayfa · Teşhis · Bakım · Geçmiş**.

### APK (EAS Build)
`eas.json` ve `app.json` (paket `com.usta.app`) hazır.
```bash
cd mobile && eas build -p android --profile preview
```

---

## Geliştirme araçları (Claude Code)
`/safety-audit` · `/generate-tests <modül>` · `/i18n-sync` · `/add-endpoint` ·
`/new-task-guide <görev>` — ilgili subagent'ları zincirler.

> **MVP kapsamı dışı (bilinçli):** Celery / Redis / pgvector(RAG) / S3 / WatermelonDB
> / push bildirim / RevenueCat. Statik TR araç kataloğu RAG yerine spec'leri
> prompt'a enjekte eder.
