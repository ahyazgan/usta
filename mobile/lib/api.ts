/**
 * Type-safe API client skeleton for the Usta AI backend.
 * Only the two documented diagnose endpoints are implemented.
 */

export const API_BASE_URL: string =
  process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8080';

/** Nine-cell grid position of a part within the frame (null = belirsiz). */
export type Konum =
  | 'sol-ust'
  | 'orta-ust'
  | 'sag-ust'
  | 'sol-orta'
  | 'merkez'
  | 'sag-orta'
  | 'sol-alt'
  | 'orta-alt'
  | 'sag-alt'
  | null;

/** Confidence level of the diagnosis. */
export type Guven = 'yuksek' | 'orta' | 'dusuk';

/** Relative risk level of a maintenance task. */
export type TaskRisk = 'dusuk' | 'orta' | 'yuksek';

/** A selectable maintenance task fetched from the backend. */
export interface Task {
  id: string;
  title_tr: string;
  title_en: string;
  risk: TaskRisk;
}

/** Sound classification categories. */
export type SesKategori =
  | 'tikirti'
  | 'kayis_sesi'
  | 'metalik_vuruntu'
  | 'islik'
  | 'egzoz_patlamasi'
  | 'normal'
  | 'belirsiz';

/** Shared AI diagnosis response shape returned by both endpoints. */
export interface DiagnoseResult {
  tespit: string;
  guven: Guven;
  konum_tarifi: Konum;
  dogru_yer_mi: boolean | null;
  sonraki_adim: string;
  guvenlik_uyarisi: string | null;
  tamirciye_git_onerisi: boolean;
}

export interface DiagnoseImageInput {
  /** Vehicle the diagnosis is for. */
  vehicle_id: number;
  /** Task id the user is performing (e.g. oil_change). */
  task: string;
  /** Optional step the user is currently on, for context. */
  step?: number;
  /** Base64-encoded JPEG frame (no data URI prefix). */
  frame_base64: string;
  /** Media type of the frame — always image/jpeg client-side. */
  media_type: 'image/jpeg';
  /** Optional free-text note from the user. */
  user_note?: string;
}

/** Condition under which the engine sound was heard (no audio is sent). */
export type KayitKosulu = 'rolanti' | 'gazda' | 'soguk_motor' | 'seyirde';

export interface DiagnoseSoundInput {
  vehicle_id: number;
  /** User's own description of the sound (engine sound is not transcribed). */
  user_description: string;
  condition: KayitKosulu;
}

export type GetToken = () => string | null | Promise<string | null>;

export interface ApiClient {
  diagnoseImage(input: DiagnoseImageInput): Promise<DiagnoseResult>;
  diagnoseSound(input: DiagnoseSoundInput): Promise<DiagnoseResult>;
  getTasks(): Promise<Task[]>;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function createApiClient(
  baseUrl: string = API_BASE_URL,
  getToken: GetToken = () => null,
): ApiClient {
  async function authHeaders(): Promise<Record<string, string>> {
    const token = await getToken();
    const headers: Record<string, string> = {
      Accept: 'application/json',
    };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    return headers;
  }

  async function request<TResult>(
    path: string,
    init: RequestInit,
  ): Promise<TResult> {
    let res: Response;
    try {
      res = await fetch(`${baseUrl}${path}`, init);
    } catch (err) {
      // Network failure / offline — surface as a catchable Error for screens.
      throw new ApiError(0, err instanceof Error ? err.message : 'network error');
    }

    if (!res.ok) {
      throw new ApiError(res.status, `Request to ${path} failed (${res.status})`);
    }

    return (await res.json()) as TResult;
  }

  async function post<TBody extends object>(
    path: string,
    body: TBody,
  ): Promise<DiagnoseResult> {
    const headers = await authHeaders();
    headers['Content-Type'] = 'application/json';
    return request<DiagnoseResult>(path, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });
  }

  return {
    diagnoseImage(input) {
      return post('/v1/ai/diagnose/image', input);
    },
    diagnoseSound(input) {
      return post('/v1/ai/diagnose/sound', input);
    },
    async getTasks() {
      const headers = await authHeaders();
      return request<Task[]>('/v1/tasks', { method: 'GET', headers });
    },
  };
}

export default createApiClient;
