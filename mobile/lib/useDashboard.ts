/**
 * Hook for dashboard warning-light identification.
 * Screen stays thin: calls `runDashboard(photoUri)` and reads state.
 * Mirrors useDiagnose but task-independent (no guide/step context).
 */
import { useCallback, useMemo, useState } from 'react';

import { capture } from '@/lib/analytics';
import { ApiError, createApiClient, type DashboardResult } from '@/lib/api';
import { captureAndEncode } from '@/lib/capture';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';

export interface UseDashboard {
  loading: boolean;
  /** i18n key describing the failure, or null when there is none. */
  error: string | null;
  result: DashboardResult | null;
  runDashboard: (photoUri: string) => Promise<void>;
  reset: () => void;
}

/** Maps a thrown error to an i18n key the screen can render via t(). */
function errorKey(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 0) return 'camera.error.offline';
    if (err.status === 401 || err.status === 403) return 'camera.error.auth';
    if (err.status === 503 || err.status === 502) return 'camera.error.aiUnavailable';
    if (err.status === 429) return 'camera.error.busy';
  }
  return 'camera.error.generic';
}

export function useDashboard(): UseDashboard {
  const vehicle = useUstaStore(selectCurrentVehicle);
  const authToken = useUstaStore((s) => s.authToken);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DashboardResult | null>(null);

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const runDashboard = useCallback(
    async (photoUri: string) => {
      if (!vehicle) {
        setError('camera.error.noVehicle');
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const { base64, mediaType } = await captureAndEncode(photoUri);
        const res = await client.diagnoseDashboard({
          vehicle_id: vehicle.id,
          frame_base64: base64,
          media_type: mediaType,
        });
        setResult(res);
        void capture('diagnosis_dashboard', {
          guven: res.guven,
          aciliyet: res.en_yuksek_aciliyet,
          isik: res.isiklar.length,
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

  return { loading, error, result, runDashboard, reset };
}

export default useDashboard;
