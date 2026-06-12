/**
 * "Mekaniğe Göster" raporu — triyaj köprüsü.
 *
 * AI teşhisini, kullanıcının tamirciye gösterebileceği/gönderebileceği
 * profesyonel, kısa bir özete çevirir. Tamirci ağı GEREKTİRMEZ: ekranı göster
 * ya da WhatsApp'tan paylaş. Sorumluluk reddi zorunludur (AI ön değerlendirme,
 * kesin teşhis değil) — hem güvenlik kuralı hem tamirci güveni için.
 *
 * Yeni AI üretimi YOK; yalnızca güvenlik kuralları zaten uygulanmış çıktıyı
 * yeniden biçimlendirir.
 */
import type { Aciliyet, Guven, Vehicle } from '@/lib/api';
import { t } from '@/lib/i18n';

/** Normalleştirilmiş teşhis — kamera/ses sonucundan ya da geçmişten doldurulur. */
export interface BriefDiag {
  /** "Görüntü teşhisi" / "Ses teşhisi" gibi tür etiketi. */
  kindLabel?: string;
  /** AI tespiti ("büyük ihtimalle ..."). */
  tespit: string;
  /** Yerelleştirilmiş görev başlığı (görüntü teşhisinde). */
  taskLabel?: string;
  /** Yerelleştirilmiş araç sistemi (varsa). */
  sistemLabel?: string;
  /** Yerelleştirilmiş ses türü (ses teşhisinde). */
  sesKategoriLabel?: string;
  guven?: Guven | null;
  aciliyet?: Aciliyet | null;
  /** AI'nın önerdiği sonraki adım. */
  sonrakiAdim?: string | null;
  /** Güvenlik uyarısı (varsa). */
  guvenlikUyarisi?: string | null;
  /** Gösterim için tarih (geçmişten gelirse). */
  dateLabel?: string;
}

/** Mekaniğe gösterilecek/paylaşılacak özet metni. */
export function buildBriefText(vehicle: Vehicle, diag: BriefDiag): string {
  const lines: string[] = [t('brief.title')];

  // Araç künyesi
  const vparts = [`${vehicle.make} ${vehicle.model} ${vehicle.year}`];
  if (vehicle.plate) vparts.push(vehicle.plate);
  lines.push(`${t('brief.vehicle')}: ${vparts.join(' · ')}`);

  const eparts: string[] = [];
  if (vehicle.engine_code) eparts.push(vehicle.engine_code);
  eparts.push(t(`vehicle.fuel.${vehicle.fuel_type}`));
  if (vehicle.current_km != null) {
    eparts.push(`${vehicle.current_km.toLocaleString('tr-TR')} km`);
  }
  lines.push(`${t('brief.engine')}: ${eparts.join(' · ')}`);

  lines.push('');

  // Teşhis
  if (diag.taskLabel) lines.push(`${t('brief.task')}: ${diag.taskLabel}`);
  lines.push(`${t('brief.complaint')}: ${diag.tespit}`);
  if (diag.sistemLabel) lines.push(`${t('brief.system')}: ${diag.sistemLabel}`);
  if (diag.sesKategoriLabel) lines.push(`${t('brief.soundType')}: ${diag.sesKategoriLabel}`);

  const meta: string[] = [];
  if (diag.guven) meta.push(`${t('brief.confidence')}: ${t(`camera.guven.${diag.guven}`)}`);
  if (diag.aciliyet) meta.push(`${t('brief.urgency')}: ${t(`sound.aciliyet.${diag.aciliyet}`)}`);
  if (meta.length) lines.push(meta.join(' · '));

  if (diag.sonrakiAdim) lines.push(`${t('brief.nextStep')}: ${diag.sonrakiAdim}`);
  if (diag.guvenlikUyarisi) lines.push(`⚠️ ${diag.guvenlikUyarisi}`);
  if (diag.dateLabel) lines.push(`${t('brief.date')}: ${diag.dateLabel}`);

  lines.push('', t('brief.disclaimer'), '', t('brief.footer'));
  return lines.join('\n');
}
