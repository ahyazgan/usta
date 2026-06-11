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

import type { Aciliyet, KayitKosulu, SoundDiagnoseResult } from '@/lib/api';
import { t } from '@/lib/i18n';
import { theme } from '@/lib/theme';
import { useSoundDiagnose } from '@/lib/useSoundDiagnose';

const CONDITIONS: KayitKosulu[] = [
  'rolanti',
  'gazda',
  'soguk_motor',
  'seyirde',
];

/** Urgency color — NEVER green; secondary/amber/red by level. */
function urgencyColor(aciliyet: Aciliyet): string {
  if (aciliyet === 'yuksek') return theme.colors.danger;
  if (aciliyet === 'orta') return theme.colors.accent;
  return theme.colors.textSecondary;
}

function ResultPanel({ result }: { result: SoundDiagnoseResult }) {
  const urgency = urgencyColor(result.aciliyet);
  return (
    <View style={styles.resultPanel}>
      <Text style={styles.resultTitle}>{t('sound.result.title')}</Text>

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('sound.result.kategori')}</Text>
        <Text style={styles.resultValue}>
          {t(`sound.kategori.${result.ses_kategorisi}`)}
        </Text>
      </View>

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('sound.result.tespit')}</Text>
        <Text style={styles.resultValue}>{result.tespit}</Text>
      </View>

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('sound.result.guven')}</Text>
        <Text style={styles.resultValue}>
          {t(`camera.guven.${result.guven}`)}
        </Text>
      </View>

      <View style={styles.resultRow}>
        <Text style={styles.resultLabel}>{t('sound.result.aciliyet')}</Text>
        <View style={[styles.urgencyBadge, { borderColor: urgency }]}>
          <Text style={[styles.urgencyText, { color: urgency }]}>
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
          <Ionicons name="warning" size={18} color={theme.colors.background} />
          <Text style={styles.warningText}>{result.guvenlik_uyarisi}</Text>
        </View>
      )}
    </View>
  );
}

export default function SoundScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { loading, error, result, runSoundDiagnose } = useSoundDiagnose();

  const [description, setDescription] = useState('');
  const [condition, setCondition] = useState<KayitKosulu>('rolanti');

  return (
    <View
      style={[styles.container, { paddingTop: insets.top + theme.spacing.lg }]}
    >
      <View style={styles.headerRow}>
        <Pressable
          accessibilityRole="button"
          onPress={() => router.back()}
          style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}
        >
          <Ionicons
            name="chevron-back"
            size={22}
            color={theme.colors.textPrimary}
          />
          <Text style={styles.backText}>{t('common.back')}</Text>
        </Pressable>
      </View>

      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>{t('sound.title')}</Text>

        <View style={styles.recordedHint}>
          <Ionicons
            name="information-circle"
            size={18}
            color={theme.colors.textSecondary}
          />
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
            const color = selected
              ? theme.colors.accent
              : theme.colors.textSecondary;
            return (
              <Pressable
                key={c}
                accessibilityRole="button"
                accessibilityState={{ selected }}
                onPress={() => setCondition(c)}
                style={({ pressed }) => [
                  styles.conditionChip,
                  { borderColor: color },
                  selected && styles.conditionChipSelected,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={[styles.conditionLabel, { color }]}>
                  {t(`sound.condition.${c}`)}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {error && (
          <View style={styles.errorBox}>
            <Ionicons
              name="alert-circle"
              size={18}
              color={theme.colors.danger}
            />
            <Text style={styles.errorText}>{t(error)}</Text>
          </View>
        )}

        {result && <ResultPanel result={result} />}

        {result?.tamirciye_git_onerisi === true && (
          <Pressable
            accessibilityRole="button"
            onPress={() => router.back()}
            style={({ pressed }) => [
              styles.mechanicButton,
              pressed && styles.pressed,
            ]}
          >
            <Ionicons
              name="construct"
              size={18}
              color={theme.colors.background}
            />
            <Text style={styles.mechanicText}>{t('common.goToMechanic')}</Text>
          </Pressable>
        )}
      </ScrollView>

      <View
        style={[
          styles.footer,
          { paddingBottom: insets.bottom + theme.spacing.lg },
        ]}
      >
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
              <ActivityIndicator color={theme.colors.background} />
              <Text style={styles.analyzeText}>{t('sound.analyzing')}</Text>
            </>
          ) : (
            <>
              <Ionicons name="pulse" size={22} color={theme.colors.background} />
              <Text style={styles.analyzeText}>{t('sound.analyze')}</Text>
            </>
          )}
        </Pressable>
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
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: theme.touchTarget,
    paddingRight: theme.spacing.md,
  },
  backText: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '600',
    color: theme.colors.textPrimary,
  },
  scroll: {
    paddingBottom: theme.spacing.xxl,
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 28,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.md,
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
    marginBottom: theme.spacing.lg,
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
    minHeight: theme.touchTarget,
    justifyContent: 'center',
    borderWidth: 1,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.lg,
  },
  conditionChipSelected: {
    backgroundColor: theme.colors.surface,
  },
  conditionLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '700',
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
  urgencyBadge: {
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderRadius: theme.radius.pill,
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.md,
    marginTop: theme.spacing.xs,
  },
  urgencyText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
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
  mechanicButton: {
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.accent,
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
    color: theme.colors.background,
  },
  footer: {
    paddingTop: theme.spacing.md,
  },
  analyzeButton: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.accent,
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
    color: theme.colors.background,
  },
  pressed: {
    opacity: 0.85,
  },
});
