"""Reproducible presentation gates. Synthetic metrics never establish OCR accuracy."""
from __future__ import annotations
import argparse,json,math,os,sys,time,threading,subprocess,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import cv2
import numpy as np
import psutil
from app.services.video_presentation import PresentationFilter,iou,draw_box

def geometry(boxes):
    b=np.asarray(boxes,dtype=float)
    return np.column_stack(((b[:,0]+b[:,2])/2,(b[:,1]+b[:,3])/2,b[:,2]-b[:,0],b[:,3]-b[:,1]))
def residual_jitter(presented,reference):
    p,r=geometry(presented),geometry(reference)
    if len(p)<2:return (0.,0.)
    diag=np.hypot(r[:,2],r[:,3])
    center=(p[:,:2]-r[:,:2])/diag[:,None]
    size=(p[:,2:]-r[:,2:])/r[:,2:]
    return tuple(float(np.sqrt(np.mean(np.sum(np.diff(channel,axis=0)**2,axis=1)))) for channel in (center,size))
def channel_pass(baseline,candidate):return candidate<=1e-6 if baseline<=1e-6 else candidate<=.8*baseline+1e-12
def temporal_lag(presented,reference):
    p,r=geometry(presented),geometry(reference)
    if len(p)<7 or np.allclose(r[1:],r[:-1],atol=1e-12):return None
    support=np.arange(3,len(p)-3)
    errors=[]
    for k in range(-3,4):
        target=r[support+k];delta=(p[support]-target)/np.column_stack((np.hypot(target[:,2],target[:,3]),)*2+(target[:,2],target[:,3]))
        errors.append((float(np.mean(delta**2)),abs(k),k))
    minimum=min(x[0] for x in errors)
    return min((x for x in errors if abs(x[0]-minimum)<=1e-12),key=lambda x:(x[1],x[2]))[2]
def quality(clip,folder):
    data=json.loads((folder/clip["observations"]).read_text(encoding="utf-8"))
    capture=cv2.VideoCapture(os.path.relpath(folder/clip["file"]));display=PresentationFilter()
    tracks={};overlaps=[];invalid=0;frames=0
    try:
        for index,(raw,reference) in enumerate(zip(data["raw"],data["reference"],strict=True)):
            ok,image=capture.read()
            if not ok:raise RuntimeError("fixture_frame_missing")
            boxes=display.present(image,index,raw);refs={x["track_id"]:x for x in reference}
            if set(boxes)-{x["track_id"] for x in raw}:raise RuntimeError("unbacked_box")
            for item in raw:
                tid=item["track_id"];b=boxes.get(tid)
                if b is None:invalid+=1;overlaps.append(0);continue
                visible=(max(0,item["bbox"][0]),max(0,item["bbox"][1]),min(clip["width"],item["bbox"][2]),min(clip["height"],item["bbox"][3]))
                overlaps.append(iou(b,visible))
                tracks.setdefault(tid,[]).append((index,item["bbox"],b,refs[tid]["bbox"]))
            frames+=1
    finally:capture.release()
    centers=[];sizes=[];lags=[];segments=[]
    for tid,rows in tracks.items():
        chunks=[];chunk=[]
        for row in rows:
            if chunk and row[0]!=chunk[-1][0]+1:chunks.append(chunk);chunk=[]
            chunk.append(row)
        if chunk:chunks.append(chunk)
        for part in chunks:
            raw=np.array([x[1] for x in part]);shown=np.array([x[2] for x in part]);ref=np.array([x[3] for x in part])
            a=residual_jitter(raw,ref);b=residual_jitter(shown,ref);lag=temporal_lag(shown,ref)
            if lag is not None:lags.append(lag)
            if clip.get("segment") and len(part)>=120:
                segments.append({"track_id":tid,"frames":len(part),"baseline_center":a[0],"candidate_center":b[0],"baseline_size":a[1],"candidate_size":b[1],"center_pass":channel_pass(a[0],b[0]),"size_pass":channel_pass(a[1],b[1]),"lag_frames":lag})
    rate=sum(x>=.9 for x in overlaps)/len(overlaps) if overlaps else None
    return {"frames":frames,"invalid_boxes":invalid,"iou_fraction":rate,"max_abs_lag":max(map(abs,lags)) if lags else None,"segments":segments,"fallback_count":display.fallback,"pass":frames==clip["frames"] and invalid==0 and (rate is None or rate>=.95) and all(abs(x)<=1 for x in lags) and all(x["center_pass"] and x["size_pass"] for x in segments)}

class RSSMonitor:
    def __init__(self):
        self.peak=0;self.parent_peak=0;self.encoder_peak=0;self.stop=threading.Event()
        self.thread=threading.Thread(target=self.run,daemon=True)
    def run(self):
        process=psutil.Process()
        while not self.stop.is_set():
            try:
                parent=process.memory_info().rss;child=sum(x.memory_info().rss for x in process.children(recursive=True) if x.is_running())
                self.parent_peak=max(self.parent_peak,parent);self.encoder_peak=max(self.encoder_peak,child);self.peak=max(self.peak,parent+child)
            except psutil.Error:pass
            self.stop.wait(.05)
    def __enter__(self):self.thread.start();return self
    def __exit__(self,*args):self.stop.set();self.thread.join()

def legacy_draw(frame,item):
    a=item["bbox"]
    cv2.rectangle(frame,tuple(a[:2]),tuple(a[2:]),(0,200,0),2)
    cv2.putText(frame,f'{item["class_name"]} #{item["track_id"]} {item["confidence"]:.2f}',(a[0],max(20,a[1]-6)),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,200,0),2,cv2.LINE_AA)
def render_measure(clip,folder,candidate):
    data=json.loads((folder/clip["observations"]).read_text(encoding="utf-8"))["raw"]
    with tempfile.TemporaryDirectory(prefix="presentation008-") as temporary:
        raw=Path(temporary)/"raw.mp4";output=Path(temporary)/"output.mp4"
        capture=cv2.VideoCapture(os.path.relpath(folder/clip["file"]))
        writer=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*"mp4v"),clip["fps"],(clip["width"],clip["height"]))
        display=PresentationFilter();index=0
        started=time.perf_counter()
        with RSSMonitor() as rss:
            try:
                while True:
                    ok,frame=capture.read()
                    if not ok:break
                    observations=data[index]
                    if candidate:
                        boxes=display.present(frame,index,observations)
                        for item in observations:
                            if item["track_id"] in boxes:draw_box(frame,boxes[item["track_id"]],item["class_name"])
                    else:
                        for item in observations:legacy_draw(frame,item)
                    writer.write(frame);index+=1
            finally:capture.release();writer.release()
            subprocess.run(["ffmpeg","-nostdin","-y","-i",str(raw),"-c:v","libx264","-movflags","+faststart",str(output)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=60)
            elapsed=time.perf_counter()-started
        return {"seconds":elapsed,"peak_rss":rss.peak,"parent_peak_rss":rss.parent_peak,"encoder_peak_rss":rss.encoder_peak,"frames":index,"width":clip["width"],"height":clip["height"],"fps":clip["fps"]}


def aggregate_paired_cost(pairs,clip):
    """All three pairs and both arms must succeed; no dropped outliers or failed runs."""
    if len(pairs)!=3:return {"pass":False,"reason":"incomplete_pairs"}
    for pair in pairs:
        for arm in ("baseline","candidate"):
            run=pair.get(arm,{})
            if "error" in run or not isinstance(run.get("seconds"),(int,float)) or not np.isfinite(run["seconds"]) or run["seconds"]<=0 or not isinstance(run.get("peak_rss"),(int,float)) or run["peak_rss"]<=0:return {"pass":False,"reason":"invalid_run"}
    baseline=float(np.median([p["baseline"]["seconds"] for p in pairs]))
    candidate=float(np.median([p["candidate"]["seconds"] for p in pairs]))
    memory=max(p["candidate"]["peak_rss"] for p in pairs)/max(p["baseline"]["peak_rss"] for p in pairs)
    geometry=True;parity=True
    for pair in pairs:
        for arm in ("baseline","candidate"):
            g=pair[arm].get("geometry",pair[arm])
            geometry=geometry and all(g.get(k)==clip[k] for k in ("frames","width","height")) and abs(g.get("fps",0)-clip["fps"])<1e-6
        if "raw_sha256" in pair["baseline"] or "raw_sha256" in pair["candidate"]:parity=parity and pair["baseline"].get("raw_sha256")==pair["candidate"].get("raw_sha256")
    return {"time_ratio":candidate/baseline,"memory_ratio":memory,"geometry_pass":geometry,"raw_parity":parity,"pass":candidate<=baseline*1.1 and memory<=1.1 and geometry and parity}

def full_model_measure(clip,folder,candidate,detector,settings):
    import shutil,logging
    from app.domain.models import VideoMetadata
    from app.services.video_job_store import VideoJobStore
    from app.services.video_artifacts import VideoArtifactStore
    from app.services.video_processing import VideoProcessor
    import importlib.util
    spec=importlib.util.spec_from_file_location("frozen_renderer_008",ROOT/"tests/fixtures/video_presentation/legacy_renderer.py")
    legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    logger=logging.getLogger("benchmark008");logger.handlers=[logging.NullHandler()];logger.propagate=False
    with tempfile.TemporaryDirectory(prefix="full008-") as temporary:
        root=Path(temporary);artifacts=VideoArtifactStore(root/"media");store=VideoJobStore(root/"jobs.sqlite",3600,2)
        staged=artifacts.staged_input_path();shutil.copyfile(folder/clip["file"],staged)
        metadata=VideoMetadata("video/mp4","mp4","mpeg4",staged.stat().st_size,clip["frames"]/clip["fps"],clip["width"],clip["height"],clip["fps"],clip["frames"])
        job=store.create("benchmark",metadata,staged);job=store.dequeue()
        processor=(VideoProcessor if candidate else legacy.VideoProcessor)(detector,store,artifacts,settings.ffmpeg_executable,settings.video_job_timeout_seconds,logger)
        started=time.perf_counter()
        try:
            with RSSMonitor() as rss:processor.process(job)
            elapsed=time.perf_counter()-started;finished=store.get(job.job_id,"benchmark")
            if finished.status.value!="completed" or not finished.output_path:raise RuntimeError("benchmark_not_completed")
            capture=cv2.VideoCapture(str(finished.output_path))
            measured={"frames":int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),"fps":capture.get(cv2.CAP_PROP_FPS),"width":int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),"height":int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))}
            capture.release()
            # Fingerprint raw rows only; IDs, timestamps and paths are excluded.
            rows=store._connection.execute("SELECT frame_index,track_id,class_id,class_name,confidence,x_min,y_min,x_max,y_max FROM video_detections WHERE job_id=? ORDER BY frame_index,track_id,class_id",(job.job_id,)).fetchall()
            digest=hashlib.sha256(json.dumps([tuple(r) for r in rows],separators=(",",":")).encode()).hexdigest()
            return {"seconds":elapsed,"peak_rss":rss.peak,"parent_peak_rss":rss.parent_peak,"encoder_peak_rss":rss.encoder_peak,"raw_sha256":digest,"geometry":measured}
        finally:store.release(job.job_id);store._connection.close();artifacts.close()

def real_model_benchmark(manifest,folder):
    import contextlib,io,platform
    from app.core.config import Settings
    from app.adapters.yolov10_detector import YOLOv10Detector
    settings=Settings();result={"kind":"complete-real-detector-and-tracker","device":settings.inference_device,"platform":platform.system(),"clips":[],"pass":False}
    try:
        weights=settings.model_weights_path
        result["weights_sha256"]=hashlib.sha256(weights.read_bytes()).hexdigest()
        result["confidence_threshold"]=settings.model_confidence_threshold
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            detector=YOLOv10Detector(weights,settings.model_confidence_threshold,settings.inference_device,settings.ultralytics_path)
            detector.detect(np.zeros((360,640,3),np.uint8))
        for clip in manifest["clips"]:
            pairs=[]
            for repeat in range(3):
                pair={}
                for arm in (["baseline","candidate"] if repeat%2==0 else ["candidate","baseline"]):
                    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                        detector.detect(np.zeros((360,640,3),np.uint8))
                        pair[arm]=full_model_measure(clip,folder,arm=="candidate",detector,settings)
                pairs.append(pair)
                print(json.dumps({"clip":clip["id"],"pair":repeat+1,"benchmark":"complete"}),flush=True)
            result["clips"].append({"clip":clip["id"],"pairs":pairs,**aggregate_paired_cost(pairs,clip)})
        result["pass"]=len(result["clips"])==len(manifest["clips"]) and all(c["pass"] for c in result["clips"])
    except Exception as error:
        result["failure_type"]=type(error).__name__
        result["incomplete"]=True
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,required=True);parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--benchmark",action="store_true")
    parser.add_argument("--real-model-benchmark",action="store_true")
    args=parser.parse_args();manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    result={"protocol":"008-v1","profile":"gated-ema-v1","kind":"synthetic-presentation","real_model_benchmark":False,"full_model_gate":"pending","manifest_sha256":hashlib.sha256(args.manifest.read_bytes()).hexdigest(),"clips":[]}
    for clip in manifest["clips"]:
        item={"clip":clip["id"],"quality":quality(clip,args.manifest.parent)}
        if args.benchmark:
            pairs=[]
            for repeat in range(3):
                pair={}
                for arm in (["baseline","candidate"] if repeat%2==0 else ["candidate","baseline"]):pair[arm]=render_measure(clip,args.manifest.parent,arm=="candidate")
                pairs.append(pair)
            baseline_time=float(np.median([p["baseline"]["seconds"] for p in pairs]));candidate_time=float(np.median([p["candidate"]["seconds"] for p in pairs]))
            baseline_rss=max(p["baseline"]["peak_rss"] for p in pairs);candidate_rss=max(p["candidate"]["peak_rss"] for p in pairs)
            item["pairs"]=pairs;item["time_ratio"]=candidate_time/baseline_time;item["rss_ratio"]=candidate_rss/baseline_rss
            item["presentation_cost_pass"]=item["time_ratio"]<=1.1 and item["rss_ratio"]<=1.1
        result["clips"].append(item)
    if args.real_model_benchmark:
        result["complete_benchmark"]=real_model_benchmark(manifest,args.manifest.parent)
        result["real_model_benchmark"]=True
        result["processing_cost_gate"]="pass" if result["complete_benchmark"]["pass"] else "failed_or_incomplete"
        result["full_model_gate"]="pending_auxiliary_measurements"
    result["quality_pass"]=all(c["quality"]["pass"] for c in result["clips"])
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"quality_pass":result["quality_pass"],"clips":len(result["clips"]),"full_model_gate":result["full_model_gate"]}))
if __name__=="__main__":main()
