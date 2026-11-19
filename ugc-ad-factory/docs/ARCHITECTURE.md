# Architecture

```
Browser ──► Nginx :8080 ─┬─► Next.js (dashboard, wizard, monitor, libraries)
                         └─► FastAPI /api ──► PostgreSQL (state, jobs, costs, QA)
                                  │                ▲
                                  ▼                │
                               Redis ◄──── Celery worker(s) ──► LetzAI API (images, edits, videos, speech, music)
                                  ▲                │        ──► Anthropic (structured agents + vision QA, optional)
                            Celery beat            │        ──► WaveSpeed lip-sync (optional)
                         (recovery, retention)     ▼
                                          S3 / MinIO (all media, presigned URLs)
                                          FFmpeg (editing + technical QA)
```

## Backend layout (`backend/app`)

| Package | Responsibility |
|---|---|
| `core/` | Settings (env only), DB engine, JWT/bcrypt, HMAC signed URLs and webhook tokens, JSON logging |
| `db/models.py` | The 17 tables (below) |
| `providers/` | Replaceable interfaces: `MediaProvider`, `LLMProvider`, `LipSyncProvider`, `TranscriptionProvider`. Implementations: `letzai/` (typed client + schemas + catalogue + adapter), `mock.py`, `llm.py` (Anthropic / heuristic), `lipsync.py` (WaveSpeed / none), `transcription.py`. Wired in `registry.py`. |
| `agents/` | The nine agents (researcher, strategist, creator director, scene director, video producer, audio director, lip-sync specialist, editor, QA), plus `schemas.py` (structured outputs) and `prompts.py` (rules and compliance) |
| `pipeline/` | `stages.py` (state machine), `runner.py` (leases, stage loop, recovery), `jobs.py` (generation-job lifecycle), `costs.py` (estimates, budgets, usage), `dispatch.py` (Celery or inline) |
| `media/ffmpeg.py` | Probe, normalise, trim, fit audio, mux, concat, captions, overlays, end card, loudness, black/freeze detection |
| `services/` | Storage (S3/local) and SSRF-safe fetcher with robots.txt |
| `api/` | REST routers, request schemas, serializers |
| `worker/` | Celery app, tasks and beat schedule |

## Workflow state machine

`research → script → character → scenes → video → voice → lipsync → editing → qa → export`

Each stage is **idempotent**. It reads persisted state, creates only the missing work, and returns one of:

| Result | Meaning |
|---|---|
| `done` | Advance to the next stage |
| `wait` | Provider jobs are in flight; a job completion re-dispatches `advance_project` |
| `pause` / `pause_budget` | Approval checkpoint (`concepts`, `creator`, `storyboard`) or budget confirmation |
| `goto:video` | QA asks to regenerate the failed scenes only (bounded by `MAX_QA_ROUNDS` and the budget) |

Concurrency is controlled by a **lease** on the project row: an atomic `UPDATE … WHERE lease expired`. Only one worker advances a project at a time. A busy lease re-queues the event, so nothing is lost.

Celery beat runs `recover_stale` every minute. It:
* re-polls overdue jobs;
* resubmits pending jobs;
* nudges idle running projects.

A worker crash or a lost message therefore self-heals. Jobs stuck in `submitting` (outcome unknown) are **failed rather than resubmitted**, to avoid a duplicate paid generation.

## Generation-job lifecycle

```
pending ─CAS→ submitting ─► submitted/running ─poll/webhook→ succeeded
   ▲                                │
   └── retry: retryable error and attempts < MAX_JOB_ATTEMPTS, exponential backoff
                                    └─► failed
```

* **Duplicate prevention.** `idempotency_key` is unique, built from purpose, scene, round and candidate.
* **Single submission.** Compare-and-set from `pending` to `submitting`.
* **Gates before every submission.** A per-project budget, a global monthly budget, and a provider concurrency limit.
* **Success is never assumed.** A job is `succeeded` only after a terminal provider status *and* a successful download into our storage. A terminal status without a URL counts as a failure.
* **Bounded error handling.**
  * Download errors and poll errors are capped (`poll_errors`).
  * Content-policy failures (`not_allowed` …) are not retried.
* **Persistence.** Every HTTP call is a `provider_requests` row (secrets redacted). Every billable success is a `usage_records` row; credits come from the provider when reported, otherwise from the catalogue estimate, flagged as `estimated`.

## Consistency strategy

1. **Creator anchor.** A photoreal portrait is generated once from a fictional creator spec and stored in the creator library, together with the voice preset and language.
2. **Per-scene keyframe.** `POST /image-edits` with `[anchor, real product photo]` and an identity- and product-lock prompt.
3. **Image-to-video from that keyframe.** Real product photos are passed as reference assets when the model supports them.
4. **Real branding in post.** Exact branding is composited in editing (end card or overlay from the real image), never generated.
5. **QA comparison.** QA compares frames against the anchor (identity ≥ 0.80) and the product photo. Only failing scenes are regenerated.

## Data model

| Table | Holds |
|---|---|
| `users` | Accounts and roles |
| `projects` | Settings, budget, approvals, lease, stage |
| `products` | Input and structured research |
| `product_assets` | Uploaded images and their provider copies |
| `creators` | Appearance, voice, consent, anchor |
| `creator_references` | Anchor, variant and uploaded references |
| `ad_concepts` | Concepts and selection |
| `scripts` | Versioned beats |
| `storyboards` | Video model, audio mode |
| `scenes` | Prompts, assets per step, regeneration round, QA status |
| `generation_jobs` | Provider job id, status, attempts, credits |
| `generated_assets` | Storage key, metadata, provider URL |
| `provider_requests` | Audit of every provider call |
| `qa_reports` | Scene and export checks and issues |
| `exports` | Versioned MP4 + thumbnail + SRT |
| `usage_records` | Credits and USD |
| `application_settings` | Settings stored in the database |

All tables use foreign keys with `CASCADE` / `SET NULL` and indexes on lookup columns. Creator assets are stored outside project ownership, so deleting a project never removes a reusable creator.

## Security

* **Credentials.** API keys exist only in backend environment variables. The settings endpoint reports `configured: yes/no` only.
* **Authentication and roles.** JWT bearer auth with bcrypt passwords. Roles are `admin`, `member` (owns their projects) and `viewer` (read-only).
* **Media access.**
  * S3 media is served via presigned URLs.
  * Local media is served via HMAC-signed, expiring URLs.
* **SSRF protection.** Applies to every outbound fetch, including redirects and provider downloads:
  * only `http`/`https`;
  * only allowed ports;
  * every resolved IP must be public (private, loopback, link-local, CGNAT and metadata ranges are blocked).
* **Robots.** robots.txt is honoured: missing → allowed, 5xx → disallowed (RFC 9309).
* **Webhooks.** Authenticated by a per-job HMAC token. The payload is ignored and the job is re-polled.
* **Uploads.** Size, type and decoding are validated. Uploaders must attest rights to product images. Real-person creators require recorded consent and an uploaded reference; anchors are never generated for them.
* **Logs.** Structured JSON with request IDs and tracebacks on unhandled errors.
