/**
 * Ana sayfa özeti: kayıtlı bakım sayısı + tahmini DIY tasarrufu (TL).
 * Backend `/v1/vehicles/{id}/summary` ucundan gerçek loglardan türetilir.
 * Hata durumunda sıfır döner; ana sayfa asla çökmesin.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';

import { createApiClient, type VehicleSummary } from '@/lib/api';
import { useUstaStore } from '@/lib/store';

const ZERO: VehicleSummary = { maintenance_count: 0, savings_try: 0 };

export function useSummary(vehicleId: number | null): VehicleSummary {
  const authToken = useUstaStore((s) => s.authToken);
  const [summary, setSummary] = useState<VehicleSummary>(ZERO);

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const load = useCallback(async () => {
    if (vehicleId == null) {
      setSummary(ZERO);
      return;
    }
    try {
      setSummary(await client.getSummary(vehicleId));
    } catch {
      setSummary(ZERO);
    }
  }, [client, vehicleId]);

  useEffect(() => {
    void load();
  }, [load]);

  return summary;
}

export default useSummary;
