# System architecture

**Status:** Proposed; not implemented or benchmarked.

## Logical components
1. **Web (React/TypeScript):** upload/record, display segment timestamps, edit transcript and translation separately, permission-scoped review, quality dashboards.
2. **API (FastAPI):** authenticated ingestion, jobs, feedback, health, audit and version metadata; validate MIME, max size, duration and rate limits.
3. **Workers (Celery + Redis):** job orchestration with idempotency and retries; Redis is not durable truth.
4. **Audio service:** FFmpeg resample to a model-supported rate, mono normalization where appropriate, VAD, segmentation, optional diarization (future).
5. **ASR adapter:** `transcribe(audio, language, model_version) -> segments, confidence_metadata`; model-specific confidence must be calibrated, not assumed comparable.
6. **MT adapter:** `translate(text, source_lang, target_lang, model_version) -> text`; preserve named entities and domain terms via reviewed glossary.
7. **PostgreSQL:** immutable-ish job metadata, status transitions, transcript and translation versions, reviewer decisions, consent/retention, model mapping and audit trail.
8. **SILO:** original/normalized audio, artifacts, versioned training datasets. Object URIs and checksums are indexed in PostgreSQL.
9. **Training/evaluation:** isolate GPU workloads; snapshot consented reviewed examples, run experiments, evaluate fixed held-out sets, human approve promotion.
10. **Registry:** model metadata, artifact checksums, signed/approved version, canary and rollback pointers.

## Direction-specific pipeline

**V1:** English audio → English ASR → English transcript → English→Khmer MT → Khmer text.

**V2:** Khmer audio → Khmer ASR → Khmer transcript → Khmer→English MT → English text.

Translation corrections are **not** ASR labels; transcript corrections are **not** automatically valid MT reference pairs until paired with reviewer-approved target text.

## Suggested data model

- `audio_assets(id, object_uri, sha256, duration_ms, language_hint, owner_id, consent_id, created_at, deletion_at)`
- `jobs(id, asset_id, direction, status, asr_model_version, mt_model_version, started_at, completed_at, error_code)`
- `transcript_segments(id, job_id, start_ms, end_ms, predicted_text, current_revision_id)`
- `transcript_revisions(id, segment_id, corrected_text, author_id, review_status, created_at)`
- `translations(id, job_id, source_revision_id, predicted_text, target_lang, current_revision_id)`
- `translation_revisions(id, translation_id, corrected_text, author_id, review_status, created_at)`
- `consents(id, subject_ref, purpose, recorded_at, revoked_at, retention_until)`
- `dataset_versions(id, manifest_uri, sha256, split_policy, consent_snapshot, created_at)`
- `model_versions(id, task, artifact_uri, sha256, license, evaluation_uri, approval_state)`
- `audit_events(id, actor_id, action, entity_type, entity_id, created_at)`

Use proper foreign keys, migrations, RBAC, encryption at rest/in transit and data-minimizing audit logs. Do not copy raw audio into database rows.

## API contract proposal

- `POST /api/v1/audio` multipart upload → asset ID.
- `POST /api/v1/jobs` `{asset_id, direction}` → queued job ID.
- `GET /api/v1/jobs/{id}` → status and model versions.
- `GET /api/v1/jobs/{id}/result` → segments, transcript and translation.
- `POST /api/v1/segments/{id}/revisions` → proposed correction.
- `POST /api/v1/translations/{id}/revisions` → proposed correction.
- `POST /api/v1/reviews/{revision_id}/decision` → reviewer approval/rejection.
- `GET /health/live`, `GET /health/ready`.

Authentication, authorization, data deletion and idempotency need explicit implementation before production use.

## Operational path

Start with a single Docker Compose environment. Later move stateless API/web/worker instances to Kubernetes; retain durable PostgreSQL and SILO volumes/backups and dedicated GPU node scheduling. Define latency, RPO/RTO and concurrency targets from measured baselines rather than assumptions.
