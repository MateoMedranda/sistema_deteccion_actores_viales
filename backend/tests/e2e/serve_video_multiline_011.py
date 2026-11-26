"""Isolated 011 browser fixture. Fake models, temporary databases, no private .env."""
from tests.e2e import serve_progressive_009 as fixture
from app.domain.models import Detection
from app.services.video_progressive_store import now
import time
app=fixture.app
NAMES=['Car','Bus','Truck','Big Truck','Motorbike','Van']
def detect(image):
 fixture.detector.calls+=1;time.sleep(.002)
 h,w=image.shape[:2];phase=min(1,max(0,(fixture.detector.calls-10)/50))
 return [Detection(i,name,.95,25+i*95,int((.18+phase*.5 if i%2==0 else .7-phase*.5)*h),85+i*95,int((.18+phase*.5 if i%2==0 else .7-phase*.5)*h)+45) for i,name in enumerate(NAMES)]
fixture.detector.detect=detect
@app.post('/test-only/expire')
def expire(job:str):
 s=app.state.progressive_store
 with s.lock,s.db:s.db.execute("UPDATE p_video SET expires='2000-01-01T00:00:00+00:00' WHERE job=?",(job,))
 return {'expired':True}
