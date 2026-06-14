/**
 * Canlı sesli oturum hook'u — yaşam döngüsünü yönetir:
 * backend token → Gemini motoru → süre sayacı (metering) → tool çevirisi.
 *
 * Ses ve WS native/protokol detayları engine + audioBridge'de (dev-build).
 * Bu hook sağlayıcı-bağımsız orkestrasyon: oturum aç, süreyi say, bitince
 * /end ile bildir, araç çağrılarını backend'imize çevir.
 */
import { useCallback, useMemo, useRef, useState } from 'react';

import { ApiError, createApiClient } from '@/lib/api';
import { LiveEngine, type LiveStatus } from '@/lib/live/engine';
import { useUstaStore } from '@/lib/store';

export interface LiveLine {
  id: number;
  role: 'usta' | 'user';
  text: string;
}

let _lineId = 1;

export function useLiveSession(vehicleType: 'araba' | 'motosiklet' = 'araba') {
  const authToken = useUstaStore((s) => s.authToken);
  const client = useMemo(() => createApiClient(undefined, () => authToken), [authToken]);

  const [status, setStatus] = useState<LiveStatus>('closed');
  const [lines, setLines] = useState<LiveLine[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  // Aylık ücretsiz canlı limiti doldu (402) → premium upsell tetikle.
  const [premiumRequired, setPremiumRequired] = useState(false);

  const engineRef = useRef<LiveEngine | null>(null);
  const usageIdRef = useRef<number | null>(null);
  const maxRef = useRef<number>(600);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stop = useCallback(async () => {
    if (timerRef.current != null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    const eng = engineRef.current;
    engineRef.current = null;
    if (eng != null) await eng.stop();
    // Süreyi bildir (metering / maliyet freni).
    const usageId = usageIdRef.current;
    usageIdRef.current = null;
    if (usageId != null) {
      try {
        await client.endLiveSession(usageId, elapsedRef.current);
      } catch {
        /* sessiz */
      }
    }
    setStatus('closed');
  }, [client]);

  // elapsed'i ref'te de tut (stop sırasında güncel değeri okumak için).
  const elapsedRef = useRef(0);

  const start = useCallback(
    async (vehicleId: number, task?: string) => {
      setError(null);
      setPremiumRequired(false);
      setLines([]);
      setElapsed(0);
      elapsedRef.current = 0;
      let session;
      try {
        session = await client.startLiveSession(vehicleId, task, 'tr');
      } catch (err) {
        if (err instanceof ApiError && err.status === 402) {
          setPremiumRequired(true); // aylık ücretsiz canlı doldu
          setError('live.error.premium');
        } else {
          setError(err instanceof Error ? err.message : 'live.error.start');
        }
        setStatus('error');
        return;
      }
      usageIdRef.current = session.live_usage_id;
      maxRef.current = session.max_seconds;

      const engine = new LiveEngine(session.token, {
        onStatus: setStatus,
        onTranscript: (role, text) =>
          setLines((l) => [...l, { id: _lineId++, role, text }]),
        onError: (m) => setError(m),
        onToolCall: async (name, args) => {
          if (name === 'fiyat_tahmini') {
            const sistem = String(args.ariza_sistem ?? 'diger');
            const est = await client.getDiagnosisEstimate(sistem, vehicleType);
            return { low_try: est.low_try, high_try: est.high_try, currency: 'TRY' };
          }
          if (name === 'tamirci_bul') {
            return { hint: 'Kullanıcı "Tamirci Bul" ekranından doğrulanmış tamircilere ulaşabilir.' };
          }
          return { error: 'unknown_tool' };
        },
      });
      engineRef.current = engine;
      await engine.connect();

      // Süre sayacı + sert üst sınırda otomatik kapat (maliyet freni).
      timerRef.current = setInterval(() => {
        elapsedRef.current += 1;
        setElapsed(elapsedRef.current);
        if (elapsedRef.current >= maxRef.current) void stop();
      }, 1000);
    },
    [client, vehicleType, stop],
  );

  const sendFrame = useCallback((base64Jpeg: string) => {
    engineRef.current?.sendFrame(base64Jpeg);
  }, []);

  return { status, lines, elapsed, error, premiumRequired, start, stop, sendFrame };
}
