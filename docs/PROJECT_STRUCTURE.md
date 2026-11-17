# Proposed project structure

```text
.
├── README.md
├── CONTRIBUTING.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   ├── PROJECT_STRUCTURE.md
│   ├── DOCKER_MVP_PLAN.md
│   └── RESEARCH_EVALUATION.md
├── apps/                         # future
│   ├── api/                      # FastAPI app, routers, auth
│   └── web/                      # React + TypeScript
├── services/                     # future
│   ├── audio/                    # FFmpeg, VAD and segmenter
│   ├── asr/                      # versioned adapter interface
│   └── mt/                       # translation and glossary adapter
├── workers/                      # future Celery processing jobs
├── training/                     # future dataset, trainers, evaluation
├── infra/                        # future Compose, Dockerfiles, configs
├── migrations/                   # future PostgreSQL migrations
├── tests/                        # future unit/integration/offline E2E
├── scripts/                      # future seed, benchmark, backup
└── .github/workflows/            # future lint/test/security CI
```

Only the documents are committed during initialization. All folders marked **future** are architectural proposals.

## Module contracts
- Keep ASR, MT, audio and storage dependencies behind adapter interfaces.
- Return version identifiers with every inference result for reproducibility.
- Log structured request IDs and durations, not sensitive transcript contents.
- Favor deterministic fixtures and migration-based DB schema over in-memory state.
- Do not check in private audio, credentials, weights or licensed datasets.
