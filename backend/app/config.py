from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KhmerLive Ingestion API"
    database_url: str = "postgresql+psycopg://khmerlive:khmerlive@postgres:5432/khmerlive"

    kafka_bootstrap_servers: str = "kafka:19093"
    kafka_security_protocol: str = "SSL"
    kafka_ssl_ca_location: str = "/etc/khmerlive/tls/ca.crt"
    kafka_ingest_topic: str = "khmerlive.ingest.requests"
    kafka_chunk_topic: str = "khmerlive.media.chunks"
    kafka_job_topic: str = "khmerlive.job.events"
    kafka_group_id: str = "khmerlive-ingestion-worker"

    # SILO is S3/MinIO API compatible. Keep MINIO_* aliases for old .env files.
    silo_endpoint: str = Field(
        default="silo:9000",
        validation_alias=AliasChoices("SILO_ENDPOINT", "MINIO_ENDPOINT"),
    )
    silo_access_key: str = Field(
        default="minioadmin",
        validation_alias=AliasChoices("SILO_ACCESS_KEY", "MINIO_ROOT_USER", "MINIO_ACCESS_KEY"),
    )
    silo_secret_key: str = Field(
        default="change-me-silo-long-password",
        validation_alias=AliasChoices("SILO_SECRET_KEY", "MINIO_ROOT_PASSWORD", "MINIO_SECRET_KEY"),
    )
    silo_bucket: str = Field(
        default="khmerlive",
        validation_alias=AliasChoices("SILO_BUCKET", "MINIO_BUCKET"),
    )
    silo_secure: bool = True
    silo_ca_file: str = "/etc/khmerlive/tls/ca.crt"

    max_stream_seconds: int = 3600
    audio_chunk_seconds: int = 30
    stream_segment_seconds: int = 10
    cors_origins: str = "https://localhost:8443,https://127.0.0.1:8443"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
