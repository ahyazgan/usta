import { Ionicons } from '@expo/vector-icons';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import { useRef } from 'react';
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

import { t } from '@/lib/i18n';
import { useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';
import { useDiagnose } from '@/lib/useDiagnose';
import type { DiagnoseResult, Konum } from '@/lib/api';

const CURRENT_STEP = 3;
const TOTAL_STEPS = 7;

/** Localized direction text for a 3x3 grid location code. */
function konumText(konum: Konum): string | null {
  if (konum == null) return null;
  return t(`camera.konum.${konum.replace('-', '_')}`);
}

function ResultPanel({ result }: { result: DiagnoseResult }) {
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
    </View>
  );
}

export default function CameraScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);

  const selectedTask = useUstaStore((s) => s.selectedTask);
  const { loading, error, result, runImageDiagnose } = useDiagnose();

  const progress = CURRENT_STEP / TOTAL_STEPS;
  const granted = permission?.granted === true;
  const canAskAgain = permission?.canAskAgain !== false;

  async function handleCheck() {
    const camera = cameraRef.current;
    if (!camera || loading) return;
    const photo = await camera.takePictureAsync();
    if (!photo?.uri) return;
    await runImageDiagnose(photo.uri);
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      {/* Step banner + progress */}
      <View style={styles.banner}>
        <Text style={styles.bannerStep}>
          {t('camera.stepBanner', { current: CURRENT_STEP, total: TOTAL_STEPS })}
        </Text>
        <Text style={styles.bannerTitle}>{t('camera.stepTitle')}</Text>
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${progress * 100}%` }]} />
        </View>
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
          <CameraView ref={cameraRef} style={styles.camera} facing="back" />
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
        {error ? (
          <View style={styles.errorBox}>
            <Ionicons name="cloud-offline" size={18} color={theme.colors.warning} />
            <Text style={styles.errorText}>{t(error)}</Text>
          </View>
        ) : result ? (
          <ResultPanel result={result} />
        ) : granted ? (
          <Text style={styles.feedbackHint}>{t('camera.hint')}</Text>
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
            onPress={() => router.back()}
          >
            <Text style={styles.secondaryText}>{t('common.cancel')}</Text>
          </Pressable>
          {result?.tamirciye_git_onerisi === true && (
            <Pressable
              accessibilityRole="button"
              style={({ pressed }) => [styles.mechanicButton, pressed && styles.pressed]}
              onPress={() => router.back()}
            >
              <Ionicons name="construct" size={18} color={theme.colors.background} />
              <Text style={styles.mechanicText}>{t('common.goToMechanic')}</Text>
            </Pressable>
          )}
        </View>
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
  banner: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
  },
  bannerStep: {
    fontFamily: theme.fonts.heading,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.accent,
    letterSpacing: 1,
  },
  bannerTitle: {
    fontFamily: theme.fonts.body,
    fontSize: 16,
    color: theme.colors.textPrimary,
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
    backgroundColor: theme.colors.warning,
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
    color: theme.colors.background,
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
    ...StyleSheet.absoluteFillObject,
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
