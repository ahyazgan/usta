import { create } from 'zustand';

import type { DiagnoseResult, Task, Vehicle } from '@/lib/api';
import { applyLocale, deviceDefaultLocale } from '@/lib/i18n';
import { type AppLocale, saveLocale, saveRemindersEnabled } from '@/lib/prefs';

// Re-export the canonical types so existing imports keep working. The backend
// `Vehicle` shape in lib/api is the single source of truth.
export type { FuelType, Vehicle } from '@/lib/api';

export type ChipState = 'ok' | 'due' | 'soon';

export interface UstaState {
  /** All vehicles owned by the logged-in user. */
  vehicles: Vehicle[];
  /** Id of the active vehicle, or null when none is selected. */
  currentVehicleId: number | null;
  authToken: string | null;
  refreshToken: string | null;
  /** False until the initial token hydrate / auto-login attempt finishes. */
  authBootstrapped: boolean;
  /** KVKK analitik rızası (backend'den senkronlanır; analytics bunu okur). */
  analyticsConsent: boolean;
  /** Aktif uygulama dili (kullanıcı tercihi; key-remount bunu izler). */
  locale: AppLocale;
  /** Yerel bakım/tarih bildirimleri açık mı (ayarlardan). */
  remindersEnabled: boolean;
  selectedTask: Task | null;
  lastResult: DiagnoseResult | null;
  /** Kaldığın adım (görev id → adım index'i) — rehbere dönünce devam et. */
  guideProgress: Record<string, number>;
  setVehicles: (vehicles: Vehicle[]) => void;
  selectVehicle: (id: number | null) => void;
  setAuthBootstrapped: (done: boolean) => void;
  setAnalyticsConsent: (granted: boolean) => void;
  /** Dili değiştir: i18n + store + kalıcılık. (Re-render için key-remount.) */
  setLocale: (locale: AppLocale) => void;
  /** Hidrasyon: kalıcılıktan okunan dili kalıcılığa tekrar yazmadan uygula. */
  hydrateLocale: (locale: AppLocale) => void;
  setRemindersEnabled: (enabled: boolean) => void;
  setGuideProgress: (taskId: string, step: number) => void;
  clearGuideProgress: (taskId: string) => void;
  setAuthToken: (token: string | null) => void;
  setRefreshToken: (token: string | null) => void;
  /** Set both tokens at once (login/hydrate) or clear both (logout). */
  setTokens: (tokens: { access: string; refresh: string } | null) => void;
  setSelectedTask: (task: Task | null) => void;
  setLastResult: (result: DiagnoseResult | null) => void;
}

/** True when an access token is present. */
export function selectIsAuthenticated(state: UstaState): boolean {
  return state.authToken != null;
}

/** The active vehicle (by id), falling back to the first one, or null. */
export function selectCurrentVehicle(state: UstaState): Vehicle | null {
  if (state.vehicles.length === 0) return null;
  if (state.currentVehicleId != null) {
    const match = state.vehicles.find((v) => v.id === state.currentVehicleId);
    if (match) return match;
  }
  return state.vehicles[0] ?? null;
}

export const useUstaStore = create<UstaState>((set) => ({
  vehicles: [],
  currentVehicleId: null,
  authToken: null,
  refreshToken: null,
  authBootstrapped: false,
  analyticsConsent: false,
  locale: deviceDefaultLocale,
  remindersEnabled: true,
  selectedTask: null,
  lastResult: null,
  guideProgress: {},
  setVehicles: (vehicles) => set({ vehicles }),
  selectVehicle: (id) => set({ currentVehicleId: id }),
  setAuthBootstrapped: (authBootstrapped) => set({ authBootstrapped }),
  setAnalyticsConsent: (analyticsConsent) => set({ analyticsConsent }),
  setLocale: (locale) => {
    applyLocale(locale);
    void saveLocale(locale);
    set({ locale });
  },
  hydrateLocale: (locale) => {
    applyLocale(locale);
    set({ locale });
  },
  setRemindersEnabled: (remindersEnabled) => {
    void saveRemindersEnabled(remindersEnabled);
    set({ remindersEnabled });
  },
  setGuideProgress: (taskId, step) =>
    set((s) => ({ guideProgress: { ...s.guideProgress, [taskId]: step } })),
  clearGuideProgress: (taskId) =>
    set((s) => {
      const { [taskId]: _removed, ...rest } = s.guideProgress;
      return { guideProgress: rest };
    }),
  setAuthToken: (authToken) => set({ authToken }),
  setRefreshToken: (refreshToken) => set({ refreshToken }),
  setTokens: (tokens) =>
    set(
      tokens
        ? { authToken: tokens.access, refreshToken: tokens.refresh }
        : {
            authToken: null,
            refreshToken: null,
            // Clear vehicle state on logout so the next user starts clean.
            vehicles: [],
            currentVehicleId: null,
          },
    ),
  // Görev değişince eski kamera sonucu geçersizdir — bayat teşhis↔log
  // bağlantısını önlemek için birlikte temizlenir.
  setSelectedTask: (selectedTask) => set({ selectedTask, lastResult: null }),
  setLastResult: (lastResult) => set({ lastResult }),
}));

export default useUstaStore;
