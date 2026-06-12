import { create } from 'zustand';

import type { DiagnoseResult, Task, Vehicle } from '@/lib/api';

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
  selectedTask: Task | null;
  lastResult: DiagnoseResult | null;
  /** Kaldığın adım (görev id → adım index'i) — rehbere dönünce devam et. */
  guideProgress: Record<string, number>;
  setVehicles: (vehicles: Vehicle[]) => void;
  selectVehicle: (id: number | null) => void;
  setAuthBootstrapped: (done: boolean) => void;
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
  selectedTask: null,
  lastResult: null,
  guideProgress: {},
  setVehicles: (vehicles) => set({ vehicles }),
  selectVehicle: (id) => set({ currentVehicleId: id }),
  setAuthBootstrapped: (authBootstrapped) => set({ authBootstrapped }),
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
