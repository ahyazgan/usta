import { create } from 'zustand';

export type FuelType = 'dizel' | 'benzin' | 'lpg' | 'elektrik' | 'hibrit';

export interface Vehicle {
  id: string;
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
  setVehicle: (vehicle: Vehicle | null) => void;
  setMaintenance: (status: Partial<MaintenanceStatus>) => void;
  setAuthToken: (token: string | null) => void;
}

const demoVehicle: Vehicle = {
  id: 'veh-demo-1',
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
  setVehicle: (vehicle) => set({ vehicle }),
  setMaintenance: (status) =>
    set((state) => ({ maintenance: { ...state.maintenance, ...status } })),
  setAuthToken: (authToken) => set({ authToken }),
}));

export default useUstaStore;
