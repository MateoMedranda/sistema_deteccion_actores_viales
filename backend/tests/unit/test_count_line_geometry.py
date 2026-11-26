import pytest
from app.services.directed_counting import advance
from tests.fixtures_011 import NAMES
@pytest.mark.parametrize('name',NAMES)
@pytest.mark.parametrize('ys',[(20,50,80),(80,50,20)])
def test_bidirectional_segment_unique_event(name,ys):
 state={};events=0
 for y in (*ys,*reversed(ys),*ys):state,event=advance(state,(50,y),[(10,50),(90,50)],'both',name);events+=event
 assert events==1
@pytest.mark.parametrize('points',[[(5,20),(5,80)],[(50,20),(50,50),(50,20)],[(10,50),(20,50),(30,50)]])
def test_no_extension_tangent_or_collinear_false_event(points):
 state={};events=[]
 for point in points:state,event=advance(state,point,[(10,50),(90,50)],'both','Truck');events.append(event)
 assert not any(events)
def test_nonvehicle_can_cross_without_claiming_an_event():
 state={}
 for y in [20,80]:state,event=advance(state,(50,y),[(10,50),(90,50)],'both','person');assert not event
