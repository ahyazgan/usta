# Marka Logoları

Araç markası logolarını buraya koy ve `lib/brandLogo.ts` kaydına ekle.

## Nasıl eklenir
1. Logoyu `mobile/assets/logos/<marka>.png` olarak kaydet
   - Dosya adı küçük harf, marka adıyla aynı: `honda.png`, `volkswagen.png`, `yamaha.png`
   - Kare, **şeffaf zemin**, ~128×128 px önerilir
2. `mobile/lib/brandLogo.ts` içindeki `LOGOS` objesine satır ekle:
   ```ts
   honda: require('../assets/logos/honda.png'),
   ```

Logosu olmayan markalar otomatik **baş-harf rozeti**ne düşer — kod gerekmez,
uygulama çalışmaya devam eder.

## Katalogdaki markalar (logo için aday)
Araba: Fiat, Renault, Toyota, Dacia, Volkswagen, Hyundai, Ford, Opel, Peugeot, Honda
Motosiklet: Honda, Yamaha, Mondial, Kuba, RKS, Bajaj

> Telif: Yalnızca kullanım hakkına sahip olduğun veya marka rehberlerinin izin
> verdiği logoları ekle.
