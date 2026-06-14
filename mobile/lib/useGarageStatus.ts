/**
 * Hook deriving the three garage status chips from real backend reminders.
 * - oil     ← reminder for task `oil_change`
 * - filter  ← reminder for task `cabin_filter`
 * - battery ← has no km interval, so it is always neutral/unknown.
 * On error it falls back to neutral chips so the garage never crashes.
 *
 * NOTE: green (theme.colors.success) is reserved for camera verification only,
 * so chip states never map to green — see the garage screen's chipColor().
 */
import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  createApiClient,
  type Reminder,
  type ReminderStatus,
} from '@/lib/api';
import { useUstaStore } from '@/lib/store';

/** Chip state including a neutral fallback (never green). */
export type GarageChipState = ReminderStatus;

export interface GarageChips {
  oil: GarageChipState;
  filter: GarageChipState;
  battery: GarageChipState;
}

export interface UseGarageStatus {
  chips: GarageChips;
  /** Tüm km-bazlı hatırlatıcılar (ana sayfa "Yapılacaklar" listesi için). */
  reminders: Reminder[];
  loading: boolean;
}

const NEUTRAL_CHIPS: GarageChips = {
  oil: 'unknown',
  filter: 'unknown',
  battery: 'unknown',
};

/** Map a reminder status to a chip state (identity, but explicit + safe). */
function toChipState(status: ReminderStatus | undefined): GarageChipState {
  if (status === 'due') return 'due';
  if (status === 'soon') return 'soon';
  if (status === 'ok') return 'ok';
  return 'unknown';
}

function findStatus(reminders: Reminder[], task: string): ReminderStatus | undefined {
  return reminders.find((r) => r.task === task)?.status;
}

export function useGarageStatus(vehicleId: number | null): UseGarageStatus {
  const authToken = useUstaStore((s) => s.authToken);

  const [chips, setChips] = useState<GarageChips>(NEUTRAL_CHIPS);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(false);

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const load = useCallback(async () => {
    if (vehicleId == null) {
      setChips(NEUTRAL_CHIPS);
      setReminders([]);
      return;
    }
    setLoading(true);
    try {
      const fetched = await client.getReminders(vehicleId);
      setReminders(fetched);
      setChips({
        oil: toChipState(findStatus(fetched, 'oil_change')),
        filter: toChipState(findStatus(fetched, 'cabin_filter')),
        // Battery has no km interval — always neutral.
        battery: 'unknown',
      });
    } catch {
      // Never crash the garage — fall back to neutral chips.
      setChips(NEUTRAL_CHIPS);
      setReminders([]);
    } finally {
      setLoading(false);
    }
  }, [client, vehicleId]);

  useEffect(() => {
    void load();
  }, [load]);

  return { chips, reminders, loading };
}

export default useGarageStatus;
