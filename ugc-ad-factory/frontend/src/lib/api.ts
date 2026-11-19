"use client";
// Thin typed client for the FastAPI backend. All calls go to the same origin
// (/api/*) - no provider credentials ever exist in the browser.

const TOKEN_KEY = "ugc_token";

export function getToken(): string | null {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}
export function setToken(t: string | null) {
  try { if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const res = await fetch(path, { ...init, headers, cache: "no-store" });
  if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/api/auth/login")) {
    setToken(null);
    window.location.href = "/login";
  }
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const b = await res.json();
      msg = typeof b.detail === "string" ? b.detail : JSON.stringify(b.detail ?? b);
    } catch { /* ignore */ }
    throw new ApiError(res.status, msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const post = <T,>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body ?? {}) });

// ------------------------------------------------------------------ types
export type StageState = "done" | "active" | "failed" | "waiting" | "cancelled" | "pending";
export interface PipelineStage { key: string; label: string; state: StageState }

export interface ProjectSummary {
  id: string; name: string; status: string; stage: string; stage_detail: string | null; error: string | null;
  created_at: string; updated_at: string; completed_at: string | null; budget_credits: number;
  estimated_credits: number; spent_credits: number; language?: string; variants?: number;
  thumbnail_url: string | null; pipeline: PipelineStage[];
}

export interface Job {
  id: string; purpose: string; kind: string; provider: string; model: string | null; status: string; progress: number;
  attempts: number; max_attempts: number; round: number; candidate_index: number; scene_id: string | null;
  provider_job_id: string | null; estimated_credits: number; actual_credits: number | null; error: string | null;
  selected: boolean; created_at: string; submitted_at: string | null; completed_at: string | null;
}

export interface QACheck { check: string; status: string; detail: string; value?: unknown }
export interface QAIssue { check: string; severity: "low" | "medium" | "high" | "critical"; detail: string }
export interface QAReport {
  id: string; scope: "scene" | "export"; round: number; passed: boolean; score: number | null;
  checks: QACheck[]; issues: QAIssue[]; scene_id: string | null; export_id: string | null; created_at: string;
}

export interface Scene {
  id: string; idx: number; beat: string; duration: number; dialogue: string; framing: string; creator_movement: string;
  product_interaction: string; environment: string; required_references: string[]; video_prompt: string;
  keyframe_prompt: string; audio_requirements: string; status: string; regen_round: number; audio_source: string | null;
  lipsync_status: string | null; qa_status: string | null; keyframe_url: string | null; video_url: string | null;
}

export interface Concept {
  id: string; angle: string; title: string; hook: string; core_message: string; emotional_angle: string;
  visual_concept: string; cta: string; target_duration: number; claims_used: string[]; score: number; rank: number;
  selected: boolean;
  script: { id: string; version: number; language: string; full_text: string; word_count: number;
    beats: { beat: string; dialogue: string; on_screen_action: string; seconds: number; validation?: string[] }[] } | null;
  storyboard: { id: string; video_model: string; audio_mode: string; total_duration: number; notes: string; scenes: Scene[] } | null;
}

export interface Creator {
  id: string; name: string; description: string | null; appearance: Record<string, string>; voice: Record<string, string>;
  status: string; is_fictional: boolean; likeness_consent: Record<string, unknown> | null; anchor_url: string | null;
  anchor_prompt: string | null; references: { id: string; kind: string; url: string | null; prompt: string | null }[];
  created_at: string; jobs?: Job[];
}

export interface ExportItem {
  id: string; project_id: string; concept_id: string; version: number; status: string; duration: number | null;
  width: number | null; height: number | null; video_url: string | null; download_url: string | null;
  thumbnail_url: string | null; subtitles_url: string | null; edit_settings: Record<string, unknown>; created_at: string;
  concept: { title: string; angle: string; hook: string; cta: string }; qa?: QAReport | null;
  project?: { id: string; name: string; language?: string };
}

export interface ProjectDetail extends ProjectSummary {
  settings: Record<string, unknown>; approvals: Record<string, unknown>; budget_confirmed: boolean; qa_round: number;
  product?: { id: string; url: string | null; name: string | null; brand_name: string | null; description: string | null;
    brand_guidelines: string | null; fetch_status: string | null; research: Record<string, unknown> | null;
    page_meta: Record<string, unknown>; assets: { id: string; kind: string; filename: string; url: string }[] };
  creator: Creator | null; concepts: Concept[]; jobs: Job[]; exports: ExportItem[]; qa_reports: QAReport[];
  usage: { provider: string; kind: string; credits: number; cost_usd: number | null; count: number }[];
}

export interface Dashboard {
  total_ads: number; completed_videos: number; needs_review: number; active_jobs: number; active_projects: number;
  failed_jobs: number; failed_projects: number; credits_spent: number; estimated_cost_usd: number | null;
  global_budget_credits: number; global_committed_this_month: number; recent_projects: ProjectSummary[];
}

export interface Estimate {
  total_credits: number; lines: { item: string; qty: number; credits: number }[]; video_model: string;
  audio_mode: string; scenes_per_ad: number; usd: number | null; basis: string;
}

export interface ModelEntry { key: string; displayName: string; status?: string; useWhen?: string; rating?: number;
  capabilities: Record<string, any> }
