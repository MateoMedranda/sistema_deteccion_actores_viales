from copy import deepcopy
import pytest
from app.api.error_handlers import ApiError
from app.core.config import Settings
from app.domain.count_lines import CollectionWrite
from app.services.count_lines_service import CountLinesService
from tests.fixtures_011 import store_at,line,frame,observation,NAMES

def service(tmp_path):
 store,state=store_at(tmp_path);return store,state,CountLinesService(store,Settings(_env_file=None))
def apply(s,state,lines,rev=0):
 return s.configure('test','owner',CollectionWrite(generation=state['generation'],expected_revision=rev,lines=lines).model_dump(mode='json'))
def test_collection_cas_retry_noop_and_tombstone(tmp_path):
 store,state,s=service(tmp_path);initial=store.db.total_changes
 assert s.descriptor('test','owner',state['generation'])['revision']==0
 assert store.db.total_changes==initial
 a=line();value=apply(s,state,[a]);assert value['revision']==1
 assert apply(s,state,[a])['revision']==1
 assert apply(s,state,[a],1)['revision']==1
 a2={**a,'name':'Ruta Viva'};assert apply(s,state,[a2],1)['lines'][0]['geometry_revision']==1
 with pytest.raises(ApiError):apply(s,state,[a],0)
 assert apply(s,state,[],2)['admitted_count']==1
 with pytest.raises(ApiError):apply(s,state,[a],3)
def test_quota_duplicates_rollback_and_swap(tmp_path):
 store,state,s=service(tmp_path);a=line();b=line('RUTA VIVA','#06B6D4')
 value=apply(s,state,[a,b]);assert len(value['lines'])==2
 with pytest.raises(ApiError):apply(s,state,[a,{**b,'name':' LÍNEA  1 '}],1)
 assert s.descriptor('test','owner',state['generation'])['revision']==1
 swapped=[{**a,'color':b['color']},{**b,'color':a['color']}]
 assert apply(s,state,swapped,1)['revision']==2
 with pytest.raises(ApiError):apply(s,state,[line(str(i),'#%06X'%i) for i in range(11)],2)
def test_six_classes_both_directions_history_and_metadata(tmp_path):
 store,state,s=service(tmp_path);a=line();b=line('RUTA VIVA','#06B6D4',.55);apply(s,state,[a,b])
 def obs(y):return [observation(track=i+1,x=10+i*15,y=y if i%2 else 100-y,cls=n) for i,n in enumerate(NAMES)]
 store.publish('test',[frame(0,obs(40)),frame(1,obs(60),False),frame(2,obs(60))]);store.finish_analysis('test')
 for _ in range(20):s.reduce('test')
 snap=s.snapshot('test','owner',state['generation'],1,200000)
 assert [v['total'] for v in snap['lines']]==[6,6]
 assert all(v['valid_until_us']==300000 for v in snap['lines'])
 assert all(v['total']==0 for v in s.snapshot('test','owner',state['generation'],1,0)['lines'])
 changed=apply(s,state,[{**a,'name':'AV SIMÓN BOLIVAR'},b],1)
 assert changed['lines'][0]['geometry_revision']==1
 assert s.snapshot('test','owner',state['generation'],2,200000)['lines'][0]['total']==6
 moved=deepcopy(a);moved['segment']['point_a']['y']=.7;moved['segment']['point_b']['y']=.7
 apply(s,state,[moved,b],2)
 result=s.snapshot('test','owner',state['generation'],3,200000)
 assert result['lines'][0]['total'] is None and result['lines'][1]['total']==6
def test_import_once_even_after_deletion(tmp_path):
 from app.services.directed_count_service import DirectedCountService
 store,state,s=service(tmp_path);old=DirectedCountService(store)
 old.configure('test','owner',dict(generation=state['generation'],expected_revision=0,line=line()['segment'],direction='negative_to_positive'))
 assert s.descriptor('test','owner',state['generation'])['legacy_import']['status']=='offered'
 first=s.import_legacy('test','owner',dict(generation=state['generation'],expected_revision=0))
 assert len(first['lines'])==1
 apply(s,state,[],1)
 assert s.import_legacy('test','owner',dict(generation=state['generation'],expected_revision=0))['lines']==[]
