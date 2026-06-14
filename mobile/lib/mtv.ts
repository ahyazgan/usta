/**
 * MTV (Motorlu Taşıt Vergisi) son ödeme tarihi hesaplayıcı.
 *
 * Türkiye'de MTV yılda iki taksit halinde ödenir: 1. taksit OCAK sonuna,
 * 2. taksit TEMMUZ sonuna kadar. Tarihler her araç için aynı ve sabittir
 * (tutar araca göre değişir; tutar hesaplanmaz — resmi/ücretsiz veri yok).
 * Bu yüzden kullanıcı girmez; bir sonraki son ödeme tarihi hesaplanır.
 */
import { daysUntil } from '@/lib/dateReminders';

/** Bir sonraki MTV son ödeme tarihini ISO (YYYY-MM-DD) olarak döndürür. */
export function nextMtvDeadline(): string {
  const year = new Date().getFullYear();
  const jan = `${year}-01-31`;
  const jul = `${year}-07-31`;
  if (daysUntil(jan) >= 0) return jan;
  if (daysUntil(jul) >= 0) return jul;
  return `${year + 1}-01-31`;
}

/** Bu son ödeme hangi taksit (1. = Ocak, 2. = Temmuz). */
export function mtvInstallment(iso: string): 1 | 2 {
  return iso.slice(5, 7) === '01' ? 1 : 2;
}

export default nextMtvDeadline;
