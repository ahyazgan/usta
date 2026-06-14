/**
 * Compact 2-column grid of AI/utility tools for the home screen.
 *
 * Replaces the old stack of six full-width "priceGuide" rows that pushed the
 * vehicle card far down the page and all looked alike. A grid makes the
 * "what can I do here" set scannable at a glance and frees vertical space so
 * the user's car + health score sit near the top.
 */
import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { t } from '@/lib/i18n';
import { theme } from '@/lib/theme';

export interface AiTool {
  key: string;
  icon: keyof typeof Ionicons.glyphMap;
  /** i18n key for the short label. */
  labelKey: string;
  /** Accent the icon (e.g. warning tools); default uses surface tint. */
  tint?: string;
  onPress: () => void;
}

function ToolTile({ tool }: { tool: AiTool }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={t(tool.labelKey)}
      onPress={tool.onPress}
      style={({ pressed }) => [styles.tile, pressed && styles.pressed]}
    >
      <View style={styles.iconWrap}>
        <Ionicons name={tool.icon} size={24} color={tool.tint ?? theme.colors.accent} />
      </View>
      <Text style={styles.label} numberOfLines={2}>
        {t(tool.labelKey)}
      </Text>
    </Pressable>
  );
}

export function AiToolsGrid({ tools }: { tools: AiTool[] }) {
  return (
    <View style={styles.grid}>
      {tools.map((tool) => (
        <ToolTile key={tool.key} tool={tool} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
  },
  tile: {
    // İki sütun: yarı genişlik eksi yarım gap. % ile sağlam (gap row'da).
    width: '48%',
    flexGrow: 1,
    minHeight: 88,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
    gap: theme.spacing.sm,
    justifyContent: 'center',
  },
  iconWrap: {
    width: 44,
    height: 44,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.textPrimary,
    lineHeight: 17,
  },
  pressed: {
    opacity: 0.85,
  },
});

export default AiToolsGrid;
