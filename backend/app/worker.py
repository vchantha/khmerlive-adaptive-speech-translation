import json
import mimetypes
import subprocess
import tempfile
import time
from pathlib import Path

from confluent_kafka import Consumer

from .config import get_settings
from .db import SessionLocal, init_db
from .events import publish
from .models import IngestJob
from .storage import ensure_bucket, get_file, put_file

settings = get_settings()

def update_job(job_id: str, **changes):
    with SessionLocal() as db:
        job = db.get(IngestJob, job_id)
        if not job:
            return
        for k, v in changes.items():
            setattr(job, k, v)
        db.commit()

def emit_job(job_id: str, state: str, **extra):
    publish(settings.kafka_job_topic, {"event_type":"job.state","job_id":job_id,"state":state,**extra}, key=job_id)

def run(cmd: list[str], timeout: int | None = None):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, timeout=timeout)

def probe(path: Path) -> dict:
    p = run(["ffprobe","-v","error","-show_entries","format=duration,format_name:stream=codec_type,codec_name,width,height,sample_rate,channels","-of","json",str(path)], timeout=60)
    return json.loads(p.stdout)

def publish_chunk(job_id: str, sequence: int, object_name: str, kind: str, content_type: str):
    publish(settings.kafka_chunk_topic, {"event_type":"media.chunk.ready","job_id":job_id,"sequence":sequence,"kind":kind,"bucket":settings.minio_bucket,"object_name":object_name,"content_type":content_type}, key=job_id)

def chunk_audio(job_id: str, source: Path, workdir: Path) -> int:
    out_dir = workdir / "audio"; out_dir.mkdir(exist_ok=True)
    pattern = out_dir / "chunk-%05d.wav"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(source),"-map","0:a:0?","-vn","-ac","1","-ar","16000","-c:a","pcm_s16le","-f","segment","-segment_time",str(settings.audio_chunk_seconds),"-reset_timestamps","1",str(pattern)])
    chunks = sorted(out_dir.glob("chunk-*.wav"))
    for idx,path in enumerate(chunks):
        obj=f"processed/{job_id}/audio/{path.name}"
        put_file(obj,str(path),"audio/wav")
        publish_chunk(job_id,idx,obj,"audio","audio/wav")
    return len(chunks)

def process_object(job: IngestJob, local: Path):
    metadata=probe(local)
    count=chunk_audio(job.id,local,local.parent)
    update_job(job.id,media_metadata=metadata,chunk_count=count,state="success",kafka_status="success",minio_status="success",error=None)
    emit_job(job.id,"success",chunk_count=count)

def handle_upload(job: IngestJob,event: dict):
    with tempfile.TemporaryDirectory(prefix=f"khmerlive-{job.id}-") as td:
        local=Path(td)/Path(event["object_name"]).name
        get_file(event["object_name"],str(local))
        process_object(job,local)

def handle_youtube(job: IngestJob,event: dict):
    with tempfile.TemporaryDirectory(prefix=f"khmerlive-{job.id}-") as td:
        target=str(Path(td)/"source.%(ext)s")
        run(["yt-dlp","--no-playlist","--no-progress","--restrict-filenames","-f","bv*+ba/b","--merge-output-format","mp4","-o",target,event["url"]],timeout=900)
        candidates=[p for p in Path(td).iterdir() if p.is_file() and not p.name.endswith(".part")]
        if not candidates: raise RuntimeError("yt-dlp produced no media file")
        local=max(candidates,key=lambda p:p.stat().st_size)
        obj=f"raw/{job.id}/{local.name}"
        put_file(obj,str(local),mimetypes.guess_type(local.name)[0] or "video/mp4")
        update_job(job.id,object_name=obj,minio_status="uploaded")
        process_object(job,local)

def upload_stream_segment(job_id: str, seq: int, seg: Path, workdir: Path):
    video_obj=f"streams/{job_id}/video/{seg.name}"
    put_file(video_obj,str(seg),"video/mp2t")
    publish_chunk(job_id,seq,video_obj,"video","video/mp2t")
    audio=workdir/f"{seg.stem}.wav"
    try:
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(seg),"-vn","-ac","1","-ar","16000","-c:a","pcm_s16le",str(audio)],timeout=60)
        if audio.exists() and audio.stat().st_size>44:
            audio_obj=f"streams/{job_id}/audio/{audio.name}"
            put_file(audio_obj,str(audio),"audio/wav")
            publish_chunk(job_id,seq,audio_obj,"audio","audio/wav")
    finally:
        audio.unlink(missing_ok=True)

def handle_stream(job: IngestJob,event: dict):
    with tempfile.TemporaryDirectory(prefix=f"khmerlive-stream-{job.id}-") as td:
        workdir=Path(td); pattern=workdir/"segment-%06d.ts"
        cmd=["ffmpeg","-hide_banner","-loglevel","warning","-y","-i",event["url"],"-t",str(settings.max_stream_seconds),"-map","0:v:0?","-map","0:a:0?","-c","copy","-f","segment","-segment_time",str(settings.stream_segment_seconds),"-reset_timestamps","1",str(pattern)]
        proc=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        seen=set(); seq=0
        update_job(job.id,state="streaming",kafka_status="streaming"); emit_job(job.id,"streaming")
        while proc.poll() is None:
            segments=sorted(workdir.glob("segment-*.ts"))
            for seg in segments[:-1]:
                if seg not in seen:
                    upload_stream_segment(job.id,seq,seg,workdir); seen.add(seg); seq+=1
                    update_job(job.id,chunk_count=seq,minio_status="uploaded")
            time.sleep(1)
        stderr=proc.stderr.read() if proc.stderr else ""
        for seg in sorted(workdir.glob("segment-*.ts")):
            if seg not in seen and seg.stat().st_size:
                upload_stream_segment(job.id,seq,seg,workdir); seen.add(seg); seq+=1
        if proc.returncode!=0 and seq==0: raise RuntimeError(f"ffmpeg stream failed: {stderr[-1500:]}")
        update_job(job.id,chunk_count=seq,state="success",kafka_status="success",minio_status="success")
        emit_job(job.id,"success",chunk_count=seq)

def handle(event: dict):
    job_id=event.get("job_id")
    if not job_id: return
    with SessionLocal() as db:
        job=db.get(IngestJob,job_id)
        if not job: return
        update_job(job.id,state="processing",kafka_status="processing"); emit_job(job.id,"processing")
        try:
            if job.source_type=="upload": handle_upload(job,event)
            elif job.source_type=="youtube": handle_youtube(job,event)
            elif job.source_type=="stream": handle_stream(job,event)
            else: raise ValueError(f"Unsupported source type: {job.source_type}")
        except Exception as exc:
            update_job(job.id,state="failed",kafka_status="failed",error=str(exc)[:2000])
            emit_job(job.id,"failed",error=str(exc)[:500])

def main():
    init_db(); ensure_bucket()
    consumer=Consumer({"bootstrap.servers":settings.kafka_bootstrap_servers,"group.id":settings.kafka_group_id,"auto.offset.reset":"earliest","enable.auto.commit":False})
    consumer.subscribe([settings.kafka_ingest_topic])
    try:
        while True:
            msg=consumer.poll(1.0)
            if msg is None: continue
            if msg.error():
                print(f"Kafka error: {msg.error()}",flush=True); continue
            try:
                handle(json.loads(msg.value().decode("utf-8")))
                consumer.commit(msg,asynchronous=False)
            except Exception as exc:
                print(f"Worker message failed: {exc}",flush=True); time.sleep(2)
    finally:
        consumer.close()

if __name__=="__main__":
    main()
