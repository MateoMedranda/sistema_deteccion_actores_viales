"""Generate distinguishable synthetic pixels; no real vehicles, plates or models."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]/"frontend"/"e2e"/"fixtures"/"exploration"
def build(name,index,boxes):
    image=Image.new("RGB",(640,400),(232,238,244));draw=ImageDraw.Draw(image)
    detections=[];results=[];expected=[]
    for ordinal,b in enumerate(boxes):
        ident=(ordinal+1)*3
        seed=index*2+ordinal+1
        color=[25+(seed*37)%180,30+(seed*53)%180,35+(seed*71)%180]
        plate_color=[30+(seed*79)%180,35+(seed*41)%180,20+(seed*97)%180]
        x1,y1,x2,y2=b;w,h=x2-x1,y2-y1
        px1,py1,px2,py2=int(w*.2),int(h*.6),int(w*.8),int(h*.8)
        draw.rectangle((x1,y1,x2-1,y2-1),fill=tuple(color))
        draw.rectangle((x1+px1,y1+py1,x1+px2-1,y1+py2-1),fill=tuple(plate_color))
        box=dict(zip(("x_min","y_min","x_max","y_max"),b))
        detections.append(dict(detection_id=ident,class_id=0,class_name="car",confidence=.95,enrichment_eligible=True,bbox=box))
        status=["read","unreadable","not_detected","failed"][(index*2+ordinal)%4]
        plate={"status":status,"text":"SYN"+str(seed) if status=="read" else "PRIVATE_CANARY","used_enhancement":False}
        if status!="not_detected":plate["bbox_relative"]={"x_min":px1/w,"y_min":py1/h,"x_max":px2/w,"y_max":py2/h}
        label="Vehicle-"+str(index)+"-"+str(ident)
        results.append(dict(vehicle_key="detection-"+str(ident),detection_id=ident,track_id=None,class_id=0,class_name="car",attributes_status="completed",attributes=[dict(name="model",label=label,confidence=.9)],plate_status=status,plate=plate))
        expected.append(dict(id=ident,label=label,color=color,plateColor=plate_color,width=w,height=h,plateWidth=px2-px1,plateHeight=py2-py1,status=status,text=plate["text"] if status=="read" else None))
    image.save(ROOT/(name+".png"))
    return dict(name=name,detections=detections,results=results,expected=expected)
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    scenes=[build("scene-"+str(i),i,[(20+i*2,30,220+i*2,250),(310,70+i,610,370+i)]) for i in range(10)]
    boxes=[(5+(i%8)*80,5+(i//8)*55,75+(i%8)*80,50+(i//8)*55) for i in range(55)]
    scenes.append(build("many",10,boxes))
    (ROOT/"manifest.json").write_text(json.dumps(scenes,indent=2),encoding="utf-8")
if __name__=="__main__":main()
