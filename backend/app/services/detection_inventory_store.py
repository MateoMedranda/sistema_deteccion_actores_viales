def initialize(store):
 with store.lock,store.db:
  store.db.execute('CREATE TABLE IF NOT EXISTS p_detection_inventory(job TEXT PRIMARY KEY,generation TEXT,cursor INTEGER DEFAULT 0,covered INTEGER DEFAULT 0,revision INTEGER DEFAULT 0,error TEXT)')
  store.db.execute('CREATE TABLE IF NOT EXISTS p_detection_votes(job TEXT,generation TEXT,track INTEGER,class_key TEXT,count INTEGER,max_confidence REAL,PRIMARY KEY(job,generation,track,class_key))')
  store.db.execute('CREATE TABLE IF NOT EXISTS p_detection_tracks(job TEXT,generation TEXT,track INTEGER,canonical_class TEXT,first_seen INTEGER,last_seen INTEGER,measured_observations INTEGER,PRIMARY KEY(job,generation,track))')
