/**
 * Hook for OBD-II fault-code (DTC) explanation. Text input (no camera).
 * Screen calls `runDtc(code, note?)` and reads state.
 */
import { useCallback, useMemo, useState } from 'react';

import { capture } from '@/lib/analytics';
import { ApiError, createApiClient, type DtcResult } from '@/lib/api';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';

export interface UseDtc {
  loading: boolean;
  error: string | null;
  result: DtcResult | null;
  runDtc: (code: string, note?: string) => Promise<void>;
  reset: () => void;
}

function errorKey(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 0) return 'camera.error.offline';
    if (err.status === 401 || err.status === 403) return 'camera.error.auth';
    if (err.status === 503 || err.status === 502) return 'camera.error.aiUnavailable';
    if (err.status === 429) return 'camera.error.busy';
  }
  return 'camera.error.generic';
}

export function useDtc(): UseDtc {
  const vehicle = useUstaStore(selectCurrentVehicle);
  const authToken = useUstaStore((s) => s.authToken);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DtcResult | null>(null);

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const runDtc = useCallback(
    async (code: string, note?: string) => {
      if (!vehicle) {
        setError('camera.error.noVehicle');
        return;
      }
      const trimmed = code.trim();
      if (trimmed.length < 2) {
        setError('dtc.error.empty');
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const res = await client.diagnoseDtc({
          vehicle_id: vehicle.id,
          code: trimmed,
          user_note: note?.trim() ? note.trim() : undefined,
        });
        setResult(res);
        void capture('diagnosis_dtc', { aciliyet: res.aciliyet, guven: res.guven });
      } catch (err) {
        setError(errorKey(err));
      } finally {
        setLoading(false);
      }
    },
    [client, vehicle],
  );

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { loading, error, result, runDtc, reset };
}

export default useDtc;
