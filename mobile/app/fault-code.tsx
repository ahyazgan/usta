import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
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

import { FeedbackRow } from '@/components/FeedbackRow';
import type { Aciliyet } from '@/lib/api';
import { t } from '@/lib/i18n';
import { goBack } from '@/lib/nav';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';
import { useDtc } from '@/lib/useDtc';

/** Aciliyet → yumuşak rozet paleti. */
function urgencyPalette(a: Aciliyet): { bg: string; fg: string } {
  if (a === 'yuksek') return { bg: theme.colors.urgentSoftBg, fg: theme.colors.urgentSoftText };
  if (a === 'orta') return { bg: theme.colors.warnSoftBg, fg: theme.colors.warnSoftText };
  return { bg: theme.colors.okSoftBg, fg: theme.colors.okSoftText };
}

export default function FaultCodeScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const vehicle = useUstaStore(selectCurrentVehicle);
  const { loading, error, result, runDtc, reset } = useDtc();

  const [code, setCode] = useState('');
  const [note, setNote] = useState('');

  function handleNew() {
    reset();
    setCode('');
    setNote('');
  }

  const drivableText =
    result == null
      ? null
      : result.surulebilir_mi === true
        ? t('dtc.drivable.yes')
        : result.surulebilir_mi === false
          ? t('dtc.drivable.no')
          : t('dtc.drivable.unknown');

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
        <Text style={styles.title}>{t('dtc.title')}</Text>
        <View style={styles.backSpacer} />
      </View>

      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {result == null ? (
          <>
            <Text style={styles.intro}>{t('dtc.intro')}</Text>
            <Text style={styles.label}>{t('dtc.codeLabel')}</Text>
            <TextInput
              style={styles.codeInput}
              value={code}
              onChangeText={(v) => setCode(v.toUpperCase())}
              placeholder={t('dtc.codePlaceholder')}
              placeholderTextColor={theme.colors.textSecondary}
              autoCapitalize="characters"
              autoCorrect={false}
              maxLength={10}
            />
            <Text style={styles.label}>{t('dtc.noteLabel')}</Text>
            <TextInput
              style={styles.noteInput}
              value={note}
              onChangeText={setNote}
              placeholder={t('dtc.notePlaceholder')}
              placeholderTextColor={theme.colors.textSecondary}
              multiline
            />
            <Text style={styles.disclaimer}>{t('dtc.disclaimer')}</Text>
          </>
        ) : (
          <>
            <View style={styles.codeChip}>
              <Ionicons name="barcode-outline" size={16} color={theme.colors.onInk} />
              <Text style={styles.codeChipText}>{result.kod}</Text>
            </View>
            <Text style={styles.baslik}>{result.baslik}</Text>
            <Text style={styles.tespit}>{result.tespit}</Text>

            <View style={styles.metaRow}>
              <View style={[styles.urgencyBadge, { backgroundColor: urgencyPalette(result.aciliyet).bg }]}>
                <Text style={[styles.urgencyText, { color: urgencyPalette(result.aciliyet).fg }]}>
                  {t(`dashboard.urgency.${result.aciliyet}`)}
                </Text>
              </View>
              {drivableText != null && <Text style={styles.drivable}>{drivableText}</Text>}
            </View>

            {result.olasi_nedenler.length > 0 && (
              <View style={styles.causesBox}>
                <Text style={styles.causesTitle}>{t('dtc.causes')}</Text>
                {result.olasi_nedenler.map((c, i) => (
                  <View key={i} style={styles.causeRow}>
                    <Text style={styles.causeBullet}>•</Text>
                    <Text style={styles.causeText}>{c}</Text>
                  </View>
                ))}
              </View>
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

            {vehicle != null && result.session_id != null && (
              <View style={styles.feedbackWrap}>
                <FeedbackRow vehicleId={vehicle.id} sessionId={result.session_id} />
              </View>
            )}
          </>
        )}
      </ScrollView>

      <View style={[styles.footer, { paddingBottom: insets.bottom + theme.spacing.md }]}>
        {error != null && <Text style={styles.errorText}>{t(error)}</Text>}
        {result != null ? (
          <Pressable
            accessibilityRole="button"
            onPress={handleNew}
            style={({ pressed }) => [styles.submitBtn, pressed && styles.pressed]}
          >
            <Ionicons name="refresh" size={20} color={theme.colors.onInk} />
            <Text style={styles.submitText}>{t('dtc.another')}</Text>
          </Pressable>
        ) : (
          <Pressable
            accessibilityRole="button"
            disabled={loading || code.trim().length < 2}
            onPress={() => void runDtc(code, note)}
            style={({ pressed }) => [
              styles.submitBtn,
              (loading || code.trim().length < 2) && styles.disabled,
              pressed && styles.pressed,
            ]}
          >
            {loading ? (
              <>
                <ActivityIndicator color={theme.colors.onInk} />
                <Text style={styles.submitText}>{t('camera.analyzing')}</Text>
              </>
            ) : (
              <>
                <Ionicons name="search" size={20} color={theme.colors.onInk} />
                <Text style={styles.submitText}>{t('dtc.explain')}</Text>
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
  title: { fontFamily: theme.fonts.heading, fontSize: 18, fontWeight: '700', color: theme.colors.textPrimary },
  scroll: { paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.md, paddingBottom: theme.spacing.xl, gap: theme.spacing.sm },
  intro: { fontFamily: theme.fonts.body, fontSize: 14, lineHeight: 20, color: theme.colors.textSecondary, marginBottom: theme.spacing.sm },
  label: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    fontWeight: '700',
    color: theme.colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: theme.spacing.md,
    marginBottom: theme.spacing.xs,
  },
  codeInput: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingHorizontal: theme.spacing.lg,
    fontFamily: theme.fonts.heading,
    fontSize: 22,
    fontWeight: '700',
    letterSpacing: 2,
    color: theme.colors.textPrimary,
  },
  noteInput: {
    minHeight: 72,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.md,
    fontFamily: theme.fonts.body,
    fontSize: 15,
    color: theme.colors.textPrimary,
    textAlignVertical: 'top',
  },
  disclaimer: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    lineHeight: 17,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.md,
  },
  codeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    alignSelf: 'flex-start',
    backgroundColor: theme.colors.ink,
    borderRadius: theme.radius.sm,
    paddingVertical: 4,
    paddingHorizontal: theme.spacing.md,
  },
  codeChipText: { fontFamily: theme.fonts.heading, fontSize: 15, fontWeight: '700', letterSpacing: 1, color: theme.colors.onInk },
  baslik: { fontFamily: theme.fonts.heading, fontSize: 20, fontWeight: '700', color: theme.colors.textPrimary, marginTop: theme.spacing.sm, letterSpacing: -0.3 },
  tespit: { fontFamily: theme.fonts.body, fontSize: 14, lineHeight: 20, color: theme.colors.textPrimary, marginTop: theme.spacing.xs },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: theme.spacing.md, marginTop: theme.spacing.sm },
  urgencyBadge: { borderRadius: theme.radius.pill, paddingVertical: 3, paddingHorizontal: theme.spacing.md },
  urgencyText: { fontFamily: theme.fonts.body, fontSize: 11, fontWeight: '700' },
  drivable: { flex: 1, fontFamily: theme.fonts.body, fontSize: 13, fontWeight: '600', color: theme.colors.textSecondary },
  causesBox: {
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    marginTop: theme.spacing.md,
    gap: theme.spacing.xs,
  },
  causesTitle: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    fontWeight: '700',
    color: theme.colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: theme.spacing.xs,
  },
  causeRow: { flexDirection: 'row', gap: theme.spacing.sm },
  causeBullet: { fontFamily: theme.fonts.body, fontSize: 14, color: theme.colors.textSecondary },
  causeText: { flex: 1, fontFamily: theme.fonts.body, fontSize: 14, lineHeight: 20, color: theme.colors.textPrimary },
  warningBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.danger,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    marginTop: theme.spacing.md,
  },
  warningText: { flex: 1, fontFamily: theme.fonts.body, fontSize: 13, lineHeight: 19, color: theme.colors.background },
  nextRow: { marginTop: theme.spacing.md, gap: 2 },
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
  submitBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.ink,
  },
  submitText: { fontFamily: theme.fonts.heading, fontSize: 17, fontWeight: '700', color: theme.colors.onInk },
  disabled: { opacity: 0.4 },
  pressed: { opacity: 0.85 },
});
