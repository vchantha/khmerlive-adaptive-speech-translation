import { useEffect, useMemo, useRef, useState } from "react";
import {Activity,Bell,Boxes,CloudUpload,Database,FileVideo2,Film,Gauge,Link2,ListVideo,Radio,RefreshCw,Settings,Upload,UserCircle2,Youtube} from "lucide-react";

const api={
  async json(path,options={}){const r=await fetch(path,options);const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.detail||`Request failed (${r.status})`);return data;},
  jobs:()=>api.json("/api/v1/jobs?limit=30"),
  status:()=>api.json("/api/v1/system/status"),
  upload:(file)=>{const body=new FormData();body.append("file",file);return api.json("/api/v1/ingest/upload",{method:"POST",body});},
  youtube:(url)=>api.json("/api/v1/ingest/url",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url})}),
  stream:(url,source_name)=>api.json("/api/v1/ingest/stream",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,source_name})})
};
const badgeClass=(value="")=>{const v=value.toLowerCase();if(["success","healthy","running","uploaded"].includes(v))return"badge good";if(["failed","unavailable"].includes(v))return"badge bad";if(["streaming","processing"].includes(v))return"badge live";return"badge warn";};

function App(){
 const[tab,setTab]=useState("upload"),[jobs,setJobs]=useState([]),[system,setSystem]=useState({jobs_queue:0,kafka:"checking",silo:"checking",processing:"checking"});
 const[selected,setSelected]=useState(null),[preview,setPreview]=useState(""),[youtubeUrl,setYoutubeUrl]=useState(""),[streamUrl,setStreamUrl]=useState(""),[streamName,setStreamName]=useState("KhmerLive Live"),[busy,setBusy]=useState(false),[message,setMessage]=useState("");
 const fileRef=useRef();
 const refresh=async()=>{try{const[j,s]=await Promise.all([api.jobs(),api.status()]);setJobs(j);setSystem(s);}catch(e){setMessage(e.message);}};
 useEffect(()=>{refresh();const id=setInterval(refresh,3000);return()=>clearInterval(id);},[]);
 useEffect(()=>()=>{if(preview)URL.revokeObjectURL(preview);},[preview]);
 const newest=useMemo(()=>jobs[0],[jobs]);
 const chooseFile=file=>{if(!file)return;if(preview)URL.revokeObjectURL(preview);setSelected(file);setPreview(URL.createObjectURL(file));setTab("upload");};
 const submit=async action=>{setBusy(true);setMessage("");try{await action();setMessage("Ingestion job accepted.");await refresh();}catch(e){setMessage(e.message);}finally{setBusy(false);}};

 return <div className="shell">
  <aside><div className="brand"><div className="brandMark"><Film size={22}/></div><strong>KhmerLive</strong></div>
   <nav><div className="nav active"><FileVideo2/>Video Ingestion</div><div className="nav"><ListVideo/>Ingest Jobs</div><div className="nav"><Boxes/>Pipeline & Systems</div><div className="nav"><Gauge/>Monitoring</div><div className="nav"><Settings/>Settings</div></nav>
   <div className="asideFooter">Adaptive Speech Translation<br/><span>Research MVP</span></div>
  </aside>
  <main>
   <header><div><h1>KhmerLive Video Ingestion</h1><p>Upload, capture, and route video to Kafka and SILO</p></div><div className="headerActions"><button className="iconBtn"><Bell/></button><div className="user"><UserCircle2/>admin</div></div></header>
   {message&&<div className="notice">{message}</div>}
   <section className="dashboardGrid">
    <div className="card ingestCard">
     <div className="cardTitle"><CloudUpload/><div><h2>Source Ingestion</h2><p>Ingest video from a file, a YouTube URL, or a live stream.</p></div></div>
     <div className="tabs"><button className={tab==="upload"?"on":""} onClick={()=>setTab("upload")}><Upload/>Upload File</button><button className={tab==="youtube"?"on":""} onClick={()=>setTab("youtube")}><Youtube/>URL (YouTube)</button><button className={tab==="stream"?"on":""} onClick={()=>setTab("stream")}><Radio/>Live Stream</button></div>
     {tab==="upload"&&<div className="uploadPane"><div><div className="dropzone" onClick={()=>fileRef.current?.click()} onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();chooseFile(e.dataTransfer.files?.[0]);}}><CloudUpload size={52}/><strong>{selected?selected.name:"Drop video here or browse files"}</strong><span>MP4, MOV, AVI, MKV, WebM or audio files</span><input ref={fileRef} type="file" hidden accept="video/*,audio/*" onChange={e=>chooseFile(e.target.files?.[0])}/></div><button className="primary wide" disabled={!selected||busy} onClick={()=>submit(()=>api.upload(selected))}><Upload/>Upload Video</button></div>
      <div className="previewCard"><div className="preview">{preview?<video src={preview} controls/>:<Film size={58}/>}</div><div className="meta"><strong>Video Metadata</strong><span>Filename <b>{selected?.name||"—"}</b></span><span>Size <b>{selected?`${(selected.size/1024/1024).toFixed(2)} MB`:"—"}</b></span><span>Source Type <b>File Upload</b></span><span>Ingestion Status <i className="dot"/> <b>{newest?.state||"Ready"}</b></span></div></div></div>}
     {tab==="youtube"&&<div className="formPane"><div className="sourceIcon youtube"><Youtube/></div><div className="grow"><label>Video URL</label><div className="input"><Link2/><input value={youtubeUrl} onChange={e=>setYoutubeUrl(e.target.value)} placeholder="https://www.youtube.com/watch?v=..."/></div></div><button className="primary" disabled={!youtubeUrl||busy} onClick={()=>submit(()=>api.youtube(youtubeUrl))}>Fetch & Ingest</button></div>}
     {tab==="stream"&&<div className="formPane"><div className="sourceIcon stream"><Radio/></div><div className="grow"><label>RTMP / HLS Stream URL</label><div className="input"><Link2/><input value={streamUrl} onChange={e=>setStreamUrl(e.target.value)} placeholder="rtmp://... or https://...m3u8"/></div></div><div className="streamName"><label>Source Name</label><input value={streamName} onChange={e=>setStreamName(e.target.value)}/></div><button className="primary" disabled={!streamUrl||busy} onClick={()=>submit(()=>api.stream(streamUrl,streamName))}>Start Streaming</button></div>}
    </div>
    <div className="sideStack">
     <div className="card"><div className="cardTitle"><Boxes/><div><h2>Processing Pipeline</h2><p>Video ingestion and delivery flow to Kafka and SILO.</p></div></div><div className="pipeline"><div className="node"><FileVideo2/><b>Video Source</b><small>Upload / URL / Live</small></div><span>→</span><div className="node"><Settings/><b>Preprocess</b><small>FFmpeg chunks</small></div><span>→</span><div className="node kafka"><Boxes/><b>Kafka</b><small>Event messages</small></div><span>→</span><div className="node silo"><Database/><b>SILO</b><small>Object storage</small></div></div></div>
     <div className="card"><div className="cardTitle"><Activity/><div><h2>System Status</h2><p>Live status of the ingestion pipeline.</p></div></div><div className="statusGrid"><Status title="Jobs Queue" value={system.jobs_queue} icon={<ListVideo/>}/><Status title="Kafka Producer" value={system.kafka} icon={<Boxes/>}/><Status title="SILO Upload" value={system.silo} icon={<Database/>}/><Status title="Processing Health" value={system.processing} icon={<Activity/>}/></div></div>
    </div>
   </section>
   <section className="card jobs"><div className="jobsHeader"><div className="cardTitle"><ListVideo/><div><h2>Recent Ingest Jobs</h2><p>Kafka and SILO delivery status for recent sources.</p></div></div><button className="secondary" onClick={refresh}><RefreshCw/>Refresh</button></div>
    <div className="tableWrap"><table><thead><tr><th>Job ID</th><th>Source</th><th>Type</th><th>State</th><th>Kafka Status</th><th>SILO Status</th><th>Chunks</th><th>Created At</th></tr></thead><tbody>{jobs.map(j=><tr key={j.id}><td className="mono">{j.id.slice(0,8)}</td><td className="sourceCell">{j.source_name||j.source}</td><td>{j.source_type}</td><td><span className={badgeClass(j.state)}>{j.state}</span></td><td><span className={badgeClass(j.kafka_status)}>{j.kafka_status}</span></td><td><span className={badgeClass((j.silo_status||j.minio_status))}>{(j.silo_status||j.minio_status)}</span></td><td>{j.chunk_count}</td><td>{new Date(j.created_at).toLocaleString()}</td></tr>)}{!jobs.length&&<tr><td colSpan="8" className="empty">No ingest jobs yet.</td></tr>}</tbody></table></div>
   </section>
  </main>
 </div>;
}
function Status({title,value,icon}){const ok=["healthy","running"].includes(String(value).toLowerCase());return <div className="statusTile"><div className="statusIcon">{icon}</div><div><span>{title}</span><strong className={ok?"green":""}>{String(value)}</strong></div></div>;}
export default App;
