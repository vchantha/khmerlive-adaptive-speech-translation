from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "KhmerLive Ingestion API"
    database_url: str = "postgresql+psycopg://khmerlive:khmerlive@postgres:5432/khmerlive"
    kafka_bootstrap_servers: str = "kafka:19092"
    kafka_ingest_topic: str = "khmerlive.ingest.requests"
    kafka_chunk_topic: str = "khmerlive.media.chunks"
    kafka_job_topic: str = "khmerlive.job.events"
    kafka_group_id: str = "khmerlive-ingestion-worker"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_secure: bool = False
    minio_bucket: str = "khmerlive"
    max_stream_seconds: int = 3600
    audio_chunk_seconds: int = 30
    stream_segment_seconds: int = 10
    cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
