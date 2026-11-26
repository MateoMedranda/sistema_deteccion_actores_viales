from tests.integration.test_count_line_mutations import service,apply
from tests.fixtures_011 import line
from app.services.directed_count_service import DirectedCountService
from app.services.count_lines_service import CountLinesService
def test_import_marker_survives_service_recreation(tmp_path):
 s,state,c=service(tmp_path);old=DirectedCountService(s);old.configure('test','owner',dict(generation=state['generation'],expected_revision=0,line=line()['segment'],direction='positive_to_negative'))
 first=c.import_legacy('test','owner',dict(generation=state['generation'],expected_revision=0));apply(c,state,[],1)
 restored=CountLinesService(s).import_legacy('test','owner',dict(generation=state['generation'],expected_revision=0))
 assert restored['lines']==[] and restored['legacy_import']['line_id']==first['legacy_import']['line_id']
 assert s.db.execute('SELECT import_fingerprint FROM p_count_lines_collection').fetchone()[0]
