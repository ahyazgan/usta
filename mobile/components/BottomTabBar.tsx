import { Ionicons } from '@expo/vector-icons';
import { usePathname, useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { t } from '@/lib/i18n';
import { theme } from '@/lib/theme';

type TabKey = 'home' | 'diagnosis' | 'maintenance' | 'history' | 'settings';

interface TabDef {
  key: TabKey;
  route: '/' | '/sound' | '/maintenance' | '/history' | '/settings';
  icon: keyof typeof Ionicons.glyphMap;
  labelKey: string;
  /** Show a small attention dot (e.g. pending diagnosis). */
  badge?: boolean;
}

const TABS: TabDef[] = [
  { key: 'home', route: '/', icon: 'home', labelKey: 'tabs.home' },
  { key: 'diagnosis', route: '/sound', icon: 'pulse', labelKey: 'tabs.diagnosis' },
  { key: 'maintenance', route: '/maintenance', icon: 'construct', labelKey: 'tabs.maintenance' },
  { key: 'history', route: '/history', icon: 'time', labelKey: 'tabs.history' },
  { key: 'settings', route: '/settings', icon: 'person', labelKey: 'tabs.settings' },
];

/**
 * Bottom tab bar shared across the main screens. Presentational: it reads the
 * current pathname to highlight the active tab and routes on press. (A future
 * phase may migrate this to an expo-router Tabs navigator.)
 */
export function BottomTabBar({ active }: { active: TabKey }) {
  const router = useRouter();
  const pathname = usePathname();
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.bar, { paddingBottom: Math.max(insets.bottom, theme.spacing.sm) }]}>
      {TABS.map((tab) => {
        const isActive = tab.key === active;
        const color = isActive ? theme.colors.ink : theme.colors.textSecondary;
        return (
          <Pressable
            key={tab.key}
            accessibilityRole="tab"
            accessibilityState={{ selected: isActive }}
            onPress={() => {
              if (pathname !== tab.route) router.replace(tab.route);
            }}
            style={styles.item}
          >
            <View>
              <Ionicons name={tab.icon} size={22} color={color} />
              {tab.badge && <View style={styles.badge} />}
            </View>
            <Text style={[styles.label, { color }]}>{t(tab.labelKey)}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
    paddingTop: theme.spacing.sm,
  },
  item: {
    flex: 1,
    alignItems: 'center',
    gap: 3,
    paddingVertical: theme.spacing.xs,
  },
  label: {
    fontFamily: theme.fonts.body,
    fontSize: 10,
    fontWeight: '600',
  },
  badge: {
    position: 'absolute',
    top: -2,
    right: -4,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: theme.colors.dangerBright,
    borderWidth: 1.5,
    borderColor: theme.colors.surface,
  },
});

export default BottomTabBar;
