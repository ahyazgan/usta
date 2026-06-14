/**
 * Büyüme motoru — paylaşım döngüleri.
 *
 * "Usta Raporu": aracın bakım karnesi + tasarruf, uygulama linkiyle paylaşılır
 * (ikinci el satışı / sosyal kanıt → yeni indirme). "Davet": arkadaş çağırma.
 * Web'de navigator.share / panoya kopyalama'ya düşer; native'de RN Share.
 */
import { Platform, Share } from 'react-native';

import { capture } from '@/lib/analytics';
import type { Vehicle, VehicleSummary } from '@/lib/api';
import { t } from '@/lib/i18n';

// Uygulama indirme bağlantısı (mağaza yayını sonrası güncellenecek).
export const APP_LINK = 'https://usta.app';

async function shareText(message: string): Promise<boolean> {
  try {
    if (Platform.OS === 'web') {
      const nav = globalThis.navigator as
        | { share?: (d: { text: string }) => Promise<void>; clipboard?: { writeText: (s: string) => Promise<void> } }
        | undefined;
      if (nav?.share) {
        await nav.share({ text: message });
        return true;
      }
      if (nav?.clipboard) {
        await nav.clipboard.writeText(message);
        return true;
      }
      return false;
    }
    const res = await Share.share({ message });
    return res.action !== Share.dismissedAction;
  } catch {
    return false;
  }
}

/** "Usta Raporu" paylaşım metnini araç + özetten kurar. */
export function buildReportText(vehicle: Vehicle, summary: VehicleSummary): string {
  const name = `${vehicle.make} ${vehicle.model}`;
  const plate = vehicle.plate ? ` (${vehicle.plate})` : '';
  const lines = [t('share.report.title'), `${name}${plate}`];
  if (vehicle.current_km != null) {
    lines.push(t('share.report.km', { km: vehicle.current_km.toLocaleString('tr-TR') }));
  }
  if (summary.maintenance_count > 0) {
    lines.push(
      t('share.report.maintenance', {
        count: summary.maintenance_count,
        savings: summary.savings_try.toLocaleString('tr-TR'),
      }),
    );
  }
  lines.push('', t('share.report.cta', { link: APP_LINK }));
  return lines.join('\n');
}

/** Aracın Usta Raporu'nu paylaş. */
export async function shareReport(vehicle: Vehicle, summary: VehicleSummary): Promise<void> {
  const ok = await shareText(buildReportText(vehicle, summary));
  if (ok) void capture('report_shared');
}

/** Arkadaş davet et (referans linkli). */
export async function shareInvite(): Promise<void> {
  const ok = await shareText(t('share.invite', { link: APP_LINK }));
  if (ok) void capture('invite_shared');
}

/** "Mekaniğe Göster" özetini paylaş (WhatsApp/SMS vb.). */
export async function shareMechanicBrief(text: string): Promise<void> {
  const ok = await shareText(text);
  if (ok) void capture('mechanic_brief_shared');
}

/** Bir başarı anını (rehber bitişi) paylaş. */
export async function shareAchievement(taskTitle: string, savingTry: number): Promise<void> {
  const msg = [
    t('share.achievement', { task: taskTitle, savings: savingTry.toLocaleString('tr-TR') }),
    '',
    t('share.report.cta', { link: APP_LINK }),
  ].join('\n');
  const ok = await shareText(msg);
  if (ok) void capture('achievement_shared', { task: taskTitle });
}
