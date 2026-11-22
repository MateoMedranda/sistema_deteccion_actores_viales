import numpy as np
from app.adapters.plate_reader_protocol import PlateReading
from app.services.plate_reading_policy import BaselinePolicy,CandidateRescuePolicy
IMAGE=np.indices((25,80)).sum(axis=0).astype(np.uint8)
IMAGE=np.repeat(IMAGE[:,:,None],3,axis=2)
def test_baseline_origin_is_actual_winner_and_attempt_not_winner():
    values=iter([PlateReading("RAW",.65),PlateReading("RETRY",.6)])
    result=BaselinePolicy().read(IMAGE,lambda c:next(values),.7,.6)
    assert result["text"]=="RAW" and result["used_enhancement"]
    assert result["provenance"]["selected_variant"]=="raw"
def test_preserves_accepted_baseline_and_rejects_disagreement():
    calls=[]
    def accepted(c):calls.append(1);return PlateReading("BASE",.9)
    result=CandidateRescuePolicy().read(IMAGE,accepted,.7,.75)
    assert result["text"]=="BASE" and len(calls)==1
    values=iter([None,None,PlateReading("ABC",.9),PlateReading("XYZ",.95)])
    result=CandidateRescuePolicy().read(IMAGE,lambda c:next(values),.7,.75)
    assert result["status"]=="unreadable" and result.get("text") is None
    assert result["provenance"]["selected_variant"]=="none"
    assert len(result["provenance"]["attempted_variants"])==4
def test_no_partial_rescue_on_deadline_and_ties_keep_variant_order():
    clock=[0.]
    values=iter([None,None,PlateReading("SAME",.9),PlateReading("SAME",.9)])
    def reader(c):
        output=next(values);clock[0]+=4;return output
    result=CandidateRescuePolicy(timer=lambda:clock[0]).read(IMAGE,reader,.7,.75)
    assert result["status"]=="read" and result["provenance"]["selected_variant"]=="bilateral-clahe-v1"
    clock[0]=0;values=iter([None,None,PlateReading("FIRST",.9),PlateReading("LAST",.99)])
    def slow(c):output=next(values);clock[0]+=6;return output
    result=CandidateRescuePolicy(timer=lambda:clock[0]).read(IMAGE,slow,.7,.75)
    assert result["status"]=="unreadable"
