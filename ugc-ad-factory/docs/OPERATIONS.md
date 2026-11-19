# Operations, costs and limitations

## Going live with LetzAI (steps that need real credentials)

1. Create an API key at <https://www.letz.ai/subscription>.
2. In `.env`, set `MEDIA_PROVIDER=letzai` and `LETZAI_API_KEY=...`. Set `LETZAI_ORGANIZATION_ID` too if you bill an organization.
3. Optional: set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=...` for model-written research, scripts and storyboards and for **visual QA**. Without it, deterministic templates are used and visual checks are reported as `not_checked`.
4. Optional: set `WEBHOOK_BASE_URL=https://your-public-host` so LetzAI can call back. Polling works without it.
5. Run the opt-in smoke test. It spends about 10 credits:
   `LETZAI_LIVE_TEST=I_ACCEPT_COSTS LIVE_LETZAI_API_KEY=... pytest backend/tests/test_integration_letzai.py -s`
6. Start with 1 variant, `resolution=480p` and the default budget. Check the QA report, then scale up.

**Verification status:** the LetzAI integration was built against the public OpenAPI spec and instructions. It is covered by mocked HTTP tests. **No real LetzAI generation was run during development (no key was available).** Run step 5 before production use.

## Cost model

* **Credits are the unit.** Estimates use the LetzAI catalogue list prices (`catalog_snapshot.json`, refreshed live from `GET /catalog`). `POST /generations/quote` is available via `LetzAIProvider.quote()`.
* **When estimates happen:**
  * at submission, from the requested settings, including a 25 % QA-regeneration contingency;
  * again after the storyboard exists, from the exact scenes.
* **Budget confirmation.** If the estimate exceeds the project budget, the project pauses (`awaiting_budget`) until confirmed.
* **Gates before every request.** Each submission checks the project budget and the global monthly budget (`GLOBAL_BUDGET_CREDITS`).
* **Usage records.** Actual credits come from the provider when reported (speech returns `credits`); otherwise the estimate is recorded and flagged `estimated`.
* **Optional dollar view.** `LETZAI_USD_PER_CREDIT` converts credits to dollars for display only.

Typical list prices (catalogue snapshot 2026-11-19; check `/settings` in the app for current values):

| Item | Credits |
|---|---|
| Anchor image (Nano Banana Pro 1k) | 80 |
| Keyframe edit | 80 |
| Video, Seedance 2.5 | 150 /s @480p, 300 /s @720p, 580 /s @1080p |
| Video, Kling 4 | 127 /s @720p |
| Video, MiniMax H3 Max | 28–42 /s (fast tests) |
| Speech, `audio-eleven-v4` | 100 per 1k characters |

A 20-second ad with 4 scenes at 720p on Seedance 2.5 costs about 6,000–6,500 credits per variant before regeneration.

## Scaling and reliability

* **Workers.** Scale with `docker compose up --scale worker=N`. Queues are split: `pipeline` (stages, FFmpeg) and `polling`.
* **Provider concurrency.** `LETZAI_MAX_CONCURRENT_JOBS` is a soft, shared limit (counted in the database).
* **Rate limits.** 429/5xx responses are retried with exponential backoff and honour `Retry-After`. 4xx validation errors are not retried.
* **Recovery.** Celery beat (`recover_stale`) re-polls, resubmits and re-advances every minute. Tasks use `acks_late`, so a killed worker's task is redelivered.
* **Data retention.** Media of finished projects older than `DATA_RETENTION_DAYS` is deleted from storage by beat; database audit rows are kept. `0` disables this.

## Storage note

MinIO no longer publishes images on Docker Hub. The compose file uses `quay.io/minio/minio` and can be overridden with `MINIO_IMAGE`. Any S3-compatible server works (AWS S3, Cloudflare R2, SeaweedFS, Garage). Point `S3_ENDPOINT_URL` at it and set `S3_PUBLIC_ENDPOINT_URL` to the URL browsers use for presigned links. The Docker validation of this project ran with SeaweedFS as the S3 server, because quay.io was not reachable from the build sandbox.

## Known limitations (honest list)

* **Automated QA cannot guarantee realism.**
  * Visual checks need a vision model. Dialogue accuracy needs `TRANSCRIPTION_PROVIDER=faster_whisper` (not installed in the default image).
  * Lip-sync accuracy is not measured. Native-audio scenes are marked "assumed".
* **Lip-sync.** LetzAI has no lip-sync endpoint. Without an external provider, TTS scenes are edited as voice-over. Scenes are then directed as non-speaking, and this is marked in QA.
* **Voice consistency.** Speech uses six LetzAI voice presets. Native-audio models generate their own voice per clip, so the voice can vary between scenes. Use `audio_mode=tts` when an identical voice across scenes matters more than in-camera speech.
* **No voice cloning or speech-to-speech** through LetzAI's public API.
* **Video cancellation.** LetzAI cannot cancel a video already rendering; cancelled projects simply ignore the result.
* **Webhook payloads** are undocumented by LetzAI, so they only trigger a re-poll.
* **Untested providers.** WaveSpeed lip-sync and live LetzAI calls are untested against real accounts in this repository.
* **Single-tenant.** Roles are basic and there is no SSO.
