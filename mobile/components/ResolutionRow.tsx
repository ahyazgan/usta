import { useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

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
  // "Tamirci çözdü" seçilince ödeme sorusu (fiyat çarkının yakıtı).
  const [askCost, setAskCost] = useState(false);
  const [cost, setCost] = useState('');

  async function send(value: ResolutionDurum, costTry?: number) {
    if (sending) return;
    setSending(true);
    try {
      await client.sendDiagnosisResolution(vehicleId, sessionId, value, costTry);
      setChosen(value);
      setAskCost(false);
    } catch {
      /* ağ hatası — sessiz */
    } finally {
      setSending(false);
    }
  }

  function onPick(opt: ResolutionDurum) {
    // Tamirci çözdüyse önce "ne ödedin?" sor; diğerleri anında gönderilir.
    if (opt === 'tamirci_cozdu') {
      setAskCost(true);
      return;
    }
    void send(opt);
  }

  function saveCost() {
    const parsed = Number(cost.trim());
    const valid = cost.trim().length > 0 && Number.isFinite(parsed) && parsed >= 0;
    void send('tamirci_cozdu', valid ? parsed : undefined);
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
              onPress={() => onPick(opt)}
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

      {askCost && (
        <View style={styles.costBox}>
          <Text style={styles.costLabel}>{t('resolution.costPrompt')}</Text>
          <View style={styles.costRow}>
            <TextInput
              style={styles.costInput}
              value={cost}
              onChangeText={setCost}
              keyboardType="number-pad"
              placeholder={t('resolution.costPlaceholder')}
              placeholderTextColor={theme.colors.textSecondary}
              editable={!sending}
            />
            <Pressable
              accessibilityRole="button"
              disabled={sending}
              onPress={saveCost}
              style={({ pressed }) => [styles.costSave, pressed && styles.pressed]}
            >
              <Text style={styles.costSaveText}>{t('resolution.costSave')}</Text>
            </Pressable>
          </View>
          <Pressable
            accessibilityRole="button"
            disabled={sending}
            onPress={() => void send('tamirci_cozdu')}
            style={styles.costSkip}
          >
            <Text style={styles.costSkipText}>{t('resolution.costSkip')}</Text>
          </Pressable>
        </View>
      )}
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
  costBox: {
    gap: theme.spacing.xs,
    backgroundColor: theme.colors.background,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    marginTop: theme.spacing.xs,
  },
  costLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    fontWeight: '600',
    color: theme.colors.textPrimary,
  },
  costRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  costInput: {
    flex: 1,
    minHeight: 44,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.surface,
    paddingHorizontal: theme.spacing.md,
    fontFamily: theme.fonts.body,
    fontSize: 15,
    color: theme.colors.textPrimary,
  },
  costSave: {
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.ink,
  },
  costSaveText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  costSkip: {
    alignSelf: 'flex-start',
    minHeight: 32,
    justifyContent: 'center',
  },
  costSkipText: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
    textDecorationLine: 'underline',
  },
  pressed: { opacity: 0.8 },
});

export default ResolutionRow;
