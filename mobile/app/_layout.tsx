import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { loadTokens } from '@/lib/auth';
// Side-effect import: initializes i18n locale before any screen renders.
import '@/lib/i18n';
import { useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';

export default function RootLayout() {
  const setTokens = useUstaStore((s) => s.setTokens);

  // Rehydrate persisted tokens on mount so a logged-in user stays logged in.
  useEffect(() => {
    let active = true;
    loadTokens()
      .then((tokens) => {
        if (active && tokens) {
          setTokens({
            access: tokens.access_token,
            refresh: tokens.refresh_token,
          });
        }
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [setTokens]);

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
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
        <Stack.Screen name="camera" />
        <Stack.Screen name="login" />
        <Stack.Screen name="sound" />
        <Stack.Screen name="history" />
      </Stack>
    </SafeAreaProvider>
  );
}
