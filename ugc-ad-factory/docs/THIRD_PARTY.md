# Third-party notices

## kofiowusuai-lab/ugc-skills (MIT)

Copyright (c) 2026 Kofi Owusu

Concepts and parameters adapted from the following files:

| Reference file | Used in |
|---|---|
| `skills/ugc-video-producer/scripts/trim_clip_tails.py` (RMS speech-end detection) | `backend/app/media/ffmpeg.py` |
| `skills/ugc-video-producer/scripts/stitch_shots.sh` (normalisation and mapping) | `backend/app/media/ffmpeg.py` |
| `skills/ugc-video-producer/scripts/realism_prompts.md` and `scripts/ugc_character_bible.sh` (prompt rules, identity lock) | `backend/app/agents/prompts.py` |
| `scripts/ugc_clip_referee.py` and `scripts/ugc_gemini_referee.py` (thresholds, frame sampling) | `backend/app/agents/qa.py` |
| `vendor/voiceswap/voiceswap/wavespeed.py` (lip-sync request flow) | `backend/app/providers/lipsync.py` |

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Runtime dependencies (selection)

| Component | Licence |
|---|---|
| FastAPI | MIT |
| Pydantic | MIT |
| SQLAlchemy / Alembic | MIT |
| Celery / kombu | BSD-3 |
| httpx | BSD-3 |
| boto3 | Apache-2.0 |
| BeautifulSoup | MIT |
| anthropic SDK | MIT |
| structlog | MIT / Apache-2.0 |
| PyJWT | MIT |
| bcrypt | Apache-2.0 |
| Next.js / React | MIT |
| Tailwind CSS | MIT |
| lucide-react | ISC |
| Radix Slot | MIT |
| class-variance-authority, clsx, tailwind-merge | MIT |
| FFmpeg (external binary; the Debian build includes GPL components such as libx264) | LGPL/GPL |
| MinIO server (optional, separate container) | AGPL-3.0 |
| PostgreSQL | PostgreSQL licence |
| Redis 7 | BSD-3 |
| Nginx | BSD-2 |

The pattern of the shadcn/ui components (`frontend/src/components/ui`) is MIT.
