import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { API_BASE_URL, createApiClient, type SystemStat } from '@/lib/api';
import { clearTokens } from '@/lib/auth';
import { ensureDemoSession } from '@/lib/demoSession';
import { t } from '@/lib/i18n';
import { goBack } from '@/lib/nav';
import { useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';

function ConsentToggle({
  title,
  desc,
  value,
  disabled,
  onChange,
}: {
  title: string;
  desc: string;
  value: boolean;
  disabled: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <View style={styles.toggleRow}>
      <View style={styles.toggleText}>
        <Text style={styles.toggleTitle}>{title}</Text>
        <Text style={styles.toggleDesc}>{desc}</Text>
      </View>
      <Switch
        value={value}
        disabled={disabled}
        onValueChange={onChange}
        trackColor={{ false: theme.colors.border, true: theme.colors.successBright }}
        thumbColor={theme.colors.surface}
      />
    </View>
  );
}

export default function PrivacyScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const authToken = useUstaStore((s) => s.authToken);
  const setTokens = useUstaStore((s) => s.setTokens);
  const setAnalyticsConsent = useUstaStore((s) => s.setAnalyticsConsent);

  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );

  const [analytics, setAnalytics] = useState(false);
  const [data, setData] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [stats, setStats] = useState<SystemStat[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const c = await client.getConsent();
      setAnalytics(c.analytics);
      setData(c.data);
      setAnalyticsConsent(c.analytics);
    } catch {
      /* sessiz */
    } finally {
      setLoading(false);
    }
    try {
      setStats(await client.getSystemStats());
    } catch {
      setStats([]);
    }
  }, [client, setAnalyticsConsent]);

  useEffect(() => {
    void load();
  }, [load]);

  async function persist(next: { analytics?: boolean; data?: boolean }) {
    setSaving(true);
    try {
      const c = await client.updateConsent(next);
      setAnalytics(c.analytics);
      setData(c.data);
      setAnalyticsConsent(c.analytics);
    } catch {
      /* sessiz — UI iyimser kaldı, sonra düzelir */
    } finally {
      setSaving(false);
    }
  }

  function confirmDelete() {
    Alert.alert(
      t('privacy.delete.confirmTitle'),
      t('privacy.delete.confirmMsg'),
      [
        { text: t('common.cancel'), style: 'cancel' },
        {
          text: t('privacy.delete.confirm'),
          style: 'destructive',
          onPress: () => void runDelete(),
        },
      ],
    );
  }

  async function runDelete() {
    if (deleting) return;
    setDeleting(true);
    try {
      await client.deleteAccount();
      await clearTokens();
      setTokens(null);
      // Demo akışı: hesabı sil → temiz bir demo oturumu yeniden kur.
      await ensureDemoSession(setTokens);
      router.replace('/');
    } catch {
      setDeleting(false);
      Alert.alert(t('privacy.delete.errorTitle'), t('privacy.delete.errorMsg'));
    }
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
        <Text style={styles.title}>{t('privacy.title')}</Text>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={theme.colors.ink} />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + theme.spacing.xl }]}
          showsVerticalScrollIndicator={false}
        >
          <Text style={styles.intro}>{t('privacy.intro')}</Text>

          <View style={styles.card}>
            <ConsentToggle
              title={t('privacy.analytics.title')}
              desc={t('privacy.analytics.desc')}
              value={analytics}
              disabled={saving}
              onChange={(v) => {
                setAnalytics(v);
                void persist({ analytics: v });
              }}
            />
            <View style={styles.divider} />
            <ConsentToggle
              title={t('privacy.data.title')}
              desc={t('privacy.data.desc')}
              value={data}
              disabled={saving}
              onChange={(v) => {
                setData(v);
                void persist({ data: v });
              }}
            />
          </View>

          {/* Anonim küme — anonimleştirmenin kanıtı */}
          <Text style={styles.sectionTitle}>{t('privacy.stats.title')}</Text>
          {stats.length === 0 ? (
            <View style={styles.emptyBox}>
              <Ionicons name="bar-chart-outline" size={26} color={theme.colors.textSecondary} />
              <Text style={styles.emptyText}>{t('privacy.stats.empty')}</Text>
            </View>
          ) : (
            <View style={styles.card}>
              {stats.map((s) => (
                <View key={s.sistem} style={styles.statRow}>
                  <Text style={styles.statName}>{t(`sistem.${s.sistem}`)}</Text>
                  <Text style={styles.statMeta}>
                    {t('privacy.stats.count', { count: s.count })}
                    {s.dogruluk_orani != null
                      ? ` · ${t('privacy.stats.accuracy', {
                          pct: Math.round(s.dogruluk_orani * 100),
                        })}`
                      : ''}
                  </Text>
                </View>
              ))}
            </View>
          )}

          {/* Tam yasal metin — mağaza zorunlu, herkese açık URL */}
          <Text style={styles.sectionTitle}>{t('privacy.policy.title')}</Text>
          <Pressable
            accessibilityRole="link"
            onPress={() => void Linking.openURL(`${API_BASE_URL}/privacy`)}
            style={({ pressed }) => [styles.policyLink, pressed && styles.pressed]}
          >
            <Ionicons name="document-text-outline" size={18} color={theme.colors.ink} />
            <Text style={styles.policyLinkText}>{t('privacy.policy.link')}</Text>
            <Ionicons name="open-outline" size={16} color={theme.colors.textSecondary} />
          </Pressable>

          {/* Silme/unutulma hakkı */}
          <Text style={styles.sectionTitle}>{t('privacy.delete.title')}</Text>
          <Text style={styles.deleteDesc}>{t('privacy.delete.desc')}</Text>
          <Pressable
            accessibilityRole="button"
            accessibilityState={{ disabled: deleting }}
            disabled={deleting}
            onPress={confirmDelete}
            style={({ pressed }) => [styles.deleteButton, pressed && styles.pressed]}
          >
            {deleting ? (
              <ActivityIndicator color={theme.colors.onInk} />
            ) : (
              <>
                <Ionicons name="trash" size={18} color={theme.colors.onInk} />
                <Text style={styles.deleteButtonText}>{t('privacy.delete.button')}</Text>
              </>
            )}
          </Pressable>
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
    gap: theme.spacing.xs,
  },
  back: { flexDirection: 'row', alignItems: 'center', minHeight: 32 },
  backText: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.ink,
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 26,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    letterSpacing: -0.3,
  },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { paddingHorizontal: theme.spacing.lg },
  intro: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    lineHeight: 20,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.lg,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
  },
  policyLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    minHeight: 56,
  },
  policyLinkText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '600',
    color: theme.colors.ink,
  },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
  },
  toggleText: { flex: 1 },
  toggleTitle: {
    fontFamily: theme.fonts.body,
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  toggleDesc: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    lineHeight: 17,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  divider: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: theme.colors.border,
    marginVertical: theme.spacing.md,
  },
  sectionTitle: {
    fontFamily: theme.fonts.heading,
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: theme.spacing.xl,
    marginBottom: theme.spacing.md,
  },
  emptyBox: {
    alignItems: 'center',
    gap: theme.spacing.xs,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderStyle: 'dashed',
    padding: theme.spacing.xl,
  },
  emptyText: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  statRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.colors.border,
  },
  statName: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  statMeta: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  deleteDesc: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    lineHeight: 18,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.md,
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.dangerBright,
  },
  deleteButtonText: {
    fontFamily: theme.fonts.heading,
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  pressed: { opacity: 0.85 },
});
