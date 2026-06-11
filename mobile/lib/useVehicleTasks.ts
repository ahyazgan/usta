/**
 * Hook fetching the maintenance tasks applicable to a given vehicle.
 * The backend filters tasks by the vehicle's fuel type (e.g. diesel has no
 * spark_plug, electric has no oil_change), so the garage only shows tasks the
 * user can actually perform on that car.
 *
 * On error it falls back to an empty list so the garage still renders. It
 * refetches whenever the vehicle id changes (e.g. after editing the fuel type).
 */
import { useCallback, useEffect, useMemo, useState } from 'react';

import { createApiClient, type Task } from '@/lib/api';
import { useUstaStore } from '@/lib/store';

export interface UseVehicleTasks {
  tasks: Task[];
  loading: boolean;
  /** i18n key describing the failure, or null when there is none. */
  error: string | null;
}

export function useVehicleTasks(vehicleId: number | null): UseVehicleTasks {
  const authToken = useUstaStore((s) => s.authToken);

  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const load = useCallback(async () => {
    if (vehicleId == null || authToken == null) {
      setTasks([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const fetched = await client.getVehicleTasks(vehicleId);
      setTasks(fetched);
    } catch {
      // Never crash the garage — fall back to an empty task list.
      setTasks([]);
      setError('vehicle.error.generic');
    } finally {
      setLoading(false);
    }
  }, [client, vehicleId, authToken]);

  useEffect(() => {
    void load();
  }, [load]);

  return { tasks, loading, error };
}

export default useVehicleTasks;
