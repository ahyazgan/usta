/**
 * Tarih-bazlı hatırlatıcı yardımcıları (muayene / sigorta).
 *
 * Backend ISO (YYYY-MM-DD) saklar; kullanıcı TR formatında (GG.AA.YYYY) görür.
 * Kalan gün ve durum (geçti / yaklaşıyor / iyi) buradan hesaplanır.
 */

export type DateStatus = 'due' | 'soon' | 'ok';

/** Kalan gün bu eşiğin altındaysa "yaklaşıyor". */
export const SOON_THRESHOLD_DAYS = 30;

/** "15.03.2027" → "2027-03-15" (ISO). Geçersizse null. */
export function parseTrDate(input: string): string | null {
  const m = input.trim().match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/);
  if (!m) return null;
  const day = Number(m[1]);
  const month = Number(m[2]);
  const year = Number(m[3]);
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;
  if (year < 1950 || year > 2100) return null;
  // Gerçek geçerlilik (örn. 31.02 reddedilsin).
  const d = new Date(Date.UTC(year, month - 1, day));
  if (d.getUTCMonth() !== month - 1 || d.getUTCDate() !== day) return null;
  const mm = String(month).padStart(2, '0');
  const dd = String(day).padStart(2, '0');
  return `${year}-${mm}-${dd}`;
}

/** "2027-03-15" → "15.03.2027". Geçersizse ham metni döndürür. */
export function formatTrDate(iso: string | null): string {
  if (iso == null) return '';
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return iso;
  return `${m[3]}.${m[2]}.${m[1]}`;
}

/** Bugünden hedef ISO tarihe kalan tam gün (geçmişse negatif). */
export function daysUntil(iso: string): number {
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return Number.NaN;
  const target = Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  const now = new Date();
  const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((target - today) / 86_400_000);
}

export function dateStatus(iso: string): DateStatus {
  const d = daysUntil(iso);
  if (d <= 0) return 'due';
  if (d <= SOON_THRESHOLD_DAYS) return 'soon';
  return 'ok';
}
