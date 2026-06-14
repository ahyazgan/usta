/**
 * Yerel (cihaz-üstü) bakım bildirimleri — Celery/sunucu push YOK.
 *
 * Uygulama açıldığında araçların muayene/sigorta tarihlerine bakar ve
 * yaklaşan tarihler için yerel bildirim planlar (varsayılan: 7 gün önce 10:00).
 * Tüm planlama bu uygulamaya ait olduğundan her senkronda önce hepsi temizlenir
 * (mükerrer önlenir). Web'de ve izin yoksa sessizce no-op.
 */
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

import type { Vehicle } from '@/lib/api';
import { daysUntil, formatTrDate } from '@/lib/dateReminders';
import { t } from '@/lib/i18n';
import { nextMtvDeadline } from '@/lib/mtv';
import { useUstaStore } from '@/lib/store';

// Tarihten kaç gün önce hatırlatılsın.
const LEAD_DAYS = 7;
// Bildirimin günün hangi saatinde çıkacağı (yerel).
const NOTIFY_HOUR = 10;

let configured = false;

function ensureHandler(): void {
  if (configured) return;
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      // SDK 52+ API: shouldShowAlert yerine banner + list.
      shouldShowBanner: true,
      shouldShowList: true,
      shouldPlaySound: false,
      shouldSetBadge: false,
    }),
  });
  configured = true;
}

interface Planned {
  whenMs: number;
  body: string;
}

/** ISO tarihten bildirim zamanını (ms) hesaplar; geçmiş/geçersizse null. */
function computeWhen(iso: string): number | null {
  const remaining = daysUntil(iso);
  if (Number.isNaN(remaining) || remaining < 0) return null; // geçmiş tarih atlanır

  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return null;
  // Tarihten LEAD_DAYS önce; zaten o pencereye girdiysek yarın hatırlat.
  const target = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), NOTIFY_HOUR, 0, 0);
  let when = new Date(target.getTime() - LEAD_DAYS * 86_400_000);
  const now = new Date();
  if (when.getTime() <= now.getTime()) {
    when = new Date(now.getTime() + 86_400_000); // yarın
    when.setHours(NOTIFY_HOUR, 0, 0, 0);
  }
  if (when.getTime() <= now.getTime()) return null;
  return when.getTime();
}

/** Bir araç + tarih için (varsa) planlanacak bildirimi üretir. */
function planFor(vehicle: Vehicle, iso: string | null, labelKey: string): Planned | null {
  if (iso == null) return null;
  const when = computeWhen(iso);
  if (when == null) return null;
  const name = vehicle.plate ?? `${vehicle.make} ${vehicle.model}`;
  const body = t('notifications.body', {
    name,
    label: t(labelKey),
    days: daysUntil(iso),
    date: formatTrDate(iso),
  });
  return { whenMs: when, body };
}

/** MTV son ödeme hatırlatıcısı (araçtan bağımsız; tek sefer planlanır). */
function planMtv(iso: string): Planned | null {
  const when = computeWhen(iso);
  if (when == null) return null;
  const body = t('notifications.mtvBody', {
    days: daysUntil(iso),
    date: formatTrDate(iso),
  });
  return { whenMs: when, body };
}

/**
 * Araç listesindeki tarih hatırlatıcılarını yerel bildirimlere senkronlar.
 * İzin yoksa bir kez ister; reddedilirse sessizce çıkar.
 */
export async function syncVehicleReminders(vehicles: Vehicle[]): Promise<void> {
  if (Platform.OS === 'web') return; // web'de zamanlanmış yerel bildirim yok

  // Kullanıcı bildirimleri ayarlardan kapattıysa: planlanmışları temizle, çık.
  if (!useUstaStore.getState().remindersEnabled) {
    try {
      ensureHandler();
      await Notifications.cancelAllScheduledNotificationsAsync();
    } catch {
      /* sessiz */
    }
    return;
  }

  try {
    ensureHandler();
    const settings = await Notifications.getPermissionsAsync();
    let granted = settings.granted;
    if (!granted && settings.canAskAgain) {
      granted = (await Notifications.requestPermissionsAsync()).granted;
    }
    if (!granted) return;

    // Bu uygulamanın planladığı her şeyi temizle (mükerrer önle).
    await Notifications.cancelAllScheduledNotificationsAsync();

    const planned: Planned[] = [];
    for (const v of vehicles) {
      const a = planFor(v, v.muayene_date, 'home.dates.muayene');
      const b = planFor(v, v.sigorta_date, 'home.dates.sigorta');
      if (a) planned.push(a);
      if (b) planned.push(b);
    }
    // MTV: araçtan bağımsız tek hatırlatıcı (araç varsa).
    if (vehicles.length > 0) {
      const mtv = planMtv(nextMtvDeadline());
      if (mtv) planned.push(mtv);
    }

    for (const p of planned) {
      await Notifications.scheduleNotificationAsync({
        content: { title: t('notifications.title'), body: p.body },
        // SDK 52+ API: ham Date yerine yapısal tarih tetikleyici.
        trigger: {
          type: Notifications.SchedulableTriggerInputTypes.DATE,
          date: p.whenMs,
        },
      });
    }
  } catch {
    /* izin/scheduler hatası — bildirim kritik değil, uygulamayı bozma */
  }
}

export default syncVehicleReminders;
