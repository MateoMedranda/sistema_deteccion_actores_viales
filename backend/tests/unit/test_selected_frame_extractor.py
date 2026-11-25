from fractions import Fraction
from pathlib import Path
import av,numpy as np,pytest
from app.adapters.selected_frame_extractor import extract_frame

def video(path):
 with av.open(str(path),'w') as c:
  stream=c.add_stream('mpeg4',rate=10);stream.width=100;stream.height=100;stream.pix_fmt='yuv420p'
  for i in range(30):
   f=av.VideoFrame.from_ndarray(np.full((100,100,3),i*5,dtype=np.uint8),format='bgr24');f.pts=i;f.time_base=Fraction(1,10)
   for packet in stream.encode(f):c.mux(packet)
  for packet in stream.encode():c.mux(packet)

def test_extracts_exact_pts_and_enforces_watchdog(tmp_path):
 source=tmp_path/'source.mp4';video(source)
 with av.open(str(source)) as c:frames=list(c.decode(video=0));target=frames[20];pts=target.pts;tb=target.time_base
 output=tmp_path/'crop.png'
 data=extract_frame(source,pts,tb.numerator,tb.denominator,dict(x_min=10,y_min=10,x_max=60,y_max=60),output,timeout=5,max_frames=300,max_bytes=8388608,active=lambda:True)
 from PIL import Image
 with Image.open(output) as image:assert image.size==(50,50) and np.asarray(image).mean()>90
 assert data==output
 with pytest.raises(TimeoutError):extract_frame(source,pts,tb.numerator,tb.denominator,dict(x_min=10,y_min=10,x_max=60,y_max=60),output,timeout=.001,max_frames=300,max_bytes=8388608,active=lambda:True)
 assert not output.exists()
