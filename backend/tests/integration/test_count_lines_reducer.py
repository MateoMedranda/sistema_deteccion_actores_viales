from tests.integration.test_count_line_mutations import service,apply
from tests.fixtures_011 import line,frame,observation
def test_prediction_ignored_and_temporal_validity(tmp_path):
 s,state,c=service(tmp_path);apply(c,state,[line()]);s.publish('test',[frame(0,[observation(y=20)]),frame(1,[observation(y=80)],False),frame(2,[observation(y=80)])]);c.reduce('test')
 old=c.snapshot('test','owner',state['generation'],1,0)['lines'][0];assert old['total']==0 and old['valid_until_us']==200000
 assert c.snapshot('test','owner',state['generation'],1,200000)['lines'][0]['total']==1
def test_work_limit_only_line_unavailable(tmp_path):
 s,state,c=service(tmp_path);apply(c,state,[line()]);s.publish('test',[frame(0)])
 with s.lock,s.db:s.db.execute('UPDATE p_frames SET payload=?',(' '* (2*1024*1024+1),))
 c.reduce('test');value=c.snapshot('test','owner',state['generation'],1,0)['lines'][0];assert value['status']=='unavailable' and value['error_code']=='count_work_limit' and value['total'] is None
def test_quota_tombstones_and_lowering_capacity_allows_metadata(tmp_path):
 from app.api.error_handlers import ApiError
 from types import SimpleNamespace
 import pytest
 s,state,c=service(tmp_path);lines=[line(str(i),'#%06X'%i) for i in range(10)];apply(c,state,lines);c.settings.video_count_max_lines=10;c.settings.video_count_max_admitted_lines=10
 apply(c,state,lines[:9],1)
 with pytest.raises(ApiError):apply(c,state,lines[:9]+[line('new','#ABCDEF')],2)
 lines[0]['name']='Renamed';assert apply(c,state,lines[:9],2)['revision']==3
