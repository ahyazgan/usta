import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { t } from '@/lib/i18n';
import { useUstaStore, type ChipState } from '@/lib/store';
import { theme } from '@/lib/theme';

function chipColor(state: ChipState): string {
  // Amber for anything needing attention; muted secondary for OK.
  // Green is reserved exclusively for verification / correct-place state.
  return state === 'ok' ? theme.colors.textSecondary : theme.colors.accent;
}

function StatusChip({ label, state }: { label: string; state: ChipState }) {
  const color = chipColor(state);
  return (
    <View style={[styles.chip, { borderColor: color }]}>
      <Text style={[styles.chipLabel, { color }]}>{label}</Text>
      <Text style={[styles.chipState, { color }]}>
        {t(`garage.chipState.${state}`)}
      </Text>
    </View>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

export default function GarageScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const vehicle = useUstaStore((s) => s.vehicle);
  const maintenance = useUstaStore((s) => s.maintenance);

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.lg }]}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.title}>{t('garage.title')}</Text>

        {vehicle && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>
              {vehicle.make} {vehicle.model}
            </Text>

            <InfoRow label={t('garage.labels.make')} value={vehicle.make} />
            <InfoRow label={t('garage.labels.model')} value={vehicle.model} />
            <InfoRow label={t('garage.labels.year')} value={String(vehicle.year)} />
            <InfoRow
              label={t('garage.labels.engine')}
              value={`${vehicle.engine} (${vehicle.engine_code})`}
            />
            <InfoRow label={t('garage.labels.fuel')} value={vehicle.fuel} />
            <InfoRow
              label={t('garage.labels.km')}
              value={`${vehicle.current_km.toLocaleString('tr-TR')} km`}
            />

            <View style={styles.chipRow}>
              <StatusChip label={t('garage.chips.oil')} state={maintenance.oil} />
              <StatusChip label={t('garage.chips.filter')} state={maintenance.filter} />
              <StatusChip label={t('garage.chips.battery')} state={maintenance.battery} />
            </View>
          </View>
        )}
      </ScrollView>

      <View style={[styles.ctaWrap, { paddingBottom: insets.bottom + theme.spacing.lg }]}>
        <Pressable
          accessibilityRole="button"
          style={({ pressed }) => [styles.cta, pressed && styles.ctaPressed]}
          onPress={() => router.push('/camera')}
        >
          <Ionicons name="camera" size={22} color={theme.colors.background} />
          <Text style={styles.ctaText}>{t('garage.cta')}</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
    paddingHorizontal: theme.spacing.lg,
  },
  scroll: {
    paddingBottom: theme.spacing.xxl,
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 32,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.lg,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
  },
  cardTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.md,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.colors.border,
  },
  infoLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  infoValue: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.textPrimary,
  },
  chipRow: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.lg,
  },
  chip: {
    flex: 1,
    borderWidth: 1,
    borderRadius: theme.radius.md,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    alignItems: 'center',
  },
  chipLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '700',
  },
  chipState: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    marginTop: 2,
  },
  ctaWrap: {
    paddingTop: theme.spacing.md,
  },
  cta: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.accent,
    borderRadius: theme.radius.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
  },
  ctaPressed: {
    opacity: 0.85,
  },
  ctaText: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.background,
  },
});
