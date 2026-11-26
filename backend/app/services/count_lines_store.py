"""Temporal storage shares the parent's connection, lock and cleanup authority."""
TABLES=['p_count_lines_tracks','p_count_lines_events','p_count_lines','p_count_lines_collection']
class CountLinesStore:
 def __init__(self,store):
  self.store=store
  with store.lock,store.db:
   store.db.executescript('''
   CREATE TABLE IF NOT EXISTS p_count_lines_collection(job TEXT PRIMARY KEY,generation TEXT,revision INTEGER NOT NULL,admitted INTEGER NOT NULL,ordinal INTEGER NOT NULL,last_expected INTEGER,last_hash TEXT,imported INTEGER DEFAULT 0,import_id TEXT);
   CREATE TABLE IF NOT EXISTS p_count_lines(job TEXT,generation TEXT,line_id TEXT,name TEXT,name_key TEXT,color TEXT,segment TEXT,ordinal INTEGER,geometry_revision INTEGER,cursor INTEGER DEFAULT 0,covered INTEGER DEFAULT 0,error TEXT,deleted INTEGER DEFAULT 0,origin TEXT DEFAULT 'user',PRIMARY KEY(job,generation,line_id));
   CREATE UNIQUE INDEX IF NOT EXISTS p_count_lines_name ON p_count_lines(job,generation,name_key) WHERE deleted=0;
   CREATE UNIQUE INDEX IF NOT EXISTS p_count_lines_color ON p_count_lines(job,generation,color) WHERE deleted=0;
   CREATE TABLE IF NOT EXISTS p_count_lines_tracks(job TEXT,generation TEXT,line_id TEXT,geometry_revision INTEGER,track INTEGER,payload TEXT,PRIMARY KEY(job,generation,line_id,geometry_revision,track));
   CREATE TABLE IF NOT EXISTS p_count_lines_events(job TEXT,generation TEXT,line_id TEXT,geometry_revision INTEGER,track INTEGER,time_us INTEGER,frame_index INTEGER,class_key TEXT,PRIMARY KEY(job,generation,line_id,geometry_revision,track));
   CREATE INDEX IF NOT EXISTS p_count_lines_time ON p_count_lines_events(job,generation,line_id,geometry_revision,time_us);
   ''')
  with store.lock,store.db:
   if 'import_fingerprint' not in {r[1] for r in store.db.execute('PRAGMA table_info(p_count_lines_collection)')}:store.db.execute('ALTER TABLE p_count_lines_collection ADD COLUMN import_fingerprint TEXT')
  if not hasattr(store,'detail_resources'):store.detail_resources=[]
  store.detail_resources.append(self)
 def paths(self,job):return []
 def purge(self,job):
  for table in TABLES:self.store.db.execute('DELETE FROM '+table+' WHERE job=?',(job,))
