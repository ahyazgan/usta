/**
 * Güvenli geri navigasyon.
 *
 * Tab bar ekranları arası geçiş `replace` ile yapılır (geçmiş bırakmaz), bu yüzden
 * bir ekrana tab'dan gelindiğinde `router.back()` "geri gidilecek ekran yok"
 * uyarısı verir. Bu yardımcı: geçmiş varsa geri gider, yoksa ana sayfaya döner.
 */
import { useRouter } from 'expo-router';

type AppRouter = ReturnType<typeof useRouter>;

export function goBack(router: AppRouter): void {
  if (router.canGoBack()) {
    router.back();
  } else {
    router.replace('/');
  }
}

export default goBack;
