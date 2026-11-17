# End-to-end Docker runbook

## Services

- Dashboard: `http://localhost:8080`
- FastAPI: `http://localhost:8000`
- JupyterHub: `http://localhost:8001`
- MLflow: `http://localhost:5000`
- MinIO S3/console: `http://localhost:9000` / `http://localhost:9001`
- Kafka host listener: `localhost:9092`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

Pipeline:

```text
Upload / YouTube / RTMP-HLS
        |
      FastAPI
        |
PostgreSQL job state
        |
Kafka: khmerlive.ingest.requests
        |
 ingestion worker + FFmpeg
        |
 MinIO raw/processed/stream objects
        |
Kafka: khmerlive.media.chunks + khmerlive.job.events
        |
JupyterHub / training / downstream ASR-MT
```

## Start

```bash
cp .env.example .env
# change every change-me secret
docker compose config
docker compose pull
docker compose build
docker compose up -d
docker compose ps
```

Run the smoke test:

```bash
make smoke
```

The test generates a short WAV in the API container, uploads it, waits for the worker and lists jobs. Inspect MinIO for `raw/<job-id>/...` and `processed/<job-id>/audio/chunk-*.wav`.

## Kafka topics

- `khmerlive.ingest.requests`
- `khmerlive.media.chunks`
- `khmerlive.job.events`

## Live stream

RTMP/RTMPS and HTTP(S) HLS are accepted. The worker uses FFmpeg to create finalized MPEG-TS segments and mono 16-kHz WAV audio objects. Each object is uploaded to MinIO and announced with a Kafka event. `MAX_STREAM_SECONDS` limits a capture session.

This MVP uses one Kafka consumer process per worker container; one long-lived stream occupies that process. Scale worker replicas or introduce a dedicated stream supervisor before high-concurrency use.

## JupyterHub training

JupyterHub uses SharedPasswordAuthenticator and SimpleLocalProcessSpawner for a trusted local research environment. It is not suitable as-is for an internet-facing multi-tenant deployment.

The image includes PyTorch/Torchaudio, Transformers, Datasets, Accelerate, PEFT, Evaluate, Faster-Whisper, SentencePiece, JiWER, SacreBLEU, Librosa, MLflow, Optuna, Kafka, MinIO/S3, PostgreSQL, Pandas/Polars and plotting tools.

Optional heavyweight build args:

```bash
docker compose build --build-arg INSTALL_NEMO=1 --build-arg INSTALL_BITSANDBYTES=1 jupyterhub
```

For real GPU training, use a CUDA/NVIDIA training image matched to your host driver and PyTorch CUDA matrix; the default portable image must not be assumed to provide GPU acceleration.

## Production gaps

Before production: TLS/OIDC, per-user notebook isolation, Kafka TLS/SASL, least-privilege MinIO/PostgreSQL credentials, SSRF-safe stream allowlists, upload scanning and hard size/type limits, Alembic migrations, HA Kafka/object storage, backup/restore, observability and tested model promotion/rollback.

The Compose file pins historical MinIO community image `RELEASE.2025-06-13T11-33-47Z` for reproducible local development. Reassess the supported MinIO/AIStor or source-build path before production.
