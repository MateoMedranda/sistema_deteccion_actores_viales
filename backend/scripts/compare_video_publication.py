"""Brief synthetic AB/BA investigation using one trusted historical store, no checkout change.

This never replaces the original write-once reference or the candidate report.
"""
from pathlib import Path
import argparse,importlib.util,json,re,statistics,subprocess,sys,types
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))

def run(ref):
 if not re.fullmatch(r'[0-9a-f]{7,40}',ref):raise ValueError('Use an explicit trusted Git commit hash')
 text=subprocess.check_output(['git','show',ref+':backend/app/services/video_progressive_store.py'],cwd=ROOT).decode('utf-8')
 baseline=types.ModuleType('historical_progressive_store');exec(compile(text,'<trusted historical ProgressiveStore>','exec'),baseline.__dict__)
 spec=importlib.util.spec_from_file_location('publication_harness',ROOT/'backend/tests/performance/test_video_detail_overhead.py');harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)
 candidate=harness.ProgressiveStore
 def measure(factory):
  harness.ProgressiveStore=factory
  try:return harness.measure()
  finally:harness.ProgressiveStore=candidate
 measure(baseline.ProgressiveStore);measure(candidate)
 pairs=[]
 for i in range(5):
  order=['baseline','candidate'] if i%2==0 else ['candidate','baseline'];pair={'order':order}
  for arm in order:pair[arm]=measure(baseline.ProgressiveStore if arm=='baseline' else candidate)
  pairs.append(pair)
 medians={arm:{key:statistics.median(pair[arm][key] for pair in pairs) for key in ['analysis_ms','publication_ms']} for arm in ['baseline','candidate']}
 delta={key:100*(medians['candidate'][key]/medians['baseline'][key]-1) for key in medians['baseline']}
 report={'baseline_commit':ref,'candidate_source_sha256':harness.fingerprint(),'context':harness.context(),'pairs':pairs,'medians':medians,'delta_percent':delta,'added_analysis_ms_per_frame':(medians['candidate']['analysis_ms']-medians['baseline']['analysis_ms'])/harness.PARAMETERS['frames'],'scope':'Short synthetic AB/BA only. Not real model FPS or deferred long comparison. The original reference remains unchanged.'}
 target=ROOT/'specs/010-video-detalle-conteo/evidence/publication-paired-check.json';target.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--baseline-ref',required=True);run(parser.parse_args().baseline_ref)
