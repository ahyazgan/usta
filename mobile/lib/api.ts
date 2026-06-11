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
  /** Base64-encoded image payload (no data URI prefix). */
  imageBase64: string;
  /** Optional step the user is currently on, for context. */
  adim?: number;
  /** Optional vehicle id for tailored guidance. */
  vehicleId?: string;
}

export interface DiagnoseSoundInput {
  /** Base64-encoded audio payload. */
  audioBase64: string;
  kategori_ipucu?: SesKategori;
  vehicleId?: string;
}

export type GetToken = () => string | null | Promise<string | null>;

export interface ApiClient {
  diagnoseImage(input: DiagnoseImageInput): Promise<DiagnoseResult>;
  diagnoseSound(input: DiagnoseSoundInput): Promise<DiagnoseResult>;
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
  async function post<TBody extends object>(
    path: string,
    body: TBody,
  ): Promise<DiagnoseResult> {
    const token = await getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const res = await fetch(`${baseUrl}${path}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      throw new ApiError(res.status, `Request to ${path} failed (${res.status})`);
    }

    return (await res.json()) as DiagnoseResult;
  }

  return {
    diagnoseImage(input) {
      return post('/v1/ai/diagnose/image', input);
    },
    diagnoseSound(input) {
      return post('/v1/ai/diagnose/sound', input);
    },
  };
}

export default createApiClient;
