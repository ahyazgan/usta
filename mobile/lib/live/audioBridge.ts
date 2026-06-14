/**
 * Gerçek-zamanlı ses köprüsü — canlı modun NATIVE entegrasyon noktası.
 *
 * Gerçek-zamanlı PCM mikrofon yakalama + oynatma React Native'de native modül
 * ister; **Expo Go yetmez, dev-build gerekir** (bkz. LIVE_SETUP.md). Bu arayüz
 * sözleşmedir; dev-build'de native modülünü `setAudioBridge(...)` ile bağlarsın.
 *
 * Beklenen format: mikrofon PCM16 16kHz mono (Gemini girişi), oynatma PCM16
 * 24kHz mono (Gemini çıkışı). Parçalar base64 string olarak taşınır.
 */
export interface AudioBridge {
  /** Mikrofonu aç; her ses parçası için onChunk(base64Pcm) çağrılır (16kHz). */
  startMic(onChunk: (base64Pcm: string) => void): Promise<void>;
  /** Gemini'den gelen ses parçasını çal (24kHz PCM16). */
  playChunk(base64Pcm: string): Promise<void>;
  /** Mikrofon + oynatmayı durdur, kaynakları bırak. */
  stop(): Promise<void>;
}

/**
 * Varsayılan stub: native modül bağlanana kadar sessizce no-op (uygulama
 * çökmesin diye). Dev-build'de gerçek köprüyle değiştir.
 */
class NoopAudioBridge implements AudioBridge {
  async startMic(): Promise<void> {
    if (__DEV__) console.warn('[live] AudioBridge bağlı değil — ses devre dışı (dev-build gerekli).');
  }
  async playChunk(): Promise<void> {}
  async stop(): Promise<void> {}
}

let _bridge: AudioBridge = new NoopAudioBridge();

/** Native ses köprüsünü kaydet (dev-build başlangıcında çağır). */
export function setAudioBridge(bridge: AudioBridge): void {
  _bridge = bridge;
}

export function getAudioBridge(): AudioBridge {
  return _bridge;
}

/** Native modül bağlı mı? (UI "ses dev-build'de" notunu göstermek için.) */
export function isAudioBridgeReady(): boolean {
  return !(_bridge instanceof NoopAudioBridge);
}
