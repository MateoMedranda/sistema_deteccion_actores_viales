"""Causal display-only filtering. Never changes tracker observations."""
import math
import cv2
import numpy as np
from app.services.class_presentation import class_presentation
PROFILE="gated-ema-v1"
def iou(a,b):
    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    return intersection/max(1,(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-intersection)
def geometry(b):return ((b[0]+b[2])/2,(b[1]+b[3])/2,b[2]-b[0],b[3]-b[1])
class PresentationFilter:
    def __init__(self):
        self.previous={};self.thumbnail=None;self.invalid=0;self.fallback=0
    def present(self,frame,index,observations):
        h,w=frame.shape[:2]
        thumbnail=cv2.resize(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY),(32,18))
        cut=self.thumbnail is not None and np.abs(thumbnail.astype(np.float32)-self.thumbnail).mean()/255>=.25
        self.thumbnail=thumbnail;current={};output={}
        for observation in observations:
            tid=observation["track_id"];name=observation["class_name"].strip().lower();key=(tid,name)
            raw=observation["bbox"]
            visible=(max(0,min(w,raw[0])),max(0,min(h,raw[1])),max(0,min(w,raw[2])),max(0,min(h,raw[3])))
            if visible[2]<=visible[0] or visible[3]<=visible[1]:self.invalid+=1;continue
            prior=self.previous.get(key);presented=visible
            if prior and not cut and prior[0]==index-1:
                old_raw,old_box=prior[1:];a=geometry(old_raw);b=geometry(visible)
                reset=iou(old_raw,visible)<.25 or math.hypot(a[0]-b[0],a[1]-b[1])>.25*math.hypot(b[2],b[3]) or not all(2/3<=b[i]/a[i]<=1.5 for i in (2,3))
                if not reset:
                    old=geometry(old_box)
                    for alpha in (.65,.8,.9,1):
                        if alpha==1:self.fallback+=1;break
                        cx,cy,bw,bh=[alpha*x+(1-alpha)*y for x,y in zip(b,old)]
                        candidate=(max(0,min(w,round(cx-bw/2))),max(0,min(h,round(cy-bh/2))),max(0,min(w,round(cx+bw/2))),max(0,min(h,round(cy+bh/2))))
                        if candidate[2]>candidate[0] and candidate[3]>candidate[1] and iou(candidate,visible)>=.9:presented=candidate;break
            current[key]=(index,visible,presented);output[tid]=presented
        self.previous=current
        return output
    def apply(self,index,observations,frame):return self.present(frame,index,observations)

def draw_box(frame,box,name):
    x1,y1,x2,y2=box
    if x2<=x1 or y2<=y1:return
    points=((int(x1),int(y1)),(int(x2)-1,int(y2)-1))
    cv2.rectangle(frame,*points,(0,0,0),5)
    cv2.rectangle(frame,*points,(255,255,255),3)
    cv2.rectangle(frame,*points,class_presentation(name)["bgr"],2)
