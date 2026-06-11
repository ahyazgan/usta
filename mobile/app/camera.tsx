import { Ionicons } from '@expo/vector-icons';
import { useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { t } from '@/lib/i18n';
import { theme } from '@/lib/theme';

const CURRENT_STEP = 3;
const TOTAL_STEPS = 7;

export default function CameraScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [permission, requestPermission] = useCameraPermissions();
  // Skeleton: no live stream, capture is button-driven per product spec.
  const [offline] = useState(false);

  const progress = CURRENT_STEP / TOTAL_STEPS;
  const permissionDenied = permission != null && !permission.granted && !permission.canAskAgain;

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

      {/* Camera area placeholder */}
      <View style={styles.cameraArea}>
        {permissionDenied ? (
          <Text style={styles.cameraDenied}>{t('camera.permissionDenied')}</Text>
        ) : (
          <>
            <Ionicons name="scan-outline" size={72} color={theme.colors.textSecondary} />
            <Text style={styles.cameraHint}>{t('camera.hint')}</Text>
            {permission != null && !permission.granted && permission.canAskAgain && (
              <Pressable
                accessibilityRole="button"
                style={styles.permButton}
                onPress={requestPermission}
              >
                <Text style={styles.permButtonText}>{t('common.retry')}</Text>
              </Pressable>
            )}
          </>
        )}
      </View>

      {offline && (
        <View style={styles.offlineBar}>
          <Ionicons name="cloud-offline" size={16} color={theme.colors.warning} />
          <Text style={styles.offlineText}>{t('camera.offline')}</Text>
        </View>
      )}

      {/* Actions */}
      <View style={[styles.actions, { paddingBottom: insets.bottom + theme.spacing.lg }]}>
        <Pressable
          accessibilityRole="button"
          style={({ pressed }) => [styles.checkButton, pressed && styles.pressed]}
        >
          <Ionicons name="checkmark-circle" size={22} color={theme.colors.background} />
          <Text style={styles.checkText}>{t('camera.check')}</Text>
        </Pressable>

        <View style={styles.secondaryRow}>
          <Pressable
            accessibilityRole="button"
            style={({ pressed }) => [styles.secondaryButton, pressed && styles.pressed]}
            onPress={() => router.back()}
          >
            <Text style={styles.secondaryText}>{t('common.cancel')}</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            style={({ pressed }) => [styles.secondaryButton, pressed && styles.pressed]}
            onPress={() => router.back()}
          >
            <Text style={[styles.secondaryText, styles.mechanicText]}>
              {t('common.goToMechanic')}
            </Text>
          </Pressable>
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
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing.xl,
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
  offlineBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.md,
  },
  offlineText: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.warning,
  },
  actions: {
    paddingTop: theme.spacing.lg,
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
  mechanicText: {
    color: theme.colors.textPrimary,
  },
  pressed: {
    opacity: 0.85,
  },
});
