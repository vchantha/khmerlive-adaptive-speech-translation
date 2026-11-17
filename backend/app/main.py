from pathlib import Path
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db, init_db
from .events import healthy as kafka_healthy, publish
from .models import IngestJob
from .schemas import StreamIngestRequest, UrlIngestRequest
from .storage import ensure_bucket, healthy as minio_healthy, put_stream

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def job_dict(job: IngestJob) -> dict:
    return {"id":job.id,"source_type":job.source_type,"source":job.source,"source_name":job.source_name,"state":job.state,"kafka_status":job.kafka_status,"minio_status":job.minio_status,"object_name":job.object_name,"metadata":job.media_metadata or {},"chunk_count":job.chunk_count,"error":job.error,"created_at":job.created_at,"updated_at":job.updated_at}

@app.on_event("startup")
def startup() -> None:
    init_db()
    ensure_bucket()

@app.get("/health/live")
def live():
    return {"status":"ok"}

@app.get("/health/ready")
def ready():
    k,m=kafka_healthy(),minio_healthy()
    return {"status":"ok" if k and m else "degraded","kafka":k,"silo":m,"minio":m}

@app.get("/api/v1/jobs")
def list_jobs(limit:int=50,db:Session=Depends(get_db)):
    rows=db.execute(select(IngestJob).order_by(desc(IngestJob.created_at)).limit(max(1,min(limit,200)))).scalars().all()
    return [job_dict(x) for x in rows]

@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id:str,db:Session=Depends(get_db)):
    job=db.get(IngestJob,job_id)
    if not job: raise HTTPException(404,"Job not found")
    return job_dict(job)

@app.get("/api/v1/system/status")
def system_status(db:Session=Depends(get_db)):
    queued=db.scalar(select(func.count()).select_from(IngestJob).where(IngestJob.state.in_(["queued","processing"]))) or 0
    storage = "healthy" if minio_healthy() else "unavailable"
    return {"jobs_queue":queued,"kafka":"running" if kafka_healthy() else "unavailable","silo":storage,"minio":storage,"processing":"healthy"}

@app.post("/api/v1/ingest/upload",status_code=202)
def ingest_upload(file:UploadFile=File(...),db:Session=Depends(get_db)):
    filename=Path(file.filename or "upload.bin").name
    job=IngestJob(source_type="upload",source=filename,source_name=filename)
    db.add(job);db.commit();db.refresh(job)
    object_name=f"raw/{job.id}/{filename}"
    try:
        file.file.seek(0,2); length=file.file.tell(); file.file.seek(0)
        put_stream(object_name,file.file,length,file.content_type or "application/octet-stream")
        job.object_name=object_name; job.minio_status="uploaded"; db.commit()
        publish(settings.kafka_ingest_topic,{"event_type":"ingest.requested","job_id":job.id,"source_type":"upload","object_name":object_name},key=job.id)
        db.refresh(job); return job_dict(job)
    except Exception as exc:
        job.state="failed"; job.error=str(exc)[:2000]; db.commit()
        raise HTTPException(503,f"Ingestion unavailable: {exc}")

@app.post("/api/v1/ingest/url",status_code=202)
def ingest_url(req:UrlIngestRequest,db:Session=Depends(get_db)):
    host=(urlparse(req.url).hostname or "").lower()
    if not (host=="youtu.be" or host=="youtube.com" or host.endswith(".youtube.com")):
        raise HTTPException(400,"Only youtube.com or youtu.be URLs are accepted")
    job=IngestJob(source_type="youtube",source=req.url,source_name=req.source_name or "YouTube")
    db.add(job);db.commit();db.refresh(job)
    publish(settings.kafka_ingest_topic,{"event_type":"ingest.requested","job_id":job.id,"source_type":"youtube","url":req.url},key=job.id)
    return job_dict(job)

@app.post("/api/v1/ingest/stream",status_code=202)
def ingest_stream(req:StreamIngestRequest,db:Session=Depends(get_db)):
    if urlparse(req.url).scheme.lower() not in {"rtmp","rtmps","http","https"}:
        raise HTTPException(400,"Stream URL must use RTMP, RTMPS, HTTP, or HTTPS")
    job=IngestJob(source_type="stream",source=req.url,source_name=req.source_name)
    db.add(job);db.commit();db.refresh(job)
    publish(settings.kafka_ingest_topic,{"event_type":"ingest.requested","job_id":job.id,"source_type":"stream","url":req.url,"source_name":req.source_name},key=job.id)
    return job_dict(job)
