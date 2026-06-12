/**
 * Login ekranı kaldırıldı — uygulama otomatik demo girişi yapıyor
 * (bkz. lib/demoSession.ts). Eski /login deep-link'leri ana sayfaya yönlenir.
 */
import { Redirect } from 'expo-router';

export default function LoginRedirect() {
  return <Redirect href="/" />;
}
