"""Brief synthetic publication comparison, without models, uploads or private jobs.

Run from backend: python tests/performance/test_video_detail_overhead.py capture|compare
Baseline is write-once. The candidate can never silently become its own reference.
"""
from pathlib import Path
import argparse, hashlib, importlib.metadata, json, platform, statistics, sys, tempfile, time
from datetime import datetime, timedelta, timezone
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'backend'))
from app.services.video_progressive_store import ProgressiveStore
PARAMETERS={'frames':300,'observations':20,'batch':15,'width':640,'height':360,'warmup':1,'repeats':5}

def context():
 return {'python':sys.version,'platform':platform.platform(),'packages':{p:importlib.metadata.version(p) for p in ['numpy','pydantic','Pillow','av']},'parameters':PARAMETERS,'fixture_sha256':hashlib.sha256(json.dumps(PARAMETERS,sort_keys=True).encode()).hexdigest()}

def fingerprint():
 h=hashlib.sha256()
 for p in sorted((ROOT/'backend/app').rglob('*.py')):
  h.update(p.relative_to(ROOT).as_posix().encode());h.update(p.read_bytes())
 return h.hexdigest()

def measure():
 with tempfile.TemporaryDirectory(prefix='video010-') as folder:
  store=ProgressiveStore(Path(folder)/'test.sqlite3')
  store.create('synthetic','test',Path(folder)/'source.mp4',{'width':640,'height':360,'duration':10},datetime.now(timezone.utc)+timedelta(hours=1),on_demand=True)
  start=time.perf_counter();publication=0;batch=[]
  for i in range(PARAMETERS['frames']):
   observations=[{'track_id':j+1,'class_id':0,'class_name':'car','confidence':.9,'raw_bbox':{'x_min':j*20,'y_min':10+i%100,'x_max':j*20+18,'y_max':40+i%100},'display_bbox':None} for j in range(PARAMETERS['observations'])]
   batch.append({'frame_index':i,'start_us':i*33333,'end_us':(i+1)*33333,'pts':str(i),'detection_performed':True,'observations':observations})
   if len(batch)==PARAMETERS['batch']:
    tick=time.perf_counter();store.publish('synthetic',batch);publication+=time.perf_counter()-tick;batch=[]
  store.finish_analysis('synthetic')
  result={'analysis_ms':(time.perf_counter()-start)*1000,'publication_ms':publication*1000}
  store.db.close();return result

def run(mode,directory=None):
 directory=Path(directory or ROOT/'specs/010-video-detalle-conteo/evidence')
 baseline=directory/'publication-baseline.json';candidate=directory/'publication-overhead.json'
 if mode=='capture' and baseline.exists():raise FileExistsError('Baseline already exists; it cannot be overwritten')
 if mode=='compare':
  old=json.loads(baseline.read_text(encoding='utf-8'))
  if old['context']!=context():raise ValueError('Baseline environment/fixture incompatible; do not recapture from candidate')
 measure()
 samples=[measure() for _ in range(PARAMETERS['repeats'])]
 report={'context':context(),'source_sha256':fingerprint(),'samples':samples,'medians':{k:statistics.median(s[k] for s in samples) for k in samples[0]},'scope':'synthetic publication only; no real model FPS or long benchmark'}
 if mode=='compare':
  report['baseline_source_sha256']=old['source_sha256'];report['baseline_medians']=old['medians']
  report['delta_percent']={k:100*(v/old['medians'][k]-1) for k,v in report['medians'].items()}
  report['requires_investigation']=report['delta_percent']['analysis_ms']>5
 directory.mkdir(parents=True,exist_ok=True)
 with (baseline if mode=='capture' else candidate).open('x' if mode=='capture' else 'w',encoding='utf-8') as f:json.dump(report,f,indent=2)
 print(json.dumps(report,indent=2));return report

def test_write_once_reference_and_missing_baseline(tmp_path):
 import pytest
 with pytest.raises(FileNotFoundError):run('compare',tmp_path)
 (tmp_path/'publication-baseline.json').write_text('{}')
 with pytest.raises(FileExistsError):run('capture',tmp_path)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['capture','compare']);run(parser.parse_args().mode)
