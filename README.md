# KhmerLive Adaptive Speech Translation

**Open-source research and engineering project for adaptive, offline-capable English–Khmer speech translation.**

> **Status:** Research / architecture initialization. No trained models, validated benchmark results, or production-ready services are included yet.

## Release direction

| Release | Input | Recognition | Translation | Output |
| --- | --- | --- | --- | --- |
| **V1** — English → Khmer | English speech | English ASR | English-to-Khmer MT | Khmer text |
| **V2** — Khmer → English | Khmer speech | Khmer ASR | Khmer-to-English MT | English text |

Speech synthesis (Khmer/English TTS) is an **optional later extension**; it is not required for V1 or V2 text output.

## Vision

Build a modular system that (1) recognizes speech, (2) translates the resulting text, (3) lets authorized reviewers correct transcripts and translations, and (4) improves models through **reviewed, versioned, evaluated and approved** adaptation. Support Khmer accents, Cambodian English, telecom terminology, code-switching research, and fully offline operation after model/artifact provisioning.

**Adaptive** does not mean self-modifying weights on every request. Immediate corrections may affect user-visible text or approved terminology, but training data must be consented, reviewed, versioned, and evaluated before a new model goes live.

## Architecture

```text
Microphone / file / stream
          |
     Ingestion API
          |
  FFmpeg normalization + VAD
          |
   Language-aware ASR adapter ----------> transcript + segment timestamps
          |                                         |
     MT model adapter ---------------------> translated text
          |                                         |
          +----------> review UI / feedback --------+
                              |
                PostgreSQL (metadata + audit)
                MinIO (encrypted audio/datasets/artifacts)
                              |
                 consent checks + annotation QA
                              |
             versioned training/evaluation datasets
                              |
              fine-tune experiments + benchmarks
                              |
            model registry / approval / rollback
                              |
                      ASR and MT adapters
```

Run inference without public network dependencies once images, Python packages, and licensed model files are packaged locally. Offline viability must be demonstrated in a disconnected test.

## MVP technical plan (not yet implemented)

- **API:** Python, FastAPI; routes for upload, jobs, transcript, translation, corrections, model version and health.
- **Web:** React + TypeScript for recordings, side-by-side transcript/translation correction, review history and dashboards.
- **ASR / MT:** Pluggable local model adapters; benchmark models and license terms before selection. Do not assume Khmer quality without measured evidence.
- **Audio:** FFmpeg normalization and voice activity detection.
- **Persistence:** PostgreSQL for job states, corrected text, provenance, consent and audit; MinIO for audio, dataset snapshots, and model files. Redis/Celery for queues only, not system of record.
- **Training:** PyTorch / Transformers / PEFT where model-compatible; MLflow experiment tracking; offline evaluation and manual promotion.
- **Operations:** Docker Compose development deployment first; Kubernetes/RKE2 later. Secrets in env/secret stores, never committed.

See [architecture](docs/ARCHITECTURE.md), [roadmap](docs/ROADMAP.md), [repository layout](docs/PROJECT_STRUCTURE.md), [Docker MVP plan](docs/DOCKER_MVP_PLAN.md), and [research and evaluation](docs/RESEARCH_EVALUATION.md).

## Getting started

1. Review the architecture and release acceptance criteria.
2. Select baseline ASR and MT candidates and check **licenses, data rights and offline feasibility**.
3. Obtain consented English and Khmer audio with reference transcripts and translations.
4. Build a reproducible V1 benchmark before coding a training pipeline.
5. Implement a minimal API and UI, then compose orchestration.
6. Only promote candidate models if held-out evaluations pass defined quality, latency, and safety gates.

**There is no runnable application or Docker Compose configuration in this documentation-only initialization.** Track implementation under [GitHub Issues](../../issues).

## Principles

- **Privacy:** explicitly consented audio, restricted reviewers, retention/deletion controls, no raw audio in logs.
- **Reliability:** idempotent processing jobs and durable PostgreSQL state.
- **Reproducibility:** pinned dependencies, dataset/model versions, recorded configurations and evaluation reports.
- **Quality:** report WER, CER, BLEU/chrF (with human adequacy review), per-language/dialect slices and latency. Khmer tokenization must be documented when using WER.
- **Safety:** never train directly on unapproved corrections or expose sensitive recordings.
- **Transparency:** distinguish implemented features from proposals, and tested from untested behavior.

## Proposed phases

**P0** research and data governance → **P1/V1** English speech-to-Khmer text MVP → **P2** human feedback and controlled adaptation → **P3/V2** Khmer speech-to-English text → **P4** offline hardening, streaming evaluation and optional TTS.

## Contributing

Start with an issue and provide reproducible evidence for proposed changes. Do not upload private recordings, secrets, or copyrighted training data without rights and documented consent. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

A source-code license has **not yet been chosen**. The project is publicly visible, but that does not by itself grant reuse rights. Model weights, datasets, and third-party dependencies may have separate terms.


## Runnable ingestion MVP

A runnable Docker Compose MVP is now included for the video-ingestion/training foundation:

- React dashboard implementing the Upload / YouTube URL / Live Stream design.
- FastAPI ingestion API and PostgreSQL durable job state.
- Apache Kafka 4.4.0 KRaft event bus.
- MinIO object storage for raw video, processed audio and live stream segments.
- FFmpeg + yt-dlp worker for file, YouTube and RTMP/HLS ingestion.
- JupyterHub research environment with the ASR/MT training libraries.
- MLflow experiment tracking plus Redis for research/runtime coordination.
- Smoke-test script and an environment-check notebook.

The implemented ingestion path is:

```text
Source -> FastAPI -> PostgreSQL -> Kafka ingest topic
       -> worker/FFmpeg -> MinIO -> Kafka chunk/job topics
       -> JupyterHub / downstream ASR-MT experiments
```

Quick start:

```bash
cp .env.example .env
# edit the development secrets first
docker compose config
docker compose up -d --build
make smoke
```

Open the UI at `http://localhost:8080`, JupyterHub at `http://localhost:8001`, MLflow at `http://localhost:5000`, and MinIO Console at `http://localhost:9001`.

See [docs/RUNBOOK.md](docs/RUNBOOK.md) for the full operating and security notes.

> **Validation status:** Python source was syntax-checked and the Compose YAML was parsed during generation. Docker itself was not available in the generation environment, so image builds and runtime integration still need to be verified on a Docker host with `docker compose config`, `docker compose up --build`, and `make smoke`. Model training/inference quality is not yet validated.
