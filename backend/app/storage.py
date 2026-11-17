from io import BytesIO
import time
from minio import Minio
from minio.error import S3Error
from .config import get_settings

settings = get_settings()

def client() -> Minio:
    return Minio(settings.minio_endpoint, access_key=settings.minio_access_key, secret_key=settings.minio_secret_key, secure=settings.minio_secure)

def ensure_bucket(retries: int = 30, delay: float = 1.0) -> None:
    last_error = None
    for _ in range(retries):
        try:
            c = client()
            if not c.bucket_exists(settings.minio_bucket):
                c.make_bucket(settings.minio_bucket)
            return
        except Exception as exc:
            last_error = exc
            time.sleep(delay)
    raise RuntimeError(f"MinIO unavailable after {retries} attempts: {last_error}")

def put_stream(object_name: str, stream, length: int, content_type: str = "application/octet-stream") -> None:
    ensure_bucket()
    client().put_object(settings.minio_bucket, object_name, stream, length, content_type=content_type)

def put_bytes(object_name: str, payload: bytes, content_type: str = "application/octet-stream") -> None:
    put_stream(object_name, BytesIO(payload), len(payload), content_type)

def put_file(object_name: str, file_path: str, content_type: str = "application/octet-stream") -> None:
    ensure_bucket()
    client().fput_object(settings.minio_bucket, object_name, file_path, content_type=content_type)

def get_file(object_name: str, file_path: str) -> None:
    ensure_bucket()
    client().fget_object(settings.minio_bucket, object_name, file_path)

def healthy() -> bool:
    try:
        ensure_bucket(retries=1)
        client().list_objects(settings.minio_bucket, recursive=False)
        return True
    except (S3Error, Exception):
        return False
