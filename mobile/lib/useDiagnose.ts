/**
 * Hook that wires the API client + store together for image diagnosis.
 * Screens stay thin: they call `runImageDiagnose(photoUri)` and read state.
 */
import { useCallback, useMemo, useState } from 'react';

import { ApiError, createApiClient, type DiagnoseResult } from '@/lib/api';
import { captureAndEncode } from '@/lib/capture';
import { useUstaStore } from '@/lib/store';

export interface UseDiagnose {
  loading: boolean;
  /** i18n key describing the failure, or null when there is none. */
  error: string | null;
  result: DiagnoseResult | null;
  runImageDiagnose: (photoUri: string) => Promise<void>;
}

/** Maps a thrown error to an i18n key the screen can render via t(). */
function errorKey(err: unknown): string {
  if (err instanceof ApiError) {
    // status 0 = network/offline failure surfaced by the client.
    if (err.status === 0) return 'camera.error.offline';
    if (err.status === 401 || err.status === 403) return 'camera.error.auth';
  }
  return 'camera.error.generic';
}

export function useDiagnose(): UseDiagnose {
  const vehicle = useUstaStore((s) => s.vehicle);
  const selectedTask = useUstaStore((s) => s.selectedTask);
  const authToken = useUstaStore((s) => s.authToken);
  const lastResult = useUstaStore((s) => s.lastResult);
  const setLastResult = useUstaStore((s) => s.setLastResult);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Recreate the client when the token changes so requests stay authed.
  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const runImageDiagnose = useCallback(
    async (photoUri: string) => {
      if (!vehicle || !selectedTask) {
        setError('camera.error.noTask');
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const { base64, mediaType } = await captureAndEncode(photoUri);
        const result = await client.diagnoseImage({
          vehicle_id: vehicle.id,
          task: selectedTask.id,
          frame_base64: base64,
          media_type: mediaType,
        });
        setLastResult(result);
      } catch (err) {
        setError(errorKey(err));
      } finally {
        setLoading(false);
      }
    },
    [client, vehicle, selectedTask, setLastResult],
  );

  return { loading, error, result: lastResult, runImageDiagnose };
}

export default useDiagnose;
