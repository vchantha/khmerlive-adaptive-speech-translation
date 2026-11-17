# KhmerLive training workspace

JupyterHub: http://localhost:8001

The image includes PyTorch/Torchaudio, Transformers, Datasets, Accelerate, PEFT, Evaluate, Faster-Whisper, SentencePiece, JiWER, SacreBLEU, Librosa, MLflow, Optuna, Kafka, SILO/S3, PostgreSQL, Pandas/Polars, and plotting libraries.

Internal services:
- Kafka: kafka:19092
- SILO: silo:9000
- PostgreSQL: postgres:5432
- MLflow: http://mlflow:5000

Consume `khmerlive.media.chunks` to discover media objects. Build a reviewed, consent-approved, versioned dataset before training.

Optional heavyweight build args: `INSTALL_NEMO=1` and `INSTALL_BITSANDBYTES=1`. GPU/CUDA compatibility must be validated separately.
