/**
 * Hafif davranış analitiği (PostHog HTTP capture API).
 *
 * Native SDK YOK — doğrudan PostHog'un /capture/ ucuna fetch atar; böylece
 * web + native aynı, bundle riski yok, ne gönderildiği tam kontrolümüzde.
 *
 * KVKK: yalnızca kullanıcı **analitik rızası** verdiyse ve bir PostHog anahtarı
 * tanımlıysa olay gönderilir. Kimlik anonimdir (kişi/araç değil, rastgele
 * kurulum kimliği). Rıza yoksa tüm çağrılar no-op.
 */
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

import { useUstaStore } from '@/lib/store';

const KEY = process.env.EXPO_PUBLIC_POSTHOG_KEY ?? '';
const HOST = process.env.EXPO_PUBLIC_POSTHOG_HOST ?? 'https://eu.i.posthog.com';
const DISTINCT_STORE_KEY = 'usta.analytics_id';

let distinctId: string | null = null;

/** Anonim, kurulum-bazlı dağıtık kimlik (kişi değil). */
async function getDistinctId(): Promise<string> {
  if (distinctId != null) return distinctId;
  try {
    const existing = await SecureStore.getItemAsync(DISTINCT_STORE_KEY);
    if (existing) {
      distinctId = existing;
      return existing;
    }
  } catch {
    /* web/secure-store yok — oturum-bazlı kimliğe düş */
  }
  const fresh = `anon-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
  distinctId = fresh;
  try {
    await SecureStore.setItemAsync(DISTINCT_STORE_KEY, fresh);
  } catch {
    /* kalıcılık yoksa sorun değil */
  }
  return fresh;
}

function enabled(): boolean {
  return KEY.length > 0 && useUstaStore.getState().analyticsConsent === true;
}

/** Bir olayı yakala (rıza yoksa / anahtar yoksa no-op). */
export async function capture(
  event: string,
  properties?: Record<string, unknown>,
): Promise<void> {
  if (!enabled()) return;
  try {
    const id = await getDistinctId();
    await fetch(`${HOST}/capture/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: KEY,
        event,
        distinct_id: id,
        properties: { platform: Platform.OS, ...properties },
      }),
    });
  } catch {
    /* analitik kritik değil — uygulamayı asla bozma */
  }
}

/** Ekran görüntüleme olayı. */
export function screen(name: string): void {
  void capture('screen_view', { screen: name });
}

export default capture;
