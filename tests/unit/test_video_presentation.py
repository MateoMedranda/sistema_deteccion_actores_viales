import numpy as np
from app.services.video_presentation import PresentationFilter,iou
def item(x=20,track=1,cls="car"):
 return {"track_id":track,"class_name":cls,"bbox":(x,20,x+80,60)}
def test_filter_never_extrapolates_or_crosses_ids_classes_cuts():
 f=PresentationFilter();dark=np.zeros((120,200,3),dtype=np.uint8)
 assert f.apply(0,[item()],dark)[1]==(20,20,100,60)
 assert f.apply(1,[],dark)=={}
 assert f.apply(2,[item(22)],dark)[1]==(22,20,102,60)
 bright=np.full_like(dark,255)
 assert f.apply(3,[item(24)],bright)[1]==(24,20,104,60)
 assert f.apply(4,[item(26,cls="truck")],bright)[1]==(26,20,106,60)
def test_integer_visible_iou_is_guarded_without_mutating_raw():
 f=PresentationFilter();image=np.zeros((120,200,3),dtype=np.uint8);raw=item()
 before=dict(raw)
 f.apply(0,[raw],image);candidate=f.apply(1,[item(22)],image)[1]
 assert iou(candidate,item(22)["bbox"])>=.9
 assert raw==before
