/**
 * Hook wiring the API client + store for the user's vehicles.
 * Fetches the vehicle list on mount, auto-selects the first one, and exposes
 * `addVehicle` which creates then selects the new vehicle. Screens stay thin.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  ApiError,
  createApiClient,
  type Vehicle,
  type VehicleCreateInput,
} from '@/lib/api';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';

export interface UseVehicles {
  vehicles: Vehicle[];
  currentVehicle: Vehicle | null;
  loading: boolean;
  /** i18n key describing the failure, or null when there is none. */
  error: string | null;
  refresh: () => Promise<Vehicle[]>;
  addVehicle: (input: VehicleCreateInput) => Promise<boolean>;
  selectVehicle: (id: number) => void;
}

/** Maps a thrown error to an i18n key the screen can render via t(). */
function errorKey(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 0) return 'vehicle.error.network';
    if (err.status === 401 || err.status === 403) return 'vehicle.error.auth';
  }
  return 'vehicle.error.generic';
}

export function useVehicles(): UseVehicles {
  const authToken = useUstaStore((s) => s.authToken);
  const vehicles = useUstaStore((s) => s.vehicles);
  const currentVehicleId = useUstaStore((s) => s.currentVehicleId);
  const currentVehicle = useUstaStore(selectCurrentVehicle);
  const setVehicles = useUstaStore((s) => s.setVehicles);
  const selectVehicle = useUstaStore((s) => s.selectVehicle);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const refresh = useCallback(async (): Promise<Vehicle[]> => {
    if (authToken == null) {
      setLoading(false);
      return [];
    }
    setLoading(true);
    setError(null);
    try {
      const fetched = await client.listVehicles();
      setVehicles(fetched);
      // Auto-select the first vehicle when none is active yet.
      if (currentVehicleId == null && fetched.length > 0) {
        selectVehicle(fetched[0].id);
      }
      return fetched;
    } catch (err) {
      setError(errorKey(err));
      return [];
    } finally {
      setLoading(false);
    }
  }, [client, authToken, currentVehicleId, setVehicles, selectVehicle]);

  useEffect(() => {
    void refresh();
    // Re-fetch whenever the auth token changes (login / hydrate).
  }, [authToken]); // eslint-disable-line react-hooks/exhaustive-deps

  const addVehicle = useCallback(
    async (input: VehicleCreateInput): Promise<boolean> => {
      setError(null);
      try {
        const created = await client.createVehicle(input);
        await refresh();
        selectVehicle(created.id);
        return true;
      } catch (err) {
        setError(errorKey(err));
        return false;
      }
    },
    [client, refresh, selectVehicle],
  );

  return {
    vehicles,
    currentVehicle,
    loading,
    error,
    refresh,
    addVehicle,
    selectVehicle,
  };
}

export default useVehicles;
