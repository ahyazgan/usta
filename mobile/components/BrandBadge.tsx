import { Image, StyleSheet, Text, View } from 'react-native';

import { brandInitials, brandLogo } from '@/lib/brandLogo';
import { theme } from '@/lib/theme';

/**
 * Marka rozeti — logo kayıtlıysa logoyu, değilse baş-harf dairesini gösterir.
 * Logolar kullanıcı tarafından `lib/brandLogo.ts` + `assets/logos/`'a eklenir;
 * eklenene kadar baş-harf yedeğiyle çalışır (bkz. brandLogo.ts).
 */
export function BrandBadge({
  make,
  size = 36,
  onInk = false,
}: {
  make: string | null | undefined;
  size?: number;
  /** Koyu zemin üstünde mi (araç kartı) — yedek rozet rengini ayarlar. */
  onInk?: boolean;
}) {
  const logo = brandLogo(make);
  const radius = size / 2;

  if (logo != null) {
    return (
      <Image
        source={logo}
        resizeMode="contain"
        accessibilityLabel={make ?? undefined}
        style={{ width: size, height: size, borderRadius: radius }}
      />
    );
  }

  return (
    <View
      style={[
        styles.fallback,
        {
          width: size,
          height: size,
          borderRadius: radius,
          backgroundColor: onInk ? 'rgba(255,255,255,0.14)' : theme.colors.background,
          borderColor: onInk ? 'rgba(255,255,255,0.22)' : theme.colors.border,
        },
      ]}
    >
      <Text
        style={[
          styles.initials,
          { fontSize: size * 0.36, color: onInk ? theme.colors.onInk : theme.colors.textPrimary },
        ]}
      >
        {brandInitials(make)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  fallback: {
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
  },
  initials: {
    fontFamily: theme.fonts.heading,
    fontWeight: '700',
  },
});

export default BrandBadge;
