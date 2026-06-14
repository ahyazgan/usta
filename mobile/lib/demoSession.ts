/**
 * Otomatik demo oturumu.
 *
 * Login ekranı kaldırıldı: uygulama açılınca arka planda sabit bir demo
 * hesabıyla oturum açılır. Kendi kendini onarır — önce giriş dener, hesap
 * yoksa oluşturup tekrar girer. Böylece hangi backend'e (yerel/Render)
 * bağlı olursa olsun çalışır.
 */
import { createApiClient, type TokenResponse } from '@/lib/api';
import { saveTokens } from '@/lib/auth';

export const DEMO_EMAIL = 'demo@usta.app';
export const DEMO_PASSWORD = 'demoparola1234';

/**
 * Bir demo oturumu sağlar ve token'ları store'a yazar.
 * @returns başarılıysa true.
 */
export async function ensureDemoSession(
  setTokens: (tokens: { access: string; refresh: string }) => void,
): Promise<boolean> {
  const client = createApiClient();
  const creds = { email: DEMO_EMAIL, password: DEMO_PASSWORD };

  let tokens: TokenResponse;
  try {
    tokens = await client.login(creds);
  } catch {
    // Hesap yoksa oluştur (zaten varsa 409'u yok say), sonra tekrar gir.
    try {
      await client.register(creds);
    } catch {
      /* yarış / zaten kayıtlı — yok say, giriş aşağıda denenecek */
    }
    tokens = await client.login(creds);
  }

  // Web'de secure-store olmayabilir; kalıcılık başarısız olsa da oturum çalışsın.
  try {
    await saveTokens(tokens);
  } catch {
    /* web / secure-store yok — yalnızca bellek içi oturum */
  }
  setTokens({ access: tokens.access_token, refresh: tokens.refresh_token });
  return true;
}

export default ensureDemoSession;
