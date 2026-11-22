"""Synthetic, public validation material for iteration008. No private media."""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/"frontend/e2e/fixtures/video-presentation"
def generate():
    DEST.mkdir(parents=True,exist_ok=True)
    images=[]
    for i in range(10):
        w,h=[(960,540),(4032,1908),(640,960)][i%3]
        canvas=np.full((h,w,3),(224,229,235),np.uint8)
        boxes=[]
        for j in range(24 if i<3 else 5):
            x=int((j%6+.2)*w/6); y=int((j//6+.4)*h/5)
            box=[x,y,min(w,x+int(w/9)),min(h,y+int(h/9))]
            cv2.rectangle(canvas,tuple(box[:2]),tuple(box[2:]),(70,100,140),-1)
            boxes.append({"id":j+1,"bbox":box})
        path=DEST/f"scene-{i:02}.png";cv2.imencode(".png",canvas)[1].tofile(path)
        images.append({"file":path.name,"width":w,"height":h,"dense":i<3,"boxes":boxes,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    clips=[]
    for index,name in enumerate(["dense-flow","dense-crossing","occlusion","cut","fast","empty"]):
        path=DEST/(name+".mp4")
        writer=cv2.VideoWriter(str(path.relative_to(Path.cwd())),cv2.VideoWriter_fourcc(*"mp4v"),30,(640,360))
        if not writer.isOpened():raise RuntimeError("fixture_encoder_unavailable")
        observations=[];references=[]
        for frame_index in range(150):
            image=np.full((360,640,3),35 if name!="cut" or frame_index<75 else 220,np.uint8)
            raw=[];ref=[]
            for actor in range(0 if name=="empty" else (21 if index<2 else 3)):
                if name=="occlusion" and actor==1 and 60<=frame_index<80:continue
                speed=1.4 if name=="fast" else .2
                x=8+(actor%6)*94+int(frame_index*speed)%30;y=12+(actor//6)*82
                bw,bh=76,44
                jitter=2 if (frame_index+actor)%2 else -2
                size=2 if (frame_index+actor)%3==0 else -1
                reference=[x,y,x+bw,y+bh]
                bbox=[x+jitter,y+jitter,x+bw+jitter+size,y+bh+jitter+size]
                item={"frame_index":frame_index,"track_id":actor+1,"class_id":actor%3,"class_name":["car","truck","bus"][actor%3],"confidence":.9,"bbox":bbox}
                raw.append(item);ref.append({**item,"bbox":reference})
                cv2.rectangle(image,tuple(reference[:2]),tuple(reference[2:]),(90,120,180),-1)
            writer.write(image);observations.append(raw);references.append(ref)
        writer.release()
        data=DEST/(name+".json");data.write_text(json.dumps({"raw":observations,"reference":references}),encoding="utf-8")
        clips.append({"id":name,"file":path.name,"observations":data.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"width":640,"height":360,"fps":30,"frames":150,"review_frames":list(range(0,150,3)),"segment":[0,149] if index<3 else None,"split":"adjustment" if index==0 else "reserved"})
    manifest={"version":1,"profile":"gated-ema-v1","origin":"synthetic","images":images,"clips":clips}
    (DEST/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest
if __name__=="__main__":
    m=generate();print(json.dumps({"images":len(m["images"]),"clips":len(m["clips"])}))
