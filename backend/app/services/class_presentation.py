import json
from importlib.resources import files
REGISTRY=json.loads(files("app.domain").joinpath("class_presentation.json").read_text(encoding="utf-8"))
def class_presentation(name):
    key=name.strip().lower();known=key in REGISTRY["classes"]
    entry=REGISTRY["classes"].get(key,{"label":name,"color":REGISTRY["fallback_color"]})
    color=entry["color"];rgb=tuple(int(color[i:i+2],16) for i in (1,3,5))
    return {**entry,"key":key,"known":known,"bgr":rgb[::-1]}
