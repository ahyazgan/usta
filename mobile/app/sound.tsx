import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { BottomTabBar } from '@/components/BottomTabBar';
import { FeedbackRow } from '@/components/FeedbackRow';
import type { Guven, KayitKosulu } from '@/lib/api';
import { t } from '@/lib/i18n';
import { theme } from '@/lib/theme';
import { useSoundDiagnose } from '@/lib/useSoundDiagnose';
import { useVehicles } from '@/lib/useVehicles';

const CONDITIONS: KayitKosulu[] = ['rolanti', 'gazda', 'soguk_motor', 'seyirde'];

/** Sohbet balonu türleri (mockup ekran 3). */
interface Msg {
  id: number;
  kind: 'usta' | 'user' | 'warning';
  text: string;
  /** Usta balonunda güven satırı. */
  conf?: Guven;
  /** Usta balonunda küçük meta satırı (kategori · aciliyet). */
  meta?: string;
}

function ModeCard({
  icon,
  title,
  desc,
  active,
  onPress,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  desc: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      onPress={onPress}
      style={({ pressed }) => [styles.modeCard, active && styles.modeCardActive, pressed && styles.pressed]}
    >
      <View style={[styles.modeIcon, active && styles.modeIconActive]}>
        <Ionicons name={icon} size={22} color={active ? theme.colors.onInk : theme.colors.ink} />
      </View>
      <Text style={styles.modeTitle}>{title}</Text>
      <Text style={styles.modeDesc}>{desc}</Text>
    </Pressable>
  );
}

function Bubble({ msg }: { msg: Msg }) {
  if (msg.kind === 'warning') {
    return (
      <View style={styles.warnBubble}>
        <Ionicons name="warning" size={16} color={theme.colors.urgentSoftText} />
        <Text style={styles.warnBubbleText}>{msg.text}</Text>
      </View>
    );
  }
  const isUsta = msg.kind === 'usta';
  return (
    <View style={[styles.bubble, isUsta ? styles.bubbleUsta : styles.bubbleUser]}>
      <Text style={isUsta ? styles.bubbleUstaText : styles.bubbleUserText}>{msg.text}</Text>
      {isUsta && (msg.conf != null || msg.meta != null) && (
        <View style={styles.confRow}>
          <View style={styles.confDot} />
          <Text style={styles.confText}>
            {[msg.conf != null ? t(`camera.guven.${msg.conf}`) : null, msg.meta]
              .filter(Boolean)
              .join(' · ')}
          </Text>
        </View>
      )}
    </View>
  );
}

let nextId = 1;

export default function DiagnosisScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { currentVehicle } = useVehicles();
  const { loading, error, result, runSoundDiagnose } = useSoundDiagnose();

  const [description, setDescription] = useState('');
  const [condition, setCondition] = useState<KayitKosulu>('rolanti');
  const [messages, setMessages] = useState<Msg[]>([
    { id: 0, kind: 'usta', text: t('diagnosis.intro') },
  ]);
  const [showMechanic, setShowMechanic] = useState(false);
  const scrollRef = useRef<ScrollView>(null);

  // Yeni teşhis sonucu geldiğinde usta balonları olarak akışa ekle.
  useEffect(() => {
    if (result == null) return;
    const additions: Msg[] = [
      {
        id: nextId++,
        kind: 'usta',
        text: result.tespit,
        conf: result.guven,
        meta: `${t(`sound.kategori.${result.ses_kategorisi}`)} · ${t(
          `sound.aciliyet.${result.aciliyet}`,
        )}`,
      },
    ];
    if (result.guvenlik_uyarisi != null && result.guvenlik_uyarisi.length > 0) {
      additions.push({ id: nextId++, kind: 'warning', text: result.guvenlik_uyarisi });
    }
    additions.push({ id: nextId++, kind: 'usta', text: result.sonraki_adim });
    setMessages((m) => [...m, ...additions]);
    setShowMechanic(result.tamirciye_git_onerisi === true);
  }, [result]);

  // Akış uzadıkça en alta kay.
  useEffect(() => {
    const id = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 80);
    return () => clearTimeout(id);
  }, [messages, loading]);

  function handleSend() {
    const text = description.trim();
    if (text.length === 0 || loading) return;
    setMessages((m) => [
      ...m,
      {
        id: nextId++,
        kind: 'user',
        text: `${text} (${t(`sound.condition.${condition}`)})`,
      },
    ]);
    setDescription('');
    void runSoundDiagnose(text, condition);
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      <View style={styles.header}>
        <Text style={styles.title}>{t('diagnosis.title')}</Text>
        {currentVehicle && (
          <View style={styles.carTag}>
            <Ionicons name="car-sport" size={13} color={theme.colors.textSecondary} />
            <Text style={styles.carTagText}>
              {currentVehicle.make} {currentVehicle.model}
            </Text>
          </View>
        )}
      </View>

      {/* Göster / Dinlet modları */}
      <View style={styles.modeGrid}>
        <ModeCard
          icon="camera"
          title={t('diagnosis.show.title')}
          desc={t('diagnosis.show.desc')}
          active={false}
          onPress={() => router.replace('/maintenance')}
        />
        <ModeCard
          icon="pulse"
          title={t('diagnosis.listen.title')}
          desc={t('diagnosis.listen.desc')}
          active
          onPress={() => undefined}
        />
      </View>

      {/* Sohbet akışı */}
      <ScrollView
        ref={scrollRef}
        style={styles.chat}
        contentContainerStyle={styles.chatContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.chatLabel}>{t('diagnosis.chatLabel')}</Text>
        {messages.map((msg) => (
          <Bubble key={msg.id} msg={msg} />
        ))}
        {loading && (
          <View style={[styles.bubble, styles.bubbleUsta, styles.typing]}>
            <ActivityIndicator size="small" color={theme.colors.onInk} />
            <Text style={styles.bubbleUstaText}>{t('sound.analyzing')}</Text>
          </View>
        )}
        {error && (
          <View style={styles.errorRow}>
            <Ionicons name="alert-circle" size={16} color={theme.colors.dangerBright} />
            <Text style={styles.errorText}>{t(error)}</Text>
          </View>
        )}
        {/* Veri çarkı: son teşhis doğru çıktı mı? */}
        {result?.session_id != null && currentVehicle != null && !loading && (
          <View style={styles.feedbackWrap}>
            <FeedbackRow
              key={result.session_id}
              vehicleId={currentVehicle.id}
              sessionId={result.session_id}
            />
          </View>
        )}
        {showMechanic && (
          <Pressable
            accessibilityRole="button"
            onPress={() => router.replace('/maintenance')}
            style={({ pressed }) => [styles.mechanicButton, pressed && styles.pressed]}
          >
            <Ionicons name="construct" size={16} color={theme.colors.onInk} />
            <Text style={styles.mechanicText}>{t('common.goToMechanic')}</Text>
          </Pressable>
        )}
      </ScrollView>

      {/* Yazma alanı */}
      <View style={styles.composer}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.conditionRow}
        >
          {CONDITIONS.map((c) => {
            const selected = condition === c;
            return (
              <Pressable
                key={c}
                accessibilityRole="button"
                accessibilityState={{ selected }}
                onPress={() => setCondition(c)}
                style={({ pressed }) => [
                  styles.conditionChip,
                  selected && styles.conditionChipSelected,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={[styles.conditionLabel, selected && styles.conditionLabelSelected]}>
                  {t(`sound.condition.${c}`)}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={description}
            onChangeText={setDescription}
            placeholder={t('sound.descriptionPlaceholder')}
            placeholderTextColor={theme.colors.textSecondary}
            multiline
            onSubmitEditing={handleSend}
          />
          <Pressable
            accessibilityRole="button"
            accessibilityState={{ disabled: loading || description.trim().length === 0 }}
            disabled={loading || description.trim().length === 0}
            onPress={handleSend}
            style={({ pressed }) => [
              styles.send,
              (loading || description.trim().length === 0) && styles.sendDisabled,
              pressed && styles.pressed,
            ]}
          >
            <Ionicons name="arrow-up" size={20} color={theme.colors.onInk} />
          </Pressable>
        </View>
      </View>

      <BottomTabBar active="diagnosis" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background },
  header: {
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.sm,
    gap: theme.spacing.xs,
  },
  title: {
    fontFamily: theme.fonts.heading,
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    letterSpacing: -0.3,
  },
  carTag: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: theme.spacing.xs,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingVertical: 3,
    paddingHorizontal: theme.spacing.md,
  },
  carTagText: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    fontWeight: '500',
    color: theme.colors.textSecondary,
  },
  modeGrid: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
  },
  modeCard: {
    flex: 1,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1.5,
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
    alignItems: 'center',
    gap: 2,
  },
  modeCardActive: { borderColor: theme.colors.ink },
  modeIcon: {
    width: 40,
    height: 40,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 2,
  },
  modeIconActive: { backgroundColor: theme.colors.ink },
  modeTitle: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    fontWeight: '700',
    color: theme.colors.textPrimary,
  },
  modeDesc: {
    fontFamily: theme.fonts.body,
    fontSize: 10,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    lineHeight: 14,
  },
  chat: { flex: 1 },
  chatContent: {
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.md,
  },
  chatLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 11,
    fontWeight: '600',
    color: theme.colors.textSecondary,
    letterSpacing: 0.6,
    textTransform: 'uppercase',
    marginBottom: theme.spacing.sm,
  },
  bubble: {
    borderRadius: theme.radius.lg,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    marginBottom: theme.spacing.sm,
    maxWidth: '90%',
  },
  bubbleUsta: {
    backgroundColor: theme.colors.ink,
    borderBottomLeftRadius: 4,
    alignSelf: 'flex-start',
  },
  bubbleUser: {
    backgroundColor: theme.colors.border,
    borderBottomRightRadius: 4,
    alignSelf: 'flex-end',
  },
  bubbleUstaText: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    lineHeight: 20,
    color: theme.colors.onInk,
  },
  bubbleUserText: {
    fontFamily: theme.fonts.body,
    fontSize: 13,
    lineHeight: 20,
    color: theme.colors.textPrimary,
  },
  confRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    marginTop: theme.spacing.sm,
  },
  confDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: theme.colors.successBright,
  },
  confText: {
    fontFamily: theme.fonts.body,
    fontSize: 10,
    color: theme.colors.onInkMuted,
  },
  warnBubble: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.sm,
    backgroundColor: theme.colors.urgentSoftBg,
    borderRadius: theme.radius.md,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.sm,
    maxWidth: '95%',
    alignSelf: 'flex-start',
  },
  warnBubbleText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 12,
    lineHeight: 18,
    color: theme.colors.urgentSoftText,
  },
  typing: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  errorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    paddingVertical: theme.spacing.sm,
  },
  errorText: {
    flex: 1,
    fontFamily: theme.fonts.body,
    fontSize: 13,
    color: theme.colors.dangerBright,
  },
  feedbackWrap: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: theme.spacing.md,
    marginTop: theme.spacing.xs,
    marginBottom: theme.spacing.sm,
  },
  mechanicButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: 48,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.ink,
    marginTop: theme.spacing.sm,
  },
  mechanicText: {
    fontFamily: theme.fonts.heading,
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.onInk,
  },
  composer: {
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
    paddingTop: theme.spacing.sm,
    paddingBottom: theme.spacing.sm,
    gap: theme.spacing.sm,
  },
  conditionRow: {
    gap: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
  },
  conditionChip: {
    minHeight: 36,
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.spacing.md,
    backgroundColor: theme.colors.surface,
  },
  conditionChipSelected: {
    backgroundColor: theme.colors.ink,
    borderColor: theme.colors.ink,
  },
  conditionLabel: {
    fontFamily: theme.fonts.body,
    fontSize: 12,
    fontWeight: '700',
    color: theme.colors.textSecondary,
  },
  conditionLabelSelected: { color: theme.colors.onInk },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 110,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
    fontFamily: theme.fonts.body,
    fontSize: 14,
    color: theme.colors.textPrimary,
  },
  send: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: theme.colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendDisabled: { opacity: 0.4 },
  pressed: { opacity: 0.85 },
});
