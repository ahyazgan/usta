import { I18n } from 'i18n-js';
import { getLocales } from 'expo-localization';

import en from '@/locales/en.json';
import tr from '@/locales/tr.json';

export const i18n = new I18n({
  tr,
  en,
});

// Fall back to Turkish for anything missing — primary market is TR.
i18n.defaultLocale = 'tr';
i18n.enableFallback = true;

const deviceLocale = getLocales()[0]?.languageCode ?? 'tr';
i18n.locale = deviceLocale === 'en' ? 'en' : 'tr';

/** Cihazın varsayılan dili (kullanıcı tercihi yoksa). */
export const deviceDefaultLocale: 'tr' | 'en' = deviceLocale === 'en' ? 'en' : 'tr';

/** Aktif dili değiştir (ayarlardan). Re-render için store + key-remount kullanılır. */
export function applyLocale(locale: 'tr' | 'en'): void {
  i18n.locale = locale;
}

export type TranslateOptions = Record<string, unknown>;

export function t(key: string, opts?: TranslateOptions): string {
  return i18n.t(key, opts);
}

export default i18n;
