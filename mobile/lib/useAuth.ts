/**
 * Auth hook — wires the API client, secure token store, and zustand store.
 * Screens call `login` / `register` / `logout` and read `loading` / `error`.
 * Errors are mapped to i18n keys so screens render them via t().
 */
import { useCallback, useMemo, useState } from 'react';

import { ApiError, createApiClient } from '@/lib/api';
import { clearTokens, saveTokens } from '@/lib/auth';
import { useUstaStore } from '@/lib/store';

export interface UseAuth {
  loading: boolean;
  /** i18n key describing the failure, or null when there is none. */
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

/** Maps a thrown error to an i18n key the screen can render via t(). */
function loginErrorKey(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 0) return 'auth.error.network';
    if (err.status === 401 || err.status === 403) return 'auth.error.invalid';
  }
  return 'auth.error.generic';
}

/** Register failures: 409 means the email already exists. */
function registerErrorKey(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 0) return 'auth.error.network';
    if (err.status === 409) return 'auth.error.exists';
  }
  return 'auth.error.generic';
}

export function useAuth(): UseAuth {
  const setTokens = useUstaStore((s) => s.setTokens);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auth endpoints are unauthenticated, so no token getter is needed.
  const client = useMemo(() => createApiClient(), []);

  const login = useCallback(
    async (email: string, password: string): Promise<boolean> => {
      setLoading(true);
      setError(null);
      try {
        const tokens = await client.login({ email, password });
        await saveTokens(tokens);
        setTokens({ access: tokens.access_token, refresh: tokens.refresh_token });
        return true;
      } catch (err) {
        setError(loginErrorKey(err));
        return false;
      } finally {
        setLoading(false);
      }
    },
    [client, setTokens],
  );

  const register = useCallback(
    async (email: string, password: string): Promise<boolean> => {
      setLoading(true);
      setError(null);
      try {
        await client.register({ email, password });
        // Register does not return tokens — log in immediately afterwards.
        const tokens = await client.login({ email, password });
        await saveTokens(tokens);
        setTokens({ access: tokens.access_token, refresh: tokens.refresh_token });
        return true;
      } catch (err) {
        setError(registerErrorKey(err));
        return false;
      } finally {
        setLoading(false);
      }
    },
    [client, setTokens],
  );

  const logout = useCallback(async (): Promise<void> => {
    await clearTokens();
    setTokens(null);
  }, [setTokens]);

  return { loading, error, login, register, logout };
}

export default useAuth;
