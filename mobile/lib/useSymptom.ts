/**
 * Hook for free-text symptom diagnosis. Screen calls `runSymptom(text)`.
 */
import { useCallback, useMemo, useState } from 'react';

import { capture } from '@/lib/analytics';
import { ApiError, createApiClient, type SymptomResult } from '@/lib/api';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';

export interface UseSymptom {
  loading: boolean;
  error: string | null;
  result: SymptomResult | null;
  runSymptom: (description: string) => Promise<void>;
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

export function useSymptom(): UseSymptom {
  const vehicle = useUstaStore(selectCurrentVehicle);
  const authToken = useUstaStore((s) => s.authToken);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SymptomResult | null>(null);

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const runSymptom = useCallback(
    async (description: string) => {
      if (!vehicle) {
        setError('camera.error.noVehicle');
        return;
      }
      const trimmed = description.trim();
      if (trimmed.length < 3) {
        setError('symptom.error.empty');
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const res = await client.diagnoseSymptom({
          vehicle_id: vehicle.id,
          description: trimmed,
        });
        setResult(res);
        void capture('diagnosis_symptom', {
          sistem: res.ariza_sistem,
          aciliyet: res.aciliyet,
        });
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

  return { loading, error, result, runSymptom, reset };
}

export default useSymptom;
