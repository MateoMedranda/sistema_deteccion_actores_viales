"""The exact six names observed in the configured checkpoint, not just Car/Truck."""
import pytest,numpy as np
from app.core.config import Settings
from app.domain.models import Detection
from app.domain.vehicle_taxonomy import is_vehicle,normalize_class
from app.services.vehicle_cropping import crop_vehicle
from app.services.directed_count_service import DirectedCountService
from app.services.class_presentation import class_presentation
from tests.fixtures_010 import store_at,frame,observation

MODEL_NAMES=['Car','Bus','Truck','Big Truck','Motorbike','Van']
@pytest.mark.parametrize('name',MODEL_NAMES)
def test_every_trained_vehicle_class_is_countable_and_has_known_presentation(name):
 assert is_vehicle(name)
 assert class_presentation(name)['known']

def test_six_model_classes_reach_counts_and_summary_without_losing_heavy_trucks(tmp_path):
 store,state=store_at(tmp_path);counter=DirectedCountService(store)
 counter.configure('test','owner',dict(generation=state['generation'],expected_revision=0,line=dict(point_a=dict(x=.05,y=.5),point_b=dict(x=.95,y=.5)),direction='negative_to_positive'))
 def observations(y):
  return [{**observation(track=i+1,x=10+15*i,y=y,cls=name),'class_id':i} for i,name in enumerate(MODEL_NAMES)]
 store.publish('test',[frame(0,observations(40)),frame(1,observations(60),False),frame(2,observations(60))]);counter.reduce('test');store.finish_analysis('test')
 result=counter.snapshot('test','owner',state['generation'],200000)
 assert result['total']==6
 summary=store.inventory.snapshot('test','owner',state['generation'])
 counts={c['class_key']:c['track_count'] for c in summary['classes']}
 assert counts==dict(car=1,bus=1,truck=1,big_truck=1,motorcycle=1,van=1)
 assert summary['total_tracks']==6 and not summary['requires_review']
 assert {r[0] for r in store.db.execute('SELECT class_key_at_crossing FROM p_directed_count_events')}==set(counts)
 assert normalize_class('Truck')!=normalize_class('Big Truck')

@pytest.mark.parametrize('name',['Big Truck',' big_truck ','Truck','Van'])
def test_configured_enrichment_and_cropping_recognize_trained_vehicle_spellings(name):
 settings=Settings(_env_file=None,vehicle_classes='car,truck,bus,van')
 detection=Detection(3,name,.95,1,1,10,10)
 assert crop_vehicle(np.zeros((20,20,3),np.uint8),detection,settings.vehicle_class_set()) is not None

def test_explicit_vehicle_config_remains_a_filter():
 settings=Settings(_env_file=None,vehicle_classes='car')
 assert not any(is_vehicle_name in settings.vehicle_class_set() for is_vehicle_name in ['truck','big truck','big_truck','van'])
 assert not is_vehicle('person') and not is_vehicle('unlisted')


@pytest.mark.parametrize('name',MODEL_NAMES)
def test_every_model_class_obeys_direction_segment_and_single_count(name):
 from app.services.directed_counting import advance
 line=((5,50),(95,50))
 state={};events=[]
 for point in [(30,40),(30,60),(30,40),(30,60)]:
  state,event=advance(state,point,line,'negative_to_positive',name);events.append(event)
 assert sum(events)==1
 for points in [[(30,60),(30,40)],[(99,40),(99,60)],[(30,40),(30,50)]]:
  state={}
  for point in points:
   state,event=advance(state,point,line,'negative_to_positive',name)
   assert not event

def test_alias_votes_are_one_class_and_keep_original_observation(tmp_path):
 import json
 store,state=store_at(tmp_path)
 store.publish('test',[frame(0,[observation(cls='Big Truck')]),frame(1,[observation(cls='big_truck')])])
 store.finish_analysis('test')
 summary=store.inventory.snapshot('test','owner',state['generation'])
 assert summary['total_tracks']==1
 assert summary['classes'][0]['class_key']=='big_truck'
 assert store.db.execute('SELECT count FROM p_detection_votes').fetchone()[0]==2
 assert json.loads(store.db.execute('SELECT payload FROM p_frames WHERE idx=0').fetchone()[0])['observations'][0]['class_name']=='Big Truck'

def test_motorbike_config_alias_does_not_enable_other_families():
 settings=Settings(_env_file=None,vehicle_classes='Motorbike')
 assert settings.vehicle_class_set()=={'motorcycle','motorbike'}
 assert Settings(_env_file=None,vehicle_classes='big_truck').vehicle_class_set()=={'big truck','big_truck'}

@pytest.mark.parametrize('interval',[1,2])
def test_real_bytetrack_preserves_all_model_classes_ids_and_count(interval,tmp_path):
 from types import SimpleNamespace
 import torch
 from ultralytics.engine.results import Boxes
 from app.adapters.yolov10_tracker import YOLOv10ByteTrackAdapter
 class Model:
  names=dict(enumerate(MODEL_NAMES))
  def predict(self,image,**kwargs):
   index=int(image[0,0,0]);y=45+index
   rows=[[10+15*c-4,y-5,10+15*c+4,y+5,.95,c] for c in range(6)]
   if index%4==2:rows.reverse()
   return [SimpleNamespace(boxes=Boxes(torch.tensor(rows),image.shape[:2]),orig_img=image)]
 tracker=YOLOv10ByteTrackAdapter(Model(),.25,'cpu');tracker.set_detection_interval(interval)
 store,state=store_at(tmp_path);counter=DirectedCountService(store)
 counter.configure('test','owner',dict(generation=state['generation'],expected_revision=0,line=dict(point_a=dict(x=.05,y=.5),point_b=dict(x=.95,y=.5)),direction='negative_to_positive'))
 ids={}
 for index in range(12):
  pairs=tracker.track(np.full((100,100,3),index,np.uint8));observations=[]
  assert len(pairs)==6
  for detection,tid in pairs:
   assert detection.class_id==MODEL_NAMES.index(detection.class_name)
   assert ids.setdefault(detection.class_name,tid)==tid
   observations.append(dict(track_id=tid,class_id=detection.class_id,class_name=detection.class_name,confidence=detection.confidence,raw_bbox=dict(x_min=detection.x_min,y_min=detection.y_min,x_max=detection.x_max,y_max=detection.y_max),display_bbox=None))
  store.publish('test',[frame(index,observations,tracker.last_was_detection)])
 counter.reduce('test');store.finish_analysis('test')
 assert len(set(ids.values()))==6
 assert counter.snapshot('test','owner',state['generation'],1100000)['total']==6
 assert {c['class_key']:c['track_count'] for c in store.inventory.snapshot('test','owner',state['generation'])['classes']}==dict(car=1,bus=1,truck=1,big_truck=1,motorcycle=1,van=1)
