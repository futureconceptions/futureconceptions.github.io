# REST API

Interactive OpenAPI docs: `http://localhost:8080/docs` (raw schema at `/openapi.json`).

All endpoints require `Authorization: Bearer <token>` unless noted.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login` | `{email, password}` → `{access_token, user}` (no auth) |
| GET | `/api/auth/me` | Current user |
| POST/GET | `/api/users` | Create / list users (admin) |
| GET | `/api/dashboard` | Totals, active/failed jobs, credits, recent projects |
| POST | `/api/projects/estimate` | Cost estimate for a `ProjectCreate` body (no charges) |
| POST | `/api/projects` | **multipart**: `payload` = ProjectCreate JSON, `images[]` = product photos. Starts the pipeline, or returns `awaiting_budget`. |
| GET | `/api/projects` | List (`?status=`) |
| GET | `/api/projects/{id}` | Full state: pipeline, product research, creator, concepts/scripts/storyboards/scenes, jobs, exports, QA, usage |
| GET | `/api/projects/{id}/estimate` | Remaining cost based on the actual storyboard |
| POST | `/api/projects/{id}/approve` | `{checkpoint: concepts\|creator\|storyboard, selected_concept_ids?}` |
| POST | `/api/projects/{id}/confirm-budget` | `{budget_credits?}` |
| POST | `/api/projects/{id}/cancel` | Stop tracking jobs; images are interrupted at LetzAI |
| POST | `/api/projects/{id}/retry` | Resume a failed or cancelled project (`?stage=` to restart earlier) |
| POST | `/api/projects/{id}/scenes/{scene_id}/regenerate` | Re-render one scene and re-edit |
| DELETE | `/api/projects/{id}` | Delete (not while running) |
| GET/POST | `/api/creators` | Creator library: list, or create (fictional by default; a real person requires consent fields) |
| GET/DELETE | `/api/creators/{id}` | Creator detail incl. jobs / delete |
| POST | `/api/creators/{id}/regenerate-anchor` | Replace the look |
| POST | `/api/creators/{id}/approve` | Approve the creator |
| POST | `/api/creators/{id}/references` | multipart `image` (`?set_as_anchor=true`) |
| GET | `/api/jobs` | Jobs (`?project_id=&status=`) |
| GET | `/api/jobs/{id}/requests` | Provider call audit for a job |
| POST | `/api/jobs/{id}/retry` | Retry a failed job |
| GET | `/api/exports` | Ad library (`?status=approved\|qa_failed\|superseded`) |
| GET | `/api/exports/{id}` | Export + script + scenes + scene QA + product + settings + version history |
| GET | `/api/assets/{id}/url` | Fresh signed URL |
| GET | `/api/files/{key}?exp=&sig=` | Signed local-storage file (no auth; signature required) |
| POST | `/api/webhooks/letzai/{job_id}?token=` | LetzAI webhook (per-job HMAC token; triggers a re-poll) |
| GET | `/api/settings` | Effective provider configuration (never secrets) |
| PUT | `/api/settings/{key}` | Admin-editable application settings |
| GET | `/api/providers/models` | LetzAI model catalogue (live or snapshot) |
| GET | `/api/usage?days=30` | Usage by provider, model and kind |
| GET | `/api/health` | Database / Redis health (no auth) |

## ProjectCreate (JSON in the `payload` form field)

```json
{
  "product_name": "AquaBottle 750",
  "product_url": "https://shop.example.com/aquabottle",
  "product_description": "Keeps drinks cold for 24 hours…",
  "brand_name": "Aqua",
  "brand_guidelines": "Friendly, no superlatives",
  "target_audience": "commuters",
  "language": "de",
  "duration": 20,
  "variants": 3,
  "cta": "Jetzt entdecken",
  "creator_id": null,
  "creator_prefs": {"gender": "female", "age_range": "25-34"},
  "approval_checkpoints": [],
  "video_model": "video-seedance25",
  "audio_mode": "auto",
  "resolution": "720p",
  "video_candidates": 1,
  "keyframes": "per_scene",
  "subtitles": true,
  "end_card": true,
  "music": false,
  "research_agents": 3,
  "research_effort": "medium",
  "research_metric": "ndcg",
  "research_max_pages": 6,
  "budget_credits": 20000,
  "confirm_budget": false,
  "assets_licensed": true
}
```

Only one of `product_url`, `product_description` or an image is required. Everything else has defaults (simple mode).
