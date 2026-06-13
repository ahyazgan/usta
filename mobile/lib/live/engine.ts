/**
 * Canlı motor — Gemini Live WebSocket istemcisi.
 *
 * ⚠️ Gemini Live protokolü (BidiGenerateContent) hızlı evriliyor. Aşağıdaki uç
 * + mesaj şekilleri en iyi çabadır; **dev-build'de güncel Gemini Live dokümanına
 * karşı DOĞRULA** (bağlantı uç'u, realtimeInput / serverContent / toolCall şekli).
 * Mantık akışı (bağlan → ses+kare gönder → ses al + tool çağrısı) sağlamdır;
 * sadece tel-formatı doğrulanmalı.
 *
 * Ephemeral token oturum config'ini (model, system instruction, voice, tools)
 * server-side BAĞLAR — istemci bunları göndermez/görmez.
 */
import { getAudioBridge, type AudioBridge } from './audioBridge';

export type LiveStatus = 'connecting' | 'live' | 'closed' | 'error';

export interface LiveEngineCallbacks {
  onStatus(status: LiveStatus): void;
  /** Konuşma dökümü (varsa) — UI'da akış göster. */
  onTranscript(role: 'usta' | 'user', text: string): void;
  /** Gemini bir aracı çağırdı → backend'imize çevir, sonucu döndür. */
  onToolCall(name: string, args: Record<string, unknown>): Promise<unknown>;
  onError(message: string): void;
}

// ⚠️ DOĞRULA: güncel Gemini Live WS uç'u.
const LIVE_WS_BASE =
  'wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent';

export class LiveEngine {
  private ws: WebSocket | null = null;
  private readonly audio: AudioBridge = getAudioBridge();
  private stopped = false;

  constructor(
    private readonly token: string,
    private readonly cb: LiveEngineCallbacks,
  ) {}

  /** Bağlan, mikrofonu başlat, gelen mesajları işle. */
  async connect(): Promise<void> {
    this.cb.onStatus('connecting');
    try {
      // Ephemeral token query param ile (RN WS özel header'ı zor). DOĞRULA.
      this.ws = new WebSocket(`${LIVE_WS_BASE}?access_token=${encodeURIComponent(this.token)}`);
    } catch {
      this.cb.onStatus('error');
      this.cb.onError('Canlı bağlantı açılamadı.');
      return;
    }

    this.ws.onopen = () => {
      // Config token'a bağlı; bazı sürümler minimal "setup" bekleyebilir. DOĞRULA.
      this.send({ setup: {} });
      this.cb.onStatus('live');
      // Mikrofonu aç — her PCM parçasını realtimeInput olarak gönder.
      void this.audio.startMic((base64Pcm) => {
        this.send({
          realtimeInput: {
            mediaChunks: [{ mimeType: 'audio/pcm;rate=16000', data: base64Pcm }],
          },
        });
      });
    };

    this.ws.onmessage = (ev) => void this.handleMessage(ev.data);
    this.ws.onerror = () => {
      if (this.stopped) return;
      this.cb.onStatus('error');
      this.cb.onError('Canlı bağlantı hatası.');
    };
    this.ws.onclose = () => {
      if (!this.stopped) this.cb.onStatus('closed');
    };
  }

  /** Kamera karesini gönder (hareket-tetikli; düşük fps, maliyet için). */
  sendFrame(base64Jpeg: string): void {
    this.send({
      realtimeInput: { mediaChunks: [{ mimeType: 'image/jpeg', data: base64Jpeg }] },
    });
  }

  async stop(): Promise<void> {
    this.stopped = true;
    try {
      await this.audio.stop();
    } catch {
      /* yut */
    }
    this.ws?.close();
    this.ws = null;
    this.cb.onStatus('closed');
  }

  private send(obj: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(obj));
  }

  // ⚠️ DOĞRULA: serverContent / toolCall yanıt şekilleri.
  private async handleMessage(raw: unknown): Promise<void> {
    let msg: Record<string, any>;
    try {
      msg = JSON.parse(typeof raw === 'string' ? raw : '{}');
    } catch {
      return;
    }

    // 1) Model çıktısı (ses + metin)
    const parts: any[] = msg?.serverContent?.modelTurn?.parts ?? [];
    for (const p of parts) {
      const data: string | undefined = p?.inlineData?.data;
      const mime: string = p?.inlineData?.mimeType ?? '';
      if (data && mime.startsWith('audio')) {
        void this.audio.playChunk(data);
      }
      if (typeof p?.text === 'string' && p.text.length > 0) {
        this.cb.onTranscript('usta', p.text);
      }
    }
    // Kullanıcı konuşma dökümü (etkinse)
    const userText: string | undefined = msg?.serverContent?.inputTranscription?.text;
    if (userText) this.cb.onTranscript('user', userText);

    // 2) Araç çağrıları → backend'imize çevir, sonucu geri gönder
    const calls: any[] = msg?.toolCall?.functionCalls ?? [];
    if (calls.length > 0) {
      const responses = [];
      for (const c of calls) {
        try {
          const result = await this.cb.onToolCall(c.name, c.args ?? {});
          responses.push({ id: c.id, name: c.name, response: { result } });
        } catch {
          responses.push({ id: c.id, name: c.name, response: { error: 'failed' } });
        }
      }
      this.send({ toolResponse: { functionResponses: responses } });
    }
  }
}
