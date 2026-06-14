import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import type { FuelLog } from '@/lib/api';
import { i18n, t } from '@/lib/i18n';
import { goBack } from '@/lib/nav';
import { theme } from '@/lib/theme';
import { useFuel } from '@/lib/useFuel';

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(i18n.locale === 'en' ? 'en-US' : 'tr-TR');
}

function Stat({ value, label, accent }: { value: string; label: string; accent?: boolean }) {
  return (
    <View style={styles.stat}>
      <Text style={[styles.statValue, accent && styles.statValueAccent]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function FuelRow({ log }: { log: FuelLog }) {
  return (
    <View style={styles.logRow}>
      <View style={styles.logIcon}>
        <Ionicons
          name={log.full_tank ? 'water' : 'water-outline'}
          size={16}
          color={theme.colors.textSecondary}
        />
      </View>
      <View style={styles.logBody}>
        <Text style={styles.logMain}>
          {t('fuel.row.liters', { liters: log.liters.toLocaleString('tr-TR') })}
          {log.total_try != null ? ` · ₺${log.total_try.toLocaleString('tr-TR')}` : ''}
        </Text>
        <Text style={styles.logMeta}>
          {t('fuel.row.km', { km: log.odometer_km.toLocaleString('tr-TR') })} · {formatDate(log.created_at)}
        </Text>
      </View>
    </View>
  );
}

export default function FuelScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { loading, submitting, error, logs, summary, addEntry } = useFuel();

  const [odometer, setOdometer] = useState('');
  const [liters, setLiters] = useState('');
  const [total, setTotal] = useState('');
  const [fullTank, setFullTank] = useState(true);

  const canSubmit =
    Number(odometer.trim()) > 0 && Number(liters.trim()) > 0 && !submitting;

  async function handleAdd() {
    if (!canSubmit) return;
    const ok = await addEntry({
      odometer_km: Math.round(Number(odometer.trim())),
      liters: Number(liters.trim()),
      total_try: total.trim() ? Math.round(Number(total.trim())) : undefined,
      full_tank: fullTank,
    });
    if (ok) {
      setOdometer('');
      setLiters('');
      setTotal('');
      setFullTank(true);
    }
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      <View style={styles.header}>
        <Pressable
          accessibilityRole="button"
          onPress={() => goBack(router)}
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Ionicons name="chevron-back" size={22} color={theme.colors.textPrimary} />
          <Text style={styles.backText}>{t('common.back')}</Text>
        </Pressable>
        <Text style={styles.title}>{t('fuel.title')}</Text>
        <View style={styles.backSpacer} />
      </View>

      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* İstatistik */}
        <View style={styles.statsCard}>
          <Stat
            value={
              summary?.avg_consumption != null
                ? t('fuel.consumptionValue', { value: summary.avg_consumption })
                : '—'
            }
            label={t('fuel.avgConsumption')}
            accent
          />
          <View style={styles.statDivider} />
          <Stat
            value={summary != null ? `₺${summary.total_spent_try.toLocaleString('tr-TR')}` : '—'}
            label={t('fuel.totalSpent')}
          />
          <View style={styles.statDivider} />
          <Stat value={summary != null ? String(summary.entry_count) : '—'} label={t('fuel.entries')} />
        </View>
        {summary?.avg_consumption == null && !loading && (
          <Text style={styles.hint}>{t('fuel.consumptionHint')}</Text>
        )}

        {/* Dolum ekle */}
        <Text style={styles.sectionTitle}>{t('fuel.addTitle')}</Text>
        <View style={styles.card}>
          <View style={styles.fieldRow}>
            <View style={styles.field}>
              <Text style={styles.label}>{t('fuel.odometer')}</Text>
              <TextInput
                style={styles.input}
                value={odometer}
                onChangeText={setOdometer}
                placeholder={t('fuel.odometerPlaceholder')}
                placeholderTextColor={theme.colors.textSecondary}
                keyboardType="number-pad"
              />
            </View>
            <View style={styles.field}>
              <Text style={styles.label}>{t('fuel.liters')}</Text>
              <TextInput
                style={styles.input}
                value={liters}
                onChangeText={setLiters}
                placeholder={t('fuel.litersPlaceholder')}
                placeholderTextColor={theme.colors.textSecondary}
                keyboardType="decimal-pad"
              />
            </View>
          </View>
          <Text style={styles.label}>{t('fuel.total')}</Text>
          <TextInput
            style={styles.input}
            value={total}
            onChangeText={setTotal}
            placeholder={t('fuel.totalPlaceholder')}
            placeholderTextColor={theme.colors.textSecondary}
            keyboardType="number-pad"
          />
          <View style={styles.switchRow}>
            <View style={styles.switchBody}>
              <Text style={styles.switchLabel}>{t('fuel.fullTank')}</Text>
              <Text style={styles.switchDesc}>{t('fuel.fullTankDesc')}</Text>
            </View>
            <Switch
              value={fullTank}
              onValueChange={setFullTank}
              trackColor={{ true: theme.colors.ink, false: theme.colors.border }}
              thumbColor={theme.colors.surface}
            />
          </View>
          {error != null && <Text style={styles.errorText}>{t(error)}</Text>}
          <Pressable
            accessibilityRole="button"
            accessibilityState={{ disabled: !canSubmit }}
            disabled={!canSubmit}
            onPress={() => void handleAdd()}
            style={({ pressed }) => [styles.submit, !canSubmit && styles.disabled, pressed && styles.pressed]}
          >
            {submitting ? (
              <ActivityIndicator color={theme.colors.onInk} />
            ) : (
              <Text style={styles.submitText}>{t('fuel.add')}</Text>
            )}
          </Pressable>
        </View>

        {/* Geçmiş */}
        <Text style={styles.sectionTitle}>{t('fuel.historyTitle')}</Text>
        {loading ? (
          <ActivityIndicator color={theme.colors.ink} style={{ marginTop: theme.spacing.lg }} />
        ) : logs.length === 0 ? (
          <View style={styles.empty}>
            <Ionicons name="water-outline" size={28} color={theme.colors.textSecondary} />
            <Text style={styles.emptyText}>{t('fuel.empty')}</Text>
          </View>
        ) : (
          <View style={styles.card}>
            {logs.map((log) => (
              <FuelRow key={log.id} log={log} />
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.sm,
  },
  back: { flexDirection: 'row', alignItems: 'center', minHeight: 40, minWidth: 72 },
  backText: { fontFamily: theme.fonts.body, fontSize: 14, fontWeight: '600', color: theme.colors.textPrimary },
  backSpacer: { minWidth: 72 },
  title: { fontFamily: theme.fonts.heading, fontSize: 18, fontWeight: '700', color: theme.colors.textPrimary },
  scroll: { paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.md, paddingBottom: theme.spacing.xxl },
  statsCard: {
    flexDirection: 'row',
    backgroundColor: theme.colors.ink,
    borderRadius: theme.radius.lg,
    paddingVertical: theme.spacing.lg,
  },
  stat: { flex: 1, alignItems: 'center', gap: 4 },
  statValue: { fontFamily: theme.fonts.heading, fontSize: 20, fontWeight: '700', color: theme.colors.onInk },
  statValueAccent: { color: theme.colors.successBright },
  statLabel: { fontFamily: theme.fonts.body, fontSize: 11, color: theme.colors.onInkMuted, textAlign: 'center' },
  statDivider: { width: StyleSheet.hairlineWidth, backgroundColor: 'rgba(255,255,255,0.18)' },
  hint: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginTop: theme.spacing.sm,
  },
  sectionTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: theme.spacing.xl,
    marginBottom: theme.spacing.md,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
  },
  fieldRow: { flexDirection: 'row', gap: theme.spacing.md },
  field: { flex: 1 },
  label: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    fontWeight: '700',
    color: theme.colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: theme.spacing.xs,
    marginTop: theme.spacing.sm,
  },
  input: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.background,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingHorizontal: theme.spacing.lg,
    fontFamily: theme.fonts.body,
    fontSize: 16,
    color: theme.colors.textPrimary,
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    marginTop: theme.spacing.md,
  },
  switchBody: { flex: 1 },
  switchLabel: { fontFamily: theme.fonts.body, fontSize: 15, fontWeight: '600', color: theme.colors.textPrimary },
  switchDesc: { fontFamily: theme.fonts.body, fontSize: 12, color: theme.colors.textSecondary, marginTop: 2 },
  errorText: { fontFamily: theme.fonts.body, fontSize: 13, color: theme.colors.danger, marginTop: theme.spacing.md },
  submit: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.ink,
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: theme.spacing.lg,
  },
  submitText: { fontFamily: theme.fonts.heading, fontSize: 17, fontWeight: '700', color: theme.colors.onInk },
  empty: {
    alignItems: 'center',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderStyle: 'dashed',
    padding: theme.spacing.xl,
  },
  emptyText: { fontFamily: theme.fonts.body, fontSize: 13, color: theme.colors.textSecondary },
  logRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.colors.border,
  },
  logIcon: {
    width: 32,
    height: 32,
    borderRadius: theme.radius.sm,
    backgroundColor: theme.colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logBody: { flex: 1 },
  logMain: { fontFamily: theme.fonts.body, fontSize: 14, fontWeight: '600', color: theme.colors.textPrimary },
  logMeta: { fontFamily: theme.fonts.body, fontSize: 12, color: theme.colors.textSecondary, marginTop: 2 },
  disabled: { opacity: 0.4 },
  pressed: { opacity: 0.85 },
});
