/**
 * Mağaza değerlendirme tetikleyicisi — ASO sıralamasının büyüme kaldıracı.
 *
 * Pozitif bir anda (rehber bitişi) yerel mağaza değerlendirme akışını açar.
 * Kurulum başına en çok bir kez (OS zaten kısıtlar; biz de bayrakla destekleriz),
 * web'de ve desteklenmeyen platformda no-op.
 */
import * as SecureStore from 'expo-secure-store';
import * as StoreReview from 'expo-store-review';
import { Platform } from 'react-native';

import { capture } from '@/lib/analytics';

const ASKED_KEY = 'usta.review_asked';

export async function maybeRequestReview(): Promise<void> {
  if (Platform.OS === 'web') return;
  try {
    const asked = await SecureStore.getItemAsync(ASKED_KEY).catch(() => null);
    if (asked) return;
    if (!(await StoreReview.isAvailableAsync())) return;
    if (!(await StoreReview.hasAction())) return;
    await StoreReview.requestReview();
    void capture('review_requested');
    await SecureStore.setItemAsync(ASKED_KEY, '1').catch(() => undefined);
  } catch {
    /* değerlendirme kritik değil — uygulamayı bozma */
  }
}

export default maybeRequestReview;
