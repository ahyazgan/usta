import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { BottomTabBar } from '@/components/BottomTabBar';
import { type Reminder, type Vehicle } from '@/lib/api';
import { dateStatus, daysUntil, formatTrDate } from '@/lib/dateReminders';
import { ensureDemoSession } from '@/lib/demoSession';
import { t } from '@/lib/i18n';
import { syncVehicleReminders } from '@/lib/notifications';
import { useUstaStore } from '@/lib/store';
import { TASK_ICON } from '@/lib/taskIcons';
import { theme } from '@/lib/theme';
import { useAuth } from '@/lib/useAuth';
import { useGarageStatus, type GarageChipState } from '@/lib/useGarageStatus';
import { useSummary } from '@/lib/useSummary';
import { useVehicles } from '@/lib/useVehicles';

/** Reminder state → 0-100 health contribution. */
const HEALTH_SCORE: Record<GarageChipState, number> = {
  ok: 100,
  soon: 55,
  due: 20,
  unknown: 70,
};

/** Reminder state → soft badge palette. */
function badgeStyle(state: GarageChipState) {
  if (state === 'due') return { bg: theme.colors.urgentSoftBg, fg: theme.colors.urgentSoftText };
  if (state === 'soon') return { bg: theme.colors.warnSoftBg, fg: theme.colors.warnSoftText };
  if (state === 'ok') return { bg: theme.colors.okSoftBg, fg: theme.colors.okSoftText };
  return { bg: theme.colors.border, fg: theme.colors.textSecondary };
}

function healthColor(pct: number): string {
  if (pct >= 70) return theme.colors.successBright;
  if (pct >= 40) return theme.colors.warningBright;
  return theme.colors.dangerBright;
}

/** Görev id → yerelleştirilmiş ad (garage.tasks sözlüğünden, yoksa ham id). */
function taskName(id: string): string {
  const translated = t(`garage.tasks.${id}`);
  return translated.startsWith('[missing') ? id : translated;
}

/** Hatırlatıcı satırı alt metni: aciliyete göre kalan km / durum. */
function reminderMeta(reminder: Reminder): string {
  if (reminder.status === 'due') return t('home.taskMeta.due');
  if (reminder.status === 'unknown') return t('home.taskMeta.unknown');
  if (reminder.remaining_km != null) {
    return t('history.reminders.remaining', {
      km: reminder.remaining_km.toLocaleString('tr-TR'),
    });
  }
  return t(`home.taskMeta.${reminder.status}`);
}

/** Aciliyet sırası: önce zamanı gelenler. */
const STATUS_PRIORITY: Record<GarageChipState, number> = {
  due: 0,
  soon: 1,
  unknown: 2,
  ok: 3,
};

/** Takvim (tarih) hatırlatıcı satırı — muayene / sigorta. */
function DateRow({
  icon,
  label,
  iso,
  onPress,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  iso: string;
  onPress: () => void;
}) {
  const status = dateStatus(iso);
  const days = daysUntil(iso);
  const badge = badgeStyle(status as GarageChipState);
  const meta =
    days < 0
      ? t('home.dates.overdue', { days: Math.abs(days) })
      : days === 0
        ? t('home.dates.today')
        : t('home.dates.remaining', { days });
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.taskRow, pressed && styles.pressed]}
    >
      <View style={[styles.taskIcon, { backgroundColor: badge.bg }]}>
        <Ionicons name={icon} size={18} color={badge.fg} />
      </View>
      <View style={styles.taskBody}>
        <View style={styles.taskTitleRow}>
          <Text style={styles.taskTitle}>{label}</Text>
          <View style={[styles.badge, { backgroundColor: badge.bg }]}>
            <Text style={[styles.badgeText, { color: badge.fg }]}>{formatTrDate(iso)}</Text>
          </View>
        </View>
        <Text style={styles.taskMeta}>{meta}</Text>
      </View>
      <Ionicons name="chevron-forward" size={18} color={theme.colors.border} />
    </Pressable>
  );
}

function TaskRow({ reminder, onPress }: { reminder: Reminder; onPress: () => void }) {
  const badge = badgeStyle(reminder.status);
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.taskRow, pressed && styles.pressed]}
    >
      <View style={[styles.taskIcon, { backgroundColor: badge.bg }]}>
        <Ionicons
          name={TASK_ICON[reminder.task] ?? 'build'}
          size={18}
          color={badge.fg}
        />
      </View>
      <View style={styles.taskBody}>
        <View style={styles.taskTitleRow}>
          <Text style={styles.taskTitle}>{taskName(reminder.task)}</Text>
          <View style={[styles.badge, { backgroundColor: badge.bg }]}>
            <Text style={[styles.badgeText, { color: badge.fg }]}>
              {t(`home.badge.${reminder.status}`)}
            </Text>
          </View>
        </View>
        <Text style={styles.taskMeta}>{reminderMeta(reminder)}</Text>
      </View>
      <Ionicons name="chevron-forward" size={18} color={theme.colors.border} />
    </Pressable>
  );
}

export default function HomeScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const authToken = useUstaStore((s) => s.authToken);
  const authBootstrapped = useUstaStore((s) => s.authBootstrapped);
  const setTokens = useUstaStore((s) => s.setTokens);
  const { logout } = useAuth();

  const {
    vehicles,
    currentVehicle,
    loading: vehiclesLoading,
    selectVehicle,
    removeVehicle,
    updateVehicle,
  } = useVehicles();
  const { chips, reminders } = useGarageStatus(currentVehicle?.id ?? null);
  const summary = useSummary(currentVehicle?.id ?? null);

  // Araç tarihleri değiştikçe yerel bildirimleri yeniden planla (web'de no-op).
  useEffect(() => {
    if (vehicles.length > 0) void syncVehicleReminders(vehicles);
  }, [vehicles]);

  // Km hızlı güncelleme modalı (km rozetine dokun → yaz → kaydet).
  const [kmModalOpen, setKmModalOpen] = useState(false);
  const [kmInput, setKmInput] = useState('');
  const [kmSaving, setKmSaving] = useState(false);

  function handleEditCurrent() {
    if (currentVehicle == null) return;
    router.push({ pathname: '/vehicle-new', params: { id: String(currentVehicle.id) } });
  }

  function openKmModal() {
    if (currentVehicle == null) return;
    setKmInput(
      currentVehicle.current_km != null ? String(currentVehicle.current_km) : '',
    );
    setKmModalOpen(true);
  }

  async function saveKm() {
    if (currentVehicle == null || kmSaving) return;
    const parsed = Number(kmInput.trim());
    if (!Number.isFinite(parsed) || parsed < 0) return;
    setKmSaving(true);
    await updateVehicle(currentVehicle.id, { current_km: Math.round(parsed) });
    setKmSaving(false);
    setKmModalOpen(false);
  }

  const isAuthenticated = authToken != null;

  function handleDelete(vehicle: Vehicle) {
    Alert.alert(
      t('vehicle.delete.confirmTitle'),
      t('vehicle.delete.confirmMessage', { make: vehicle.make, model: vehicle.model }),
      [
        { text: t('vehicle.delete.cancel'), style: 'cancel' },
        {
          text: t('vehicle.delete.confirm'),
          style: 'destructive',
          onPress: () => void removeVehicle(vehicle.id),
        },
      ],
    );
  }

  // --- Auto-login bootstrap (login screen removed) ----------------------- //
  if (!isAuthenticated) {
    // Demo girişi henüz sürüyor → spinner. Bittiyse ve hâlâ token yoksa,
    // demo girişi başarısız olmuştur → tekrar dene.
    if (!authBootstrapped) {
      return (
        <View style={[styles.container, styles.center, { paddingTop: insets.top + theme.spacing.lg }]}>
          <Ionicons name="construct" size={56} color={theme.colors.ink} />
          <Text style={styles.title}>{t('app.name')}</Text>
          <ActivityIndicator color={theme.colors.ink} />
          <Text style={styles.gatePrompt}>{t('home.signingIn')}</Text>
        </View>
      );
    }
    return (
      <View style={[styles.container, styles.center, { paddingTop: insets.top + theme.spacing.lg }]}>
        <Ionicons name="cloud-offline-outline" size={56} color={theme.colors.textSecondary} />
        <Text style={styles.title}>{t('app.name')}</Text>
        <Text style={styles.gatePrompt}>{t('home.connectError')}</Text>
        <Pressable
          accessibilityRole="button"
          onPress={() => void ensureDemoSession(setTokens)}
          style={({ pressed }) => [styles.cta, pressed && styles.pressed]}
        >
          <Ionicons name="refresh" size={20} color={theme.colors.onInk} />
          <Text style={styles.ctaText}>{t('common.retry')}</Text>
        </Pressable>
      </View>
    );
  }

  const header = (
    <View style={styles.headerRow}>
      <View>
        <Text style={styles.greeting}>{t('home.greeting')}</Text>
        <Text style={styles.greetingName}>{t('home.welcome')}</Text>
      </View>
      <View style={styles.headerActions}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t('privacy.title')}
          onPress={() => router.push('/privacy')}
          style={({ pressed }) => [styles.headerIcon, pressed && styles.pressed]}
        >
          <Ionicons name="shield-checkmark-outline" size={22} color={theme.colors.textSecondary} />
        </Pressable>
        <Pressable
          accessibilityRole="button"
          onPress={() => void logout()}
          style={({ pressed }) => [styles.headerIcon, pressed && styles.pressed]}
        >
          <Ionicons name="log-out-outline" size={22} color={theme.colors.textSecondary} />
        </Pressable>
      </View>
    </View>
  );

  // --- Loading ----------------------------------------------------------- //
  if (vehiclesLoading) {
    return (
      <View style={[styles.container, { paddingTop: insets.top + theme.spacing.lg }]}>
        {header}
        <View style={styles.center}>
          <ActivityIndicator color={theme.colors.ink} />
          <Text style={styles.loadingText}>{t('garage.loading')}</Text>
        </View>
        <BottomTabBar active="home" />
      </View>
    );
  }

  // --- Empty (no vehicle) ------------------------------------------------ //
  if (!currentVehicle) {
    return (
      <View style={[styles.container, { paddingTop: insets.top + theme.spacing.lg }]}>
        {header}
        <View style={styles.center}>
          <Ionicons name="car-sport-outline" size={72} color={theme.colors.textSecondary} />
          <Text style={styles.emptyTitle}>{t('vehicle.empty.title')}</Text>
          <Text style={styles.emptyDesc}>{t('vehicle.empty.desc')}</Text>
          <Pressable
            accessibilityRole="button"
            onPress={() => router.push('/vehicle-new')}
            style={({ pressed }) => [styles.cta, pressed && styles.pressed]}
          >
            <Ionicons name="add-circle" size={20} color={theme.colors.onInk} />
            <Text style={styles.ctaText}>{t('vehicle.add')}</Text>
          </Pressable>
        </View>
        <BottomTabBar active="home" />
      </View>
    );
  }

  // --- Main -------------------------------------------------------------- //
  const fuelLabel = t(`vehicle.fuel.${currentVehicle.fuel_type}`);
  const subParts = [String(currentVehicle.year), fuelLabel];
  if (currentVehicle.spec?.transmission_type) subParts.push(currentVehicle.spec.transmission_type);

  // Sağlık skoru: tüm km-bazlı hatırlatıcıların ortalaması; hiç yoksa nötr çipler.
  const states: GarageChipState[] =
    reminders.length > 0
      ? reminders.map((r) => r.status)
      : [chips.oil, chips.filter, chips.battery];
  const health = Math.round(states.reduce((s, x) => s + HEALTH_SCORE[x], 0) / states.length);

  // Yapılacaklar: aciliyete göre sıralı gerçek hatırlatıcılar (ilk 4).
  const taskRows = [...reminders]
    .sort((a, b) => STATUS_PRIORITY[a.status] - STATUS_PRIORITY[b.status])
    .slice(0, 4);

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {header}

        {vehicles.length > 1 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.switcherRow}
          >
            {vehicles.map((v) => {
              const selected = v.id === currentVehicle.id;
              return (
                <Pressable
                  key={v.id}
                  accessibilityRole="button"
                  accessibilityState={{ selected }}
                  onPress={() => selectVehicle(v.id)}
                  style={[styles.switchChip, selected && styles.switchChipSelected]}
                >
                  <Text style={[styles.switchChipText, selected && styles.switchChipTextSelected]}>
                    {v.make} {v.model}
                  </Text>
                </Pressable>
              );
            })}
          </ScrollView>
        )}

        {/* Araç kartı (koyu) */}
        <View style={styles.carCard}>
          <Pressable
            accessibilityRole="button"
            onPress={openKmModal}
            style={({ pressed }) => [styles.kmBadge, pressed && styles.pressed]}
          >
            <Text style={styles.kmNum}>
              {currentVehicle.current_km != null
                ? currentVehicle.current_km.toLocaleString('tr-TR')
                : '—'}
            </Text>
            <View style={styles.kmLabelRow}>
              <Text style={styles.kmLabel}>km</Text>
              <Ionicons name="pencil" size={9} color={theme.colors.onInkMuted} />
            </View>
          </Pressable>
          {currentVehicle.plate != null && currentVehicle.plate.length > 0 && (
            <View style={styles.plateBadge}>
              <Text style={styles.plateText}>{currentVehicle.plate}</Text>
            </View>
          )}
          <Text style={styles.carName}>
            {currentVehicle.make} {currentVehicle.model}
          </Text>
          <Text style={styles.carSub}>{subParts.join(' · ')}</Text>
          <View style={styles.healthRow}>
            <View style={styles.healthTrack}>
              <View
                style={[
                  styles.healthFill,
                  { width: `${health}%`, backgroundColor: healthColor(health) },
                ]}
              />
            </View>
            <Text style={[styles.healthPct, { color: healthColor(health) }]}>%{health}</Text>
          </View>
        </View>

        {/* Yönet (düzenle / sil / ekle) */}
        <View style={styles.manageRow}>
          <Pressable
            accessibilityRole="button"
            onPress={() =>
              router.push({ pathname: '/vehicle-new', params: { id: String(currentVehicle.id) } })
            }
            style={({ pressed }) => [styles.manageButton, pressed && styles.pressed]}
          >
            <Ionicons name="create-outline" size={16} color={theme.colors.ink} />
            <Text style={styles.manageText}>{t('vehicle.edit.cta')}</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            onPress={() => router.push('/vehicle-new')}
            style={({ pressed }) => [styles.manageButton, pressed && styles.pressed]}
          >
            <Ionicons name="add" size={16} color={theme.colors.ink} />
            <Text style={styles.manageText}>{t('vehicle.add')}</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            onPress={() => handleDelete(currentVehicle)}
            style={({ pressed }) => [styles.manageButton, pressed && styles.pressed]}
          >
            <Ionicons name="trash-outline" size={16} color={theme.colors.dangerBright} />
          </Pressable>
        </View>

        {/* Yapılacaklar */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>{t('home.tasksTitle')}</Text>
          <Pressable accessibilityRole="button" onPress={() => router.replace('/maintenance')}>
            <Text style={styles.sectionLink}>{t('home.allMaintenance')}</Text>
          </Pressable>
        </View>

        {taskRows.length === 0 ? (
          <View style={styles.taskEmpty}>
            <Ionicons name="sparkles-outline" size={20} color={theme.colors.textSecondary} />
            <Text style={styles.taskEmptyText}>{t('home.tasksEmpty')}</Text>
          </View>
        ) : (
          taskRows.map((row) => (
            <TaskRow
              key={row.task}
              reminder={row}
              onPress={() => router.replace('/maintenance')}
            />
          ))
        )}

        {/* Takvim — muayene / sigorta (tarih bazlı) */}
        {(currentVehicle.muayene_date != null || currentVehicle.sigorta_date != null) && (
          <>
            <Text style={styles.sectionTitle}>{t('home.dates.title')}</Text>
            {currentVehicle.muayene_date != null && (
              <DateRow
                icon="clipboard"
                label={t('home.dates.muayene')}
                iso={currentVehicle.muayene_date}
                onPress={() => handleEditCurrent()}
              />
            )}
            {currentVehicle.sigorta_date != null && (
              <DateRow
                icon="shield-checkmark"
                label={t('home.dates.sigorta')}
                iso={currentVehicle.sigorta_date}
                onPress={() => handleEditCurrent()}
              />
            )}
          </>
        )}

        {/* Tasarruf bandı — gerçek loglardan tahmini DIY tasarrufu */}
        <View style={styles.savingsBanner}>
          <Ionicons name="trending-up" size={22} color={theme.colors.savingsText} />
          <Text style={styles.savingsText}>
            {summary.savings_try > 0
              ? t('home.savings', {
                  amount: summary.savings_try.toLocaleString('tr-TR'),
                  count: summary.maintenance_count,
                })
              : t('home.savingsTeaser')}
          </Text>
        </View>
      </ScrollView>

      {/* Km hızlı güncelleme */}
      <Modal
        visible={kmModalOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setKmModalOpen(false)}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>{t('home.kmModal.title')}</Text>
            <TextInput
              style={styles.modalInput}
              value={kmInput}
              onChangeText={setKmInput}
              placeholder={t('home.kmModal.placeholder')}
              placeholderTextColor={theme.colors.textSecondary}
              keyboardType="number-pad"
              autoFocus
            />
            <View style={styles.modalRow}>
              <Pressable
                accessibilityRole="button"
                onPress={() => setKmModalOpen(false)}
                style={({ pressed }) => [styles.modalCancel, pressed && styles.pressed]}
              >
                <Text style={styles.modalCancelText}>{t('common.cancel')}</Text>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                accessibilityState={{ disabled: kmSaving }}
                disabled={kmSaving}
                onPress={() => void saveKm()}
                style={({ pressed }) => [styles.modalSave, pressed && styles.pressed]}
              >
                {kmSaving ? (
                  <ActivityIndicator color={theme.colors.onInk} />
                ) : (
                  <Text style={styles.modalSaveText}>{t('common.save')}</Text>
                )}
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      <BottomTabBar active="home" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scroll: {
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.xl,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.md,
  },
  greeting: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
  },
  greetingName: {
    fontFamily: theme.fonts.heading,
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    letterSpacing: -0.3,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerIcon: {
    width: 44,
    height: theme.touchTarget,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 32,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  gatePrompt: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  loadingText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  emptyTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 22,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    textAlign: 'center',
    marginTop: theme.spacing.sm,
  },
  emptyDesc: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: theme.spacing.sm,
  },
  switcherRow: {
    gap: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.md,
  },
  switchChip: {
    minHeight: 40,
    justifyContent: 'center',
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
  },
  switchChipSelected: {
    backgroundColor: theme.colors.ink,
    borderColor: theme.colors.ink,
  },
  switchChipText: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '700',
    color: theme.colors.textSecondary,
  },
  switchChipTextSelected: {
    color: theme.colors.onInk,
  },
  carCard: {
    backgroundColor: theme.colors.ink,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.xl,
    marginHorizontal: theme.spacing.lg,
    overflow: 'hidden',
  },
  kmBadge: {
    position: 'absolute',
    top: theme.spacing.lg,
    right: theme.spacing.lg,
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderRadius: theme.radius.md,
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.md,
    alignItems: 'center',
  },
  kmNum: {
    fontFamily: theme.fonts.heading,
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  kmLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  kmLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 9,
    color: theme.colors.onInkMuted,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing.xl,
  },
  modalCard: {
    width: '100%',
    maxWidth: 360,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.xl,
    gap: theme.spacing.md,
  },
  modalTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  modalInput: {
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
  modalRow: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  modalCancel: {
    flex: 1,
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  modalCancelText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.textSecondary,
  },
  modalSave: {
    flex: 1,
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.ink,
  },
  modalSaveText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  plateBadge: {
    alignSelf: 'flex-start',
    backgroundColor: theme.colors.onInk,
    borderRadius: theme.radius.sm,
    paddingVertical: 3,
    paddingHorizontal: theme.spacing.sm,
    marginBottom: theme.spacing.sm,
  },
  plateText: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    fontWeight: '700',
    color: theme.colors.ink,
    letterSpacing: 1,
  },
  carName: {
    fontFamily: theme.fonts.heading,
    fontSize: 22,
    fontWeight: '700',
    color: theme.colors.onInk,
    letterSpacing: -0.3,
  },
  carSub: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.onInkMuted,
    marginTop: theme.spacing.xs,
    marginBottom: theme.spacing.lg,
  },
  healthRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
  },
  healthTrack: {
    flex: 1,
    height: 6,
    borderRadius: theme.radius.pill,
    backgroundColor: 'rgba(255,255,255,0.15)',
    overflow: 'hidden',
  },
  healthFill: {
    height: '100%',
    borderRadius: theme.radius.pill,
  },
  healthPct: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '700',
  },
  manageRow: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
    marginTop: theme.spacing.md,
  },
  manageButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.xs,
    minHeight: 40,
    paddingHorizontal: theme.spacing.md,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
  },
  manageText: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.ink,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg,
    marginTop: theme.spacing.xl,
    marginBottom: theme.spacing.md,
  },
  sectionTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sectionLink: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.success,
  },
  taskRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    marginHorizontal: theme.spacing.lg,
    marginBottom: theme.spacing.sm,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
  },
  taskIcon: {
    width: 40,
    height: 40,
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  taskBody: {
    flex: 1,
  },
  taskTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  taskTitle: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.textPrimary,
  },
  taskMeta: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  taskEmpty: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginHorizontal: theme.spacing.lg,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderStyle: 'dashed',
    padding: theme.spacing.lg,
  },
  taskEmptyText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
  },
  badge: {
    borderRadius: theme.radius.pill,
    paddingVertical: 2,
    paddingHorizontal: theme.spacing.sm,
  },
  badgeText: {
    fontFamily: theme.fonts.body,
    fontSize: 10,
    fontWeight: '700',
  },
  savingsBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    marginHorizontal: theme.spacing.lg,
    marginTop: theme.spacing.md,
    backgroundColor: theme.colors.savingsBg,
    borderWidth: 1,
    borderColor: theme.colors.savingsBorder,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
  },
  savingsText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 13,
    lineHeight: 19,
    color: theme.colors.savingsText,
  },
  cta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: theme.touchTarget,
    paddingHorizontal: theme.spacing.xl,
    backgroundColor: theme.colors.ink,
    borderRadius: theme.radius.md,
  },
  ctaText: {
    fontFamily: theme.fonts.heading,
    fontSize: 17,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  pressed: {
    opacity: 0.85,
  },
});
