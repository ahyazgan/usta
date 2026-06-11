# Usta 🔧

**Araç sahipleri için AI bakım asistanı.** Kullanıcı aracını tanıtır, bir bakım
görevi seçer (yağ değişimi, buji, filtre...), Usta o araca özel **adım adım**
rehberlik eder. Kamerayla **"doğru yeri buldun ✓"** doğrulaması ve motor sesi
**tarif** analizi yapar.

> **Farkımız (rakip: [MECH AI](https://mechai.app)):** canlı rehberli kamera,
> Türkiye odağı (TR araç parkı, LPG farkındalığı), çift dil (TR/EN).

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
│   │   ├── api/          # rotalar (auth, vehicles, ai)
│   │   ├── services/     # iş mantığı (auth, vehicle, ai/vision, ai/audio)
│   │   ├── domain/       # modeller, enum'lar, şemalar, güvenlik kuralları
│   │   ├── core/         # security (bcrypt/JWT), rate limit, deps
│   │   ├── config.py · database.py · main.py
│   ├── prompts/          # AI prompt'ları (vision/, audio/) — kod dışında
│   └── tests/            # pytest (Claude mock'lu, 4'lü matris + güvenlik)
└── mobile/              # Expo + TypeScript + expo-router
    ├── app/             # ekranlar (index = Garajım, camera)
    ├── lib/             # theme, i18n, api, store
    └── locales/         # tr.json + en.json
```

## Mimari kuralı
`api/ → services/ → domain/` (atlama yasak) · `screens → components → hooks → lib`

## Güvenlik (en yüksek öncelik)
Kesin teşhis dili yasak ("büyük ihtimalle" zorunlu) · sıcak motor/kriko/akü/yakıt/
soğutma/fren/LPG yanıtlarında güvenlik uyarısı zorunlu · **LPG müdahale tarifi
yasak** · her görevde "tamirciye git" çıkışı. Kurallar `domain/safety.py` içinde
zorlanır.

## Maliyet
Vision = `claude-sonnet-4-5` (Opus yasak) · frame max 1024px JPEG 0.7 · token
loglama (`AISession`) · hedef teşhis başına **< $0.05**.

---

## Backend — çalıştırma

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Geliştirme sunucusu
export USTA_ANTHROPIC_API_KEY=sk-ant-...   # gerçek AI çağrıları için
uvicorn app.main:app --reload --port 8080

# Testler (Claude mock'lu — API anahtarı gerekmez)
python -m pytest
```

Sağlık kontrolü: `GET /health` (DB ping'li).

### Önemli endpoint'ler
| Method | Yol | Açıklama |
|---|---|---|
| POST | `/v1/auth/register` · `/login` · `/refresh` | bcrypt12, sha256 refresh token |
| GET/POST/PATCH/DELETE | `/v1/vehicles` | yalnızca kendi araçların (403) |
| POST | `/v1/ai/diagnose/image` | görsel teşhis (3x3 konum şeması) |
| POST | `/v1/ai/diagnose/sound` | ses **tarifi** analizi (transkripsiyon yok) |

Her endpoint: JWT + kullanıcı-bazlı rate limit + 30s timeout + tenacity retry(2).

---

## Mobile — çalıştırma

```bash
cd mobile
npm install
npx expo start
```

- Tema **"Gece Garajı"** (koyu varsayılan), dokunma hedefi min 56dp.
- Tüm metinler `locales/tr.json` + `en.json` üzerinden (hardcoded string yok).
- `app/index.tsx` = **Garajım** (araç kartı + Yağ/Filtre/Akü çipleri + "Ustaya
  Göster"), `app/camera.tsx` = adım banner'ı + kalıcı sarı güvenlik şeridi +
  "Kontrol Et".

---

## Geliştirme araçları (Claude Code)
`/safety-audit` · `/generate-tests <modül>` · `/i18n-sync` · `/add-endpoint` ·
`/new-task-guide <görev>` — ilgili subagent'ları zincirler.

> MVP kapsamı: Celery / Redis / pgvector / S3 **yok**.
