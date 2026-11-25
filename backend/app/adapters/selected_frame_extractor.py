"""Hard extraction deadline includes child startup; never fall back to another frame."""
import json,subprocess,sys,time
from pathlib import Path

def extract_frame(source,pts,num,den,box,output,*,timeout,max_frames,max_bytes,active):
 start=time.monotonic();output=Path(output);output.unlink(missing_ok=True)
 data=dict(source=str(source),pts=int(pts),num=num,den=den,box=box,output=str(output),max_frames=max_frames,max_bytes=max_bytes)
 child=None
 try:
  child=subprocess.Popen([sys.executable,str(Path(__file__).with_name('selected_frame_worker.py'))],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  child.stdin.write(json.dumps(data).encode());child.stdin.close()
  while child.poll() is None:
   if time.monotonic()-start>=timeout:raise TimeoutError('inspection_decode_timeout')
   if not active():raise RuntimeError('inspection_interrupted')
   time.sleep(.01)
  if child.returncode or not output.is_file() or output.stat().st_size>max_bytes:raise ValueError('inspection_frame_unavailable')
  if not active():raise RuntimeError('inspection_interrupted')
  return output
 except BaseException:
  if child is not None and child.poll() is None:child.terminate();child.wait()
  output.unlink(missing_ok=True);raise
 finally:
  if child is not None:
   if child.poll() is None:child.terminate()
   child.wait()
