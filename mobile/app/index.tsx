import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { createApiClient, type Task, type Vehicle } from '@/lib/api';
import { i18n, t } from '@/lib/i18n';
import { useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';
import { useAuth } from '@/lib/useAuth';
import { useGarageStatus, type GarageChipState } from '@/lib/useGarageStatus';
import { useVehicles } from '@/lib/useVehicles';

/**
 * Local fallback task ids + risk, used when GET /v1/tasks is unavailable.
 * Titles are resolved from i18n (no hardcoded user-facing strings).
 */
const DEFAULT_TASK_IDS: { id: string; risk: Task['risk'] }[] = [
  { id: 'oil_change', risk: 'orta' },
  { id: 'battery', risk: 'orta' },
  { id: 'cabin_filter', risk: 'dusuk' },
];

const DEFAULT_TASKS: Task[] = DEFAULT_TASK_IDS.map(({ id, risk }) => ({
  id,
  title_tr: t(`garage.tasks.${id}`, { locale: 'tr' }),
  title_en: t(`garage.tasks.${id}`, { locale: 'en' }),
  risk,
}));

function taskTitle(task: Task): string {
  return i18n.locale === 'en' ? task.title_en : task.title_tr;
}

/**
 * Chip color for a reminder-derived garage status. Green is reserved
 * exclusively for camera verification, so it never appears here:
 * due → danger, soon → accent, ok → secondary, unknown → muted secondary.
 */
function chipColor(state: GarageChipState): string {
  if (state === 'due') return theme.colors.danger;
  if (state === 'soon') return theme.colors.accent;
  return theme.colors.textSecondary;
}

function StatusChip({
  label,
  state,
}: {
  label: string;
  state: GarageChipState;
}) {
  const color = chipColor(state);
  return (
    <View style={[styles.chip, { borderColor: color }]}>
      <Text style={[styles.chipLabel, { color }]}>{label}</Text>
      <Text
        style={[
          styles.chipState,
          { color },
          state === 'unknown' && styles.chipStateMuted,
        ]}
      >
        {t(`garage.chipState.${state}`)}
      </Text>
    </View>
  );
}

function TaskChip({
  task,
  selected,
  onPress,
}: {
  task: Task;
  selected: boolean;
  onPress: () => void;
}) {
  // Selected = amber accent; unselected = muted. Green stays reserved for
  // verification success only.
  const color = selected ? theme.colors.accent : theme.colors.textSecondary;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected }}
      onPress={onPress}
      style={({ pressed }) => [
        styles.taskChip,
        { borderColor: color },
        selected && styles.taskChipSelected,
        pressed && styles.pressed,
      ]}
    >
      <Text style={[styles.taskChipLabel, { color }]}>{taskTitle(task)}</Text>
    </Pressable>
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

function VehicleSwitcher({
  vehicles,
  currentId,
  onSelect,
}: {
  vehicles: Vehicle[];
  currentId: number;
  onSelect: (id: number) => void;
}) {
  return (
    <View style={styles.switcher}>
      <Text style={styles.switchLabel}>{t('vehicle.switch')}</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.switcherRow}
      >
        {vehicles.map((v) => {
          const selected = v.id === currentId;
          const color = selected
            ? theme.colors.accent
            : theme.colors.textSecondary;
          return (
            <Pressable
              key={v.id}
              accessibilityRole="button"
              accessibilityState={{ selected }}
              onPress={() => onSelect(v.id)}
              style={({ pressed }) => [
                styles.switchChip,
                { borderColor: color },
                selected && styles.switchChipSelected,
                pressed && styles.pressed,
              ]}
            >
              <Text style={[styles.switchChipLabel, { color }]}>
                {v.make} {v.model}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}

export default function GarageScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const authToken = useUstaStore((s) => s.authToken);
  const selectedTask = useUstaStore((s) => s.selectedTask);
  const setSelectedTask = useUstaStore((s) => s.setSelectedTask);
  const { logout } = useAuth();

  const {
    vehicles,
    currentVehicle,
    loading: vehiclesLoading,
    selectVehicle,
  } = useVehicles();
  const { chips } = useGarageStatus(currentVehicle?.id ?? null);

  const isAuthenticated = authToken != null;

  const [tasks, setTasks] = useState<Task[]>(DEFAULT_TASKS);

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;
    client
      .getTasks()
      .then((fetched) => {
        if (active && fetched.length > 0) setTasks(fetched);
      })
      // Graceful fallback: keep the localized DEFAULT_TASKS already in state.
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [client, isAuthenticated]);

  const hasSelection = selectedTask != null;

  if (!isAuthenticated) {
    return (
      <View
        style={[
          styles.container,
          styles.gateContainer,
          { paddingTop: insets.top + theme.spacing.lg },
        ]}
      >
        <Text style={styles.title}>{t('garage.title')}</Text>
        <Text style={styles.gatePrompt}>{t('auth.loggedOutPrompt')}</Text>
        <Pressable
          accessibilityRole="button"
          onPress={() => router.push('/login')}
          style={({ pressed }) => [styles.cta, pressed && styles.ctaPressed]}
        >
          <Ionicons name="log-in" size={22} color={theme.colors.background} />
          <Text style={styles.ctaText}>{t('auth.loggedOutCta')}</Text>
        </Pressable>
      </View>
    );
  }

  const header = (
    <View style={styles.headerRow}>
      <Text style={styles.title}>{t('garage.title')}</Text>
      <Pressable
        accessibilityRole="button"
        onPress={() => void logout()}
        style={({ pressed }) => [styles.logoutButton, pressed && styles.pressed]}
      >
        <Ionicons name="log-out" size={20} color={theme.colors.textSecondary} />
        <Text style={styles.logoutText}>{t('auth.logout')}</Text>
      </Pressable>
    </View>
  );

  // Loading the vehicle list.
  if (vehiclesLoading) {
    return (
      <View
        style={[styles.container, { paddingTop: insets.top + theme.spacing.lg }]}
      >
        {header}
        <View style={styles.loadingBox}>
          <ActivityIndicator color={theme.colors.accent} />
          <Text style={styles.loadingText}>{t('garage.loading')}</Text>
        </View>
      </View>
    );
  }

  // No vehicles yet — prominent empty state CTA.
  if (!currentVehicle) {
    return (
      <View
        style={[styles.container, { paddingTop: insets.top + theme.spacing.lg }]}
      >
        {header}
        <View style={styles.emptyBox}>
          <Ionicons
            name="car-sport-outline"
            size={72}
            color={theme.colors.textSecondary}
          />
          <Text style={styles.emptyTitle}>{t('vehicle.empty.title')}</Text>
          <Text style={styles.emptyDesc}>{t('vehicle.empty.desc')}</Text>
          <Pressable
            accessibilityRole="button"
            onPress={() => router.push('/vehicle-new')}
            style={({ pressed }) => [styles.cta, pressed && styles.ctaPressed]}
          >
            <Ionicons name="add-circle" size={22} color={theme.colors.background} />
            <Text style={styles.ctaText}>{t('vehicle.add')}</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  const fuelLabel = t(`vehicle.fuel.${currentVehicle.fuel_type}`);

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.lg }]}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
      >
        {header}

        {vehicles.length > 1 && (
          <VehicleSwitcher
            vehicles={vehicles}
            currentId={currentVehicle.id}
            onSelect={selectVehicle}
          />
        )}

        <View style={styles.card}>
          <Text style={styles.cardTitle}>
            {currentVehicle.make} {currentVehicle.model}
          </Text>

          <InfoRow label={t('garage.labels.make')} value={currentVehicle.make} />
          <InfoRow label={t('garage.labels.model')} value={currentVehicle.model} />
          <InfoRow
            label={t('garage.labels.year')}
            value={String(currentVehicle.year)}
          />
          {currentVehicle.engine_code != null &&
            currentVehicle.engine_code.length > 0 && (
              <InfoRow
                label={t('garage.labels.engineCode')}
                value={currentVehicle.engine_code}
              />
            )}
          <InfoRow label={t('garage.labels.fuel')} value={fuelLabel} />
          {currentVehicle.current_km != null && (
            <InfoRow
              label={t('garage.labels.km')}
              value={`${currentVehicle.current_km.toLocaleString('tr-TR')} km`}
            />
          )}

          <View style={styles.chipRow}>
            <StatusChip label={t('garage.chips.oil')} state={chips.oil} />
            <StatusChip label={t('garage.chips.filter')} state={chips.filter} />
            <StatusChip label={t('garage.chips.battery')} state={chips.battery} />
          </View>
        </View>

        <Pressable
          accessibilityRole="button"
          onPress={() => router.push('/vehicle-new')}
          style={({ pressed }) => [styles.addVehicle, pressed && styles.pressed]}
        >
          <Ionicons name="add" size={18} color={theme.colors.accent} />
          <Text style={styles.addVehicleText}>{t('vehicle.add')}</Text>
        </Pressable>

        <Text style={styles.sectionTitle}>{t('garage.tasks.title')}</Text>
        <View style={styles.taskRow}>
          {tasks.map((task) => (
            <TaskChip
              key={task.id}
              task={task}
              selected={selectedTask?.id === task.id}
              onPress={() => setSelectedTask(task)}
            />
          ))}
        </View>

        <View style={styles.navRow}>
          <Pressable
            accessibilityRole="button"
            onPress={() => router.push('/sound')}
            style={({ pressed }) => [styles.navButton, pressed && styles.pressed]}
          >
            <Ionicons name="pulse" size={20} color={theme.colors.accent} />
            <Text style={styles.navText}>{t('nav.sound')}</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            onPress={() => router.push('/history')}
            style={({ pressed }) => [styles.navButton, pressed && styles.pressed]}
          >
            <Ionicons name="time" size={20} color={theme.colors.accent} />
            <Text style={styles.navText}>{t('nav.history')}</Text>
          </Pressable>
        </View>
      </ScrollView>

      <View style={[styles.ctaWrap, { paddingBottom: insets.bottom + theme.spacing.lg }]}>
        {!hasSelection && (
          <Text style={styles.ctaHint}>{t('garage.tasks.selectHint')}</Text>
        )}
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled: !hasSelection }}
          disabled={!hasSelection}
          style={({ pressed }) => [
            styles.cta,
            !hasSelection && styles.ctaDisabled,
            pressed && styles.ctaPressed,
          ]}
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
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    minHeight: theme.touchTarget,
    paddingHorizontal: theme.spacing.md,
  },
  logoutText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.textSecondary,
  },
  gateContainer: {
    justifyContent: 'center',
    gap: theme.spacing.lg,
  },
  gatePrompt: {
    fontFamily: theme.fonts.body,
    fontSize: 16,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  loadingBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.md,
  },
  loadingText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  emptyBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
  },
  emptyTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 22,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    textAlign: 'center',
    marginTop: theme.spacing.md,
  },
  emptyDesc: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: theme.spacing.md,
  },
  switcher: {
    marginBottom: theme.spacing.md,
  },
  switchLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
  },
  switcherRow: {
    gap: theme.spacing.sm,
    paddingRight: theme.spacing.lg,
  },
  switchChip: {
    minHeight: theme.touchTarget,
    justifyContent: 'center',
    borderWidth: 1,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.lg,
  },
  switchChipSelected: {
    backgroundColor: theme.colors.surface,
  },
  switchChipLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
  },
  navRow: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginTop: theme.spacing.xl,
  },
  navButton: {
    flex: 1,
    minHeight: theme.touchTarget,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingHorizontal: theme.spacing.md,
  },
  navText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.textPrimary,
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
  addVehicle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.xs,
    minHeight: theme.touchTarget,
    marginTop: theme.spacing.md,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.accent,
  },
  addVehicleText: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.accent,
  },
  sectionTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    marginTop: theme.spacing.xl,
    marginBottom: theme.spacing.md,
  },
  taskRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
  },
  taskChip: {
    minHeight: theme.touchTarget,
    justifyContent: 'center',
    borderWidth: 1,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.lg,
  },
  taskChipSelected: {
    backgroundColor: theme.colors.surface,
  },
  taskChipLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '700',
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
  chipStateMuted: {
    opacity: 0.6,
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
    paddingHorizontal: theme.spacing.lg,
  },
  ctaPressed: {
    opacity: 0.85,
  },
  ctaDisabled: {
    opacity: 0.4,
  },
  pressed: {
    opacity: 0.85,
  },
  ctaHint: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: theme.spacing.sm,
  },
  ctaText: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.background,
  },
});
