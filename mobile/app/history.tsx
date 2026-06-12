import { Ionicons } from '@expo/vector-icons';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { BottomTabBar } from '@/components/BottomTabBar';
import { FeedbackRow } from '@/components/FeedbackRow';
import { MechanicBriefSheet } from '@/components/MechanicBriefSheet';
import { ResolutionRow } from '@/components/ResolutionRow';
import { type BriefDiag } from '@/lib/mechanicBrief';
import {
  createApiClient,
  type DiagnosisHistory,
  type MaintenanceLog,
  type Reminder,
  type ReminderStatus,
} from '@/lib/api';
import { i18n, t } from '@/lib/i18n';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';
import { useHistory } from '@/lib/useHistory';
import { useVehicleTasks } from '@/lib/useVehicleTasks';

/** Seçici boşken / yüklenirken kullanılacak çekirdek görevler. */
const FALLBACK_TASK_IDS = ['oil_change', 'battery', 'cabin_filter'];

/** Resolve a task id to a localized title, falling back to the raw id. */
function taskTitle(id: string): string {
  const key = `garage.tasks.${id}`;
  const translated = t(key);
  // i18n-js returns a "[missing ...]" marker when the key is unknown.
  return translated.startsWith('[missing') ? id : translated;
}

/** Status color — NEVER green; secondary/amber/red per the project rule. */
function statusColor(status: ReminderStatus): string {
  if (status === 'due') return theme.colors.danger;
  if (status === 'soon') return theme.colors.accent;
  // ok + unknown both render muted (unknown a touch more so via opacity).
  return theme.colors.textSecondary;
}

function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString(i18n.locale === 'en' ? 'en-US' : 'tr-TR');
}

function ReminderRow({ reminder }: { reminder: Reminder }) {
  const color = statusColor(reminder.status);
  const remaining =
    reminder.remaining_km != null
      ? t('history.reminders.remaining', {
          km: reminder.remaining_km.toLocaleString(),
        })
      : t('history.reminders.unknownKm');
  const dueAt =
    reminder.due_km != null
      ? t('history.reminders.dueAt', { km: reminder.due_km.toLocaleString() })
      : t('history.reminders.unknownKm');

  return (
    <View style={styles.reminderRow}>
      <View style={styles.reminderMain}>
        <Text style={styles.reminderTask}>{taskTitle(reminder.task)}</Text>
        <Text style={styles.reminderMeta}>
          {remaining} · {dueAt}
        </Text>
      </View>
      <View style={[styles.statusBadge, { borderColor: color }]}>
        <Text
          style={[
            styles.statusText,
            { color },
            reminder.status === 'unknown' && styles.statusMuted,
          ]}
        >
          {t(`history.reminders.status.${reminder.status}`)}
        </Text>
      </View>
    </View>
  );
}

function DiagnosisRow({
  item,
  vehicleId,
  onShowMechanic,
}: {
  item: DiagnosisHistory;
  vehicleId: number | null;
  onShowMechanic: (item: DiagnosisHistory) => void;
}) {
  const icon = item.kind === 'image' ? 'camera' : 'pulse';
  const metaParts = [
    formatDate(item.created_at),
    item.guven != null ? t(`camera.guven.${item.guven}`) : null,
    item.task != null ? taskTitle(item.task) : null,
  ].filter(Boolean);
  return (
    <View style={styles.diagRow}>
      <View style={styles.diagIcon}>
        <Ionicons name={icon} size={16} color={theme.colors.textSecondary} />
      </View>
      <View style={styles.diagBody}>
        <View style={styles.diagTopRow}>
          <Text style={[styles.diagText, styles.diagTextFlex]} numberOfLines={2}>
            {item.tespit}
          </Text>
          {item.ariza_sistem != null && (
            <View style={styles.sistemPill}>
              <Text style={styles.sistemPillText}>{t(`sistem.${item.ariza_sistem}`)}</Text>
            </View>
          )}
          {item.tamirciye_git === true && (
            <View style={styles.diagPill}>
              <Text style={styles.diagPillText}>{t('history.diagnoses.mechanic')}</Text>
            </View>
          )}
        </View>
        <Text style={styles.diagMeta}>{metaParts.join(' · ')}</Text>
        {vehicleId != null && (
          <View style={styles.diagFeedback}>
            <FeedbackRow
              vehicleId={vehicleId}
              sessionId={item.id}
              initial={item.feedback_dogru}
            />
          </View>
        )}
        {vehicleId != null && (
          <View style={styles.diagResolution}>
            <ResolutionRow
              vehicleId={vehicleId}
              sessionId={item.id}
              initial={item.resolution}
            />
          </View>
        )}
        <Pressable
          accessibilityRole="button"
          onPress={() => onShowMechanic(item)}
          style={({ pressed }) => [styles.diagBrief, pressed && styles.pressed]}
        >
          <Ionicons name="construct-outline" size={14} color={theme.colors.ink} />
          <Text style={styles.diagBriefText}>{t('brief.cta')}</Text>
        </Pressable>
      </View>
    </View>
  );
}

function LogRow({ log }: { log: MaintenanceLog }) {
  const km =
    log.km != null
      ? t('history.logs.kmValue', { km: log.km.toLocaleString() })
      : t('history.logs.noKm');
  const metaParts = [km];
  if (log.cost_try != null) {
    metaParts.push(`₺${log.cost_try.toLocaleString('tr-TR')}`);
  }
  return (
    <View style={styles.logRow}>
      <View style={styles.logHeader}>
        <Text style={styles.logTask}>{taskTitle(log.task)}</Text>
        <Text style={styles.logDate}>{formatDate(log.created_at)}</Text>
      </View>
      <Text style={styles.logMeta}>{metaParts.join(' · ')}</Text>
      {log.note != null && log.note.length > 0 && (
        <Text style={styles.logNote}>{log.note}</Text>
      )}
    </View>
  );
}

export default function HistoryScreen() {
  const insets = useSafeAreaInsets();
  const {
    loading,
    error,
    reminders,
    logs,
    refresh,
    addLog,
    submitting,
    submitError,
  } = useHistory();

  // Kayıt seçicisi bu aracın TÜM uygun görevlerini listeler (sunucu filtreli).
  const vehicle = useUstaStore(selectCurrentVehicle);
  const { tasks: vehicleTasks } = useVehicleTasks(vehicle?.id ?? null);
  const taskIds =
    vehicleTasks.length > 0 ? vehicleTasks.map((x) => x.id) : FALLBACK_TASK_IDS;

  const [task, setTask] = useState<string>(FALLBACK_TASK_IDS[0]);
  const [km, setKm] = useState('');
  const [note, setNote] = useState('');
  const [cost, setCost] = useState('');

  // "Mekaniğe Göster" — geçmiş teşhisten özet üret.
  const [briefDiag, setBriefDiag] = useState<BriefDiag | null>(null);
  function openBrief(item: DiagnosisHistory) {
    setBriefDiag({
      kindLabel: item.kind === 'image' ? t('brief.kindImage') : t('brief.kindSound'),
      tespit: item.tespit ?? '',
      taskLabel: item.task ? taskTitle(item.task) : undefined,
      sistemLabel: item.ariza_sistem ? t(`sistem.${item.ariza_sistem}`) : undefined,
      guven: item.guven,
      dateLabel: formatDate(item.created_at),
      sistem: item.ariza_sistem,
      sessionId: item.id,
    });
  }

  // Teşhis geçmişi (görüntü + ses) — hata sessizce boş listeye düşer.
  const authToken = useUstaStore((s) => s.authToken);
  const diagClient = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );
  const [diagnoses, setDiagnoses] = useState<DiagnosisHistory[]>([]);
  const loadDiagnoses = useCallback(async () => {
    if (vehicle == null) {
      setDiagnoses([]);
      return;
    }
    try {
      setDiagnoses(await diagClient.getDiagnoses(vehicle.id));
    } catch {
      setDiagnoses([]);
    }
  }, [diagClient, vehicle]);
  useEffect(() => {
    void loadDiagnoses();
  }, [loadDiagnoses]);

  async function handleAdd() {
    if (submitting) return;
    const parsedKm = km.trim().length > 0 ? Number(km.trim()) : undefined;
    const parsedCost = cost.trim().length > 0 ? Number(cost.trim()) : undefined;
    const ok = await addLog({
      task,
      km: Number.isFinite(parsedKm) ? parsedKm : undefined,
      note: note.trim().length > 0 ? note.trim() : undefined,
      cost_try:
        parsedCost != null && Number.isFinite(parsedCost) && parsedCost >= 0
          ? Math.round(parsedCost)
          : undefined,
    });
    if (ok) {
      setKm('');
      setNote('');
      setCost('');
    }
  }

  return (
    <View
      style={[styles.container, { paddingTop: insets.top + theme.spacing.lg }]}
    >
      <ScrollView
        contentContainerStyle={[
          styles.scroll,
          { paddingBottom: insets.bottom + theme.spacing.xxl },
        ]}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>{t('history.title')}</Text>

        {loading ? (
          <ActivityIndicator color={theme.colors.accent} style={styles.loader} />
        ) : error ? (
          <View style={styles.errorBox}>
            <Ionicons
              name="cloud-offline"
              size={18}
              color={theme.colors.warning}
            />
            <Text style={styles.errorText}>{t(error)}</Text>
            <Pressable
              accessibilityRole="button"
              onPress={() => void refresh()}
              style={({ pressed }) => [
                styles.retryButton,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.retryText}>{t('common.retry')}</Text>
            </Pressable>
          </View>
        ) : (
          <>
            <Text style={styles.sectionTitle}>
              {t('history.reminders.title')}
            </Text>
            {reminders.length === 0 ? (
              <View style={styles.emptyBox}>
                <Ionicons name="notifications-off-outline" size={28} color={theme.colors.textSecondary} />
                <Text style={styles.empty}>{t('history.reminders.empty')}</Text>
                <Text style={styles.emptyHint}>{t('history.reminders.emptyHint')}</Text>
              </View>
            ) : (
              <View style={styles.card}>
                {reminders.map((reminder) => (
                  <ReminderRow key={reminder.task} reminder={reminder} />
                ))}
              </View>
            )}

            <Text style={styles.sectionTitle}>{t('history.logs.title')}</Text>
            {logs.length === 0 ? (
              <View style={styles.emptyBox}>
                <Ionicons name="document-text-outline" size={28} color={theme.colors.textSecondary} />
                <Text style={styles.empty}>{t('history.logs.empty')}</Text>
                <Text style={styles.emptyHint}>{t('history.logs.emptyHint')}</Text>
              </View>
            ) : (
              <View style={styles.card}>
                {logs.map((log) => (
                  <LogRow key={log.id} log={log} />
                ))}
              </View>
            )}

            <Text style={styles.sectionTitle}>{t('history.diagnoses.title')}</Text>
            {diagnoses.length === 0 ? (
              <View style={styles.emptyBox}>
                <Ionicons name="scan-outline" size={28} color={theme.colors.textSecondary} />
                <Text style={styles.empty}>{t('history.diagnoses.empty')}</Text>
                <Text style={styles.emptyHint}>{t('history.diagnoses.emptyHint')}</Text>
              </View>
            ) : (
              <View style={styles.card}>
                {diagnoses.map((item) => (
                  <DiagnosisRow
                    key={item.id}
                    item={item}
                    vehicleId={vehicle?.id ?? null}
                    onShowMechanic={openBrief}
                  />
                ))}
              </View>
            )}
          </>
        )}

        <Text style={styles.sectionTitle}>{t('history.addLog.title')}</Text>
        <View style={styles.card}>
          <Text style={styles.label}>{t('history.addLog.taskLabel')}</Text>
          <View style={styles.taskRow}>
            {taskIds.map((id) => {
              const selected = task === id;
              const color = selected
                ? theme.colors.accent
                : theme.colors.textSecondary;
              return (
                <Pressable
                  key={id}
                  accessibilityRole="button"
                  accessibilityState={{ selected }}
                  onPress={() => setTask(id)}
                  style={({ pressed }) => [
                    styles.taskChip,
                    { borderColor: color },
                    selected && styles.taskChipSelected,
                    pressed && styles.pressed,
                  ]}
                >
                  <Text style={[styles.taskChipLabel, { color }]}>
                    {taskTitle(id)}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <Text style={styles.label}>{t('history.addLog.kmLabel')}</Text>
          <TextInput
            style={styles.input}
            value={km}
            onChangeText={setKm}
            placeholder={t('history.addLog.kmPlaceholder')}
            placeholderTextColor={theme.colors.textSecondary}
            keyboardType="number-pad"
          />

          <Text style={styles.label}>{t('history.addLog.costLabel')}</Text>
          <TextInput
            style={styles.input}
            value={cost}
            onChangeText={setCost}
            placeholder={t('history.addLog.costPlaceholder')}
            placeholderTextColor={theme.colors.textSecondary}
            keyboardType="number-pad"
          />

          <Text style={styles.label}>{t('history.addLog.noteLabel')}</Text>
          <TextInput
            style={styles.input}
            value={note}
            onChangeText={setNote}
            placeholder={t('history.addLog.notePlaceholder')}
            placeholderTextColor={theme.colors.textSecondary}
          />

          {submitError && (
            <View style={styles.errorBox}>
              <Ionicons
                name="alert-circle"
                size={18}
                color={theme.colors.danger}
              />
              <Text style={styles.errorText}>{t(submitError)}</Text>
            </View>
          )}

          <Pressable
            accessibilityRole="button"
            accessibilityState={{ disabled: submitting }}
            disabled={submitting}
            onPress={handleAdd}
            style={({ pressed }) => [
              styles.submit,
              submitting && styles.submitDisabled,
              pressed && styles.pressed,
            ]}
          >
            {submitting ? (
              <ActivityIndicator color={theme.colors.background} />
            ) : (
              <Text style={styles.submitText}>{t('history.addLog.submit')}</Text>
            )}
          </Pressable>
        </View>
      </ScrollView>

      <MechanicBriefSheet
        visible={briefDiag != null}
        vehicle={vehicle}
        diag={briefDiag}
        onClose={() => setBriefDiag(null)}
      />

      <BottomTabBar active="history" />
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
    paddingBottom: theme.spacing.xxl,
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 28,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.md,
  },
  loader: {
    marginTop: theme.spacing.xl,
  },
  sectionTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.textPrimary,
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
  empty: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.textSecondary,
  },
  emptyBox: {
    alignItems: 'center',
    gap: theme.spacing.xs,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderStyle: 'dashed',
    padding: theme.spacing.xl,
  },
  emptyHint: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    opacity: 0.8,
  },
  reminderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.colors.border,
  },
  reminderMain: {
    flex: 1,
    paddingRight: theme.spacing.md,
  },
  reminderTask: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  reminderMeta: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  statusBadge: {
    borderWidth: 1,
    borderRadius: theme.radius.pill,
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.md,
  },
  statusText: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    fontWeight: '700',
  },
  statusMuted: {
    opacity: 0.6,
  },
  diagRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.md,
    paddingVertical: theme.spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.colors.border,
  },
  diagIcon: {
    width: 32,
    height: 32,
    borderRadius: theme.radius.sm,
    backgroundColor: theme.colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  diagBody: { flex: 1 },
  diagTopRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.sm,
  },
  diagText: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    lineHeight: 19,
    color: theme.colors.textPrimary,
  },
  diagTextFlex: { flex: 1 },
  diagFeedback: {
    marginTop: theme.spacing.sm,
  },
  diagBrief: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    alignSelf: 'flex-start',
    marginTop: theme.spacing.sm,
    paddingVertical: 4,
    paddingHorizontal: theme.spacing.sm,
    borderRadius: theme.radius.sm,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  diagBriefText: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    fontWeight: '700',
    color: theme.colors.ink,
  },
  diagResolution: {
    marginTop: theme.spacing.sm,
    paddingTop: theme.spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: theme.colors.border,
  },
  sistemPill: {
    backgroundColor: theme.colors.background,
    borderRadius: theme.radius.pill,
    paddingVertical: 2,
    paddingHorizontal: theme.spacing.sm,
  },
  sistemPillText: {
    fontFamily: theme.fonts.body,
    fontSize: 10,
    fontWeight: '700',
    color: theme.colors.textSecondary,
  },
  diagMeta: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  diagPill: {
    backgroundColor: theme.colors.urgentSoftBg,
    borderRadius: theme.radius.pill,
    paddingVertical: 2,
    paddingHorizontal: theme.spacing.sm,
  },
  diagPillText: {
    fontFamily: theme.fonts.body,
    fontSize: 10,
    fontWeight: '700',
    color: theme.colors.urgentSoftText,
  },
  logRow: {
    paddingVertical: theme.spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.colors.border,
  },
  logHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logTask: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  logDate: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  logMeta: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  logNote: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.textPrimary,
    marginTop: theme.spacing.xs,
  },
  label: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
    marginTop: theme.spacing.md,
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
    backgroundColor: theme.colors.background,
  },
  taskChipLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '700',
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
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.lg,
  },
  errorText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.danger,
  },
  retryButton: {
    minHeight: theme.touchTarget,
    justifyContent: 'center',
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.accent,
  },
  retryText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.accent,
  },
  submit: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.accent,
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: theme.spacing.lg,
  },
  submitDisabled: {
    opacity: 0.5,
  },
  submitText: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.background,
  },
  pressed: {
    opacity: 0.85,
  },
});
