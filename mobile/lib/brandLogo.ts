/**
 * Marka logoları.
 *
 * React Native `require()` STATİK yol ister; dinamik string ile yüklenemez.
 * Bu yüzden logoları AŞAĞIDAKİ KAYDA tek tek eklersin:
 *
 *   1) Logo PNG'sini `mobile/assets/logos/<marka>.png` olarak koy
 *      (örn. assets/logos/honda.png) — kare, şeffaf zemin, ~128px önerilir.
 *   2) Aşağıdaki LOGOS objesine satırı ekle (anahtar küçük harf, marka adı):
 *        honda: require('../assets/logos/honda.png'),
 *
 * Logosu olmayan markalar otomatik olarak baş-harf rozetine düşer (kod gerekmez).
 * Kayıt boşken her şey baş-harf rozetiyle çalışır; build kırılmaz.
 */
import type { ImageSourcePropType } from 'react-native';

const LOGOS: Record<string, ImageSourcePropType> = {
  // Buraya logo ekle. Örnekler (dosyayı ekledikten sonra yorumdan çıkar):
  // fiat: require('../assets/logos/fiat.png'),
  // renault: require('../assets/logos/renault.png'),
  // volkswagen: require('../assets/logos/volkswagen.png'),
  // honda: require('../assets/logos/honda.png'),
  // yamaha: require('../assets/logos/yamaha.png'),
};

/** Markanın logosu (kayıtlıysa) veya null. */
export function brandLogo(make: string | null | undefined): ImageSourcePropType | null {
  if (!make) return null;
  return LOGOS[make.trim().toLowerCase()] ?? null;
}

/** Logosu olmayan markalar için baş harf(ler) — rozet yedeği. */
export function brandInitials(make: string | null | undefined): string {
  const m = (make ?? '').trim();
  if (m.length === 0) return '?';
  // İki kelimeyse baş harfleri, değilse ilk iki harf.
  const parts = m.split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return m.slice(0, 2).toUpperCase();
}
