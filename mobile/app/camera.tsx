import { Ionicons } from '@expo/vector-icons';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';

import { goBack } from '@/lib/nav';
import { useRef, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type ViewStyle,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { CameraGrid } from '@/components/CameraGrid';
import { FeedbackRow } from '@/components/FeedbackRow';
import { MechanicBriefSheet } from '@/components/MechanicBriefSheet';
import { i18n, t } from '@/lib/i18n';
import { type BriefDiag } from '@/lib/mechanicBrief';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';
import { useDiagnose } from '@/lib/useDiagnose';
import type { DiagnoseResult, Konum, Task } from '@/lib/api';

/** Localized task title for the banner. */
function taskTitle(task: Task): string {
  return i18n.locale === 'en' ? task.title_en : task.title_tr;
}

/** Localized direction text for a 3x3 grid location code. */
function konumText(konum: Konum): string | null {
  if (konum == null) return null;
  return t(`camera.konum.${konum.replace('-', '_')}`);
}

function ResultPanel({
  result,
  vehicleId,
  onShowMechanic,
}: {
  result: DiagnoseResult;
  vehicleId: number | null;
  onShowMechanic: () => void;
}) {
  // Banner color is the ONLY place green may appear: dogru_yer_mi === true.
  let bannerStyle: ViewStyle = styles.bannerNeutral;
  let bannerText = t('camera.result.uncertain');
  let bannerIcon: keyof typeof Ionicons.glyphMap = 'help-circle';

  if (result.dogru_yer_mi === true) {
    bannerStyle = styles.bannerSuccess;
    bannerText = t('camera.result.correct');
    bannerIcon = 'checkmark-circle';
  } else if (result.dogru_yer_mi === false) {
    bannerStyle = styles.bannerWrong;
    bannerText = t('camera.result.wrong');
    bannerIcon = 'close-circle';
  }

  const hint = result.dogru_yer_mi === false ? konumText(result.konum_tarifi) : null;

  return (
    <View style={styles.resultPanel}>
      <View style={[styles.resultBanner, bannerStyle]}>
        <Ionicons name={bannerIcon} size={22} color={theme.colors.background} />
        <Text style={styles.resultBannerText}>{bannerText}</Text>
      </View>

      {hint && (
        <Text style={styles.locationHint}>
          {t('camera.result.locationHint', { yon: hint })}
        </Text>
      )}

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('camera.result.tespit')}</Text>
        <Text style={styles.resultValue}>{result.tespit}</Text>
      </View>

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('camera.result.guven')}</Text>
        <Text style={styles.resultValue}>{t(`camera.guven.${result.guven}`)}</Text>
      </View>

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('camera.result.sonrakiAdim')}</Text>
        <Text style={styles.resultValue}>{result.sonraki_adim}</Text>
      </View>

      {result.guvenlik_uyarisi != null && (
        <View style={styles.warningBox}>
          <Ionicons name="warning" size={18} color={theme.colors.background} />
          <Text style={styles.warningText}>{result.guvenlik_uyarisi}</Text>
        </View>
      )}

      {/* Triyaj köprüsü: kendin yapmayacaksan tamirciye göster */}
      <Pressable
        accessibilityRole="button"
        onPress={onShowMechanic}
        style={({ pressed }) => [styles.mechanicBrief, pressed && styles.pressed]}
      >
        <Ionicons name="construct-outline" size={18} color={theme.colors.ink} />
        <Text style={styles.mechanicBriefText}>{t('brief.cta')}</Text>
        <Ionicons name="chevron-forward" size={16} color={theme.colors.textSecondary} />
      </Pressable>

      {/* Veri çarkı: teşhis doğru çıktı mı? */}
      {vehicleId != null && result.session_id != null && (
        <View style={styles.feedbackWrap}>
          <FeedbackRow vehicleId={vehicleId} sessionId={result.session_id} />
        </View>
      )}
    </View>
  );
}

export default function CameraScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);

  const selectedTask = useUstaStore((s) => s.selectedTask);
  const guideProgress = useUstaStore((s) => s.guideProgress);
  const currentVehicle = useUstaStore(selectCurrentVehicle);
  const { loading, error, result, runImageDiagnose } = useDiagnose();
  const [briefOpen, setBriefOpen] = useState(false);
  // Local: a failed takePictureAsync (camera busy / hardware) never reaches
  // the diagnose hook, so surface it here in the same error slot.
  const [captureError, setCaptureError] = useState<string | null>(null);

  const briefDiag: BriefDiag | null = result
    ? {
        kindLabel: t('brief.kindImage'),
        tespit: result.tespit,
        taskLabel: selectedTask ? taskTitle(selectedTask) : undefined,
        guven: result.guven,
        sonrakiAdim: result.sonraki_adim,
        guvenlikUyarisi: result.guvenlik_uyarisi,
        sessionId: result.session_id ?? undefined,
        costLow: result.cost_estimate?.low_try ?? undefined,
        costHigh: result.cost_estimate?.high_try ?? undefined,
      }
    : null;

  // Rehberden gelindiyse kaldığı adım (1 bazlı) banner'da görünür.
  const guideStep =
    selectedTask != null && guideProgress[selectedTask.id] != null
      ? guideProgress[selectedTask.id] + 1
      : null;

  const granted = permission?.granted === true;
  const canAskAgain = permission?.canAskAgain !== false;

  async function handleCheck() {
    const camera = cameraRef.current;
    if (!camera || loading) return;
    setCaptureError(null);
    let uri: string | undefined;
    try {
      const photo = await camera.takePictureAsync({ quality: 0.6, skipProcessing: true });
      uri = photo?.uri;
    } catch {
      setCaptureError('camera.error.captureFailed');
      return;
    }
    if (!uri) {
      setCaptureError('camera.error.captureFailed');
      return;
    }
    await runImageDiagnose(uri);
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      {/* Görev banner'ı */}
      <View style={styles.banner}>
        <View style={styles.bannerTopRow}>
          <Text style={styles.bannerStep}>{t('camera.taskLabel')}</Text>
          {guideStep != null && (
            <View style={styles.stepChip}>
              <Text style={styles.stepChipText}>
                {t('camera.guideStep', { step: guideStep })}
              </Text>
            </View>
          )}
        </View>
        <Text style={styles.bannerTitle}>
          {selectedTask ? taskTitle(selectedTask) : t('camera.stepTitle')}
        </Text>
        <Text style={styles.bannerHint}>{t('camera.hint')}</Text>
      </View>

      {/* Persistent safety strip */}
      <View style={styles.safetyStrip}>
        <Ionicons name="warning" size={18} color={theme.colors.background} />
        <Text style={styles.safetyText}>{t('camera.safetyStrip')}</Text>
      </View>

      {/* Camera area */}
      <View style={styles.cameraArea}>
        {permission == null ? (
          <ActivityIndicator color={theme.colors.accent} />
        ) : granted ? (
          <>
            <CameraView ref={cameraRef} style={styles.camera} facing="back" />
            <CameraGrid />
          </>
        ) : canAskAgain ? (
          <>
            <Ionicons name="camera-outline" size={72} color={theme.colors.textSecondary} />
            <Text style={styles.cameraHint}>{t('camera.permissionRequest')}</Text>
            <Pressable
              accessibilityRole="button"
              style={styles.permButton}
              onPress={requestPermission}
            >
              <Text style={styles.permButtonText}>{t('camera.grantPermission')}</Text>
            </Pressable>
          </>
        ) : (
          <>
            <Text style={styles.cameraDenied}>{t('camera.permissionDenied')}</Text>
            <Pressable
              accessibilityRole="button"
              style={styles.permButton}
              onPress={requestPermission}
            >
              <Text style={styles.permButtonText}>{t('common.retry')}</Text>
            </Pressable>
          </>
        )}
      </View>

      {/* Result / error / hint area */}
      <ScrollView
        style={styles.feedbackScroll}
        contentContainerStyle={styles.feedbackContent}
        showsVerticalScrollIndicator={false}
      >
        {error || captureError ? (
          <View style={styles.errorBox}>
            <Ionicons name="cloud-offline" size={18} color={theme.colors.warning} />
            <Text style={styles.errorText}>{t(captureError ?? error!)}</Text>
          </View>
        ) : result ? (
          <ResultPanel
            result={result}
            vehicleId={currentVehicle?.id ?? null}
            onShowMechanic={() => setBriefOpen(true)}
          />
        ) : granted ? (
          <Text style={styles.feedbackHint}>{t('camera.gridHint')}</Text>
        ) : null}
      </ScrollView>

      {/* Actions */}
      <View style={[styles.actions, { paddingBottom: insets.bottom + theme.spacing.lg }]}>
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled: !granted || loading || !selectedTask }}
          disabled={!granted || loading || !selectedTask}
          onPress={handleCheck}
          style={({ pressed }) => [
            styles.checkButton,
            (!granted || loading || !selectedTask) && styles.checkDisabled,
            pressed && styles.pressed,
          ]}
        >
          {loading ? (
            <>
              <ActivityIndicator color={theme.colors.background} />
              <Text style={styles.checkText}>{t('camera.analyzing')}</Text>
            </>
          ) : (
            <>
              <Ionicons name="checkmark-circle" size={22} color={theme.colors.background} />
              <Text style={styles.checkText}>{t('camera.check')}</Text>
            </>
          )}
        </Pressable>

        <View style={styles.secondaryRow}>
          <Pressable
            accessibilityRole="button"
            style={({ pressed }) => [styles.secondaryButton, pressed && styles.pressed]}
            onPress={() => goBack(router)}
          >
            <Text style={styles.secondaryText}>{t('common.cancel')}</Text>
          </Pressable>
          {result?.tamirciye_git_onerisi === true && (
            <Pressable
              accessibilityRole="button"
              style={({ pressed }) => [styles.mechanicButton, pressed && styles.pressed]}
              onPress={() => setBriefOpen(true)}
            >
              <Ionicons name="construct" size={18} color={theme.colors.background} />
              <Text style={styles.mechanicText}>{t('common.goToMechanic')}</Text>
            </Pressable>
          )}
        </View>
      </View>

      <MechanicBriefSheet
        visible={briefOpen}
        vehicle={currentVehicle}
        diag={briefDiag}
        onClose={() => setBriefOpen(false)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
    paddingHorizontal: theme.spacing.lg,
  },
  banner: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
  },
  bannerTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  bannerStep: {
    fontFamily: theme.fonts.heading,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.accent,
    letterSpacing: 1,
  },
  stepChip: {
    backgroundColor: theme.colors.okSoftBg,
    borderRadius: theme.radius.pill,
    paddingVertical: 3,
    paddingHorizontal: theme.spacing.md,
  },
  stepChipText: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    fontWeight: '700',
    color: theme.colors.okSoftText,
  },
  bannerTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 20,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    marginTop: theme.spacing.xs,
  },
  bannerHint: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
  },
  progressTrack: {
    height: 6,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.colors.border,
    marginTop: theme.spacing.md,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: theme.radius.pill,
    backgroundColor: theme.colors.accent,
  },
  safetyStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.warningBright,
    borderRadius: theme.radius.sm,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    marginTop: theme.spacing.md,
  },
  safetyText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 12,
    fontWeight: '600',
    color: theme.colors.ink,
  },
  cameraArea: {
    flex: 1,
    marginTop: theme.spacing.lg,
    borderRadius: theme.radius.lg,
    borderWidth: 2,
    borderColor: theme.colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    padding: theme.spacing.xl,
  },
  camera: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  cameraHint: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginTop: theme.spacing.md,
  },
  cameraDenied: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.danger,
    textAlign: 'center',
  },
  permButton: {
    minHeight: theme.touchTarget,
    marginTop: theme.spacing.lg,
    paddingHorizontal: theme.spacing.xl,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  permButtonText: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '600',
    color: theme.colors.accent,
  },
  feedbackScroll: {
    maxHeight: 220,
    marginTop: theme.spacing.md,
  },
  feedbackContent: {
    paddingBottom: theme.spacing.sm,
  },
  feedbackHint: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    paddingVertical: theme.spacing.md,
  },
  errorText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.warning,
    textAlign: 'center',
  },
  resultPanel: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
  },
  resultBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    borderRadius: theme.radius.sm,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.md,
  },
  bannerSuccess: {
    backgroundColor: theme.colors.success,
  },
  bannerWrong: {
    backgroundColor: theme.colors.danger,
  },
  bannerNeutral: {
    backgroundColor: theme.colors.accent,
  },
  resultBannerText: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.background,
  },
  locationHint: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.danger,
    marginTop: theme.spacing.md,
  },
  resultRow: {
    marginTop: theme.spacing.md,
  },
  resultLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  resultValue: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    color: theme.colors.textPrimary,
    marginTop: 2,
  },
  warningBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.warning,
    borderRadius: theme.radius.sm,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.md,
    marginTop: theme.spacing.lg,
  },
  feedbackWrap: {
    marginTop: theme.spacing.md,
    paddingTop: theme.spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: theme.colors.border,
  },
  mechanicBrief: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.md,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.ink,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.md,
  },
  mechanicBriefText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.ink,
  },
  warningText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.background,
  },
  actions: {
    paddingTop: theme.spacing.md,
  },
  checkButton: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.accent,
    borderRadius: theme.radius.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
  },
  checkDisabled: {
    opacity: 0.4,
  },
  checkText: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.background,
  },
  secondaryRow: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginTop: theme.spacing.md,
  },
  secondaryButton: {
    flex: 1,
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryText: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '600',
    color: theme.colors.textSecondary,
  },
  mechanicButton: {
    flex: 1,
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.accent,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
  },
  mechanicText: {
    fontFamily: theme.fonts.heading,
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.background,
  },
  pressed: {
    opacity: 0.85,
  },
});
