def initialize(store):
 with store.lock,store.db:
  store.db.execute('CREATE TABLE IF NOT EXISTS p_directed_count_state(job TEXT PRIMARY KEY,generation TEXT,revision INTEGER,line TEXT,direction TEXT,cursor INTEGER DEFAULT 0,covered INTEGER DEFAULT 0,error TEXT)')
  store.db.execute('CREATE TABLE IF NOT EXISTS p_directed_count_tracks(job TEXT,revision INTEGER,track INTEGER,payload TEXT,PRIMARY KEY(job,revision,track))')
  store.db.execute('CREATE TABLE IF NOT EXISTS p_directed_count_events(job TEXT,revision INTEGER,track INTEGER,time_us INTEGER,confirming_frame_index INTEGER,class_key_at_crossing TEXT,PRIMARY KEY(job,revision,track))')
  store.db.execute('CREATE INDEX IF NOT EXISTS p_directed_count_time ON p_directed_count_events(job,revision,time_us)')
