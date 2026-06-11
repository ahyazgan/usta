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

import type { FuelType } from '@/lib/api';
import { t } from '@/lib/i18n';
import { theme } from '@/lib/theme';
import { useVehicles } from '@/lib/useVehicles';

const FUEL_TYPES: FuelType[] = ['benzin', 'dizel', 'lpg', 'hibrit', 'elektrik'];

const MIN_YEAR = 1950;
const MAX_YEAR = 2100;

export default function VehicleNewScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { addVehicle, error } = useVehicles();

  const [make, setMake] = useState('');
  const [model, setModel] = useState('');
  const [year, setYear] = useState('');
  const [fuelType, setFuelType] = useState<FuelType | null>(null);
  const [engineCode, setEngineCode] = useState('');
  const [km, setKm] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  async function handleSave() {
    if (submitting) return;
    const parsedYear = Number(year.trim());
    const validYear =
      Number.isInteger(parsedYear) &&
      parsedYear >= MIN_YEAR &&
      parsedYear <= MAX_YEAR;
    if (
      make.trim().length === 0 ||
      model.trim().length === 0 ||
      !validYear ||
      fuelType == null
    ) {
      setValidationError('vehicle.form.validation');
      return;
    }
    setValidationError(null);

    const parsedKm = km.trim().length > 0 ? Number(km.trim()) : undefined;
    const current_km =
      parsedKm != null && Number.isFinite(parsedKm) && parsedKm >= 0
        ? parsedKm
        : undefined;

    setSubmitting(true);
    const ok = await addVehicle({
      make: make.trim(),
      model: model.trim(),
      year: parsedYear,
      fuel_type: fuelType,
      engine_code:
        engineCode.trim().length > 0 ? engineCode.trim() : undefined,
      current_km,
    });
    setSubmitting(false);
    if (ok) router.replace('/');
  }

  // Validation key wins (it is set on submit); otherwise show hook error.
  const errorKey = validationError ?? error;

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
        contentContainerStyle={[
          styles.scroll,
          { paddingBottom: insets.bottom + theme.spacing.xxl },
        ]}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>{t('vehicle.form.title')}</Text>

        <View style={styles.specHint}>
          <Ionicons
            name="information-circle"
            size={18}
            color={theme.colors.textSecondary}
          />
          <Text style={styles.specHintText}>
            {t('vehicle.form.specAutoHint')}
          </Text>
        </View>

        <Text style={styles.label}>{t('vehicle.form.make')}</Text>
        <TextInput
          style={styles.input}
          value={make}
          onChangeText={setMake}
          placeholder={t('vehicle.form.makePlaceholder')}
          placeholderTextColor={theme.colors.textSecondary}
          autoCapitalize="words"
        />

        <Text style={styles.label}>{t('vehicle.form.model')}</Text>
        <TextInput
          style={styles.input}
          value={model}
          onChangeText={setModel}
          placeholder={t('vehicle.form.modelPlaceholder')}
          placeholderTextColor={theme.colors.textSecondary}
          autoCapitalize="words"
        />

        <Text style={styles.label}>{t('vehicle.form.year')}</Text>
        <TextInput
          style={styles.input}
          value={year}
          onChangeText={setYear}
          placeholder={t('vehicle.form.yearPlaceholder')}
          placeholderTextColor={theme.colors.textSecondary}
          keyboardType="number-pad"
          maxLength={4}
        />

        <Text style={styles.label}>{t('vehicle.form.fuel')}</Text>
        <View style={styles.fuelRow}>
          {FUEL_TYPES.map((fuel) => {
            const selected = fuelType === fuel;
            const color = selected
              ? theme.colors.accent
              : theme.colors.textSecondary;
            return (
              <Pressable
                key={fuel}
                accessibilityRole="button"
                accessibilityState={{ selected }}
                onPress={() => setFuelType(fuel)}
                style={({ pressed }) => [
                  styles.fuelChip,
                  { borderColor: color },
                  selected && styles.fuelChipSelected,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={[styles.fuelLabel, { color }]}>
                  {t(`vehicle.fuel.${fuel}`)}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <Text style={styles.label}>{t('vehicle.form.engineCode')}</Text>
        <TextInput
          style={styles.input}
          value={engineCode}
          onChangeText={setEngineCode}
          placeholder={t('vehicle.form.engineCodePlaceholder')}
          placeholderTextColor={theme.colors.textSecondary}
          autoCapitalize="characters"
          autoCorrect={false}
        />

        <Text style={styles.label}>{t('vehicle.form.km')}</Text>
        <TextInput
          style={styles.input}
          value={km}
          onChangeText={setKm}
          placeholder={t('vehicle.form.kmPlaceholder')}
          placeholderTextColor={theme.colors.textSecondary}
          keyboardType="number-pad"
        />

        {errorKey && (
          <View style={styles.errorBox}>
            <Ionicons
              name="alert-circle"
              size={18}
              color={theme.colors.danger}
            />
            <Text style={styles.errorText}>{t(errorKey)}</Text>
          </View>
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
          accessibilityState={{ disabled: submitting }}
          disabled={submitting}
          onPress={handleSave}
          style={({ pressed }) => [
            styles.save,
            submitting && styles.saveDisabled,
            pressed && styles.pressed,
          ]}
        >
          {submitting ? (
            <ActivityIndicator color={theme.colors.background} />
          ) : (
            <>
              <Ionicons
                name="add-circle"
                size={22}
                color={theme.colors.background}
              />
              <Text style={styles.saveText}>{t('vehicle.form.save')}</Text>
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
  specHint: {
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
  specHintText: {
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
  input: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingHorizontal: theme.spacing.lg,
    fontFamily: theme.fonts.body,
    fontSize: 16,
    color: theme.colors.textPrimary,
  },
  fuelRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
  },
  fuelChip: {
    minHeight: theme.touchTarget,
    justifyContent: 'center',
    borderWidth: 1,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.lg,
  },
  fuelChipSelected: {
    backgroundColor: theme.colors.surface,
  },
  fuelLabel: {
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
  footer: {
    paddingTop: theme.spacing.md,
  },
  save: {
    minHeight: theme.touchTarget,
    backgroundColor: theme.colors.accent,
    borderRadius: theme.radius.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
  },
  saveDisabled: {
    opacity: 0.5,
  },
  saveText: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.background,
  },
  pressed: {
    opacity: 0.85,
  },
});
