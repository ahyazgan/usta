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
import { useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';

export default function RootLayout() {
  const setTokens = useUstaStore((s) => s.setTokens);
  const setAuthBootstrapped = useUstaStore((s) => s.setAuthBootstrapped);
  const setAnalyticsConsent = useUstaStore((s) => s.setAnalyticsConsent);

  // On launch: reuse a persisted session if any, otherwise auto-login a demo
  // account (login screen removed). `authBootstrapped` flips true either way so
  // screens can show a spinner instead of the login gate during this window.
  useEffect(() => {
    let active = true;
    (async () => {
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
          await ensureDemoSession(setTokens);
        } catch {
          /* ağ hatası — kullanıcı tekrar deneyebilir */
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
  }, [setTokens, setAuthBootstrapped, setAnalyticsConsent]);

  return (
    <SafeAreaProvider>
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
      </Stack>
    </SafeAreaProvider>
  );
}
