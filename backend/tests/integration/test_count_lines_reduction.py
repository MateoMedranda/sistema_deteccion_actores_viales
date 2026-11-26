from copy import deepcopy
import pytest
from app.api.error_handlers import ApiError
from tests.integration.test_count_line_mutations import service,apply
from tests.fixtures_011 import line,frame,observation
import app.services.count_lines_reducer as module


def test_failure_of_pending_line_preserves_completed_line(tmp_path,monkeypatch):
 store,state,c=service(tmp_path);a=line('A');b=line('B','#112233',.6)
 apply(c,state,[a]);store.publish('test',[frame(0,[observation(y=20)]),frame(1,[observation(y=80)])]);c.reduce('test')
 apply(c,state,[a,b],1)
 monkeypatch.setattr(module,'advance',lambda *args:(_ for _ in ()).throw(RuntimeError('controlled failure')))
 c.reduce('test')
 values=c.snapshot('test','owner',state['generation'],2,100000)['lines']
 assert values[0]['status']=='ready' and values[0]['total']==1
 assert values[1]['status']=='unavailable' and values[1]['error_code']=='count_reducer_failed'


@pytest.mark.parametrize('operation',['geometry','delete','retire'])
def test_failure_does_not_publish_into_changed_or_retired_context(tmp_path,monkeypatch,operation):
 store,state,c=service(tmp_path);a=line('A');apply(c,state,[a]);store.publish('test',[frame(0,[observation(y=20)])])
 def fail(*args):
  if operation=='geometry':
   moved=deepcopy(a);moved['segment']['point_a']['y']=.7;apply(c,state,[moved],1)
  elif operation=='delete':apply(c,state,[],1)
  else:
   with store.lock,store.db:store.db.execute('UPDATE p_video SET retired=1 WHERE job=?',('test',))
  raise RuntimeError('controlled stale failure')
 monkeypatch.setattr(module,'advance',fail)
 if operation=='retire':
  with pytest.raises(ApiError):c.reduce('test')
 else:c.reduce('test')
 row=store.db.execute('SELECT error FROM p_count_lines WHERE job=?',('test',)).fetchone()
 assert row['error'] is None


def test_one_failed_line_does_not_poison_another_pending_line(tmp_path,monkeypatch):
 store,state,c=service(tmp_path);a=line('A',y=.5);b=line('B','#112233',.6);apply(c,state,[a,b]);store.publish('test',[frame(0,[observation(y=20)]),frame(1,[observation(y=80)])])
 real=module.advance
 def fail_one(state,point,geometry,*args):
  if geometry[0][1]==50:raise RuntimeError('only A')
  return real(state,point,geometry,*args)
 monkeypatch.setattr(module,'advance',fail_one);c.reduce('test')
 values=c.snapshot('test','owner',state['generation'],1,100000)['lines']
 assert values[0]['status']=='unavailable'
 assert values[1]['status']=='ready' and values[1]['total']==1
