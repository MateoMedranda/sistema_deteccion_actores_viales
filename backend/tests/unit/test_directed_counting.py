import pytest
from app.services.directed_counting import advance
LINE=((10,50),(90,50))
def movement(points,classes=None,direction='negative_to_positive'):
 state={};events=[]
 for i,p in enumerate(points):
  state,event=advance(state,p,LINE,direction,(classes or ['car']*len(points))[i])
  if event:events.append(i)
 return events
@pytest.mark.parametrize('points,expected',[
 ([(50,40),(50,60)],[1]), ([(50,60),(50,40)],[]),
 ([(95,40),(95,60)],[]), ([(10,40),(10,60)],[1]),
 ([(50,40),(50,50),(50,40)],[]), ([(50,50),(50,60)],[]),
 ([(50,40),(50,50),(50,50),(50,60)],[3]),
 ([(95,40),(95,60),(50,40),(50,60)],[3]),
 ([(50,40),(50,60),(50,40),(50,60)],[1]),
])
def test_finite_directed_geometry(points,expected):assert movement(points)==expected
def test_class_at_confirmation_and_later_eligibility():
 assert movement([(50,40),(50,60)],['car','person'])==[]
 assert movement([(50,40),(50,60)],['car','unlisted'])==[]
 assert movement([(50,40),(50,60)],['car','bicycle'])==[1]
 assert movement([(50,40),(50,60),(50,40),(50,60)],['car','person','car','motorcycle'])==[3]
 assert movement([(50,60),(50,40)],direction='positive_to_negative')==[1]
