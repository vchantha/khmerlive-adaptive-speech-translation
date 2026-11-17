# Docker-based MVP implementation plan

**Planning document only.** No Compose file or running containers are provided by repository initialization.

## Services for local development

| Service | Purpose | Durability |
| --- | --- | --- |
| `web` | React reviewer UI | stateless |
| `api` | FastAPI REST service | stateless |
| `worker` | Celery audio/ASR/MT jobs | stateless; job state in PostgreSQL |
| `postgres` | jobs, audit, revisions, consent and model metadata | persistent named volume |
| `redis` | broker/cache only | ephemeral/rebuildable |
| `minio` | audio, datasets, model artifacts | persistent named volume |
| `mlflow` (optional dev profile) | experiment tracking | backed by DB and object store |

## Required configuration
- `DATABASE_URL`, `REDIS_URL`, `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`
- `MODEL_DIR`, `ASR_MODEL_ID`, `MT_MODEL_ID`, `MAX_AUDIO_SECONDS`, `UPLOAD_MAX_BYTES`
- `JWT_PUBLIC_KEY` or equivalent auth configuration, `CORS_ALLOWED_ORIGINS`
- Keep .env secrets out of Git. Supply `.env.example` with nonsecret placeholders.

## Startup order
1. Provision directories, volumes and secrets.
2. Start PostgreSQL, Redis, MinIO and validate health.
3. Run one-off migration job and required object-bucket provisioning.
4. Start API, worker and web with readiness checks.
5. Run integration test: audio upload → persistent job → ASR → MT → result.
6. Restart containers and verify metadata, corrections and artifacts remain.
7. Simulate failure/retry without duplicate job outputs.

## Implementation acceptance checks
- `docker compose config` validates; images build with pinned dependencies.
- `docker compose up --build` works on documented host/GPU conditions (after implementation).
- Clean installation, restart persistence, reprocessing idempotency and backup/restore tests pass.
- Health probes indicate missing model files / broken DB connections correctly.
- No external network calls in proven air-gapped mode; models and Python dependencies prepackaged.
- Set CPU-only baseline first, then optional NVIDIA GPU profile.
- Limit upload sizes, apply API auth and network isolation; do not expose PostgreSQL, Redis or MinIO admin publicly.
- Add a repeatable `make test` and CI smoke checks.

## Explicit non-goals at initialization
No claim of production-grade security, measured accuracy, real-time latency, offline compliance or trained model quality is made until verified in tests.
