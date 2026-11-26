from copy import deepcopy
import pytest
from app.api.error_handlers import ApiError
from app.services.count_lines_service import CountLinesService
from app.services.video_progressive_store import ProgressiveStore
from tests.integration.test_count_line_mutations import service,apply
from tests.fixtures_011 import line,frame,observation
def test_reopen_cursor_and_parent_cleanup(tmp_path):
 s,state,c=service(tmp_path);l=line();apply(c,state,[l]);s.publish('test',[frame(0,[observation(y=20)]),frame(1,[observation(y=80)])]);c.reduce('test');before=c.snapshot('test','owner',state['generation'],1,100000);assert before['lines'][0]['total']==1
 path=s.db.execute('PRAGMA database_list').fetchone()[2];s.db.close();other=ProgressiveStore(__import__("pathlib").Path(path));reopened=CountLinesService(other);after=reopened.snapshot('test','owner',state['generation'],1,100000);assert after['analysis_state']=='partial_failed' and after['lines'][0]['result_scope']=='partial';assert after['lines'][0]['total']==before['lines'][0]['total'] and after['lines'][0]['covered_until_us']==before['lines'][0]['covered_until_us']
 other.withdraw('test','owner');other.cleanup();assert other.db.execute('SELECT count(*) FROM p_count_lines_collection').fetchone()[0]==0
 with pytest.raises(ApiError):reopened.descriptor('test','owner',state['generation'])
def test_inflight_geometry_change_discards_only_edited_line(tmp_path,monkeypatch):
 import app.services.count_lines_reducer as module
 s,state,c=service(tmp_path);a=line();b=line('B','#123456');apply(c,state,[a,b]);s.publish('test',[frame(0,[observation(y=20)]),frame(1,[observation(y=80)])]);original=module.advance;changed=False
 def race(*args):
  nonlocal changed
  if not changed:
   changed=True;moved=deepcopy(a);moved['segment']['point_a']['y']=.9;moved['segment']['point_b']['y']=.9;apply(c,state,[moved,b],1)
  return original(*args)
 monkeypatch.setattr(module,'advance',race);c.reduce('test');result=c.snapshot('test','owner',state['generation'],2,100000)
 assert result['lines'][0]['status']=='pending'
 for _ in range(3):c.reduce('test')
 assert c.snapshot('test','owner',state['generation'],2,100000)['lines'][1]['total']==1
def test_expiry_during_compute_never_resurrects(tmp_path,monkeypatch):
 import app.services.count_lines_reducer as module
 s,state,c=service(tmp_path);apply(c,state,[line()]);s.publish('test',[frame(0)]);original=module.advance
 def race(*args):s.withdraw('test','owner');s.cleanup();return original(*args)
 monkeypatch.setattr(module,'advance',race)
 with pytest.raises(ApiError):c.reduce('test')
 assert s.db.execute('SELECT count(*) FROM p_count_lines').fetchone()[0]==0
