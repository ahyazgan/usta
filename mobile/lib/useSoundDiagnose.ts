/**
 * Hook wiring the API client + store for engine-sound diagnosis.
 * Screens stay thin: they call `runSoundDiagnose(description, condition)`
 * and read loading / error / result.
 */
import { useCallback, useMemo, useState } from 'react';

import {
  ApiError,
  createApiClient,
  type KayitKosulu,
  type SoundDiagnoseResult,
} from '@/lib/api';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';

export interface UseSoundDiagnose {
  loading: boolean;
  /** i18n key describing the failure, or null when there is none. */
  error: string | null;
  result: SoundDiagnoseResult | null;
  runSoundDiagnose: (
    userDescription: string,
    condition: KayitKosulu,
  ) => Promise<void>;
  reset: () => void;
}

/** Maps a thrown error to an i18n key the screen can render via t(). */
function errorKey(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 0) return 'sound.error.offline';
    if (err.status === 401 || err.status === 403) return 'sound.error.auth';
    if (err.status === 503 || err.status === 502) return 'sound.error.aiUnavailable';
    if (err.status === 429) return 'sound.error.busy';
  }
  return 'sound.error.generic';
}

export function useSoundDiagnose(): UseSoundDiagnose {
  const vehicle = useUstaStore(selectCurrentVehicle);
  const authToken = useUstaStore((s) => s.authToken);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SoundDiagnoseResult | null>(null);

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const runSoundDiagnose = useCallback(
    async (userDescription: string, condition: KayitKosulu) => {
      if (!vehicle) {
        setError('sound.error.noVehicle');
        return;
      }
      if (userDescription.trim().length === 0) {
        setError('sound.error.noDescription');
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const res = await client.diagnoseSound({
          vehicle_id: vehicle.id,
          user_description: userDescription.trim(),
          condition,
        });
        setResult(res);
      } catch (err) {
        setError(errorKey(err));
      } finally {
        setLoading(false);
      }
    },
    [client, vehicle],
  );

  const reset = useCallback(() => {
    setError(null);
    setResult(null);
  }, []);

  return { loading, error, result, runSoundDiagnose, reset };
}

export default useSoundDiagnose;
