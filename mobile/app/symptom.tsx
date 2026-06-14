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
import { useSymptom } from '@/lib/useSymptom';

/** Hızlı başlangıç örnekleri. */
const EXAMPLE_KEYS = ['idle', 'brake', 'start', 'noise'] as const;

function urgencyPalette(a: Aciliyet): { bg: string; fg: string } {
  if (a === 'yuksek') return { bg: theme.colors.urgentSoftBg, fg: theme.colors.urgentSoftText };
  if (a === 'orta') return { bg: theme.colors.warnSoftBg, fg: theme.colors.warnSoftText };
  return { bg: theme.colors.okSoftBg, fg: theme.colors.okSoftText };
}

export default function SymptomScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const vehicle = useUstaStore(selectCurrentVehicle);
  const { loading, error, result, runSymptom, reset } = useSymptom();
  const [text, setText] = useState('');

  function handleNew() {
    reset();
    setText('');
  }

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
        <Text style={styles.title}>{t('symptom.title')}</Text>
        <View style={styles.backSpacer} />
      </View>

      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {result == null ? (
          <>
            <Text style={styles.intro}>{t('symptom.intro')}</Text>
            <TextInput
              style={styles.input}
              value={text}
              onChangeText={setText}
              placeholder={t('symptom.placeholder')}
              placeholderTextColor={theme.colors.textSecondary}
              multiline
              maxLength={600}
              autoFocus
            />
            <Text style={styles.examplesTitle}>{t('symptom.examplesTitle')}</Text>
            <View style={styles.examplesRow}>
              {EXAMPLE_KEYS.map((k) => {
                const ex = t(`symptom.examples.${k}`);
                return (
                  <Pressable
                    key={k}
                    accessibilityRole="button"
                    onPress={() => setText(ex)}
                    style={({ pressed }) => [styles.exampleChip, pressed && styles.pressed]}
                  >
                    <Text style={styles.exampleChipText}>{ex}</Text>
                  </Pressable>
                );
              })}
            </View>
            <Text style={styles.disclaimer}>{t('symptom.disclaimer')}</Text>
          </>
        ) : (
          <>
            <Text style={styles.tespit}>{result.tespit}</Text>
            <View style={styles.metaRow}>
              <View style={styles.sistemPill}>
                <Text style={styles.sistemPillText}>{t(`sistem.${result.ariza_sistem}`)}</Text>
              </View>
              <View style={[styles.urgencyBadge, { backgroundColor: urgencyPalette(result.aciliyet).bg }]}>
                <Text style={[styles.urgencyText, { color: urgencyPalette(result.aciliyet).fg }]}>
                  {t(`dashboard.urgency.${result.aciliyet}`)}
                </Text>
              </View>
              <Text style={styles.guven}>{t(`camera.guven.${result.guven}`)}</Text>
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

            {result.cost_estimate != null && (
              <View style={styles.costBox}>
                <Ionicons name="pricetag-outline" size={16} color={theme.colors.savingsText} />
                <Text style={styles.costText}>
                  {t('symptom.cost', {
                    low: result.cost_estimate.low_try.toLocaleString('tr-TR'),
                    high: result.cost_estimate.high_try.toLocaleString('tr-TR'),
                  })}
                </Text>
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
            <Text style={styles.submitText}>{t('symptom.another')}</Text>
          </Pressable>
        ) : (
          <Pressable
            accessibilityRole="button"
            disabled={loading || text.trim().length < 3}
            onPress={() => void runSymptom(text)}
            style={({ pressed }) => [
              styles.submitBtn,
              (loading || text.trim().length < 3) && styles.disabled,
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
                <Ionicons name="sparkles" size={20} color={theme.colors.onInk} />
                <Text style={styles.submitText}>{t('symptom.diagnose')}</Text>
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
  input: {
    minHeight: 110,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.md,
    fontFamily: theme.fonts.body,
    fontSize: 16,
    lineHeight: 22,
    color: theme.colors.textPrimary,
    textAlignVertical: 'top',
  },
  examplesTitle: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    fontWeight: '700',
    color: theme.colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: theme.spacing.md,
  },
  examplesRow: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.spacing.sm, marginTop: theme.spacing.xs },
  exampleChip: {
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.pill,
    paddingVertical: 6,
    paddingHorizontal: theme.spacing.md,
  },
  exampleChipText: { fontFamily: theme.fonts.body, fontSize: 13, color: theme.colors.textPrimary },
  disclaimer: { fontFamily: theme.fonts.body, fontSize: 12, lineHeight: 17, color: theme.colors.textSecondary, marginTop: theme.spacing.md },
  tespit: { fontFamily: theme.fonts.heading, fontSize: 20, fontWeight: '700', color: theme.colors.textPrimary, letterSpacing: -0.3 },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: theme.spacing.sm, marginTop: theme.spacing.sm, flexWrap: 'wrap' },
  sistemPill: { backgroundColor: theme.colors.ink, borderRadius: theme.radius.pill, paddingVertical: 3, paddingHorizontal: theme.spacing.md },
  sistemPillText: { fontFamily: theme.fonts.body, fontSize: 11, fontWeight: '700', color: theme.colors.onInk },
  urgencyBadge: { borderRadius: theme.radius.pill, paddingVertical: 3, paddingHorizontal: theme.spacing.md },
  urgencyText: { fontFamily: theme.fonts.body, fontSize: 11, fontWeight: '700' },
  guven: { fontFamily: theme.fonts.body, fontSize: 12, color: theme.colors.textSecondary },
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
  costBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.savingsBg,
    borderWidth: 1,
    borderColor: theme.colors.savingsBorder,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    marginTop: theme.spacing.md,
  },
  costText: { flex: 1, fontFamily: theme.fonts.body, fontSize: 13, fontWeight: '600', color: theme.colors.savingsText },
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
