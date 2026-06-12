import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { capture } from '@/lib/analytics';
import { createApiClient, type LeadChannel, type Mechanic } from '@/lib/api';
import { t } from '@/lib/i18n';
import { goBack } from '@/lib/nav';
import { cityFromPlate } from '@/lib/plateCity';
import { selectCurrentVehicle, useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';

function MechanicCard({
  mechanic,
  onLead,
}: {
  mechanic: Mechanic;
  onLead: (channel: LeadChannel) => void;
}) {
  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.name}>{mechanic.name}</Text>
        {mechanic.verified && (
          <View style={styles.verified}>
            <Ionicons name="checkmark-circle" size={13} color={theme.colors.okSoftText} />
            <Text style={styles.verifiedText}>{t('mechanics.verified')}</Text>
          </View>
        )}
      </View>
      {(mechanic.district || mechanic.city) && (
        <Text style={styles.location}>
          {[mechanic.district, mechanic.city].filter(Boolean).join(' · ')}
        </Text>
      )}
      {mechanic.specialties && <Text style={styles.specialties}>{mechanic.specialties}</Text>}

      <View style={styles.actions}>
        <Pressable
          accessibilityRole="button"
          onPress={() => onLead('call')}
          style={({ pressed }) => [styles.action, styles.actionPrimary, pressed && styles.pressed]}
        >
          <Ionicons name="call" size={16} color={theme.colors.onInk} />
          <Text style={styles.actionPrimaryText}>{t('mechanics.call')}</Text>
        </Pressable>
        {mechanic.whatsapp && (
          <Pressable
            accessibilityRole="button"
            onPress={() => onLead('whatsapp')}
            style={({ pressed }) => [styles.action, styles.actionOutline, pressed && styles.pressed]}
          >
            <Ionicons name="logo-whatsapp" size={16} color={theme.colors.ink} />
            <Text style={styles.actionOutlineText}>{t('mechanics.whatsapp')}</Text>
          </Pressable>
        )}
        {mechanic.maps_url && (
          <Pressable
            accessibilityRole="button"
            onPress={() => onLead('directions')}
            style={({ pressed }) => [styles.action, styles.actionOutline, pressed && styles.pressed]}
          >
            <Ionicons name="navigate" size={16} color={theme.colors.ink} />
            <Text style={styles.actionOutlineText}>{t('mechanics.directions')}</Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}

export default function MechanicsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ system?: string; sessionId?: string }>();
  const authToken = useUstaStore((s) => s.authToken);
  const vehicle = useUstaStore(selectCurrentVehicle);

  const client = useMemo(() => createApiClient(undefined, () => authToken), [authToken]);

  const system = typeof params.system === 'string' && params.system.length > 0 ? params.system : undefined;
  const sessionId =
    typeof params.sessionId === 'string' && params.sessionId.length > 0
      ? Number(params.sessionId)
      : undefined;
  const plateCity = cityFromPlate(vehicle?.plate);

  const [mechanics, setMechanics] = useState<Mechanic[]>([]);
  const [loading, setLoading] = useState(true);
  const [allCities, setAllCities] = useState(false); // şehir filtresi gevşetildi mi

  const load = useCallback(async () => {
    setLoading(true);
    const city = allCities ? undefined : plateCity ?? undefined;
    try {
      let list = await client.getMechanics(city, system);
      // Şehirde sonuç yoksa otomatik olarak tüm şehirlere düş.
      if (list.length === 0 && city != null) {
        list = await client.getMechanics(undefined, system);
        if (list.length > 0) setAllCities(true);
      }
      setMechanics(list);
    } catch {
      setMechanics([]);
    } finally {
      setLoading(false);
    }
  }, [client, plateCity, system, allCities]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleLead(m: Mechanic, channel: LeadChannel) {
    void client.sendMechanicLead(m.id, channel, sessionId);
    void capture('mechanic_lead', { channel, system: system ?? null });
    let url: string | null = null;
    if (channel === 'call') url = `tel:${m.phone}`;
    else if (channel === 'whatsapp' && m.whatsapp) {
      url = `https://wa.me/${m.whatsapp.replace(/[^\d]/g, '')}`;
    } else if (channel === 'directions' && m.maps_url) url = m.maps_url;
    if (url) {
      try {
        await Linking.openURL(url);
      } catch {
        /* açılamadı — lead yine kaydedildi */
      }
    }
  }

  const scopeLabel = allCities
    ? t('mechanics.allCities')
    : plateCity ?? t('mechanics.allCities');

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
        <Text style={styles.title}>{t('mechanics.title')}</Text>
        <Text style={styles.subtitle}>
          {scopeLabel}
          {system ? ` · ${t(`sistem.${system}`)}` : ''}
        </Text>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={theme.colors.ink} />
        </View>
      ) : mechanics.length === 0 ? (
        <View style={styles.center}>
          <Ionicons name="construct-outline" size={48} color={theme.colors.textSecondary} />
          <Text style={styles.emptyText}>{t('mechanics.empty')}</Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + theme.spacing.xl }]}
          showsVerticalScrollIndicator={false}
        >
          <Text style={styles.disclaimer}>{t('mechanics.disclaimer')}</Text>
          {!allCities && plateCity != null && (
            <Pressable
              accessibilityRole="button"
              onPress={() => setAllCities(true)}
              style={({ pressed }) => [styles.allCitiesBtn, pressed && styles.pressed]}
            >
              <Ionicons name="globe-outline" size={15} color={theme.colors.ink} />
              <Text style={styles.allCitiesText}>{t('mechanics.showAll')}</Text>
            </Pressable>
          )}
          {mechanics.map((m) => (
            <MechanicCard key={m.id} mechanic={m} onLead={(c) => void handleLead(m, c)} />
          ))}
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
    gap: 2,
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
  subtitle: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textSecondary,
  },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: theme.spacing.md, padding: theme.spacing.lg },
  emptyText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  scroll: { paddingHorizontal: theme.spacing.lg },
  disclaimer: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.md,
  },
  allCitiesBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: theme.spacing.xs,
    paddingVertical: 6,
    paddingHorizontal: theme.spacing.md,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.colors.border,
    marginBottom: theme.spacing.md,
  },
  allCitiesText: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    fontWeight: '700',
    color: theme.colors.ink,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.md,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.spacing.sm,
  },
  name: {
    flex: 1,
    fontFamily: theme.fonts.heading,
    fontSize: 17,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  verified: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: theme.colors.okSoftBg,
    borderRadius: theme.radius.pill,
    paddingVertical: 2,
    paddingHorizontal: theme.spacing.sm,
  },
  verifiedText: {
    fontFamily: theme.fonts.body,
    fontSize: 10,
    fontWeight: '700',
    color: theme.colors.okSoftText,
  },
  location: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  specialties: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.textPrimary,
    marginTop: theme.spacing.sm,
  },
  actions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
    marginTop: theme.spacing.md,
  },
  action: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    minHeight: 44,
    paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radius.md,
  },
  actionPrimary: { backgroundColor: theme.colors.ink },
  actionPrimaryText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  actionOutline: {
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.background,
  },
  actionOutlineText: {
    fontFamily: theme.fonts.body,
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.ink,
  },
  pressed: { opacity: 0.85 },
});
