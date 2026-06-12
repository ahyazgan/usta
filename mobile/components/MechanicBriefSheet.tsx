import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { capture } from '@/lib/analytics';
import type { Vehicle } from '@/lib/api';
import { t } from '@/lib/i18n';
import { buildBriefText, type BriefDiag } from '@/lib/mechanicBrief';
import { shareMechanicBrief } from '@/lib/share';
import { theme } from '@/lib/theme';

/**
 * "Mekaniğe Göster" alt sayfası — teşhisi profesyonel bir özet kartı olarak
 * gösterir; tamirciye ekranı göster ya da Paylaş ile gönder. Triyaj köprüsü:
 * DIY yapmayacak kullanıcıyı çıkmaz sokağa değil, değerli bir çıktıya götürür.
 */
export function MechanicBriefSheet({
  visible,
  vehicle,
  diag,
  onClose,
}: {
  visible: boolean;
  vehicle: Vehicle | null;
  diag: BriefDiag | null;
  onClose: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    if (visible) void capture('mechanic_brief_opened');
  }, [visible]);

  const text = vehicle != null && diag != null ? buildBriefText(vehicle, diag) : '';

  function findMechanic() {
    onClose();
    router.push({
      pathname: '/mechanics',
      params: {
        system: diag?.sistem ?? '',
        sessionId: diag?.sessionId != null ? String(diag.sessionId) : '',
      },
    });
  }

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <View style={styles.header}>
            <View style={styles.headerText}>
              <Ionicons name="construct" size={18} color={theme.colors.ink} />
              <Text style={styles.title}>{t('brief.sheetTitle')}</Text>
            </View>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={t('common.cancel')}
              onPress={onClose}
              style={({ pressed }) => [styles.close, pressed && styles.pressed]}
            >
              <Ionicons name="close" size={22} color={theme.colors.textSecondary} />
            </Pressable>
          </View>

          <Text style={styles.hint}>{t('brief.sheetHint')}</Text>

          <ScrollView style={styles.cardScroll} contentContainerStyle={styles.card}>
            <Text style={styles.briefText}>{text}</Text>
          </ScrollView>

          <Pressable
            accessibilityRole="button"
            onPress={findMechanic}
            style={({ pressed }) => [styles.findButton, pressed && styles.pressed]}
          >
            <Ionicons name="location" size={18} color={theme.colors.ink} />
            <Text style={styles.findText}>{t('brief.findMechanic')}</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            onPress={() => void shareMechanicBrief(text)}
            style={({ pressed }) => [styles.shareButton, pressed && styles.pressed]}
          >
            <Ionicons name="share-social" size={18} color={theme.colors.onInk} />
            <Text style={styles.shareText}>{t('brief.share')}</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: theme.colors.background,
    borderTopLeftRadius: theme.radius.lg,
    borderTopRightRadius: theme.radius.lg,
    padding: theme.spacing.lg,
    paddingBottom: theme.spacing.xl,
    maxHeight: '88%',
  },
  handle: {
    alignSelf: 'center',
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: theme.colors.border,
    marginBottom: theme.spacing.md,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  headerText: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  close: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  hint: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
    marginBottom: theme.spacing.md,
  },
  cardScroll: {
    flexGrow: 0,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.lg,
  },
  briefText: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    lineHeight: 21,
    color: theme.colors.textPrimary,
  },
  findButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    borderWidth: 1.5,
    borderColor: theme.colors.ink,
    marginTop: theme.spacing.md,
  },
  findText: {
    fontFamily: theme.fonts.heading,
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.ink,
  },
  shareButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.ink,
    marginTop: theme.spacing.sm,
  },
  shareText: {
    fontFamily: theme.fonts.heading,
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  pressed: { opacity: 0.85 },
});

export default MechanicBriefSheet;
