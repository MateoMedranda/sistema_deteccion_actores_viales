import json
from pathlib import Path

def capabilities(store,job,owner):
 with store.lock:
  row=store.row(job,owner)
  timeline=json.loads(row['timeline'])
  source=Path(row['source']).is_file() and row['frames']>0
  sufficient=bool(row['frames']) and store.db.execute("SELECT 1 FROM p_frames WHERE job=? AND json_type(payload,'$.detection_performed') IS NULL LIMIT 1",(job,)).fetchone() is None
  return dict(job_id=job,generation=row['generation'],protocol='video-detail-v1',temporal_inspection='supported' if source else 'unavailable',directed_count='supported' if sufficient else 'unavailable',detection_summary='supported' if sufficient else 'unavailable',label_export='supported' if source else 'unavailable',reason_codes=[] if source and sufficient else ['reanalysis_required'],expires_at=row['expires'])
