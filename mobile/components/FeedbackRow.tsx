import { Ionicons } from '@expo/vector-icons';
import { useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { createApiClient } from '@/lib/api';
import { t } from '@/lib/i18n';
import { useUstaStore } from '@/lib/store';
import { theme } from '@/lib/theme';

/**
 * "Bu teşhis doğru çıktı mı?" 👍/👎 satırı.
 *
 * Veri çarkının en değerli etiketi: kullanıcı doğrulaması, ham AI tahminlerini
 * doğrulanmış arıza-örüntü verisine çevirir. Oylama sessizce gönderilir,
 * başarısız olursa kullanıcı engellenmez (tekrar dokunabilir).
 */
export function FeedbackRow({
  vehicleId,
  sessionId,
  initial = null,
}: {
  vehicleId: number;
  sessionId: number;
  /** Önceden verilmiş oy (geçmiş listesinde dolu gelir). */
  initial?: boolean | null;
}) {
  const authToken = useUstaStore((s) => s.authToken);
  const client = useMemo(
    () => createApiClient(undefined, () => authToken),
    [authToken],
  );
  const [vote, setVote] = useState<boolean | null>(initial);
  const [sending, setSending] = useState(false);

  async function send(dogru: boolean) {
    if (sending) return;
    setSending(true);
    try {
      await client.sendDiagnosisFeedback(vehicleId, sessionId, dogru);
      setVote(dogru);
    } catch {
      /* ağ hatası — sessiz; kullanıcı tekrar dokunabilir */
    } finally {
      setSending(false);
    }
  }

  return (
    <View style={styles.row}>
      <Text style={styles.question}>
        {vote == null ? t('feedback.question') : t('feedback.thanks')}
      </Text>
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ selected: vote === true, disabled: sending }}
        disabled={sending}
        onPress={() => void send(true)}
        style={({ pressed }) => [
          styles.thumb,
          vote === true && styles.thumbUp,
          pressed && styles.pressed,
        ]}
      >
        <Ionicons
          name={vote === true ? 'thumbs-up' : 'thumbs-up-outline'}
          size={16}
          color={vote === true ? theme.colors.okSoftText : theme.colors.textSecondary}
        />
      </Pressable>
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ selected: vote === false, disabled: sending }}
        disabled={sending}
        onPress={() => void send(false)}
        style={({ pressed }) => [
          styles.thumb,
          vote === false && styles.thumbDown,
          pressed && styles.pressed,
        ]}
      >
        <Ionicons
          name={vote === false ? 'thumbs-down' : 'thumbs-down-outline'}
          size={16}
          color={vote === false ? theme.colors.urgentSoftText : theme.colors.textSecondary}
        />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  question: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  thumb: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  thumbUp: {
    backgroundColor: theme.colors.okSoftBg,
    borderColor: theme.colors.okSoftText,
  },
  thumbDown: {
    backgroundColor: theme.colors.urgentSoftBg,
    borderColor: theme.colors.urgentSoftText,
  },
  pressed: { opacity: 0.8 },
});

export default FeedbackRow;
