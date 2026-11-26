"""011 immutable baseline and bounded synthetic steady/catch-up comparison."""
from pathlib import Path
import importlib.util,sys,json,time,tempfile,statistics,uuid,psutil
from datetime import datetime,timedelta,timezone
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'backend'))
spec=importlib.util.spec_from_file_location('reference010',ROOT/'backend/tests/performance/test_video_detail_overhead.py')
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
DIRECTORY=ROOT/'specs/011-video-multilinea-velocidad/evidence'
def capture():return reference.run('capture',DIRECTORY)
def percentile(values,p=.95):return sorted(values)[min(len(values)-1,int(len(values)*p))] if values else 0
def measure(lines,mode):
 from app.services.count_lines_service import CountLinesService,PALETTE
 from app.services.video_progressive_store import ProgressiveStore
 with tempfile.TemporaryDirectory(prefix='count011-') as folder:
  store=ProgressiveStore(Path(folder)/'test.sqlite3');state=store.create('synthetic','test',Path(folder)/'source.mp4',{'width':640,'height':360,'duration':10},datetime.now(timezone.utc)+timedelta(hours=1),True);service=CountLinesService(store)
  if lines:service.configure('synthetic','test',dict(generation=state['generation'],expected_revision=0,lines=[dict(line_id=str(uuid.uuid4()),name='Road '+str(i),color=PALETTE[i],segment=dict(point_a=dict(x=.01,y=.3+i*.02),point_b=dict(x=.99,y=.3+i*.02))) for i in range(lines)]))
  locks=[];gets=[];steps=[];publication=0;batch=[];start=time.perf_counter()
  def reduce():
   service.reduce('synthetic');m=service.reducer.last_metrics
   if m:locks.extend([m['capture_lock_ms'],m['commit_lock_ms']]);steps.append(m)
  for i in range(300):
   obs=[{'track_id':j+1,'class_id':0,'class_name':'car','confidence':.9,'raw_bbox':{'x_min':j*20,'y_min':10+i%100,'x_max':j*20+18,'y_max':40+i%100},'display_bbox':None} for j in range(20)]
   batch.append(dict(frame_index=i,start_us=i*33333,end_us=(i+1)*33333,pts=str(i),detection_performed=True,observations=obs))
   if len(batch)==15:
    tick=time.perf_counter();store.publish('synthetic',batch);publication+=(time.perf_counter()-tick)*1000;batch=[]
    if lines and mode=='steady':reduce()
  store.finish_analysis('synthetic');analysis=(time.perf_counter()-start)*1000;tick=time.perf_counter();iterations=0
  while lines and store.db.execute('SELECT min(cursor) FROM p_count_lines WHERE deleted=0').fetchone()[0]<300:
   reduce();iterations+=1
   if iterations>1000:raise RuntimeError('count_catchup_stalled')
  catchup=(time.perf_counter()-tick)*1000
  for _ in range(50):
   tick=time.perf_counter();service.snapshot('synthetic','test',state['generation'],int(bool(lines)),9_900_000);gets.append((time.perf_counter()-tick)*1000)
  result=dict(analysis_ms=analysis,publication_ms=publication,catchup_ms=catchup,lock_p95_ms=percentile(locks),lock_max_ms=max(locks,default=0),get_p95_ms=percentile(gets),reducer_steps=len(steps),max_frame_line_pairs=max([s['frame_line_pairs'] for s in steps],default=0),capture_compute_commit_ms=sum(s['total_ms'] for s in steps),capture_ms=sum(s['capture_lock_ms'] for s in steps),compute_ms=sum(s.get('compute_ms',0) for s in steps),commit_ms=sum(s['commit_lock_ms'] for s in steps),covered_frames=300,lag_frames=0)
  info=psutil.Process().memory_info();result['process_rss_mb']=info.rss/1024**2;result['process_peak_rss_mb']=getattr(info,'peak_wset',info.rss)/1024**2
  store.db.close();return result
def compare():
 baseline=json.loads((DIRECTORY/'publication-baseline.json').read_text(encoding='utf-8'))
 if baseline['context']!=reference.context():raise ValueError('Reference context mismatch; never recapture from candidate')
 report=dict(context=reference.context(),source_sha256=reference.fingerprint(),baseline_source_sha256=baseline['source_sha256'],baseline_medians=baseline['medians'],cases={})
 for lines in [0,1,10]:
  for mode in ['steady','catchup']:
   measure(lines,mode);samples=[measure(lines,mode) for _ in range(5)];report['cases'][str(lines)+'-'+mode]=dict(samples=samples,medians={k:statistics.median(s[k] for s in samples) for k in samples[0]})
 zero=report['cases']['0-steady']['medians'];report['zero_delta_percent']={k:100*(zero[k]/v-1) for k,v in baseline['medians'].items()};report['requires_investigation']=report['zero_delta_percent']['analysis_ms']>5
 report['targets']=dict(lock_p95_pass=all(c['medians']['lock_p95_ms']<=10 for c in report['cases'].values()),get_pass=all(c['medians']['get_p95_ms']<=250 for c in report['cases'].values()),catchup_pass=report['cases']['10-catchup']['medians']['catchup_ms']<=5000)
 report['scope']='300x20 synthetic; no model FPS, no private media; catch-up runs cooperatively without the worker 50ms scheduling delay'
 (DIRECTORY/'count-lines-overhead.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ['cases','context']},indent=2));return report
if __name__=='__main__':
 if sys.argv[1:]==['capture']:capture()
 elif sys.argv[1:]==['compare']:compare()
 else:raise SystemExit('capture|compare')
