from tests.fixtures_011 import store_at
from app.services.count_lines_store import CountLinesStore,TABLES
from app.services.directed_count_service import DirectedCountService
def test_additive_reopen_and_purge(tmp_path):
 s,state=store_at(tmp_path);DirectedCountService(s);storage=CountLinesStore(s)
 with s.lock,s.db:
  s.db.execute('INSERT INTO p_count_lines_collection(job,generation,revision,admitted,ordinal) VALUES(?,?,?,?,?)',('test',state['generation'],0,0,0))
  for table in TABLES[:-1]:s.db.execute('INSERT INTO '+table+'(job) VALUES(?)',('test',))
 before=s.row('test')['expires'];CountLinesStore(s)
 assert s.db.execute('SELECT count(*) FROM p_count_lines_collection').fetchone()[0]==1
 assert s.db.execute("SELECT name FROM sqlite_master WHERE name='p_directed_count_state'").fetchone()
 assert s.row('test')['expires']==before
 with s.lock,s.db:storage.purge('test')
 assert all(s.db.execute('SELECT count(*) FROM '+table).fetchone()[0]==0 for table in TABLES)
 assert s.row('test')['expires']==before
