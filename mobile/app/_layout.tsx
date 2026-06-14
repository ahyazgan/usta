import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { capture } from '@/lib/analytics';
import { createApiClient } from '@/lib/api';
import { loadTokens } from '@/lib/auth';
import { ensureDemoSession } from '@/lib/demoSession';
// Side-effect import: initializes i18n locale before any screen renders.
import '@/lib/i18n';
import { loadPrefs } from '@/lib/prefs';
import { useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';

export default function RootLayout() {
  const setTokens = useUstaStore((s) => s.setTokens);
  const setAuthBootstrapped = useUstaStore((s) => s.setAuthBootstrapped);
  const setAnalyticsConsent = useUstaStore((s) => s.setAnalyticsConsent);
  const hydrateLocale = useUstaStore((s) => s.hydrateLocale);
  const setRemindersEnabled = useUstaStore((s) => s.setRemindersEnabled);
  // Dil değişince tüm ağaç bu key ile yeniden monte olur → metinler güncellenir.
  const locale = useUstaStore((s) => s.locale);

  // On launch: reuse a persisted session if any, otherwise auto-login a demo
  // account (login screen removed). `authBootstrapped` flips true either way so
  // screens can show a spinner instead of the login gate during this window.
  useEffect(() => {
    let active = true;
    (async () => {
      // Kullanıcı tercihlerini (dil/bildirim) ekranlardan önce uygula.
      try {
        const prefs = await loadPrefs();
        if (active) {
          if (prefs.locale) hydrateLocale(prefs.locale);
          setRemindersEnabled(prefs.remindersEnabled);
        }
      } catch {
        /* tercih okunamadı — varsayılanlar kalır */
      }

      let tokens = null;
      try {
        tokens = await loadTokens();
      } catch {
        /* secure-store yok (web) — demo girişine düş */
      }
      if (tokens) {
        if (active) {
          setTokens({ access: tokens.access_token, refresh: tokens.refresh_token });
        }
      } else {
        try {
          // Üst zaman sınırı: cold-start'ta login+register zinciri çok
          // uzayabilir; bootstrap'ı kilitleme. Süre dolarsa retry ekranı
          // gösterilir (arka plandaki istek dönerse oturum yine açılır).
          await Promise.race([
            ensureDemoSession(setTokens),
            new Promise((_, reject) =>
              setTimeout(() => reject(new Error('bootstrap timeout')), 65_000),
            ),
          ]);
        } catch {
          /* ağ hatası / zaman aşımı — kullanıcı tekrar deneyebilir */
        }
      }
      if (active) setAuthBootstrapped(true);

      // KVKK rızasını senkronla (analytics bunu okur) ve oturum açılışını yakala.
      const token = useUstaStore.getState().authToken;
      if (token != null) {
        try {
          const consent = await createApiClient(undefined, () => token).getConsent();
          if (active) setAnalyticsConsent(consent.analytics);
        } catch {
          /* sessiz — rıza varsayılan kapalı kalır */
        }
        void capture('app_open');
      }
    })();
    return () => {
      active = false;
    };
  }, [setTokens, setAuthBootstrapped, setAnalyticsConsent, hydrateLocale, setRemindersEnabled]);

  return (
    <SafeAreaProvider key={locale}>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: theme.colors.surface },
          headerTintColor: theme.colors.textPrimary,
          headerTitleStyle: { color: theme.colors.textPrimary },
          contentStyle: { backgroundColor: theme.colors.background },
          headerShown: false,
        }}
      >
        <Stack.Screen name="index" />
        <Stack.Screen name="maintenance" />
        <Stack.Screen name="guide" />
        <Stack.Screen name="camera" />
        <Stack.Screen name="login" />
        <Stack.Screen name="sound" />
        <Stack.Screen name="history" />
        <Stack.Screen name="vehicle-new" />
        <Stack.Screen name="privacy" />
        <Stack.Screen name="mechanics" />
      </Stack>
    </SafeAreaProvider>
  );
}
