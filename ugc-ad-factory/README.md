# UGC Ad Factory

A self-hosted platform that turns **one product** (URL, description and/or photos) into **several finished, vertical UGC advertisements**. It is built on the [LetzAI](https://letz.ai/docs/api) API.

```
Research → Script → Character → Scenes → Video → Voice → Lip Sync → Editing → QA → Export
```

Nine agents run as a persistent, resumable workflow on Celery:

1. **Product researcher.** Fetches the page (SSRF-safe, robots.txt-aware) and extracts only claims it can back with evidence.
2. **Advertising strategist.** Writes several angles with hook, script, emotion, visual and CTA. Fabricated testimonials are rejected.
3. **Creator director.** Casts a fictional creator and creates a reusable anchor image with LetzAI.
4. **Scene director.** Builds a storyboard fitted to the selected model's duration limits.
5. **Video producer.** Renders scenes with LetzAI image-to-video from per-scene keyframes built from the anchor plus the real product photo.
6. **Audio director.** Uses the video model's native audio, or LetzAI speech in English or German.
7. **Lip-sync specialist.** Keeps native sync, or calls an external lip-sync adapter, or falls back to voice-over.
8. **Video editor.** FFmpeg: 1080×1920 H.264/AAC, captions, real-photo end card, loudness normalisation.
9. **QA.** Technical checks plus multimodal identity and product checks. Failed scenes are regenerated within retry and budget limits.

Cost tracking, budgets, approval checkpoints, retries and an audit trail of every provider call are built in.

## Quick start (one command)

```bash
cp .env.example .env
docker compose up --build
```

* **UI:** <http://localhost:8080>. Sign in as `admin@example.com` / `admin12345` and change this in `.env`.
* **API docs:** <http://localhost:8080/docs>
* **Default mode is `MEDIA_PROVIDER=mock`.** The complete pipeline runs end to end with real FFmpeg-rendered placeholder media and **never spends credits**.

To generate real ads, follow [docs/OPERATIONS.md → Going live](docs/OPERATIONS.md#going-live-with-letzai-steps-that-need-real-credentials). In short, set `MEDIA_PROVIDER=letzai` and `LETZAI_API_KEY`, and optionally `LLM_PROVIDER=anthropic` with `ANTHROPIC_API_KEY` for model-written scripts and visual QA.

## Local development without Docker

**Requirements:** Python 3.12+, Node 22, FFmpeg, PostgreSQL, Redis. For a single process you can skip Redis with `TASK_DISPATCH=inline`.

```bash
# backend
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://ugc:ugc@localhost:5432/ugc STORAGE_BACKEND=local
alembic upgrade head
uvicorn app.main:app --reload --port 8000
celery -A app.worker.celery_app worker -Q pipeline,polling   # second terminal
celery -A app.worker.celery_app beat                         # third terminal

# frontend
cd frontend && npm ci && BACKEND_URL=http://localhost:8000 npm run dev   # http://localhost:3000
```

## Tests

```bash
cd backend && pytest            # 82 tests (1 opt-in live test skipped), mocked providers, real FFmpeg, no paid calls
cd frontend && npm run typecheck && npm run build
```

The tests cover:
* the LetzAI client: auth, retries, upload flow, request mapping, status normalisation;
* schema validation, webhooks, the job lifecycle (idempotency, compare-and-set, retries, budget and concurrency gates);
* SSRF and robots handling, product extraction, script validation, scene planning;
* FFmpeg assembly, tail trimming and audio fitting, storage signing;
* cost estimates and QA decisions, including a regeneration round;
* full API end-to-end runs: approvals, budget confirmation, failure and resume, creator reuse.

A live LetzAI test exists but is **opt-in** (`LETZAI_LIVE_TEST=I_ACCEPT_COSTS`).

## Repository layout

```
backend/    FastAPI app, agents, pipeline, providers, Alembic migrations, tests, Dockerfile
frontend/   Next.js 15 + TypeScript + Tailwind + shadcn-style UI, Dockerfile
deploy/     Nginx reverse proxy config
docs/       COMPATIBILITY (Phase 1 matrix), ARCHITECTURE, API, OPERATIONS, THIRD_PARTY
docker-compose.yml, .env.example
```

## Documentation

* [Compatibility matrix: reference repo vs. LetzAI](docs/COMPATIBILITY.md)
* [Architecture, state machine, data model, security](docs/ARCHITECTURE.md)
* [REST API](docs/API.md)
* [Operations, costs, going live, limitations](docs/OPERATIONS.md)
* [Third-party notices](docs/THIRD_PARTY.md)

## Responsible use

* Creators are fictional by default. Real likenesses require recorded consent and an uploaded reference.
* Scripts may only use claims backed by the product page or your description.
* Phrasing that presents fabricated personal experience or reviews is rejected automatically.
* Uploaded product images require a rights attestation.
* Automated QA reduces errors but **does not guarantee** realism or correctness, so review ads before publishing.
