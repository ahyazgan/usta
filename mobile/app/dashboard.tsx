import { Ionicons } from '@expo/vector-icons';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import { useRef, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { CameraGrid } from '@/components/CameraGrid';
import { FeedbackRow } from '@/components/FeedbackRow';
import type { Aciliyet, DashboardLight, DashboardRenk } from '@/lib/api';
import { t } from '@/lib/i18n';
import { goBack } from '@/lib/nav';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';
import { useDashboard } from '@/lib/useDashboard';

/** Uyarı ışığı rengi → ekran rengi. */
const RENK_COLOR: Record<DashboardRenk, string> = {
  kirmizi: theme.colors.danger,
  sari: theme.colors.warningBright,
  yesil: theme.colors.success,
  mavi: '#2E6BC0',
  bilinmiyor: theme.colors.textSecondary,
};

/** Aciliyet → yumuşak rozet paleti. */
function urgencyPalette(a: Aciliyet): { bg: string; fg: string } {
  if (a === 'yuksek') return { bg: theme.colors.urgentSoftBg, fg: theme.colors.urgentSoftText };
  if (a === 'orta') return { bg: theme.colors.warnSoftBg, fg: theme.colors.warnSoftText };
  return { bg: theme.colors.okSoftBg, fg: theme.colors.okSoftText };
}

function LightCard({ light }: { light: DashboardLight }) {
  const palette = urgencyPalette(light.aciliyet);
  return (
    <View style={styles.lightCard}>
      <View style={styles.lightHeader}>
        <View style={[styles.renkDot, { backgroundColor: RENK_COLOR[light.renk] }]} />
        <Text style={styles.lightName}>{light.isim}</Text>
        <View style={[styles.urgencyBadge, { backgroundColor: palette.bg }]}>
          <Text style={[styles.urgencyBadgeText, { color: palette.fg }]}>
            {t(`dashboard.urgency.${light.aciliyet}`)}
          </Text>
        </View>
      </View>
      <Text style={styles.lightMeaning}>{light.anlam}</Text>
      <View style={styles.whatToDoRow}>
        <Ionicons name="arrow-forward-circle-outline" size={16} color={theme.colors.textSecondary} />
        <Text style={styles.whatToDoText}>{light.ne_yapmali}</Text>
      </View>
    </View>
  );
}

export default function DashboardScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const vehicle = useUstaStore(selectCurrentVehicle);
  const { loading, error, result, runDashboard, reset } = useDashboard();
  // Local: a failed takePictureAsync never reaches the diagnose hook.
  const [captureError, setCaptureError] = useState<string | null>(null);

  const granted = permission?.granted === true;
  const canAskAgain = permission?.canAskAgain !== false;

  async function handleScan() {
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
    await runDashboard(uri);
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      {/* Başlık */}
      <View style={styles.header}>
        <Pressable
          accessibilityRole="button"
          onPress={() => goBack(router)}
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Ionicons name="chevron-back" size={22} color={theme.colors.textPrimary} />
          <Text style={styles.backText}>{t('common.back')}</Text>
        </Pressable>
        <Text style={styles.title}>{t('dashboard.title')}</Text>
        <View style={styles.backSpacer} />
      </View>

      {/* Güvenlik şeridi */}
      <View style={styles.safetyStrip}>
        <Ionicons name="warning" size={16} color={theme.colors.background} />
        <Text style={styles.safetyText}>{t('dashboard.safetyStrip')}</Text>
      </View>

      {result == null ? (
        // --- Kamera / tarama ---
        <View style={styles.cameraArea}>
          {permission == null ? (
            <ActivityIndicator color={theme.colors.ink} />
          ) : granted ? (
            <>
              <CameraView ref={cameraRef} style={styles.camera} facing="back" />
              <CameraGrid />
            </>
          ) : canAskAgain ? (
            <>
              <Ionicons name="camera-outline" size={64} color={theme.colors.textSecondary} />
              <Text style={styles.cameraHint}>{t('camera.permissionRequest')}</Text>
              <Pressable
                accessibilityRole="button"
                onPress={() => void requestPermission()}
                style={({ pressed }) => [styles.cta, pressed && styles.pressed]}
              >
                <Text style={styles.ctaText}>{t('camera.grantPermission')}</Text>
              </Pressable>
            </>
          ) : (
            <>
              <Ionicons name="camera-outline" size={64} color={theme.colors.textSecondary} />
              <Text style={styles.cameraHint}>{t('camera.permissionDenied')}</Text>
            </>
          )}
        </View>
      ) : (
        // --- Sonuç ---
        <ScrollView contentContainerStyle={styles.results} showsVerticalScrollIndicator={false}>
          <Text style={styles.tespit}>{result.tespit}</Text>
          <Text style={styles.guven}>{t(`camera.guven.${result.guven}`)}</Text>

          {result.isiklar.length === 0 ? (
            <View style={styles.noLights}>
              <Ionicons name="help-circle-outline" size={22} color={theme.colors.textSecondary} />
              <Text style={styles.noLightsText}>{t('dashboard.noLights')}</Text>
            </View>
          ) : (
            result.isiklar.map((light, i) => <LightCard key={`${light.isim}-${i}`} light={light} />)
          )}

          {result.guvenlik_uyarisi != null && (
            <View style={styles.warningBox}>
              <Ionicons name="warning" size={18} color={theme.colors.background} />
              <Text style={styles.warningText}>{result.guvenlik_uyarisi}</Text>
            </View>
          )}

          <View style={styles.nextRow}>
            <Text style={styles.nextLabel}>{t('camera.result.sonrakiAdim')}</Text>
            <Text style={styles.nextText}>{result.sonraki_adim}</Text>
          </View>

          {result.tamirciye_git_onerisi && (
            <Pressable
              accessibilityRole="button"
              onPress={() => router.push('/mechanics')}
              style={({ pressed }) => [styles.mechanicCta, pressed && styles.pressed]}
            >
              <Ionicons name="construct-outline" size={18} color={theme.colors.onInk} />
              <Text style={styles.mechanicCtaText}>{t('dashboard.findMechanic')}</Text>
            </Pressable>
          )}

          {/* Veri çarkı: teşhis doğru çıktı mı? */}
          {vehicle != null && result.session_id != null && (
            <View style={styles.feedbackWrap}>
              <FeedbackRow vehicleId={vehicle.id} sessionId={result.session_id} />
            </View>
          )}
        </ScrollView>
      )}

      {/* Alt eylem */}
      <View style={[styles.footer, { paddingBottom: insets.bottom + theme.spacing.md }]}>
        {(captureError ?? error) != null && (
          <Text style={styles.errorText}>{t(captureError ?? error!)}</Text>
        )}
        {result != null ? (
          <Pressable
            accessibilityRole="button"
            onPress={reset}
            style={({ pressed }) => [styles.scanBtn, pressed && styles.pressed]}
          >
            <Ionicons name="refresh" size={20} color={theme.colors.onInk} />
            <Text style={styles.scanBtnText}>{t('dashboard.retake')}</Text>
          </Pressable>
        ) : (
          <Pressable
            accessibilityRole="button"
            disabled={!granted || loading}
            onPress={() => void handleScan()}
            style={({ pressed }) => [
              styles.scanBtn,
              (!granted || loading) && styles.disabled,
              pressed && styles.pressed,
            ]}
          >
            {loading ? (
              <>
                <ActivityIndicator color={theme.colors.onInk} />
                <Text style={styles.scanBtnText}>{t('camera.analyzing')}</Text>
              </>
            ) : (
              <>
                <Ionicons name="scan" size={20} color={theme.colors.onInk} />
                <Text style={styles.scanBtnText}>{t('dashboard.scan')}</Text>
              </>
            )}
          </Pressable>
        )}
      </View>
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
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  safetyStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginHorizontal: theme.spacing.lg,
    marginTop: theme.spacing.sm,
    backgroundColor: theme.colors.warning,
    borderRadius: theme.radius.sm,
    paddingVertical: 8,
    paddingHorizontal: theme.spacing.md,
  },
  safetyText: { flex: 1, fontFamily: theme.fonts.body, fontSize: 12, color: theme.colors.background },
  cameraArea: {
    flex: 1,
    margin: theme.spacing.lg,
    borderRadius: theme.radius.lg,
    overflow: 'hidden',
    backgroundColor: '#000',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.md,
    padding: theme.spacing.xl,
  },
  camera: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 },
  cameraHint: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  results: {
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.md,
    paddingBottom: theme.spacing.xl,
    gap: theme.spacing.sm,
  },
  tespit: {
    fontFamily: theme.fonts.heading,
    fontSize: 20,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    letterSpacing: -0.3,
  },
  guven: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
  },
  noLights: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.md,
    padding: theme.spacing.lg,
  },
  noLightsText: { flex: 1, fontFamily: theme.fonts.body, fontSize: 13, color: theme.colors.textSecondary },
  lightCard: {
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  lightHeader: { flexDirection: 'row', alignItems: 'center', gap: theme.spacing.sm },
  renkDot: { width: 14, height: 14, borderRadius: 7 },
  lightName: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  urgencyBadge: { borderRadius: theme.radius.pill, paddingVertical: 2, paddingHorizontal: theme.spacing.sm },
  urgencyBadgeText: { fontFamily: theme.fonts.body, fontSize: 10, fontWeight: '700' },
  lightMeaning: { fontFamily: theme.fonts.body, fontSize: 13, lineHeight: 19, color: theme.colors.textPrimary },
  whatToDoRow: { flexDirection: 'row', alignItems: 'flex-start', gap: theme.spacing.xs },
  whatToDoText: { flex: 1, fontFamily: theme.fonts.body, fontSize: 13, lineHeight: 19, color: theme.colors.textSecondary },
  warningBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.danger,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    marginTop: theme.spacing.xs,
  },
  warningText: { flex: 1, fontFamily: theme.fonts.body, fontSize: 13, lineHeight: 19, color: theme.colors.background },
  nextRow: { marginTop: theme.spacing.sm, gap: 2 },
  nextLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    fontWeight: '700',
    color: theme.colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  nextText: { fontFamily: theme.fonts.body, fontSize: 14, lineHeight: 20, color: theme.colors.textPrimary },
  mechanicCta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.ink,
    marginTop: theme.spacing.md,
  },
  mechanicCtaText: { fontFamily: theme.fonts.heading, fontSize: 16, fontWeight: '700', color: theme.colors.onInk },
  feedbackWrap: { marginTop: theme.spacing.md },
  footer: { paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.sm, gap: theme.spacing.sm },
  errorText: { fontFamily: theme.fonts.body, fontSize: 12, color: theme.colors.dangerBright, textAlign: 'center' },
  scanBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.ink,
  },
  scanBtnText: { fontFamily: theme.fonts.heading, fontSize: 17, fontWeight: '700', color: theme.colors.onInk },
  cta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: theme.touchTarget,
    paddingHorizontal: theme.spacing.xl,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.ink,
  },
  ctaText: { fontFamily: theme.fonts.heading, fontSize: 16, fontWeight: '700', color: theme.colors.onInk },
  disabled: { opacity: 0.4 },
  pressed: { opacity: 0.85 },
});
