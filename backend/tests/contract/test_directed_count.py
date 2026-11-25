import pytest
from app.services.directed_count_service import DirectedCountService
from app.api.error_handlers import ApiError
from tests.fixtures_010 import store_at,frame,observation
from tests.contract.test_video_inspections import schema_check

def test_cas_historical_get_and_coverage_boundary(tmp_path):
 store,state=store_at(tmp_path);service=DirectedCountService(store)
 body=dict(generation=state['generation'],expected_revision=0,line=dict(point_a=dict(x=.1,y=.5),point_b=dict(x=.9,y=.5)),direction='negative_to_positive')
 assert service.configure('test','owner',body)['revision']==1
 with pytest.raises(ApiError):service.configure('test','owner',body)
 assert service.configure('test','owner',{**body,'expected_revision':1})['revision']==1
 store.publish('test',[frame(0,[observation(y=40)]),frame(1,[observation(y=60)],False),frame(2,[observation(y=60)])])
 before=store.db.total_changes
 assert service.snapshot('test','owner',state['generation'],200000)['status']=='pending'
 assert store.db.total_changes==before  # GET never computes events
 service.reduce('test',limit=2)
 assert service.snapshot('test','owner',state['generation'],200000)['total'] is None
 service.reduce('test');result=service.snapshot('test','owner',state['generation'],200000)
 schema_check('DirectedCount',result);assert result['total']==1
 assert service.snapshot('test','owner',state['generation'],0)['total']==0
 assert service.snapshot('test','owner',state['generation'],200000)['total']==1
 assert store.db.execute('SELECT class_key_at_crossing FROM p_directed_count_events').fetchone()[0]=='car'
 service.disable('test','owner',state['generation'],1)
 assert service.snapshot('test','owner',state['generation'],200000)['revision']==2
 service.disable('test','owner',state['generation'],2)
 assert service.snapshot('test','owner',state['generation'],200000)['revision']==2
