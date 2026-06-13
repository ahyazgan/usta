/**
 * Cihaz-üstü kullanıcı tercihleri (dil, bildirim) — secure-store ile kalıcı.
 * Sır değil ama uygulamanın tek kalıcılık deposu secure-store olduğu için onu
 * kullanır. Web'de secure-store yoksa sessizce no-op (bellek-içi davranış).
 */
import * as SecureStore from 'expo-secure-store';

const LOCALE_KEY = 'usta.locale';
const REMINDERS_KEY = 'usta.reminders_enabled';

export type AppLocale = 'tr' | 'en';

export interface Prefs {
  locale: AppLocale | null;
  remindersEnabled: boolean;
}

/** Kayıtlı tercihleri yükle (yoksa null/varsayılan). */
export async function loadPrefs(): Promise<Prefs> {
  try {
    const [locale, reminders] = await Promise.all([
      SecureStore.getItemAsync(LOCALE_KEY),
      SecureStore.getItemAsync(REMINDERS_KEY),
    ]);
    return {
      locale: locale === 'tr' || locale === 'en' ? locale : null,
      // Varsayılan açık; yalnızca açıkça "false" kaydedildiyse kapalı.
      remindersEnabled: reminders !== 'false',
    };
  } catch {
    return { locale: null, remindersEnabled: true };
  }
}

export async function saveLocale(locale: AppLocale): Promise<void> {
  try {
    await SecureStore.setItemAsync(LOCALE_KEY, locale);
  } catch {
    /* web / secure-store yok */
  }
}

export async function saveRemindersEnabled(enabled: boolean): Promise<void> {
  try {
    await SecureStore.setItemAsync(REMINDERS_KEY, enabled ? 'true' : 'false');
  } catch {
    /* web / secure-store yok */
  }
}
