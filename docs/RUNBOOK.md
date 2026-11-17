# End-to-end Docker runbook — SILO + TLS

## Current secure endpoints

- Dashboard: `https://localhost:8443` (default; configurable with `HTTPS_PORT`)
- HTTP redirect: `http://localhost:8080`
- FastAPI direct: `https://localhost:8000`
- JupyterHub: `https://localhost:8001`
- SILO S3 API: `https://localhost:9000`
- SILO Console: `https://localhost:9001`
- Kafka SSL listener: `localhost:9093`
- PostgreSQL: `127.0.0.1:5432` (host loopback only)
- Redis: `127.0.0.1:6379` (host loopback only)
- MLflow: `http://127.0.0.1:5000` (loopback only; internal research service)

The browser-facing UI/API/JupyterHub, Kafka clients, and SILO object storage use TLS. Kafka's KRaft controller listener remains private PLAINTEXT inside the Docker network in this single-node development topology.

## Storage compatibility

SILO is the S3-compatible maintained fork used by this project. The stack pins:

```text
docker.io/pgsty/silo:RELEASE.2026-11-09T00-00-00Z
```

SILO intentionally retains MinIO-compatible credential environment names. Existing values can remain:

```dotenv
MINIO_ROOT_USER=...
MINIO_ROOT_PASSWORD=...
MINIO_BUCKET=khmerlive
```

Application-facing settings use `SILO_ENDPOINT`, `SILO_SECURE`, and `SILO_CA_FILE`. The API also returns legacy `minio` / `minio_status` aliases so existing consumers and stored PostgreSQL records do not break.

## Pipeline

```text
Upload / YouTube / RTMP-HLS
        |
   HTTPS FastAPI
        |
PostgreSQL job state
        |
Kafka SSL: khmerlive.ingest.requests
        |
 ingestion worker + FFmpeg
        |
 SILO HTTPS raw/processed/stream objects
        |
Kafka SSL: khmerlive.media.chunks + khmerlive.job.events
        |
JupyterHub / training / downstream ASR-MT
```

## First start

```bash
git pull origin main
cp -n .env.example .env

# Edit .env and replace every change-me value.
# JupyterHub 6.x requires the admin password to be >= 32 characters.

make tls

docker compose config
docker compose pull
docker compose build
docker compose up -d
docker compose ps
```

`make tls` creates a local KhmerLive CA and SAN certificates under `infra/tls/generated/`. Private keys are gitignored.

For browser access without warnings, import:

```text
infra/tls/generated/ca.crt
```

into your local workstation/browser trust store. For production, replace these generated certificates with certificates from your internal PKI or a public CA.

## Verify

```bash
make smoke
```

The smoke test:

1. verifies the HTTPS gateway using the project CA;
2. generates a short WAV inside the API container;
3. sends it through the TLS API;
4. publishes the ingest request to Kafka over SSL;
5. lets the worker write objects to SILO over HTTPS;
6. reads the recent PostgreSQL-backed job status.

Inspect SILO for:

```text
raw/<job-id>/...
processed/<job-id>/audio/chunk-*.wav
streams/<job-id>/video/...
streams/<job-id>/audio/...
```

## Kafka TLS topics

- `khmerlive.ingest.requests`
- `khmerlive.media.chunks`
- `khmerlive.job.events`

Internal clients use:

```dotenv
KAFKA_BOOTSTRAP_SERVERS=kafka:19093
KAFKA_SECURITY_PROTOCOL=SSL
KAFKA_SSL_CA_LOCATION=/etc/khmerlive/tls/ca.crt
```

The host SSL listener is `localhost:9093`.

## JupyterHub

Current project requirement: JupyterHub 6.2.x.

Users:

- `researcher` — shared research password
- `admin` — admin password (minimum 32 characters)

The included notebook `training/notebooks/00_environment_check.ipynb` verifies PostgreSQL, SILO HTTPS and Kafka SSL connectivity.

## Environment migration from the previous stack

If an existing `.env` already contains:

```dotenv
MINIO_ROOT_USER=...
MINIO_ROOT_PASSWORD=...
MINIO_BUCKET=...
```

keep those variables. Add:

```dotenv
SILO_ENDPOINT=silo:9000
SILO_SECURE=true
SILO_CA_FILE=/etc/khmerlive/tls/ca.crt

KAFKA_BOOTSTRAP_SERVERS=kafka:19093
KAFKA_SECURITY_PROTOCOL=SSL
KAFKA_SSL_CA_LOCATION=/etc/khmerlive/tls/ca.crt
KAFKA_TLS_PASSWORD=<strong-password>
HTTPS_PORT=8443
```

Also update `JUPYTERHUB_ADMIN_PASSWORD` to at least 32 characters.

## Development vs production

This Compose deployment is a secure development/research baseline, not HA production infrastructure. Before production add OIDC/SSO, dedicated user isolation for JupyterHub, Kafka authentication (mTLS or SASL_SSL), PostgreSQL TLS, Redis TLS or network isolation, HA Kafka/SILO, secret management, backups, observability, rate limits, SSRF-safe stream allowlists, malware/upload validation, and tested recovery/model rollback.
