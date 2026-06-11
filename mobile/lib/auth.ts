/**
 * Secure token persistence backed by expo-secure-store.
 * Keeps access + refresh tokens on the device keychain so a logged-in
 * user stays logged in across app launches.
 */
import * as SecureStore from 'expo-secure-store';

const ACCESS_KEY = 'usta.access_token';
const REFRESH_KEY = 'usta.refresh_token';

/** The subset of TokenResponse we persist (token_type is constant). */
export interface StoredTokens {
  access_token: string;
  refresh_token: string;
}

/** Load persisted tokens, or null when the user is not logged in. */
export async function loadTokens(): Promise<StoredTokens | null> {
  const [access, refresh] = await Promise.all([
    SecureStore.getItemAsync(ACCESS_KEY),
    SecureStore.getItemAsync(REFRESH_KEY),
  ]);
  if (!access || !refresh) return null;
  return { access_token: access, refresh_token: refresh };
}

/** Persist the access + refresh tokens to the secure store. */
export async function saveTokens(tokens: StoredTokens): Promise<void> {
  await Promise.all([
    SecureStore.setItemAsync(ACCESS_KEY, tokens.access_token),
    SecureStore.setItemAsync(REFRESH_KEY, tokens.refresh_token),
  ]);
}

/** Remove any persisted tokens (logout). */
export async function clearTokens(): Promise<void> {
  await Promise.all([
    SecureStore.deleteItemAsync(ACCESS_KEY),
    SecureStore.deleteItemAsync(REFRESH_KEY),
  ]);
}
