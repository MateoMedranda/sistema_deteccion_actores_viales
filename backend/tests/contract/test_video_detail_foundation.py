import pytest
from pydantic import ValidationError
from app.domain.video_detail import InspectionRequest, DirectedCountRequest

def test_closed_safe_integer_body():
 base=dict(generation='11111111-1111-4111-8111-111111111111',track_id=1,frame_index=0)
 assert InspectionRequest(**base).track_id==1
 for patch in ({'track_id':True},{'frame_index':2**53},{'unknown':1},{'generation':'bad'}):
  with pytest.raises(ValidationError):InspectionRequest(**{**base,**patch})
 for point in (float('nan'),float('inf'),True):
  with pytest.raises(ValidationError):DirectedCountRequest(generation=base['generation'],expected_revision=0,line={'point_a':{'x':point,'y':0},'point_b':{'x':1,'y':1}},direction='negative_to_positive')

def test_capabilities_closed_and_no_effects(client,auth_headers):
 response=client.get('/api/v1/video-jobs/missing/playback/capabilities',headers=auth_headers)
 assert response.status_code==404
 assert client.get('/api/v1/video-jobs/missing/playback/capabilities?unknown=1',headers=auth_headers).status_code==422
