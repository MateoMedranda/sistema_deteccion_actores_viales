"""Freeze pre-007 decisions and pixel recipe before extracting the policy."""
import cv2,numpy as np,pytest
from app.services.enrichment_processing import EnrichmentProcessor
from app.services.plate_quality import conservative_enhance,rectify_plate
from app.adapters.plate_reader_protocol import PlateReading
from tests.enrichment_fixtures import FakeLocalizer
class Sequence:
    def __init__(self,values):self.values=iter(values);self.calls=[]
    def read(self,crop):self.calls.append(crop.copy());return next(self.values)
@pytest.mark.parametrize("raw,retry,expected,text,used,calls",[
 (PlateReading("RAW",.9),None,.9,"RAW",False,1),
 (PlateReading("RAW",.5),PlateReading("RETRY",.5),.5,None,True,2),
 (PlateReading("RAW",.6),PlateReading("RETRY",.8),.8,"RETRY",True,2),
 (None,PlateReading("RETRY",.8),.8,"RETRY",True,2),
 (PlateReading("",.9),None,.9,None,False,1),
])
def test_frozen_decisions(raw,retry,expected,text,used,calls):
    reader=Sequence([raw,retry]);p=EnrichmentProcessor(None,FakeLocalizer(),reader,.7,.75)
    result=p._plate(np.arange(40*60*3,dtype=np.uint8).reshape(40,60,3),None)
    assert result["ocr_confidence"]==expected and result.get("text")==text
    assert result["used_enhancement"]==used and len(reader.calls)==calls
def test_exact_legacy_enhancement_pixels():
    image=np.arange(17*39*3,dtype=np.uint8).reshape(17,39,3);s=max(1,min(4,64/17))
    expected=cv2.resize(image,(round(39*s),round(17*s)),interpolation=cv2.INTER_CUBIC)
    expected=cv2.cvtColor(expected,cv2.COLOR_BGR2GRAY)
    expected=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8)).apply(expected)
    expected=cv2.copyMakeBorder(expected,8,8,8,8,cv2.BORDER_REPLICATE)
    expected=cv2.cvtColor(expected,cv2.COLOR_GRAY2BGR)
    assert np.array_equal(conservative_enhance(image),expected)
    assert rectify_plate(np.zeros((20,40,3),np.uint8)).shape==(20,40,3)
