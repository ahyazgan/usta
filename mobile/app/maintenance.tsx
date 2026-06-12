import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { BottomTabBar } from '@/components/BottomTabBar';
import { type Task, type TaskRisk } from '@/lib/api';
import { i18n, t } from '@/lib/i18n';
import { useUstaStore } from '@/lib/store';
import { TASK_ICON } from '@/lib/taskIcons';
import { theme } from '@/lib/theme';
import { useVehicleTasks } from '@/lib/useVehicleTasks';
import { useVehicles } from '@/lib/useVehicles';

function taskTitle(task: Task): string {
  return i18n.locale === 'en' ? task.title_en : task.title_tr;
}

/** Risk → soft badge palette + icon. */
function riskMeta(risk: TaskRisk) {
  if (risk === 'yuksek') {
    return { bg: theme.colors.urgentSoftBg, fg: theme.colors.urgentSoftText, icon: 'alert-circle' as const };
  }
  if (risk === 'orta') {
    return { bg: theme.colors.warnSoftBg, fg: theme.colors.warnSoftText, icon: 'construct' as const };
  }
  return { bg: theme.colors.okSoftBg, fg: theme.colors.okSoftText, icon: 'leaf' as const };
}

export default function MaintenanceScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const authToken = useUstaStore((s) => s.authToken);
  const setSelectedTask = useUstaStore((s) => s.setSelectedTask);

  const { currentVehicle, loading: vehiclesLoading } = useVehicles();
  const { tasks } = useVehicleTasks(currentVehicle?.id ?? null);

  const header = (
    <View style={styles.header}>
      <Text style={styles.title}>{t('maintenance.title')}</Text>
      {currentVehicle && (
        <View style={styles.carTag}>
          <Ionicons name="car-sport" size={14} color={theme.colors.textSecondary} />
          <Text style={styles.carTagText}>
            {currentVehicle.make} {currentVehicle.model}
          </Text>
        </View>
      )}
    </View>
  );

  function startTask(task: Task) {
    setSelectedTask(task);
    router.push('/guide');
  }

  let body: React.ReactNode;
  if (authToken == null) {
    body = (
      <View style={styles.center}>
        <Text style={styles.muted}>{t('auth.loggedOutPrompt')}</Text>
      </View>
    );
  } else if (vehiclesLoading) {
    body = (
      <View style={styles.center}>
        <ActivityIndicator color={theme.colors.ink} />
      </View>
    );
  } else if (!currentVehicle) {
    body = (
      <View style={styles.center}>
        <Ionicons name="car-sport-outline" size={64} color={theme.colors.textSecondary} />
        <Text style={styles.muted}>{t('vehicle.error.noVehicle')}</Text>
        <Pressable
          accessibilityRole="button"
          onPress={() => router.push('/vehicle-new')}
          style={({ pressed }) => [styles.cta, pressed && styles.pressed]}
        >
          <Ionicons name="add-circle" size={20} color={theme.colors.onInk} />
          <Text style={styles.ctaText}>{t('vehicle.add')}</Text>
        </Pressable>
      </View>
    );
  } else {
    body = (
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Text style={styles.subtitle}>{t('maintenance.subtitle')}</Text>
        {tasks.map((task) => {
          const meta = riskMeta(task.risk);
          return (
            <Pressable
              key={task.id}
              accessibilityRole="button"
              onPress={() => startTask(task)}
              style={({ pressed }) => [styles.card, pressed && styles.pressed]}
            >
              <View style={[styles.cardIcon, { backgroundColor: meta.bg }]}>
                <Ionicons name={TASK_ICON[task.id] ?? 'build'} size={20} color={meta.fg} />
              </View>
              <View style={styles.cardBody}>
                <Text style={styles.cardTitle}>{taskTitle(task)}</Text>
                <View style={[styles.badge, { backgroundColor: meta.bg }]}>
                  <Text style={[styles.badgeText, { color: meta.fg }]}>
                    {t(`maintenance.risk.${task.risk}`)}
                  </Text>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={18} color={theme.colors.border} />
            </Pressable>
          );
        })}
      </ScrollView>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      {header}
      <View style={styles.flex}>{body}</View>
      <BottomTabBar active="maintenance" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background },
  flex: { flex: 1 },
  header: {
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 26,
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
  },
  carTagText: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    fontWeight: '600',
    color: theme.colors.textSecondary,
  },
  subtitle: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.md,
  },
  scroll: {
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.xl,
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
    width: 44,
    height: 44,
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardBody: { flex: 1, gap: 4 },
  cardTitle: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '600',
    color: theme.colors.textPrimary,
  },
  badge: {
    alignSelf: 'flex-start',
    borderRadius: theme.radius.pill,
    paddingVertical: 2,
    paddingHorizontal: theme.spacing.sm,
  },
  badgeText: {
    fontFamily: theme.fonts.body,
    fontSize: 10,
    fontWeight: '700',
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
  cta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: theme.touchTarget,
    paddingHorizontal: theme.spacing.xl,
    backgroundColor: theme.colors.ink,
    borderRadius: theme.radius.md,
  },
  ctaText: {
    fontFamily: theme.fonts.heading,
    fontSize: 17,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  pressed: { opacity: 0.85 },
});
