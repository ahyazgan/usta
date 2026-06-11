/**
 * Hook wiring the API client + store for maintenance history.
 * Fetches reminders + logs, and exposes an `addLog` that refreshes on success.
 * Screens stay thin and just render the returned state.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  ApiError,
  createApiClient,
  type MaintenanceLog,
  type MaintenanceLogInput,
  type Reminder,
} from '@/lib/api';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';

export interface UseHistory {
  loading: boolean;
  /** i18n key describing the failure, or null when there is none. */
  error: string | null;
  reminders: Reminder[];
  logs: MaintenanceLog[];
  refresh: () => Promise<void>;
  addLog: (input: MaintenanceLogInput) => Promise<boolean>;
  submitting: boolean;
  /** i18n key for an add-log failure, or null. */
  submitError: string | null;
}

function errorKey(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 0) return 'history.error.offline';
    if (err.status === 401 || err.status === 403) return 'history.error.auth';
  }
  return 'history.error.generic';
}

export function useHistory(): UseHistory {
  const vehicle = useUstaStore(selectCurrentVehicle);
  const authToken = useUstaStore((s) => s.authToken);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [logs, setLogs] = useState<MaintenanceLog[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const refresh = useCallback(async () => {
    if (!vehicle) {
      setError('history.error.noVehicle');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [fetchedReminders, fetchedLogs] = await Promise.all([
        client.getReminders(vehicle.id),
        client.listLogs(vehicle.id),
      ]);
      setReminders(fetchedReminders);
      setLogs(fetchedLogs);
    } catch (err) {
      setError(errorKey(err));
    } finally {
      setLoading(false);
    }
  }, [client, vehicle]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const addLog = useCallback(
    async (input: MaintenanceLogInput): Promise<boolean> => {
      if (!vehicle) {
        setSubmitError('history.error.noVehicle');
        return false;
      }
      setSubmitting(true);
      setSubmitError(null);
      try {
        await client.addLog(vehicle.id, input);
        await refresh();
        return true;
      } catch (err) {
        setSubmitError(errorKey(err));
        return false;
      } finally {
        setSubmitting(false);
      }
    },
    [client, vehicle, refresh],
  );

  return {
    loading,
    error,
    reminders,
    logs,
    refresh,
    addLog,
    submitting,
    submitError,
  };
}

export default useHistory;
