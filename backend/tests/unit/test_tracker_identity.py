import numpy as np
import torch
from types import SimpleNamespace
from ultralytics.engine.results import Boxes
from app.adapters.yolov10_tracker import YOLOv10ByteTrackAdapter

class Detector:
    names={0:"Car",1:"Truck"}
    def predict(self,frame,**kwargs):
        i=int(frame[0,0,0]);car=[10+i,10,30+i,30,.95,0];truck=[100+i,10,140+i,60,.94,1]
        rows=[car,truck] if i%2==0 else [truck,car]
        return [SimpleNamespace(boxes=Boxes(torch.tensor(rows),frame.shape[:2]),orig_img=frame)]
    def track(self,frame,persist=False,**kwargs):
        # Reproduce the installed engine: callback persist is captured at first registration.
        if not hasattr(self,"callback_persist"):self.callback_persist=persist
        result=self.predict(frame,**kwargs)[0]
        rows=result.boxes.data.tolist()
        result.boxes=Boxes(torch.tensor([r[:4]+[i+1]+r[4:] for i,r in enumerate(rows)]),frame.shape[:2])
        return [result]

def test_tracks_keep_identity_when_detection_order_changes_and_images_are_interleaved():
    model=Detector();tracker=YOLOv10ByteTrackAdapter(model,.25,"cpu");tracker.reset();identities={}
    for i in range(8):
        frame=np.full((100,180,3),i,np.uint8)
        result=tracker.track(frame)
        for detection,tid in result:
            assert identities.setdefault(detection.class_name,tid)==tid
        model.predict(np.zeros_like(frame))
    assert len(identities)==2 and len(set(identities.values()))==2

def test_reset_starts_fresh_job_state_without_reloading_detector():
    model=Detector();tracker=YOLOv10ByteTrackAdapter(model,.25,"cpu");tracker.reset()
    frame=np.zeros((100,180,3),np.uint8);first=[(d.class_name,tid) for d,tid in tracker.track(frame)]
    tracker.reset();assert first==[(d.class_name,tid) for d,tid in tracker.track(frame)]
