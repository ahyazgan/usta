import { create } from 'zustand';

import type { DiagnoseResult, Task } from '@/lib/api';

export type FuelType = 'dizel' | 'benzin' | 'lpg' | 'elektrik' | 'hibrit';

export interface Vehicle {
  id: number;
  make: string;
  model: string;
  year: number;
  engine: string;
  engine_code: string;
  fuel: FuelType;
  current_km: number;
}

export type ChipState = 'ok' | 'due' | 'soon';

export interface MaintenanceStatus {
  oil: ChipState;
  filter: ChipState;
  battery: ChipState;
}

export interface UstaState {
  vehicle: Vehicle | null;
  maintenance: MaintenanceStatus;
  authToken: string | null;
  refreshToken: string | null;
  selectedTask: Task | null;
  lastResult: DiagnoseResult | null;
  setVehicle: (vehicle: Vehicle | null) => void;
  setMaintenance: (status: Partial<MaintenanceStatus>) => void;
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

const demoVehicle: Vehicle = {
  id: 1,
  make: 'Renault',
  model: 'Clio',
  year: 2019,
  engine: '1.5 dCi',
  engine_code: 'K9K',
  fuel: 'dizel',
  current_km: 138420,
};

const demoMaintenance: MaintenanceStatus = {
  oil: 'due',
  filter: 'soon',
  battery: 'ok',
};

export const useUstaStore = create<UstaState>((set) => ({
  vehicle: demoVehicle,
  maintenance: demoMaintenance,
  authToken: null,
  refreshToken: null,
  selectedTask: null,
  lastResult: null,
  setVehicle: (vehicle) => set({ vehicle }),
  setMaintenance: (status) =>
    set((state) => ({ maintenance: { ...state.maintenance, ...status } })),
  setAuthToken: (authToken) => set({ authToken }),
  setRefreshToken: (refreshToken) => set({ refreshToken }),
  setTokens: (tokens) =>
    set(
      tokens
        ? { authToken: tokens.access, refreshToken: tokens.refresh }
        : { authToken: null, refreshToken: null },
    ),
  setSelectedTask: (selectedTask) => set({ selectedTask }),
  setLastResult: (lastResult) => set({ lastResult }),
}));

export default useUstaStore;
