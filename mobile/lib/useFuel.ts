/**
 * Hook for fuel tracking: loads the fill-up list + summary, and adds entries.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';

import { capture } from '@/lib/analytics';
import {
  ApiError,
  createApiClient,
  type FuelLog,
  type FuelLogInput,
  type FuelSummary,
} from '@/lib/api';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';

export interface UseFuel {
  loading: boolean;
  submitting: boolean;
  error: string | null;
  logs: FuelLog[];
  summary: FuelSummary | null;
  addEntry: (input: FuelLogInput) => Promise<boolean>;
}

function errorKey(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 0) return 'camera.error.offline';
    if (err.status === 401 || err.status === 403) return 'camera.error.auth';
    if (err.status === 422) return 'fuel.error.invalid';
  }
  return 'camera.error.generic';
}

export function useFuel(): UseFuel {
  const vehicle = useUstaStore(selectCurrentVehicle);
  const authToken = useUstaStore((s) => s.authToken);
  const client = useMemo(() => createApiClient(undefined, () => authToken), [authToken]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<FuelLog[]>([]);
  const [summary, setSummary] = useState<FuelSummary | null>(null);

  const load = useCallback(async () => {
    if (!vehicle) {
      setLogs([]);
      setSummary(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [l, s] = await Promise.all([
        client.listFuelLogs(vehicle.id),
        client.getFuelSummary(vehicle.id),
      ]);
      setLogs(l);
      setSummary(s);
      setError(null);
    } catch (err) {
      setError(errorKey(err));
    } finally {
      setLoading(false);
    }
  }, [client, vehicle]);

  useEffect(() => {
    void load();
  }, [load]);

  const addEntry = useCallback(
    async (input: FuelLogInput): Promise<boolean> => {
      if (!vehicle || submitting) return false;
      setSubmitting(true);
      setError(null);
      try {
        await client.addFuelLog(vehicle.id, input);
        void capture('fuel_add', { full: input.full_tank !== false });
        await load();
        return true;
      } catch (err) {
        setError(errorKey(err));
        return false;
      } finally {
        setSubmitting(false);
      }
    },
    [client, vehicle, submitting, load],
  );

  return { loading, submitting, error, logs, summary, addEntry };
}

export default useFuel;
