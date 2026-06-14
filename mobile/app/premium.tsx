import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { createApiClient, type Subscription } from '@/lib/api';
import { t } from '@/lib/i18n';
import { goBack } from '@/lib/nav';
import { useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';

const BENEFITS: { icon: keyof typeof Ionicons.glyphMap; key: string }[] = [
  { icon: 'mic', key: 'live' },
  { icon: 'sparkles', key: 'diagnosis' },
  { icon: 'pricetags', key: 'prices' },
  { icon: 'heart', key: 'support' },
];

export default function PremiumScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const authToken = useUstaStore((s) => s.authToken);
  const client = useMemo(() => createApiClient(undefined, () => authToken), [authToken]);

  const [sub, setSub] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setSub(await client.getSubscription());
    } catch {
      setSub(null);
    } finally {
      setLoading(false);
    }
  }, [client]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const premium = sub?.is_premium === true;

  function handleSubscribe() {
    // Faturalandırma (RevenueCat → Apple/Google IAP) lansmanda bağlanır.
    Alert.alert(t('premium.cta'), t('premium.comingSoon'));
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Pressable
          accessibilityRole="button"
          onPress={() => goBack(router)}
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Ionicons name="chevron-back" size={20} color={theme.colors.onInk} />
          <Text style={styles.backText}>{t('common.back')}</Text>
        </Pressable>

        <View style={styles.hero}>
          <View style={styles.crown}>
            <Ionicons name="star" size={30} color={theme.colors.warningBright} />
          </View>
          <Text style={styles.title}>{t('premium.title')}</Text>
          <Text style={styles.tagline}>{t('premium.tagline')}</Text>
        </View>

        {loading ? (
          <ActivityIndicator color={theme.colors.onInk} style={{ marginVertical: theme.spacing.xl }} />
        ) : premium ? (
          <View style={styles.activeCard}>
            <Ionicons name="checkmark-circle" size={22} color={theme.colors.success} />
            <Text style={styles.activeText}>{t('premium.active')}</Text>
          </View>
        ) : (
          <Text style={styles.statusFree}>{t('premium.free')}</Text>
        )}

        <View style={styles.benefits}>
          {BENEFITS.map((b) => (
            <View key={b.key} style={styles.benefitRow}>
              <View style={styles.benefitIcon}>
                <Ionicons name={b.icon} size={18} color={theme.colors.warningBright} />
              </View>
              <Text style={styles.benefitText}>{t(`premium.benefit.${b.key}`)}</Text>
            </View>
          ))}
        </View>

        {!premium && (
          <>
            <View style={styles.priceRow}>
              <View style={styles.priceCard}>
                <Text style={styles.priceAmount}>{t('premium.priceMonthly')}</Text>
                <Text style={styles.pricePeriod}>{t('premium.perMonth')}</Text>
              </View>
              <View style={[styles.priceCard, styles.priceCardBest]}>
                <Text style={styles.bestTag}>{t('premium.bestValue')}</Text>
                <Text style={styles.priceAmount}>{t('premium.priceYearly')}</Text>
                <Text style={styles.pricePeriod}>{t('premium.perYear')}</Text>
              </View>
            </View>

            <Pressable
              accessibilityRole="button"
              onPress={handleSubscribe}
              style={({ pressed }) => [styles.cta, pressed && styles.pressed]}
            >
              <Text style={styles.ctaText}>{t('premium.cta')}</Text>
            </Pressable>
            <Text style={styles.disclaimer}>{t('premium.disclaimer')}</Text>
          </>
        )}

        <Pressable accessibilityRole="button" onPress={() => void refresh()} style={styles.refresh}>
          <Text style={styles.refreshText}>{t('premium.refresh')}</Text>
        </Pressable>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.ink },
  scroll: { paddingHorizontal: theme.spacing.lg, paddingBottom: theme.spacing.xl },
  back: { flexDirection: 'row', alignItems: 'center', minHeight: 32, marginBottom: theme.spacing.sm },
  backText: { fontFamily: theme.fonts.body, fontSize: 13, fontWeight: '600', color: theme.colors.onInk },
  hero: { alignItems: 'center', gap: theme.spacing.sm, marginVertical: theme.spacing.lg },
  crown: {
    width: 64, height: 64, borderRadius: 32, alignItems: 'center', justifyContent: 'center',
    backgroundColor: 'rgba(255,138,0,0.14)', borderWidth: 1, borderColor: theme.colors.warningBright,
  },
  title: { fontFamily: theme.fonts.heading, fontSize: 26, fontWeight: '800', color: theme.colors.onInk },
  tagline: { fontFamily: theme.fonts.body, fontSize: 14, color: theme.colors.onInkMuted, textAlign: 'center' },
  activeCard: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: theme.spacing.sm,
    backgroundColor: 'rgba(34,197,94,0.12)', borderRadius: theme.radius.md, padding: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  activeText: { fontFamily: theme.fonts.body, fontSize: 15, fontWeight: '700', color: theme.colors.onInk },
  statusFree: { fontFamily: theme.fonts.body, fontSize: 12, color: theme.colors.onInkMuted, textAlign: 'center', marginBottom: theme.spacing.md },
  benefits: { gap: theme.spacing.sm, marginBottom: theme.spacing.lg },
  benefitRow: {
    flexDirection: 'row', alignItems: 'center', gap: theme.spacing.md,
    backgroundColor: 'rgba(255,255,255,0.06)', borderRadius: theme.radius.md, padding: theme.spacing.md,
  },
  benefitIcon: {
    width: 34, height: 34, borderRadius: theme.radius.sm, alignItems: 'center', justifyContent: 'center',
    backgroundColor: 'rgba(255,138,0,0.12)',
  },
  benefitText: { flex: 1, fontFamily: theme.fonts.body, fontSize: 14, color: theme.colors.onInk },
  priceRow: { flexDirection: 'row', gap: theme.spacing.md, marginBottom: theme.spacing.lg },
  priceCard: {
    flex: 1, backgroundColor: 'rgba(255,255,255,0.06)', borderWidth: 1, borderColor: theme.colors.border,
    borderRadius: theme.radius.md, padding: theme.spacing.md, alignItems: 'center', gap: 2,
  },
  priceCardBest: { borderColor: theme.colors.warningBright },
  bestTag: {
    fontFamily: theme.fonts.body, fontSize: 10, fontWeight: '800', color: theme.colors.warningBright,
    textTransform: 'uppercase', letterSpacing: 0.5,
  },
  priceAmount: { fontFamily: theme.fonts.heading, fontSize: 20, fontWeight: '800', color: theme.colors.onInk },
  pricePeriod: { fontFamily: theme.fonts.body, fontSize: 11, color: theme.colors.onInkMuted },
  cta: {
    minHeight: theme.touchTarget, alignItems: 'center', justifyContent: 'center',
    borderRadius: theme.radius.md, backgroundColor: theme.colors.warningBright,
  },
  ctaText: { fontFamily: theme.fonts.heading, fontSize: 17, fontWeight: '800', color: '#1a1a1a' },
  disclaimer: { fontFamily: theme.fonts.body, fontSize: 11, color: theme.colors.onInkMuted, textAlign: 'center', marginTop: theme.spacing.sm },
  refresh: { alignItems: 'center', minHeight: 40, justifyContent: 'center', marginTop: theme.spacing.md },
  refreshText: { fontFamily: theme.fonts.body, fontSize: 12, color: theme.colors.onInkMuted, textDecorationLine: 'underline' },
  pressed: { opacity: 0.85 },
});
