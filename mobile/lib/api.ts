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
  /** AISession id — 👍/👎 feedback attaches to this. */
  session_id: number | null;
  /** Mechanic cost estimate for the detected fault system (price transparency). */
  cost_estimate?: CostEstimate | null;
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
  /** AISession id — 👍/👎 feedback attaches to this. */
  session_id: number | null;
  /** Mechanic cost estimate for the detected fault system (price transparency). */
  cost_estimate?: CostEstimate | null;
}

/** Dashboard warning light color (severity signal). */
export type DashboardRenk = 'kirmizi' | 'sari' | 'yesil' | 'mavi' | 'bilinmiyor';

/** One identified dashboard warning light. */
export interface DashboardLight {
  isim: string;
  renk: DashboardRenk;
  anlam: string;
  aciliyet: Aciliyet;
  ne_yapmali: string;
}

/** Dashboard warning-light identification response. */
export interface DashboardResult {
  tespit: string;
  guven: Guven;
  isiklar: DashboardLight[];
  en_yuksek_aciliyet: Aciliyet;
  guvenlik_uyarisi: string | null;
  sonraki_adim: string;
  tamirciye_git_onerisi: boolean;
  /** AISession id — 👍/👎 feedback attaches to this. */
  session_id: number | null;
}

export interface DashboardInput {
  vehicle_id: number;
  /** Base64-encoded JPEG frame (no data URI prefix). */
  frame_base64: string;
  media_type: 'image/jpeg';
  user_note?: string;
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
  cost_try: number | null;
  created_at: string;
}

/** Payload for creating a maintenance log. */
export interface MaintenanceLogInput {
  task: string;
  km?: number;
  note?: string;
  /** Diagnosis session that led to this job (data-flywheel link). */
  ai_session_id?: number;
  /** Actual cost the user paid (TRY, optional). */
  cost_try?: number;
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

/** One prep-list item: a vehicle-specific part/consumable (label + value). */
export interface PrepPart {
  label_tr: string;
  label_en: string;
  value: string;
  /** Affiliate skeleton: tappable buy link for this part (null = disabled). */
  buy_url?: string | null;
}

/** Step-by-step guide for a maintenance task, tailored to a vehicle. */
export interface TaskGuide {
  task_id: string;
  title_tr: string;
  title_en: string;
  risk: TaskRisk;
  est_minutes: number;
  /** Estimated labour saved by doing it yourself (TRY) — celebration screen. */
  diy_saving_try: number;
  /** "Prep before you start" — vehicle-specific parts/numbers from the spec. */
  parts: PrepPart[];
  steps: GuideStep[];
  mechanic_note_tr: string;
  mechanic_note_en: string;
}

/** Mechanic cost estimate range for a job (price-transparency wedge). */
export interface CostEstimate {
  low_try: number;
  high_try: number;
  currency: string;
  /** 'seed' = TR baseline; 'community' = derived from real paid prices. */
  source: 'seed' | 'community';
  /** Real-price samples that fed a 'community' estimate. */
  sample_size: number;
}

/** Subscription status + premium feature gates. */
export interface Subscription {
  tier: 'free' | 'premium';
  is_premium: boolean;
  live_unlimited: boolean;
  /** Remaining free live seconds this month (null = premium / unlimited). */
  free_live_seconds_remaining: number | null;
}

/** Live voice session start response (ephemeral token + session info). */
export interface LiveSession {
  /** Ephemeral token to connect directly to Gemini Live. */
  token: string;
  model: string;
  voice: string;
  language: string;
  /** Usage row id — report duration to this on end (minute metering). */
  live_usage_id: number;
  /** Hard cap on a single session (seconds). */
  max_seconds: number;
}

/** One row of the price showroom: a task + its mechanic cost estimate. */
export interface TaskEstimate {
  id: string;
  title_tr: string;
  title_en: string;
  risk: TaskRisk;
  low_try: number;
  high_try: number;
  currency: string;
  source: 'seed' | 'community';
  sample_size: number;
}

/** Vehicle-system taxonomy a diagnosis maps to (queryable stats). */
export type ArizaSistem =
  | 'motor'
  | 'atesleme'
  | 'fren'
  | 'elektrik'
  | 'lastik'
  | 'filtre'
  | 'suspansiyon'
  | 'sanziman'
  | 'gorus'
  | 'diger';

/** How a diagnosis was resolved — the closure signal. */
export type ResolutionDurum =
  | 'kendim_cozdum'
  | 'tamirci_cozdu'
  | 'sorun_devam'
  | 'yanlis_teshis';

/** A past AI diagnosis (image or sound), newest first. */
export interface DiagnosisHistory {
  id: number;
  kind: 'image' | 'sound';
  task: string | null;
  tespit: string | null;
  guven: Guven | null;
  tamirciye_git: boolean | null;
  /** Structured category: task id (image) or sound type (sound). */
  kategori: string | null;
  /** Vehicle-system taxonomy (motor / fren / elektrik …). */
  ariza_sistem: ArizaSistem | null;
  /** User feedback: was the diagnosis right? (null = not voted yet) */
  feedback_dogru: boolean | null;
  /** Closure signal: how it was resolved (null = not reported). */
  resolution: ResolutionDurum | null;
  /** Real mechanic price the user paid (only for 'tamirci_cozdu'). */
  cost_try: number | null;
  created_at: string;
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

/** Vehicle type — affects which maintenance tasks apply. */
export type VehicleType = 'araba' | 'motosiklet';

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
  vehicle_type: VehicleType | null;
  engine_code: string | null;
  current_km: number | null;
  /** ISO YYYY-MM-DD — date-based reminders (inspection / insurance). */
  muayene_date: string | null;
  sigorta_date: string | null;
  spec: VehicleSpec | null;
}

/** Payload for creating a vehicle. `spec` is auto-filled server-side. */
export interface VehicleCreateInput {
  make: string;
  model: string;
  year: number;
  plate?: string;
  fuel_type: FuelType;
  vehicle_type?: VehicleType;
  engine_code?: string;
  current_km?: number;
  /** ISO YYYY-MM-DD, or null to clear. */
  muayene_date?: string | null;
  sigorta_date?: string | null;
}

/** KVKK açık rıza durumu. */
export interface Consent {
  analytics: boolean;
  data: boolean;
}

/** Anonim küme istatistiği — bir araç sistemi için (kişi-bağımsız). */
export interface SystemStat {
  sistem: ArizaSistem;
  count: number;
  dogrulanan: number;
  dogruluk_orani: number | null;
}

/** Küratörlü tamirci dizini kaydı. */
export interface Mechanic {
  id: number;
  name: string;
  city: string;
  district: string | null;
  phone: string;
  whatsapp: string | null;
  address: string | null;
  maps_url: string | null;
  specialties: string | null;
  systems: string | null;
  verified: boolean;
}

/** Tamirciye ulaşma kanalı (lead). */
export type LeadChannel = 'call' | 'whatsapp' | 'directions';

export type GetToken = () => string | null | Promise<string | null>;

export interface ApiClient {
  diagnoseImage(input: DiagnoseImageInput): Promise<DiagnoseResult>;
  diagnoseSound(input: DiagnoseSoundInput): Promise<SoundDiagnoseResult>;
  /** Identify dashboard warning lights from a photo of the instrument cluster. */
  diagnoseDashboard(input: DashboardInput): Promise<DashboardResult>;
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
  /** Mechanic cost estimate for a task on this vehicle (404 if none). */
  getTaskEstimate(vehicleId: number, taskId: string): Promise<CostEstimate>;
  /** Price showroom: all applicable tasks + their estimates, one call. */
  getVehicleEstimates(vehicleId: number): Promise<TaskEstimate[]>;
  /** Subscription status + premium feature gates. */
  getSubscription(): Promise<Subscription>;
  /** Log a part 'Buy' tap (affiliate demand metric / partnership proof). */
  logBuyIntent(vehicleId: number, partLabel: string, task?: string): Promise<void>;
  /** Mechanic cost estimate for a fault system (live tool 'fiyat_tahmini'). */
  getDiagnosisEstimate(
    arizaSistem: string,
    vehicleType?: 'araba' | 'motosiklet',
  ): Promise<CostEstimate>;
  /** Start a live voice session → ephemeral token (503 if disabled, 402 if over limit). */
  startLiveSession(
    vehicleId: number,
    task?: string,
    lang?: 'tr' | 'en',
  ): Promise<LiveSession>;
  /** Report live session duration (minute metering / cost guard). */
  endLiveSession(liveUsageId: number, seconds: number): Promise<void>;
  /** Recent AI diagnoses for this vehicle (image + sound), newest first. */
  getDiagnoses(vehicleId: number): Promise<DiagnosisHistory[]>;
  /** 👍/👎 a past diagnosis; re-voting overwrites. Returns the updated row. */
  sendDiagnosisFeedback(
    vehicleId: number,
    sessionId: number,
    dogru: boolean,
  ): Promise<DiagnosisHistory>;
  /**
   * Closure signal: how the diagnosis was resolved. Re-reporting overwrites.
   * costTry is the real mechanic price (only stored for 'tamirci_cozdu') —
   * the fuel that turns estimates from seed to community data.
   */
  sendDiagnosisResolution(
    vehicleId: number,
    sessionId: number,
    resolution: ResolutionDurum,
    costTry?: number,
  ): Promise<DiagnosisHistory>;
  /** KVKK consent: read + partial update. */
  getConsent(): Promise<Consent>;
  updateConsent(patch: Partial<Consent>): Promise<Consent>;
  /** Anonymous aggregate stats (k-anonymity, consent-gated server-side). */
  getSystemStats(): Promise<SystemStat[]>;
  /** Curated mechanic directory, filtered by city/system. */
  getMechanics(city?: string, system?: string): Promise<Mechanic[]>;
  /** Record a lead when the user reaches out to a mechanic. */
  sendMechanicLead(
    mechanicId: number,
    channel: LeadChannel,
    aiSessionId?: number,
  ): Promise<void>;
  /** Right to erasure: delete the account and all its data (204). */
  deleteAccount(): Promise<void>;
  /** Known catalog brands for a vehicle type (form quick-pick). */
  getCatalogBrands(vehicleType: VehicleType): Promise<string[]>;
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
    diagnoseDashboard(input) {
      return post<DashboardResult, DashboardInput>(
        '/v1/ai/diagnose/dashboard',
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
    async getTaskEstimate(vehicleId, taskId) {
      const headers = await authHeaders();
      return request<CostEstimate>(
        `/v1/vehicles/${vehicleId}/tasks/${taskId}/estimate`,
        { method: 'GET', headers },
      );
    },
    async getVehicleEstimates(vehicleId) {
      const headers = await authHeaders();
      return request<TaskEstimate[]>(`/v1/vehicles/${vehicleId}/estimates`, {
        method: 'GET',
        headers,
      });
    },
    async getSubscription() {
      const headers = await authHeaders();
      return request<Subscription>('/v1/me/subscription', { method: 'GET', headers });
    },
    async logBuyIntent(vehicleId, partLabel, task) {
      const headers = await authHeaders();
      await requestVoid('/v1/parts/buy-intent', {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ vehicle_id: vehicleId, part_label: partLabel, task }),
      });
    },
    async getDiagnosisEstimate(arizaSistem, vehicleType = 'araba') {
      const headers = await authHeaders();
      return request<CostEstimate>(
        `/v1/estimate/diagnosis?ariza_sistem=${arizaSistem}&vehicle_type=${vehicleType}`,
        { method: 'GET', headers },
      );
    },
    async startLiveSession(vehicleId, task, lang = 'tr') {
      const headers = await authHeaders();
      return request<LiveSession>('/v1/live/session', {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ vehicle_id: vehicleId, task, lang }),
      });
    },
    async endLiveSession(liveUsageId, seconds) {
      const headers = await authHeaders();
      await requestVoid(`/v1/live/session/${liveUsageId}/end`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ seconds }),
      });
    },
    async getDiagnoses(vehicleId) {
      const headers = await authHeaders();
      return request<DiagnosisHistory[]>(`/v1/vehicles/${vehicleId}/diagnoses`, {
        method: 'GET',
        headers,
      });
    },
    sendDiagnosisFeedback(vehicleId, sessionId, dogru) {
      return post<DiagnosisHistory, { dogru: boolean }>(
        `/v1/vehicles/${vehicleId}/diagnoses/${sessionId}/feedback`,
        { dogru },
      );
    },
    sendDiagnosisResolution(vehicleId, sessionId, resolution, costTry) {
      return post<
        DiagnosisHistory,
        { resolution: ResolutionDurum; cost_try?: number }
      >(`/v1/vehicles/${vehicleId}/diagnoses/${sessionId}/resolution`, {
        resolution,
        ...(costTry != null ? { cost_try: costTry } : {}),
      });
    },
    async getConsent() {
      const headers = await authHeaders();
      return request<Consent>('/v1/me/consent', { method: 'GET', headers });
    },
    updateConsent(body) {
      return patch<Consent, Partial<Consent>>('/v1/me/consent', body);
    },
    async getSystemStats() {
      const headers = await authHeaders();
      return request<SystemStat[]>('/v1/stats/systems', { method: 'GET', headers });
    },
    async getMechanics(city, system) {
      const headers = await authHeaders();
      const qs = new URLSearchParams();
      if (city) qs.set('city', city);
      if (system) qs.set('system', system);
      const suffix = qs.toString() ? `?${qs.toString()}` : '';
      return request<Mechanic[]>(`/v1/mechanics${suffix}`, { method: 'GET', headers });
    },
    sendMechanicLead(mechanicId, channel, aiSessionId) {
      return post<{ id: number }, { channel: LeadChannel; ai_session_id?: number }>(
        `/v1/mechanics/${mechanicId}/lead`,
        { channel, ai_session_id: aiSessionId },
      ).then(() => undefined);
    },
    async deleteAccount() {
      const headers = await authHeaders();
      await requestVoid('/v1/me', { method: 'DELETE', headers });
    },
    async getCatalogBrands(vehicleType) {
      const headers = await authHeaders();
      return request<string[]>(`/v1/catalog/brands?vehicle_type=${vehicleType}`, {
        method: 'GET',
        headers,
      });
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
