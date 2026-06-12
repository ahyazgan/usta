import type { Ionicons } from '@expo/vector-icons';

/** Görev id → temsilî ikon (Ana Sayfa + Bakım listelerinde ortak). */
export const TASK_ICON: Record<string, keyof typeof Ionicons.glyphMap> = {
  oil_change: 'water',
  spark_plug: 'flash',
  battery: 'battery-charging',
  brake_check: 'disc',
  air_filter: 'funnel',
  cabin_filter: 'leaf',
  coolant: 'thermometer',
  tire: 'ellipse',
  wiper: 'rainy',
  headlight: 'bulb',
};

export default TASK_ICON;
