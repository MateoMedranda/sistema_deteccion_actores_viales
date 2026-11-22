"""Reproducible, synthetic annotation fixtures; no personal evidence."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3] / "frontend/e2e/fixtures/annotations"
CLASSES = "car truck bus van pickup suv sedan hatchback mpv estate person bicycle motorcycle unknown".split()
def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    scenes = []
    for scene in range(10):
        image = Image.new("RGB", (960, 600), "white" if scene % 2 else "black")
        draw = ImageDraw.Draw(image)
        detections, results = [], []
        count = 28 if scene < 3 else 14
        for i in range(count):
            ident = [1, 12, 123][i % 3] + (i // 3) * 150
            x, y = 10 + (i % 7)*135, 10 + (i // 7)*140
            w, h = (110, 100) if i % 4 else (24, 30)
            if scene==9 and i==1:x,y=10,10
            color = (30+(i*31+scene*17)%180, 40+(i*57)%180, 50+(scene*43+i*7)%180)
            draw.rectangle((x,y,x+w-1,y+h-1), fill=color)
            draw.point((x,y),fill=(7,i,7))
            draw.rectangle((x+w//4,y+h*2//3,x+w*3//4-1,y+h*5//6-1), fill="white")
            for p in range(w//2):
                if (p+scene+i)%3: draw.line((x+w//4+p,y+h*2//3,x+w//4+p,y+h*5//6-1),fill=(i*11%255,scene*19%255,60))
            draw.point((x+w//4,y+h*2//3),fill=(8,i,8))
            name=CLASSES[i%len(CLASSES)]
            eligible=name not in ("person","bicycle","motorcycle","unknown")
            detections.append(dict(detection_id=ident,class_id=i%14,class_name=name,confidence=.95,enrichment_eligible=eligible,bbox=dict(x_min=x,y_min=y,x_max=x+w,y_max=y+h)))
            if eligible:
                status=("read","unreadable","failed","not_detected")[i%4]
                plate=dict(status=status,text="SYN"+str(i) if status=="read" else None,used_enhancement=False,evidence_frame_indexes=[])
                if status!="not_detected":
                    plate["bbox_relative"]=dict(x_min=(w//4)/w,y_min=(h*2//3)/h,x_max=(w*3//4)/w,y_max=(h*5//6)/h)
                results.append(dict(vehicle_key=f"detection-{ident}",detection_id=ident,track_id=None,class_id=i%14,class_name=name,attributes_status="completed",attributes=[],plate_status=status,plate=plate))
        draw.point((959,599),fill=(7,scene,7))
        image.save(ROOT/f"scene-{scene}.png")
        annotated=image.copy(); labels=ImageDraw.Draw(annotated); labels.rectangle((0,0,960,120),fill="magenta"); labels.text((10,10),"ANNOTATED #1 #12 #123 #456",fill="black")
        annotated.save(ROOT/f"scene-{scene}-annotated.png")
        scenes.append(dict(name=f"scene-{scene}",width=960,height=600,detections=detections,results=results))
    (ROOT/"manifest.json").write_text(json.dumps(scenes,indent=2),encoding="utf-8")
if __name__=="__main__": main()
