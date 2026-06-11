/**
 * "Gece Garajı" (Night Garage) design tokens for Usta.
 * Dark theme is the default and only theme.
 */

export const colors = {
  /** zemin */
  background: '#16181D',
  /** yüzey */
  surface: '#1D2026',
  border: '#2A2D34',
  /** vurgu / amber */
  accent: '#FF8A00',
  /** ✓ — green ONLY for verification / correct-place state */
  success: '#22C55E',
  /** ✗ */
  danger: '#EF4444',
  /** uyarı */
  warning: '#EAB308',
  textPrimary: '#F2F3F5',
  textSecondary: '#8B8E96',
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
