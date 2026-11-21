"""007-only counted adapters. Marker pixels occur only in our synthetic fixtures."""
import json
from pathlib import Path
from app.domain.models import Detection
from app.adapters.plate_localizer_protocol import PlateLocation
from app.adapters.plate_reader_protocol import PlateReading
from tests.image_exploration_fixtures import SceneDetector
from tests.enrichment_fixtures import FakeReader,FakeAttributes
from threading import local
MODE=local()
COUNTS={"detection":0,"localization":0,"ocr":0,"attributes":0}
class AnnotationAttributes(FakeAttributes):
    def extract(self,crop):COUNTS["attributes"]+=1;return super().extract(crop)
def marked(image,value):
    return image is not None and image.ndim==3 and int(image[0,0,0])==value and int(image[0,0,2])==value
class AnnotationDetector(SceneDetector):
    def detect(self,image):
        COUNTS["detection"]+=1
        if image.shape[:2]==(600,960) and int(image[-1,-1,0])==7 and int(image[-1,-1,2])==7:
            index=int(image[-1,-1,1])
            root=Path(__file__).resolve().parents[2]/"frontend/e2e/fixtures/annotations/manifest.json"
            scene=json.loads(root.read_text())[index]
            return [Detection(d["class_id"],d["class_name"],d["confidence"],**d["bbox"]) for d in scene["detections"]]
        return super().detect(image)
class AnnotationLocalizer:
    def locate(self,crop):
        COUNTS["localization"]+=1
        h,w=crop.shape[:2]
        MODE.value=0
        if marked(crop,7):
            ordinal=int(crop[0,0,1]);MODE.value=ordinal%4
            if ordinal%4==3:return None
            return PlateLocation(w//4,h*2//3,w*3//4,h*5//6,.95)
        return PlateLocation(int(w*.12),int(h*.65),int(w*.52),int(h*.82),.95)
class AnnotationReader(FakeReader):
    def read(self,crop):
        COUNTS["ocr"]+=1
        if getattr(MODE,"value",0)==1:return None
        if marked(crop,8):
            ordinal=int(crop[0,0,1])
            if ordinal%4==1:return None
            if ordinal%4==2:raise RuntimeError("synthetic_failure")
        # Legacy fixtures retain the legacy returned value and modest delay.
        import time
        if not marked(crop,8):time.sleep(.05)
        return super().read(crop)
