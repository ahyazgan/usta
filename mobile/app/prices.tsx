import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { BrandBadge } from '@/components/BrandBadge';
import { ApiError, createApiClient, type TaskEstimate } from '@/lib/api';
import { i18n, t } from '@/lib/i18n';
import { goBack } from '@/lib/nav';
import { useUstaStore } from '@/lib/store';
import { TASK_ICON } from '@/lib/taskIcons';
import { theme } from '@/lib/theme';
import { useVehicles } from '@/lib/useVehicles';

function title(est: TaskEstimate): string {
  return i18n.locale === 'en' ? est.title_en : est.title_tr;
}

export default function PricesScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const authToken = useUstaStore((s) => s.authToken);
  const setSelectedTask = useUstaStore((s) => s.setSelectedTask);
  const { currentVehicle } = useVehicles();

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const [rows, setRows] = useState<TaskEstimate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (currentVehicle == null) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setRows(await client.getVehicleEstimates(currentVehicle.id));
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 0
          ? 'vehicle.error.network'
          : 'vehicle.error.generic',
      );
    } finally {
      setLoading(false);
    }
  }, [client, currentVehicle]);

  useEffect(() => {
    void load();
  }, [load]);

  function openGuide(est: TaskEstimate) {
    setSelectedTask({
      id: est.id,
      title_tr: est.title_tr,
      title_en: est.title_en,
      risk: est.risk,
    });
    router.push('/guide');
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      <View style={styles.header}>
        <Pressable
          accessibilityRole="button"
          onPress={() => goBack(router)}
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Ionicons name="chevron-back" size={20} color={theme.colors.ink} />
          <Text style={styles.backText}>{t('common.back')}</Text>
        </Pressable>
        <Text style={styles.title}>{t('prices.title')}</Text>
        {currentVehicle && (
          <View style={styles.carTag}>
            <BrandBadge make={currentVehicle.make} size={18} />
            <Text style={styles.carTagText}>
              {currentVehicle.make} {currentVehicle.model}
            </Text>
          </View>
        )}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={theme.colors.ink} />
        </View>
      ) : error || currentVehicle == null ? (
        <View style={styles.center}>
          <Ionicons name="cloud-offline-outline" size={48} color={theme.colors.textSecondary} />
          <Text style={styles.muted}>
            {t(error ?? 'vehicle.error.noVehicle')}
          </Text>
          {error != null && (
            <Pressable
              accessibilityRole="button"
              onPress={() => void load()}
              style={({ pressed }) => [styles.retry, pressed && styles.pressed]}
            >
              <Text style={styles.retryText}>{t('common.retry')}</Text>
            </Pressable>
          )}
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
          <Text style={styles.subtitle}>{t('prices.subtitle')}</Text>
          {rows.map((est) => (
            <Pressable
              key={est.id}
              accessibilityRole="button"
              onPress={() => openGuide(est)}
              style={({ pressed }) => [styles.card, pressed && styles.pressed]}
            >
              <View style={styles.cardIcon}>
                <Ionicons name={TASK_ICON[est.id] ?? 'build'} size={20} color={theme.colors.ink} />
              </View>
              <View style={styles.cardBody}>
                <Text style={styles.cardTitle}>{title(est)}</Text>
                <Text style={styles.cardSource}>
                  {est.source === 'community'
                    ? t('prices.community', { count: est.sample_size })
                    : t('prices.seed')}
                </Text>
              </View>
              <View style={styles.priceCol}>
                <Text style={styles.priceText}>
                  {est.low_try.toLocaleString('tr-TR')}–{est.high_try.toLocaleString('tr-TR')} ₺
                </Text>
                <Ionicons name="chevron-forward" size={16} color={theme.colors.border} />
              </View>
            </Pressable>
          ))}
          <View style={styles.note}>
            <Ionicons name="information-circle" size={15} color={theme.colors.textSecondary} />
            <Text style={styles.noteText}>{t('prices.disclaimer')}</Text>
          </View>
        </ScrollView>
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
    gap: theme.spacing.xs,
  },
  back: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 32,
  },
  backText: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.ink,
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    letterSpacing: -0.3,
  },
  carTag: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: theme.spacing.xs,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingVertical: 4,
    paddingHorizontal: theme.spacing.md,
    marginTop: theme.spacing.xs,
  },
  carTagText: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    fontWeight: '600',
    color: theme.colors.textSecondary,
  },
  scroll: {
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.md,
    paddingBottom: theme.spacing.xl,
  },
  subtitle: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.md,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.sm,
  },
  cardIcon: {
    width: 40,
    height: 40,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardBody: { flex: 1, gap: 2 },
  cardTitle: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '600',
    color: theme.colors.textPrimary,
  },
  cardSource: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    color: theme.colors.textSecondary,
  },
  priceCol: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
  },
  priceText: {
    fontFamily: theme.fonts.heading,
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  note: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.sm,
    paddingHorizontal: theme.spacing.xs,
  },
  noteText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 11,
    lineHeight: 16,
    color: theme.colors.textSecondary,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
  },
  muted: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
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
  pressed: { opacity: 0.85 },
});
