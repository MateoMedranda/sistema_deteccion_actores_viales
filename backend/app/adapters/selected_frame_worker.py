"""One short-lived, PyAV-only child. No API, detector or enrichment imports."""
import json,sys
from pathlib import Path
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import av
from av.video.reformatter import VideoReformatter
from PIL import Image
from app.adapters.timed_video_decoder import frame_to_bgr

def main():
 data=json.loads(sys.stdin.read(65536));target=Fraction(data['pts'])*Fraction(data['num'],data['den'])
 with av.open(data['source']) as c:
  stream=c.streams.video[0];c.seek(int(target/Fraction(stream.time_base)),stream=stream,backward=True,any_frame=False)
  reformatter=VideoReformatter()
  for i,frame in enumerate(c.decode(stream)):
   if i>=data['max_frames']:raise ValueError('inspection_decode_limit')
   if frame.pts is None:raise ValueError('inspection_pts_missing')
   stamp=frame.pts*Fraction(frame.time_base)
   if stamp<target:continue
   if stamp!=target:raise ValueError('inspection_frame_unavailable')
   image=frame_to_bgr(frame,reformatter);h,w=image.shape[:2];b=data['box'];x1,y1,x2,y2=[b[k] for k in ('x_min','y_min','x_max','y_max')]
   if not (0<=x1<x2<=w and 0<=y1<y2<=h):raise ValueError('inspection_bbox_invalid')
   Image.fromarray(image[y1:y2,x1:x2,::-1]).save(data['output'],format='PNG')
   if Path(data['output']).stat().st_size>data['max_bytes']:raise ValueError('inspection_resource_limit')
   return
 raise ValueError('inspection_frame_unavailable')
if __name__=='__main__':main()
