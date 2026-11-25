from datetime import datetime, timedelta, timezone
from app.services.video_progressive_store import ProgressiveStore

def observation(track=1,x=50,y=40,cls='car',confidence=.9):
 return dict(track_id=track,class_id=0,class_name=cls,confidence=confidence,raw_bbox=dict(x_min=x-5,y_min=y-5,x_max=x+5,y_max=y+5),display_bbox=None)

def frame(index,observations=None,measured=True):
 return dict(frame_index=index,start_us=index*100000,end_us=(index+1)*100000,pts=str(index),detection_performed=measured,observations=observations if observations is not None else [observation()])

def store_at(tmp_path):
 store=ProgressiveStore(tmp_path/'video.sqlite3');source=tmp_path/'source.mp4';source.write_bytes(b'fixture')
 state=store.create('test','owner',source,dict(width=100,height=100,duration=30),datetime.now(timezone.utc)+timedelta(hours=1),True)
 return store,state
