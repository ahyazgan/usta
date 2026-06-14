/**
 * "Gündüz Servisi" (Daylight Service) design tokens for Usta.
 * Light theme — cream surfaces, ink-black primary, green for healthy state.
 * (Mockup-aligned redesign; replaces the former dark "Gece Garajı" theme.)
 */

export const colors = {
  /** sayfa zemini (krem) */
  background: '#FAFAF8',
  /** kart yüzeyi */
  surface: '#FFFFFF',
  border: '#EBEBEB',
  /** birincil eylem / mürekkep — koyu kartlar ve ana butonlar */
  ink: '#111111',
  /** vurgu = birincil mürekkep (eski amber yerine) */
  accent: '#111111',
  /** olumlu / sağlıklı / ✓ doğrulama */
  success: '#1D9E75',
  /** sağlık çubuğu / canlı yeşil */
  successBright: '#2ECC71',
  /** ✗ / acil */
  danger: '#C0392B',
  dangerBright: '#E24B4A',
  /** uyarı / yaklaşıyor */
  warning: '#BA7517',
  warningBright: '#F59E0B',
  textPrimary: '#111111',
  textSecondary: '#888888',
  /** koyu kart üzerindeki metin */
  onInk: '#FFFFFF',
  onInkMuted: 'rgba(255,255,255,0.55)',

  /** durum rozeti / yumuşak zeminler */
  okSoftBg: '#E8F8F2',
  okSoftText: '#1D9E75',
  warnSoftBg: '#FFF3E0',
  warnSoftText: '#BA7517',
  urgentSoftBg: '#FEECEC',
  urgentSoftText: '#C0392B',
  /** tasarruf bandı */
  savingsBg: '#F0FBF6',
  savingsBorder: '#C8EFE0',
  savingsText: '#0F6E56',
} as const;

export const fonts = {
  heading: 'Barlow Condensed',
  body: 'Inter',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radius = {
  sm: 6,
  md: 12,
  lg: 20,
  pill: 999,
} as const;

/** Minimum touch target for a gloved hand (dp). */
export const touchTarget = 56;

export const theme = {
  colors,
  fonts,
  spacing,
  radius,
  touchTarget,
} as const;

export type Theme = typeof theme;
export type ThemeColors = typeof colors;

export default theme;
