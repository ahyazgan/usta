import { Ionicons } from '@expo/vector-icons';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { CameraGrid } from '@/components/CameraGrid';
import { isAudioBridgeReady } from '@/lib/live/audioBridge';
import { goBack } from '@/lib/nav';
import { theme } from '@/lib/theme';
import { t } from '@/lib/i18n';
import { useLiveSession } from '@/lib/useLiveSession';
import { useVehicles } from '@/lib/useVehicles';

const FRAME_INTERVAL_MS = 2000; // kare/2sn — düşük fps, maliyet için

function mmss(total: number): string {
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function LiveScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ task?: string }>();
  const { currentVehicle } = useVehicles();
  const cameraRef = useRef<CameraView>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const scrollRef = useRef<ScrollView>(null);

  const vtype = currentVehicle?.vehicle_type === 'motosiklet' ? 'motosiklet' : 'araba';
  const { status, lines, elapsed, error, premiumRequired, start, stop, sendFrame } =
    useLiveSession(vtype);

  const live = status === 'live';

  // Canlıyken periyodik kamera karesi gönder (hareket yerine sade aralık).
  useEffect(() => {
    if (!live) return;
    const id = setInterval(async () => {
      const cam = cameraRef.current;
      if (cam == null) return;
      try {
        const photo = await cam.takePictureAsync({ base64: true, quality: 0.4, skipProcessing: true });
        if (photo?.base64) sendFrame(photo.base64);
      } catch {
        /* kare atla */
      }
    }, FRAME_INTERVAL_MS);
    return () => clearInterval(id);
  }, [live, sendFrame]);

  // Ekrandan çıkınca oturumu kapat (metering + kaynak).
  useEffect(() => () => void stop(), [stop]);

  // Döküm uzadıkça en alta kay.
  useEffect(() => {
    const id = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 60);
    return () => clearTimeout(id);
  }, [lines]);

  async function handleStart() {
    if (currentVehicle == null) return;
    if (permission?.granted !== true) {
      const res = await requestPermission();
      if (!res.granted) return;
    }
    await start(currentVehicle.id, params.task);
  }

  function handleEnd() {
    void stop();
    goBack(router);
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top + theme.spacing.md }]}>
      <View style={styles.header}>
        <Pressable
          accessibilityRole="button"
          onPress={handleEnd}
          style={({ pressed }) => [styles.back, pressed && styles.pressed]}
        >
          <Ionicons name="chevron-back" size={20} color={theme.colors.onInk} />
          <Text style={styles.backText}>{t('common.back')}</Text>
        </Pressable>
        <View style={styles.statusPill}>
          <View style={[styles.dot, live && styles.dotLive]} />
          <Text style={styles.statusText}>
            {t(`live.status.${status}`)} · {mmss(elapsed)}
          </Text>
        </View>
      </View>

      {/* Kamera önizleme */}
      <View style={styles.cameraWrap}>
        {permission?.granted === true ? (
          <>
            <CameraView ref={cameraRef} style={styles.camera} facing="back" />
            <CameraGrid />
          </>
        ) : (
          <View style={styles.cameraPlaceholder}>
            <Ionicons name="camera-outline" size={48} color={theme.colors.onInkMuted} />
            <Text style={styles.placeholderText}>{t('live.cameraHint')}</Text>
          </View>
        )}
      </View>

      {/* Ses köprüsü uyarısı (dev-build'de bağlanır) */}
      {!isAudioBridgeReady() && (
        <View style={styles.audioWarn}>
          <Ionicons name="warning" size={14} color={theme.colors.warnSoftText} />
          <Text style={styles.audioWarnText}>{t('live.audioNotReady')}</Text>
        </View>
      )}

      {/* Döküm */}
      <ScrollView ref={scrollRef} style={styles.transcript} contentContainerStyle={styles.transcriptInner}>
        {lines.length === 0 ? (
          <Text style={styles.hint}>{t('live.intro')}</Text>
        ) : (
          lines.map((l) => (
            <View key={l.id} style={[styles.bubble, l.role === 'user' ? styles.bubbleUser : styles.bubbleUsta]}>
              <Text style={l.role === 'user' ? styles.bubbleUserText : styles.bubbleUstaText}>{l.text}</Text>
            </View>
          ))
        )}
        {error != null && <Text style={styles.errorText}>{t(error) !== error ? t(error) : error}</Text>}
      </ScrollView>

      {/* Kontroller */}
      <View style={[styles.footer, { paddingBottom: insets.bottom + theme.spacing.md }]}>
        {premiumRequired ? (
          <Pressable
            accessibilityRole="button"
            onPress={() => router.push('/premium')}
            style={({ pressed }) => [styles.startBtn, pressed && styles.pressed]}
          >
            <Ionicons name="star" size={20} color={theme.colors.ink} />
            <Text style={styles.startText}>{t('premium.cta')}</Text>
          </Pressable>
        ) : status === 'connecting' ? (
          <View style={styles.connecting}>
            <ActivityIndicator color={theme.colors.onInk} />
            <Text style={styles.connectingText}>{t('live.connecting')}</Text>
          </View>
        ) : live ? (
          <Pressable
            accessibilityRole="button"
            onPress={handleEnd}
            style={({ pressed }) => [styles.endBtn, pressed && styles.pressed]}
          >
            <Ionicons name="stop-circle" size={20} color={theme.colors.onInk} />
            <Text style={styles.endText}>{t('live.end')}</Text>
          </Pressable>
        ) : (
          <Pressable
            accessibilityRole="button"
            disabled={currentVehicle == null}
            onPress={() => void handleStart()}
            style={({ pressed }) => [styles.startBtn, currentVehicle == null && styles.disabled, pressed && styles.pressed]}
          >
            <Ionicons name="mic" size={20} color={theme.colors.ink} />
            <Text style={styles.startText}>{t('live.start')}</Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.ink },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.sm,
  },
  back: { flexDirection: 'row', alignItems: 'center', minHeight: 32 },
  backText: { fontFamily: theme.fonts.body, fontSize: 13, fontWeight: '600', color: theme.colors.onInk },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderRadius: theme.radius.pill,
    paddingVertical: 4,
    paddingHorizontal: theme.spacing.md,
  },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: theme.colors.onInkMuted },
  dotLive: { backgroundColor: theme.colors.success },
  statusText: { fontFamily: theme.fonts.body, fontSize: 11, fontWeight: '700', color: theme.colors.onInk },
  cameraWrap: {
    marginHorizontal: theme.spacing.lg,
    aspectRatio: 4 / 3,
    borderRadius: theme.radius.lg,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  camera: { flex: 1 },
  cameraPlaceholder: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: theme.spacing.sm },
  placeholderText: { fontFamily: theme.fonts.body, fontSize: 13, color: theme.colors.onInkMuted, textAlign: 'center', paddingHorizontal: theme.spacing.xl },
  audioWarn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    marginHorizontal: theme.spacing.lg,
    marginTop: theme.spacing.sm,
    backgroundColor: theme.colors.warnSoftBg,
    borderRadius: theme.radius.sm,
    paddingVertical: 6,
    paddingHorizontal: theme.spacing.md,
  },
  audioWarnText: { flex: 1, fontFamily: theme.fonts.body, fontSize: 11, color: theme.colors.warnSoftText },
  transcript: { flex: 1, marginTop: theme.spacing.md },
  transcriptInner: { paddingHorizontal: theme.spacing.lg, paddingBottom: theme.spacing.md, gap: theme.spacing.sm },
  hint: { fontFamily: theme.fonts.body, fontSize: 13, color: theme.colors.onInkMuted, textAlign: 'center', marginTop: theme.spacing.lg },
  bubble: { maxWidth: '90%', borderRadius: theme.radius.md, padding: theme.spacing.md },
  bubbleUsta: { alignSelf: 'flex-start', backgroundColor: 'rgba(255,255,255,0.12)' },
  bubbleUser: { alignSelf: 'flex-end', backgroundColor: theme.colors.onInk },
  bubbleUstaText: { fontFamily: theme.fonts.body, fontSize: 14, color: theme.colors.onInk },
  bubbleUserText: { fontFamily: theme.fonts.body, fontSize: 14, color: theme.colors.ink, fontWeight: '600' },
  errorText: { fontFamily: theme.fonts.body, fontSize: 12, color: theme.colors.dangerBright, textAlign: 'center' },
  footer: { paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.sm },
  startBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.onInk,
  },
  startText: { fontFamily: theme.fonts.heading, fontSize: 17, fontWeight: '700', color: theme.colors.ink },
  endBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: theme.touchTarget,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.danger,
  },
  endText: { fontFamily: theme.fonts.heading, fontSize: 17, fontWeight: '700', color: theme.colors.onInk },
  connecting: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: theme.spacing.sm, minHeight: theme.touchTarget },
  connectingText: { fontFamily: theme.fonts.body, fontSize: 14, color: theme.colors.onInk },
  disabled: { opacity: 0.4 },
  pressed: { opacity: 0.85 },
});
