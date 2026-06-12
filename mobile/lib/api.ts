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

/** Urgency level of a finding. */
export type Aciliyet = 'dusuk' | 'orta' | 'yuksek';

/** Sound diagnosis response shape (distinct from the image diagnosis shape). */
export interface SoundDiagnoseResult {
  tespit: string;
  guven: Guven;
  ses_kategorisi: SesKategori;
  aciliyet: Aciliyet;
  guvenlik_uyarisi: string | null;
  sonraki_adim: string;
  tamirciye_git_onerisi: boolean;
}

/** Auth token bundle returned by login/register-then-login/refresh. */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/** Authentication request payload shared by register + login. */
export interface AuthInput {
  email: string;
  password: string;
}

/** Public-facing user record returned by register. */
export interface UserOut {
  id: number;
  email: string;
  subscription_tier: string;
  created_at: string;
}

/** A persisted maintenance log entry. */
export interface MaintenanceLog {
  id: number;
  task: string;
  km: number | null;
  note: string | null;
  created_at: string;
}

/** Payload for creating a maintenance log. */
export interface MaintenanceLogInput {
  task: string;
  km?: number;
  note?: string;
}

/** Reminder status returned by the backend. */
export type ReminderStatus = 'ok' | 'soon' | 'due' | 'unknown';

/** Home summary: completed maintenance count + estimated DIY savings (TRY). */
export interface VehicleSummary {
  maintenance_count: number;
  savings_try: number;
}

/** One step of a maintenance guide (spec values already filled server-side). */
export interface GuideStep {
  step: number;
  instruction_tr: string;
  instruction_en: string;
  tool_tr: string | null;
  tool_en: string | null;
  torque_nm: number | null;
  warning_tr: string | null;
  warning_en: string | null;
}

/** Step-by-step guide for a maintenance task, tailored to a vehicle. */
export interface TaskGuide {
  task_id: string;
  title_tr: string;
  title_en: string;
  risk: TaskRisk;
  est_minutes: number;
  steps: GuideStep[];
  mechanic_note_tr: string;
  mechanic_note_en: string;
}

/** A maintenance reminder derived from logs + intervals. */
export interface Reminder {
  task: string;
  interval_km: number;
  last_km: number | null;
  due_km: number | null;
  remaining_km: number | null;
  status: ReminderStatus;
}

/** Supported fuel types (matches the backend enum). */
export type FuelType = 'benzin' | 'dizel' | 'lpg' | 'hibrit' | 'elektrik';

/** Per-vehicle technical spec, auto-filled by the backend TR catalog. */
export interface VehicleSpec {
  oil_spec: string | null;
  oil_capacity_l: number | null;
  oil_drain_bolt_size: string | null;
  oil_drain_location: string | null;
  oil_filter_part: string | null;
  air_filter_part: string | null;
  cabin_filter_part: string | null;
  spark_plug_part: string | null;
  battery_spec: string | null;
  battery_location: string | null;
  transmission_type: string | null;
}

/** A vehicle record (matches the backend `VehicleOut`). */
export interface Vehicle {
  id: number;
  make: string;
  model: string;
  year: number;
  plate: string | null;
  fuel_type: FuelType;
  engine_code: string | null;
  current_km: number | null;
  spec: VehicleSpec | null;
}

/** Payload for creating a vehicle. `spec` is auto-filled server-side. */
export interface VehicleCreateInput {
  make: string;
  model: string;
  year: number;
  plate?: string;
  fuel_type: FuelType;
  engine_code?: string;
  current_km?: number;
}

export type GetToken = () => string | null | Promise<string | null>;

export interface ApiClient {
  diagnoseImage(input: DiagnoseImageInput): Promise<DiagnoseResult>;
  diagnoseSound(input: DiagnoseSoundInput): Promise<SoundDiagnoseResult>;
  getTasks(): Promise<Task[]>;
  register(input: AuthInput): Promise<UserOut>;
  login(input: AuthInput): Promise<TokenResponse>;
  refresh(refreshToken: string): Promise<TokenResponse>;
  addLog(vehicleId: number, input: MaintenanceLogInput): Promise<MaintenanceLog>;
  listLogs(vehicleId: number): Promise<MaintenanceLog[]>;
  getReminders(vehicleId: number): Promise<Reminder[]>;
  getSummary(vehicleId: number): Promise<VehicleSummary>;
  /** Step-by-step guide for a task, filled with this vehicle's spec. */
  getGuide(vehicleId: number, taskId: string): Promise<TaskGuide>;
  listVehicles(): Promise<Vehicle[]>;
  createVehicle(input: VehicleCreateInput): Promise<Vehicle>;
  getVehicle(id: number): Promise<Vehicle>;
  /** Tasks applicable to this vehicle's fuel type (filtered server-side). */
  getVehicleTasks(vehicleId: number): Promise<Task[]>;
  updateVehicle(id: number, patch: Partial<VehicleCreateInput>): Promise<Vehicle>;
  /** Deletes a vehicle. Backend returns 204 No Content. */
  deleteVehicle(id: number): Promise<void>;
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

  /** Like `request`, but resolves without parsing a body (e.g. 204). */
  async function requestVoid(path: string, init: RequestInit): Promise<void> {
    let res: Response;
    try {
      res = await fetch(`${baseUrl}${path}`, init);
    } catch (err) {
      throw new ApiError(0, err instanceof Error ? err.message : 'network error');
    }

    if (!res.ok) {
      throw new ApiError(res.status, `Request to ${path} failed (${res.status})`);
    }
  }

  async function post<TResult, TBody extends object>(
    path: string,
    body: TBody,
  ): Promise<TResult> {
    const headers = await authHeaders();
    headers['Content-Type'] = 'application/json';
    return request<TResult>(path, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });
  }

  async function patch<TResult, TBody extends object>(
    path: string,
    body: TBody,
  ): Promise<TResult> {
    const headers = await authHeaders();
    headers['Content-Type'] = 'application/json';
    return request<TResult>(path, {
      method: 'PATCH',
      headers,
      body: JSON.stringify(body),
    });
  }

  /** POST without an auth header — used by the unauthenticated auth flows. */
  async function postPublic<TResult, TBody extends object>(
    path: string,
    body: TBody,
  ): Promise<TResult> {
    return request<TResult>(path, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
  }

  return {
    diagnoseImage(input) {
      return post<DiagnoseResult, DiagnoseImageInput>(
        '/v1/ai/diagnose/image',
        input,
      );
    },
    diagnoseSound(input) {
      return post<SoundDiagnoseResult, DiagnoseSoundInput>(
        '/v1/ai/diagnose/sound',
        input,
      );
    },
    async getTasks() {
      const headers = await authHeaders();
      return request<Task[]>('/v1/tasks', { method: 'GET', headers });
    },
    register(input) {
      return postPublic<UserOut, AuthInput>('/v1/auth/register', input);
    },
    login(input) {
      return postPublic<TokenResponse, AuthInput>('/v1/auth/login', input);
    },
    refresh(refreshToken) {
      return postPublic<TokenResponse, { refresh_token: string }>(
        '/v1/auth/refresh',
        { refresh_token: refreshToken },
      );
    },
    addLog(vehicleId, input) {
      return post<MaintenanceLog, MaintenanceLogInput>(
        `/v1/vehicles/${vehicleId}/logs`,
        input,
      );
    },
    async listLogs(vehicleId) {
      const headers = await authHeaders();
      return request<MaintenanceLog[]>(`/v1/vehicles/${vehicleId}/logs`, {
        method: 'GET',
        headers,
      });
    },
    async getReminders(vehicleId) {
      const headers = await authHeaders();
      return request<Reminder[]>(`/v1/vehicles/${vehicleId}/reminders`, {
        method: 'GET',
        headers,
      });
    },
    async getSummary(vehicleId) {
      const headers = await authHeaders();
      return request<VehicleSummary>(`/v1/vehicles/${vehicleId}/summary`, {
        method: 'GET',
        headers,
      });
    },
    async getGuide(vehicleId, taskId) {
      const headers = await authHeaders();
      return request<TaskGuide>(
        `/v1/vehicles/${vehicleId}/tasks/${taskId}/guide`,
        { method: 'GET', headers },
      );
    },
    async listVehicles() {
      const headers = await authHeaders();
      return request<Vehicle[]>('/v1/vehicles', { method: 'GET', headers });
    },
    createVehicle(input) {
      return post<Vehicle, VehicleCreateInput>('/v1/vehicles', input);
    },
    async getVehicle(id) {
      const headers = await authHeaders();
      return request<Vehicle>(`/v1/vehicles/${id}`, { method: 'GET', headers });
    },
    async getVehicleTasks(vehicleId) {
      const headers = await authHeaders();
      return request<Task[]>(`/v1/vehicles/${vehicleId}/tasks`, {
        method: 'GET',
        headers,
      });
    },
    updateVehicle(id, patchBody) {
      return patch<Vehicle, Partial<VehicleCreateInput>>(
        `/v1/vehicles/${id}`,
        patchBody,
      );
    },
    async deleteVehicle(id) {
      const headers = await authHeaders();
      // 204 No Content — empty body, do not parse JSON.
      await requestVoid(`/v1/vehicles/${id}`, { method: 'DELETE', headers });
    },
  };
}

export default createApiClient;
