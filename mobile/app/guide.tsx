import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { capture } from '@/lib/analytics';
import {
  ApiError,
  createApiClient,
  type GuideStep,
  type TaskGuide,
} from '@/lib/api';
import { i18n, t } from '@/lib/i18n';
import { goBack } from '@/lib/nav';
import { maybeRequestReview } from '@/lib/review';
import { shareAchievement } from '@/lib/share';
import { useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';
import { useVehicles } from '@/lib/useVehicles';

const TR = () => i18n.locale !== 'en';

function instruction(step: GuideStep): string {
  return TR() ? step.instruction_tr : step.instruction_en;
}
function tool(step: GuideStep): string | null {
  return TR() ? step.tool_tr : step.tool_en;
}
function warning(step: GuideStep): string | null {
  return TR() ? step.warning_tr : step.warning_en;
}

/** Progress dots: done ✓ / active number / upcoming number. */
function ProgressRow({ total, current }: { total: number; current: number }) {
  const items: React.ReactNode[] = [];
  for (let i = 0; i < total; i += 1) {
    const done = i < current;
    const active = i === current;
    items.push(
      <View
        key={`dot-${i}`}
        style={[styles.dot, done && styles.dotDone, active && styles.dotActive]}
      >
        {done ? (
          <Ionicons name="checkmark" size={14} color={theme.colors.onInk} />
        ) : (
          <Text style={[styles.dotNum, active && styles.dotNumActive]}>{i + 1}</Text>
        )}
      </View>,
    );
    if (i < total - 1) {
      items.push(
        <View key={`line-${i}`} style={[styles.line, done && styles.lineDone]} />,
      );
    }
  }
  return <View style={styles.progressRow}>{items}</View>;
}

export default function GuideScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const authToken = useUstaStore((s) => s.authToken);
  const selectedTask = useUstaStore((s) => s.selectedTask);
  const lastResult = useUstaStore((s) => s.lastResult);
  const guideProgress = useUstaStore((s) => s.guideProgress);
  const setGuideProgress = useUstaStore((s) => s.setGuideProgress);
  const clearGuideProgress = useUstaStore((s) => s.clearGuideProgress);
  const { currentVehicle } = useVehicles();

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const [guide, setGuide] = useState<TaskGuide | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Kaldığın adımdan devam et (kameraya gidip dönünce sıfırlanmasın).
  const [current, setCurrent] = useState(
    selectedTask != null ? (guideProgress[selectedTask.id] ?? 0) : 0,
  );
  const [finishing, setFinishing] = useState(false);
  // Bitiş kutlaması: bakım kaydedildi, tasarruf göster, garaja dön.
  const [celebrating, setCelebrating] = useState(false);

  // Adım değiştikçe ilerlemeyi hatırla.
  useEffect(() => {
    if (selectedTask != null) setGuideProgress(selectedTask.id, current);
  }, [current, selectedTask, setGuideProgress]);

  const load = useCallback(async () => {
    if (currentVehicle == null || selectedTask == null) {
      setLoading(false);
      setError('camera.error.noTask');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const g = await client.getGuide(currentVehicle.id, selectedTask.id);
      setGuide(g);
      // Hatırlanan adım rehber sınırını aşıyorsa (içerik değişmiş olabilir) kırp.
      setCurrent((c) => Math.min(c, Math.max(0, g.steps.length - 1)));
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 0
          ? 'vehicle.error.network'
          : 'vehicle.error.generic',
      );
    } finally {
      setLoading(false);
    }
  }, [client, currentVehicle, selectedTask]);

  useEffect(() => {
    void load();
  }, [load]);

  const step = guide?.steps[current] ?? null;
  const total = guide?.steps.length ?? 0;
  const isLast = guide != null && current === total - 1;

  async function handleNext() {
    if (guide == null || currentVehicle == null) return;
    if (!isLast) {
      setCurrent((c) => c + 1);
      return;
    }
    // Son adım: bakımı geçmişe işle (tasarruf bandını besler) ve kutla.
    if (finishing) return;
    setFinishing(true);
    try {
      await client.addLog(currentVehicle.id, {
        task: guide.task_id,
        km: currentVehicle.current_km ?? undefined,
        // Veri çarkı: bu rehberdeki kamera doğrulamasının teşhisi log'a bağlanır
        // (görev değişince lastResult temizlendiği için bayat bağ riski yok).
        ai_session_id: lastResult?.session_id ?? undefined,
      });
    } catch {
      /* kayıt başarısız olsa da kullanıcıyı rehberde kilitleme */
    }
    setFinishing(false);
    clearGuideProgress(guide.task_id); // bitti — sonraki sefer baştan
    void capture('guide_finished', { task: guide.task_id, saving: guide.diy_saving_try });
    setCelebrating(true);
    // Pozitif an: mağaza değerlendirmesi iste (kurulum başına bir kez, native).
    void maybeRequestReview();
  }

  function backToGarage() {
    setCelebrating(false);
    // Ana sayfa yeniden mount olur -> hatırlatıcı/tasarruf/sağlık tazelenir.
    router.replace('/');
  }

  const title = guide
    ? TR()
      ? guide.title_tr
      : guide.title_en
    : selectedTask
      ? TR()
        ? selectedTask.title_tr
        : selectedTask.title_en
      : '';

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      {/* Başlık */}
      <View style={styles.header}>
        <Pressable
          accessibilityRole="button"
          onPress={() => goBack(router)}
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Ionicons name="chevron-back" size={20} color={theme.colors.success} />
          <Text style={styles.backText}>{t('common.back')}</Text>
        </Pressable>
        <Text style={styles.title}>{title}</Text>
        {currentVehicle && guide && (
          <Text style={styles.subtitle}>
            {currentVehicle.make} {currentVehicle.model} ·{' '}
            {t('guide.estMinutes', { min: guide.est_minutes })}
          </Text>
        )}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={theme.colors.ink} />
        </View>
      ) : error || guide == null ? (
        <View style={styles.center}>
          <Ionicons name="cloud-offline-outline" size={48} color={theme.colors.textSecondary} />
          <Text style={styles.errorText}>{t(error ?? 'vehicle.error.generic')}</Text>
          <Pressable
            accessibilityRole="button"
            onPress={() => void load()}
            style={({ pressed }) => [styles.retry, pressed && styles.pressed]}
          >
            <Text style={styles.retryText}>{t('common.retry')}</Text>
          </Pressable>
        </View>
      ) : (
        <>
          <ProgressRow total={total} current={current} />

          <ScrollView
            contentContainerStyle={styles.scroll}
            showsVerticalScrollIndicator={false}
          >
            {/* Adım uyarısı */}
            {step != null && warning(step) != null && (
              <View style={styles.warnStrip}>
                <Ionicons name="warning" size={16} color={theme.colors.warnSoftText} />
                <Text style={styles.warnText}>{warning(step)}</Text>
              </View>
            )}

            {/* Adım kartı */}
            {step != null && (
              <View style={styles.stepCard}>
                <Text style={styles.stepNum}>
                  {t('guide.stepOf', { current: current + 1, total })}
                </Text>
                <Text style={styles.instruction}>{instruction(step)}</Text>
                {(tool(step) != null || step.torque_nm != null) && (
                  <View style={styles.toolRow}>
                    <Ionicons name="construct" size={16} color={theme.colors.textSecondary} />
                    <Text style={styles.toolText}>
                      {tool(step) != null && (
                        <>
                          {t('guide.toolLabel')}{' '}
                          <Text style={styles.toolStrong}>{tool(step)}</Text>
                        </>
                      )}
                      {tool(step) != null && step.torque_nm != null && ' · '}
                      {step.torque_nm != null && (
                        <>
                          {t('guide.torqueLabel')}{' '}
                          <Text style={styles.toolStrong}>{step.torque_nm} Nm</Text>
                        </>
                      )}
                    </Text>
                  </View>
                )}
              </View>
            )}

            {/* Kamera doğrulama bandı */}
            <Pressable
              accessibilityRole="button"
              onPress={() => router.push('/camera')}
              style={({ pressed }) => [styles.verifyBanner, pressed && styles.pressed]}
            >
              <Ionicons name="camera" size={20} color={theme.colors.savingsText} />
              <Text style={styles.verifyText}>{t('guide.verifyCta')}</Text>
              <Ionicons name="chevron-forward" size={16} color={theme.colors.savingsText} />
            </Pressable>

            {/* Tamirciye git çıkışı */}
            <View style={styles.mechanicNote}>
              <Ionicons name="information-circle" size={16} color={theme.colors.textSecondary} />
              <Text style={styles.mechanicNoteText}>
                {TR() ? guide.mechanic_note_tr : guide.mechanic_note_en}
              </Text>
            </View>
          </ScrollView>

          {/* Bitiş kutlaması */}
          <Modal
            visible={celebrating}
            transparent
            animationType="fade"
            onRequestClose={backToGarage}
          >
            <View style={styles.celebrateBackdrop}>
              <View style={styles.celebrateCard}>
                <View style={styles.celebrateIcon}>
                  <Ionicons name="trophy" size={36} color={theme.colors.warningBright} />
                </View>
                <Text style={styles.celebrateTitle}>{t('guide.done.title')}</Text>
                <Text style={styles.celebrateDesc}>
                  {t('guide.done.desc', { task: title })}
                </Text>
                {guide.diy_saving_try > 0 && (
                  <View style={styles.celebrateSavings}>
                    <Ionicons name="trending-up" size={18} color={theme.colors.savingsText} />
                    <Text style={styles.celebrateSavingsText}>
                      {t('guide.done.savings', {
                        amount: guide.diy_saving_try.toLocaleString('tr-TR'),
                      })}
                    </Text>
                  </View>
                )}
                <Pressable
                  accessibilityRole="button"
                  onPress={() => void shareAchievement(title, guide.diy_saving_try)}
                  style={({ pressed }) => [styles.celebrateShare, pressed && styles.pressed]}
                >
                  <Ionicons name="share-social" size={18} color={theme.colors.ink} />
                  <Text style={styles.celebrateShareText}>{t('guide.done.share')}</Text>
                </Pressable>
                <Pressable
                  accessibilityRole="button"
                  onPress={backToGarage}
                  style={({ pressed }) => [styles.celebrateCta, pressed && styles.pressed]}
                >
                  <Ionicons name="home" size={18} color={theme.colors.onInk} />
                  <Text style={styles.celebrateCtaText}>{t('guide.done.cta')}</Text>
                </Pressable>
              </View>
            </View>
          </Modal>

          {/* Alt eylemler */}
          <View style={[styles.footer, { paddingBottom: insets.bottom + theme.spacing.md }]}>
            <Pressable
              accessibilityRole="button"
              accessibilityState={{ disabled: current === 0 }}
              disabled={current === 0}
              onPress={() => setCurrent((c) => Math.max(0, c - 1))}
              style={({ pressed }) => [
                styles.btnBack,
                current === 0 && styles.btnDisabled,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.btnBackText}>{t('common.back')}</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={() => void handleNext()}
              style={({ pressed }) => [styles.btnNext, pressed && styles.pressed]}
            >
              {finishing ? (
                <ActivityIndicator color={theme.colors.onInk} />
              ) : (
                <Text style={styles.btnNextText}>
                  {isLast ? t('guide.finish') : t('guide.next')}
                </Text>
              )}
            </Pressable>
          </View>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background },
  header: {
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  back: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 32,
    marginBottom: theme.spacing.xs,
  },
  backText: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.success,
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 22,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    letterSpacing: -0.3,
  },
  subtitle: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  progressRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
  },
  dot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: theme.colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dotDone: { backgroundColor: theme.colors.success },
  dotActive: { backgroundColor: theme.colors.ink },
  dotNum: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    fontWeight: '700',
    color: theme.colors.textSecondary,
  },
  dotNumActive: { color: theme.colors.onInk },
  line: {
    flex: 1,
    height: 2,
    borderRadius: 1,
    backgroundColor: theme.colors.border,
  },
  lineDone: { backgroundColor: theme.colors.success },
  scroll: {
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.lg,
  },
  warnStrip: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.warnSoftBg,
    borderLeftWidth: 3,
    borderLeftColor: theme.colors.warningBright,
    borderRadius: theme.radius.sm,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  warnText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 12,
    lineHeight: 18,
    color: theme.colors.warnSoftText,
  },
  stepCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.md,
  },
  stepNum: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    fontWeight: '700',
    color: theme.colors.success,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: theme.spacing.sm,
  },
  instruction: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    lineHeight: 24,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.md,
  },
  toolRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.background,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
  },
  toolText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  toolStrong: {
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  verifyBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    backgroundColor: theme.colors.savingsBg,
    borderWidth: 1,
    borderColor: theme.colors.savingsBorder,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  verifyText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.savingsText,
  },
  mechanicNote: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.sm,
    paddingHorizontal: theme.spacing.xs,
  },
  mechanicNoteText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 12,
    lineHeight: 18,
    color: theme.colors.textSecondary,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
  },
  errorText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  retry: {
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: theme.spacing.xl,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.ink,
  },
  retryText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.ink,
  },
  footer: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
  },
  btnBack: {
    flex: 1,
    minHeight: theme.touchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
  },
  btnBackText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.textSecondary,
  },
  btnNext: {
    flex: 2,
    minHeight: theme.touchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.ink,
  },
  btnNextText: {
    fontFamily: theme.fonts.heading,
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  btnDisabled: { opacity: 0.4 },
  pressed: { opacity: 0.85 },
  celebrateBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing.xl,
  },
  celebrateCard: {
    width: '100%',
    maxWidth: 360,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.xl,
    alignItems: 'center',
    gap: theme.spacing.md,
  },
  celebrateIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: theme.colors.warnSoftBg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  celebrateTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 22,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  celebrateDesc: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    lineHeight: 21,
  },
  celebrateSavings: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.savingsBg,
    borderWidth: 1,
    borderColor: theme.colors.savingsBorder,
    borderRadius: theme.radius.md,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
  },
  celebrateSavingsText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.savingsText,
  },
  celebrateShare: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: 48,
    alignSelf: 'stretch',
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.ink,
    marginTop: theme.spacing.sm,
  },
  celebrateShareText: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.ink,
  },
  celebrateCta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: theme.touchTarget,
    alignSelf: 'stretch',
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.ink,
    marginTop: theme.spacing.sm,
  },
  celebrateCtaText: {
    fontFamily: theme.fonts.heading,
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
});
