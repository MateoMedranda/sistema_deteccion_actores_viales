from tests.integration.test_count_line_mutations import service,apply
from tests.fixtures_011 import line,frame,observation
def test_metadata_preserves_geometry_cursor_and_events(tmp_path):
 s,state,c=service(tmp_path);a=line();b=line('Other','#123456');apply(c,state,[a,b]);s.publish('test',[frame(0,[observation(y=20)]),frame(1,[observation(y=80)])]);c.reduce('test')
 rows=[tuple(r) for r in s.db.execute('SELECT line_id,geometry_revision,cursor,covered FROM p_count_lines ORDER BY ordinal')];events=[tuple(r) for r in s.db.execute('SELECT * FROM p_count_lines_events')]
 a['name'],b['name']=b['name'],a['name'];a['color'],b['color']=b['color'],a['color'];apply(c,state,[a,b],1)
 assert rows==[tuple(r) for r in s.db.execute('SELECT line_id,geometry_revision,cursor,covered FROM p_count_lines ORDER BY ordinal')]
 assert events==[tuple(r) for r in s.db.execute('SELECT * FROM p_count_lines_events')]
