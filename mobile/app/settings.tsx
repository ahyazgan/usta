import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';
import { useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { BottomTabBar } from '@/components/BottomTabBar';
import { createApiClient, type Subscription } from '@/lib/api';
import { t } from '@/lib/i18n';
import type { AppLocale } from '@/lib/prefs';
import { useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';
import { useAuth } from '@/lib/useAuth';

const LOCALES: AppLocale[] = ['tr', 'en'];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.card}>{children}</View>
    </View>
  );
}

function Row({
  icon,
  label,
  desc,
  right,
  onPress,
  danger,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  desc?: string;
  right?: React.ReactNode;
  onPress?: () => void;
  danger?: boolean;
}) {
  const color = danger ? theme.colors.danger : theme.colors.textPrimary;
  const body = (
    <View style={styles.row}>
      <Ionicons name={icon} size={20} color={danger ? theme.colors.danger : theme.colors.textSecondary} />
      <View style={styles.rowBody}>
        <Text style={[styles.rowLabel, { color }]}>{label}</Text>
        {desc != null && <Text style={styles.rowDesc}>{desc}</Text>}
      </View>
      {right ?? (onPress != null && <Ionicons name="chevron-forward" size={18} color={theme.colors.textSecondary} />)}
    </View>
  );
  if (onPress == null) return body;
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => pressed && styles.pressed}>
      {body}
    </Pressable>
  );
}

export default function SettingsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { logout } = useAuth();

  const locale = useUstaStore((s) => s.locale);
  const setLocale = useUstaStore((s) => s.setLocale);
  const remindersEnabled = useUstaStore((s) => s.remindersEnabled);
  const setRemindersEnabled = useUstaStore((s) => s.setRemindersEnabled);
  const analyticsConsent = useUstaStore((s) => s.analyticsConsent);
  const setAnalyticsConsent = useUstaStore((s) => s.setAnalyticsConsent);
  const authToken = useUstaStore((s) => s.authToken);

  const client = useMemo(() => createApiClient(undefined, () => authToken), [authToken]);
  const [sub, setSub] = useState<Subscription | null>(null);

  useEffect(() => {
    let active = true;
    client
      .getSubscription()
      .then((s) => active && setSub(s))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [client]);

  function toggleAnalytics(next: boolean) {
    setAnalyticsConsent(next); // iyimser
    client.updateConsent({ analytics: next }).catch(() => setAnalyticsConsent(!next));
  }

  async function handleLogout() {
    await logout();
    router.replace('/');
  }

  function handleDelete() {
    Alert.alert(
      t('settings.delete.confirmTitle'),
      t('settings.delete.confirmMessage'),
      [
        { text: t('common.cancel'), style: 'cancel' },
        {
          text: t('settings.delete.confirm'),
          style: 'destructive',
          onPress: async () => {
            try {
              await client.deleteAccount();
            } catch {
              /* yine de çıkış yap */
            }
            await logout();
            router.replace('/');
          },
        },
      ],
    );
  }

  const version = Constants.expoConfig?.version ?? '1.0.0';
  const isPremium = sub?.is_premium === true;

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.lg }]}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Text style={styles.title}>{t('settings.title')}</Text>

        {/* Hesap */}
        <Section title={t('settings.account.title')}>
          <Row
            icon={isPremium ? 'star' : 'star-outline'}
            label={isPremium ? t('settings.account.premiumActive') : t('settings.account.free')}
            desc={isPremium ? undefined : t('settings.account.upgradeDesc')}
            onPress={isPremium ? undefined : () => router.push('/premium')}
            right={
              isPremium ? (
                <View style={styles.premiumBadge}>
                  <Text style={styles.premiumBadgeText}>{t('settings.account.premiumTag')}</Text>
                </View>
              ) : undefined
            }
          />
        </Section>

        {/* Tercihler */}
        <Section title={t('settings.prefs.title')}>
          <View style={styles.row}>
            <Ionicons name="language-outline" size={20} color={theme.colors.textSecondary} />
            <Text style={[styles.rowLabel, styles.rowBody]}>{t('settings.prefs.language')}</Text>
            <View style={styles.segment}>
              {LOCALES.map((l) => {
                const selected = locale === l;
                return (
                  <Pressable
                    key={l}
                    accessibilityRole="button"
                    accessibilityState={{ selected }}
                    onPress={() => setLocale(l)}
                    style={[styles.segmentItem, selected && styles.segmentItemSelected]}
                  >
                    <Text style={[styles.segmentText, selected && styles.segmentTextSelected]}>
                      {l.toUpperCase()}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>
          <View style={styles.divider} />
          <Row
            icon="notifications-outline"
            label={t('settings.prefs.notifications')}
            desc={t('settings.prefs.notificationsDesc')}
            right={
              <Switch
                value={remindersEnabled}
                onValueChange={setRemindersEnabled}
                trackColor={{ true: theme.colors.ink, false: theme.colors.border }}
                thumbColor={theme.colors.surface}
              />
            }
          />
        </Section>

        {/* Gizlilik & Yasal */}
        <Section title={t('settings.privacy.title')}>
          <Row
            icon="shield-checkmark-outline"
            label={t('settings.privacy.policy')}
            onPress={() => router.push('/privacy')}
          />
          <View style={styles.divider} />
          <Row
            icon="analytics-outline"
            label={t('settings.privacy.analytics')}
            desc={t('settings.privacy.analyticsDesc')}
            right={
              <Switch
                value={analyticsConsent}
                onValueChange={toggleAnalytics}
                trackColor={{ true: theme.colors.ink, false: theme.colors.border }}
                thumbColor={theme.colors.surface}
              />
            }
          />
        </Section>

        {/* Hesap işlemleri */}
        <Section title={t('settings.actions.title')}>
          <Row icon="log-out-outline" label={t('settings.actions.logout')} onPress={() => void handleLogout()} />
          <View style={styles.divider} />
          <Row icon="trash-outline" label={t('settings.actions.delete')} onPress={handleDelete} danger />
        </Section>

        <Text style={styles.version}>{t('settings.about.version', { version })}</Text>
      </ScrollView>

      <BottomTabBar active="settings" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background },
  scroll: { paddingHorizontal: theme.spacing.lg, paddingBottom: theme.spacing.xxl },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 28,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.md,
  },
  section: { marginTop: theme.spacing.lg },
  sectionTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: theme.spacing.sm,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingHorizontal: theme.spacing.lg,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    minHeight: theme.touchTarget,
    paddingVertical: theme.spacing.sm,
  },
  rowBody: { flex: 1 },
  rowLabel: { fontFamily: theme.fonts.body, fontSize: 15, fontWeight: '600', color: theme.colors.textPrimary },
  rowDesc: { fontFamily: theme.fonts.body, fontSize: 12, color: theme.colors.textSecondary, marginTop: 2 },
  divider: { height: StyleSheet.hairlineWidth, backgroundColor: theme.colors.border },
  segment: {
    flexDirection: 'row',
    backgroundColor: theme.colors.background,
    borderRadius: theme.radius.pill,
    padding: 3,
    gap: 2,
  },
  segmentItem: {
    minWidth: 44,
    paddingVertical: 6,
    paddingHorizontal: theme.spacing.md,
    borderRadius: theme.radius.pill,
    alignItems: 'center',
  },
  segmentItemSelected: { backgroundColor: theme.colors.ink },
  segmentText: { fontFamily: theme.fonts.body, fontSize: 13, fontWeight: '700', color: theme.colors.textSecondary },
  segmentTextSelected: { color: theme.colors.onInk },
  premiumBadge: {
    backgroundColor: theme.colors.okSoftBg,
    borderRadius: theme.radius.pill,
    paddingVertical: 3,
    paddingHorizontal: theme.spacing.md,
  },
  premiumBadgeText: { fontFamily: theme.fonts.body, fontSize: 11, fontWeight: '700', color: theme.colors.okSoftText },
  version: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginTop: theme.spacing.xl,
  },
  pressed: { opacity: 0.6 },
});
