from pathlib import Path
from app.api.error_handlers import ApiError
from app.services.video_progressive_store import now
VERSION='vehicle-labels-v1'
class VideoExportVariantStore:
 def __init__(self,store,settings):
  self.store,self.settings=store,settings
  with store.lock,store.db:
   store.db.execute('CREATE TABLE IF NOT EXISTS p_video_label_exports(job TEXT,renderer TEXT,state TEXT,frames INTEGER DEFAULT 0,error TEXT,output TEXT,temporary TEXT,PRIMARY KEY(job,renderer))')
   for row in store.db.execute("SELECT * FROM p_video_label_exports WHERE state IN ('rendering','encoding')").fetchall():
    for key in ['output','temporary']:
     if row[key]:Path(row[key]).unlink(missing_ok=True)
   store.db.execute("UPDATE p_video_label_exports SET state='failed',error='export_interrupted' WHERE state IN ('rendering','encoding')")
  if not hasattr(store,'detail_resources'):store.detail_resources=[]
  store.detail_resources.append(self)
 def paths(self,job):return [Path(p) for row in self.store.db.execute('SELECT output,temporary FROM p_video_label_exports WHERE job=?',(job,)) for p in row if p]
 def purge(self,job):self.store.db.execute('DELETE FROM p_video_label_exports WHERE job=?',(job,))
 def retains(self,path):return self.store.db.execute('SELECT 1 FROM p_video_label_exports e JOIN p_video v ON e.job=v.job WHERE e.output=? AND v.retired=0 AND v.expires>?',(str(path),now().isoformat())).fetchone() is not None
 def status(self,job,owner,renderer=VERSION):
  with self.store.lock:
   row=self.store.row(job,owner)
   if renderer!=VERSION:raise ApiError(422,'renderer_invalid','Invalid renderer.')
   export=self.store.db.execute('SELECT * FROM p_video_label_exports WHERE job=? AND renderer=?',(job,renderer)).fetchone()
   ready=export and export['state']=='ready' and export['output'] and Path(export['output']).is_file()
   state='ready' if ready else export['state'] if export and export['state']!='ready' else 'waiting'
   return dict(job_id=job,renderer_version=renderer,state=state,processed_frames=row['frames'] if ready else export['frames'] if export else 0,total_frames=row['frames'],expires_at=row['expires'],url=f'/api/v1/video-jobs/{job}/playback/export/content?renderer={renderer}' if ready else None,error_code=export['error'] if export else None)
 def request(self,job,owner,renderer=VERSION):
  s=self.store
  with s.lock,s.db:
   row=s.row(job,owner)
   if row['analysis']!='complete':raise ApiError(409,'analysis_not_ready','Complete the analysis before exporting.')
   current=self.status(job,owner,renderer)
   if current['state'] in ['queued','rendering','encoding','ready']:return current
   if s.db.execute("SELECT count(*) FROM p_video_label_exports WHERE state='queued'").fetchone()[0]>=self.settings.max_queued_video_jobs:raise ApiError(429,'export_queue_full','Export capacity reached.')
   s.db.execute("INSERT INTO p_video_label_exports(job,renderer,state) VALUES(?,?,'queued') ON CONFLICT(job,renderer) DO UPDATE SET state='queued',frames=0,error=NULL",(job,renderer));return self.status(job,owner,renderer)
 def claim(self):
  s=self.store
  with s.lock,s.db:
   if s.db.execute("SELECT 1 FROM video_jobs WHERE status IN ('queued','processing') LIMIT 1").fetchone():return
   row=s.db.execute("SELECT e.job,e.renderer,v.owner FROM p_video_label_exports e JOIN p_video v ON e.job=v.job WHERE e.state='queued' AND v.analysis='complete' AND v.retired=0 AND v.expires>? ORDER BY e.rowid LIMIT 1",(now().isoformat(),)).fetchone()
   if row:s.db.execute("UPDATE p_video_label_exports SET state='rendering' WHERE job=? AND renderer=?",(row['job'],row['renderer']));return row['job'],row['owner'],row['renderer']
 def path(self,job,owner,renderer):
  with self.store.lock:
   if self.status(job,owner,renderer)['state']!='ready':raise ApiError(409,'export_not_ready','The export is not ready.')
   return Path(self.store.db.execute('SELECT output FROM p_video_label_exports WHERE job=? AND renderer=?',(job,renderer)).fetchone()[0])
