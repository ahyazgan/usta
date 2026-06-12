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

import { BottomTabBar } from '@/components/BottomTabBar';
import type { Aciliyet, KayitKosulu, SoundDiagnoseResult } from '@/lib/api';
import { t } from '@/lib/i18n';
import { theme } from '@/lib/theme';
import { useSoundDiagnose } from '@/lib/useSoundDiagnose';

const CONDITIONS: KayitKosulu[] = ['rolanti', 'gazda', 'soguk_motor', 'seyirde'];

/** Urgency → soft badge palette. */
function urgencyMeta(aciliyet: Aciliyet) {
  if (aciliyet === 'yuksek') return { bg: theme.colors.urgentSoftBg, fg: theme.colors.urgentSoftText };
  if (aciliyet === 'orta') return { bg: theme.colors.warnSoftBg, fg: theme.colors.warnSoftText };
  return { bg: theme.colors.okSoftBg, fg: theme.colors.okSoftText };
}

function ModeCard({
  icon,
  title,
  desc,
  active,
  onPress,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  desc: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      onPress={onPress}
      style={({ pressed }) => [styles.modeCard, active && styles.modeCardActive, pressed && styles.pressed]}
    >
      <View style={[styles.modeIcon, active && styles.modeIconActive]}>
        <Ionicons name={icon} size={24} color={active ? theme.colors.onInk : theme.colors.ink} />
      </View>
      <Text style={styles.modeTitle}>{title}</Text>
      <Text style={styles.modeDesc}>{desc}</Text>
    </Pressable>
  );
}

function ResultPanel({ result }: { result: SoundDiagnoseResult }) {
  const urgency = urgencyMeta(result.aciliyet);
  return (
    <View style={styles.resultPanel}>
      <Text style={styles.resultTitle}>{t('sound.result.title')}</Text>

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('sound.result.kategori')}</Text>
        <Text style={styles.resultValue}>{t(`sound.kategori.${result.ses_kategorisi}`)}</Text>
      </View>

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('sound.result.tespit')}</Text>
        <Text style={styles.resultValue}>{result.tespit}</Text>
      </View>

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('sound.result.guven')}</Text>
        <Text style={styles.resultValue}>{t(`camera.guven.${result.guven}`)}</Text>
      </View>

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('sound.result.aciliyet')}</Text>
        <View style={[styles.badge, { backgroundColor: urgency.bg }]}>
          <Text style={[styles.badgeText, { color: urgency.fg }]}>
            {t(`sound.aciliyet.${result.aciliyet}`)}
          </Text>
        </View>
      </View>

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('sound.result.sonrakiAdim')}</Text>
        <Text style={styles.resultValue}>{result.sonraki_adim}</Text>
      </View>

      {result.guvenlik_uyarisi != null && (
        <View style={styles.warningBox}>
          <Ionicons name="warning" size={18} color={theme.colors.onInk} />
          <Text style={styles.warningText}>{result.guvenlik_uyarisi}</Text>
        </View>
      )}
    </View>
  );
}

export default function DiagnosisScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { loading, error, result, runSoundDiagnose } = useSoundDiagnose();

  const [description, setDescription] = useState('');
  const [condition, setCondition] = useState<KayitKosulu>('rolanti');

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      <Text style={styles.title}>{t('diagnosis.title')}</Text>

      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Göster / Dinlet modları */}
        <View style={styles.modeGrid}>
          <ModeCard
            icon="camera"
            title={t('diagnosis.show.title')}
            desc={t('diagnosis.show.desc')}
            active={false}
            onPress={() => router.replace('/maintenance')}
          />
          <ModeCard
            icon="pulse"
            title={t('diagnosis.listen.title')}
            desc={t('diagnosis.listen.desc')}
            active
            onPress={() => undefined}
          />
        </View>

        <View style={styles.recordedHint}>
          <Ionicons name="information-circle" size={18} color={theme.colors.textSecondary} />
          <Text style={styles.recordedHintText}>{t('sound.recordedHint')}</Text>
        </View>

        <Text style={styles.label}>{t('sound.descriptionLabel')}</Text>
        <TextInput
          style={styles.textArea}
          value={description}
          onChangeText={setDescription}
          placeholder={t('sound.descriptionPlaceholder')}
          placeholderTextColor={theme.colors.textSecondary}
          multiline
          textAlignVertical="top"
        />

        <Text style={styles.label}>{t('sound.conditionLabel')}</Text>
        <View style={styles.conditionRow}>
          {CONDITIONS.map((c) => {
            const selected = condition === c;
            return (
              <Pressable
                key={c}
                accessibilityRole="button"
                accessibilityState={{ selected }}
                onPress={() => setCondition(c)}
                style={({ pressed }) => [
                  styles.conditionChip,
                  selected && styles.conditionChipSelected,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={[styles.conditionLabel, selected && styles.conditionLabelSelected]}>
                  {t(`sound.condition.${c}`)}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {error && (
          <View style={styles.errorBox}>
            <Ionicons name="alert-circle" size={18} color={theme.colors.dangerBright} />
            <Text style={styles.errorText}>{t(error)}</Text>
          </View>
        )}

        {result && <ResultPanel result={result} />}

        {result?.tamirciye_git_onerisi === true && (
          <Pressable
            accessibilityRole="button"
            onPress={() => router.replace('/maintenance')}
            style={({ pressed }) => [styles.mechanicButton, pressed && styles.pressed]}
          >
            <Ionicons name="construct" size={18} color={theme.colors.onInk} />
            <Text style={styles.mechanicText}>{t('common.goToMechanic')}</Text>
          </Pressable>
        )}
      </ScrollView>

      <View style={styles.footer}>
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled: loading }}
          disabled={loading}
          onPress={() => void runSoundDiagnose(description, condition)}
          style={({ pressed }) => [
            styles.analyzeButton,
            loading && styles.analyzeDisabled,
            pressed && styles.pressed,
          ]}
        >
          {loading ? (
            <>
              <ActivityIndicator color={theme.colors.onInk} />
              <Text style={styles.analyzeText}>{t('sound.analyzing')}</Text>
            </>
          ) : (
            <>
              <Ionicons name="pulse" size={22} color={theme.colors.onInk} />
              <Text style={styles.analyzeText}>{t('sound.analyze')}</Text>
            </>
          )}
        </Pressable>
      </View>

      <BottomTabBar active="diagnosis" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 26,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    letterSpacing: -0.3,
    paddingHorizontal: theme.spacing.lg,
    marginBottom: theme.spacing.md,
  },
  scroll: {
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.lg,
  },
  modeGrid: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.lg,
  },
  modeCard: {
    flex: 1,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1.5,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
    alignItems: 'center',
    gap: 4,
  },
  modeCardActive: {
    borderColor: theme.colors.ink,
  },
  modeIcon: {
    width: 48,
    height: 48,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.xs,
  },
  modeIconActive: {
    backgroundColor: theme.colors.ink,
  },
  modeTitle: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  modeDesc: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    lineHeight: 15,
  },
  recordedHint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.sm,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  recordedHintText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  label: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
    marginTop: theme.spacing.md,
  },
  textArea: {
    minHeight: 96,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
    fontFamily: theme.fonts.body,
    fontSize: 16,
    color: theme.colors.textPrimary,
  },
  conditionRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
  },
  conditionChip: {
    minHeight: 44,
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.lg,
    backgroundColor: theme.colors.surface,
  },
  conditionChipSelected: {
    backgroundColor: theme.colors.ink,
    borderColor: theme.colors.ink,
  },
  conditionLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.textSecondary,
  },
  conditionLabelSelected: {
    color: theme.colors.onInk,
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
    color: theme.colors.dangerBright,
  },
  resultPanel: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
    marginTop: theme.spacing.lg,
  },
  resultTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.sm,
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
  badge: {
    alignSelf: 'flex-start',
    borderRadius: theme.radius.pill,
    paddingVertical: 3,
    paddingHorizontal: theme.spacing.md,
    marginTop: theme.spacing.xs,
  },
  badgeText: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    fontWeight: '700',
  },
  warningBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.warningBright,
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
    color: theme.colors.onInk,
  },
  mechanicButton: {
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.ink,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.lg,
  },
  mechanicText: {
    fontFamily: theme.fonts.heading,
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  footer: {
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.sm,
    paddingBottom: theme.spacing.sm,
  },
  analyzeButton: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.ink,
    borderRadius: theme.radius.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
  },
  analyzeDisabled: {
    opacity: 0.5,
  },
  analyzeText: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  pressed: {
    opacity: 0.85,
  },
});
