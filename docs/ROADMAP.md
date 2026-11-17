# Delivery roadmap

These are **proposed** milestones and acceptance criteria, not achieved functionality.

## P0 — Discovery / dataset and baseline
- Capture operating requirements (offline, batch vs streaming, languages, devices, CPU/GPU budget).
- Create data consent, license, retention and annotation policies.
- Assemble small, speaker-disjoint, domain-balanced held-out test sets.
- Benchmark candidate English ASR and English→Khmer MT, including Khmer native-speaker review.
- **Exit:** reproducible evaluation scripts, licensed candidate shortlist, baseline error/latency report.

## V1 / P1 — English speech → Khmer text MVP
- Audio upload, normalization, English ASR adapter, English→Khmer MT adapter.
- Persistent job queue/states, transcript+translation results, React review UI.
- Docker Compose development stack, deterministic migrations/seeds, smoke tests.
- **Exit:** automated end-to-end test from sample English WAV to displayed Khmer text, restart persistence test, documented measured quality and known limitations.

## P2 — Human feedback and adaptive learning
- Separate transcript and translation corrections with review approvals and audit.
- Consent-aware, deduplicated dataset snapshots and leakage-safe splits.
- Fine-tuning experiments, held-out comparisons, registry and manual deployment gate.
- **Exit:** reproducible model comparison demonstrating measured improvement or an explicit no-promotion decision; rollback demonstrated.

## V2 / P3 — Khmer speech → English text
- Khmer ASR evaluation and adaptation, Khmer→English MT adapter.
- Mixed language, regional accent and noise stress tests; Khmer normalization policy.
- **Exit:** verified Khmer-audio→English-text E2E tests and representative human review; backwards compatibility with V1.

## P4 — Hardening / research extensions
- Air-gapped installation and backup/restore drill.
- RBAC, privacy reviews, monitoring, resource and concurrency load tests.
- Evaluate streaming and speaker diarization; optional speech-to-speech via TTS only after text quality is accepted.
- **Exit:** disconnected reproducibility check, security checklist, operational runbook and evidence-backed SLO.

## Prioritization
No training-data ingestion before consent design; no production model promotion before fixed held-out and human-reviewed evaluations; no online-only dependencies in the offline release.
