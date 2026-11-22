from app.services.class_presentation import class_presentation,REGISTRY
def test_palette_preserves_007_and_unknown():
 assert len(REGISTRY["classes"])==13
 assert class_presentation(" CAR ")["color"]=="#2563EB"
 assert class_presentation("<unknown>")["color"]=="#64748B"
 assert class_presentation("truck")["bgr"]==(6,119,217)
