import { useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { createApiClient, type ResolutionDurum } from '@/lib/api';
import { t } from '@/lib/i18n';
import { useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';

const OPTIONS: ResolutionDurum[] = [
  'kendim_cozdum',
  'tamirci_cozdu',
  'sorun_devam',
  'yanlis_teshis',
];

/**
 * Kapanış mini-anketi: "Bu teşhis nasıl sonuçlandı?"
 *
 * Veri toplama katmanını tamamlayan sinyal — AI tahmin doğruluğunu ölçer
 * (kendim çözdüm / tamirci çözdü / sorun devam / yanlış teşhis). Sessizce
 * gönderilir; başarısız olursa kullanıcı engellenmez.
 */
export function ResolutionRow({
  vehicleId,
  sessionId,
  initial = null,
}: {
  vehicleId: number;
  sessionId: number;
  initial?: ResolutionDurum | null;
}) {
  const authToken = useUstaStore((s) => s.authToken);
  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );
  const [chosen, setChosen] = useState<ResolutionDurum | null>(initial);
  const [sending, setSending] = useState(false);

  async function send(value: ResolutionDurum) {
    if (sending) return;
    setSending(true);
    try {
      await client.sendDiagnosisResolution(vehicleId, sessionId, value);
      setChosen(value);
    } catch {
      /* ağ hatası — sessiz */
    } finally {
      setSending(false);
    }
  }

  return (
    <View style={styles.wrap}>
      <Text style={styles.title}>
        {chosen == null ? t('resolution.title') : t('resolution.thanks')}
      </Text>
      <View style={styles.chips}>
        {OPTIONS.map((opt) => {
          const active = chosen === opt;
          return (
            <Pressable
              key={opt}
              accessibilityRole="button"
              accessibilityState={{ selected: active, disabled: sending }}
              disabled={sending}
              onPress={() => void send(opt)}
              style={({ pressed }) => [
                styles.chip,
                active && styles.chipActive,
                pressed && styles.pressed,
              ]}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>
                {t(`resolution.${opt}`)}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: theme.spacing.sm },
  title: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.xs,
  },
  chip: {
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.background,
    borderRadius: theme.radius.pill,
    paddingVertical: 5,
    paddingHorizontal: theme.spacing.md,
  },
  chipActive: {
    backgroundColor: theme.colors.ink,
    borderColor: theme.colors.ink,
  },
  chipText: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    fontWeight: '600',
    color: theme.colors.textSecondary,
  },
  chipTextActive: { color: theme.colors.onInk },
  pressed: { opacity: 0.8 },
});

export default ResolutionRow;
