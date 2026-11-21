"""Synthetic evidence with no personal information."""
from io import BytesIO
from PIL import Image, ImageDraw
from app.domain.models import Detection

def scene_bytes(orientation: int = 1, size=(640, 400)) -> bytes:
    image = Image.new("RGB", size, "#dce4ea")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 25, 290, 300), fill="#27485d")
    draw.rectangle((340, 45, 610, 330), fill="#b19d7d")
    draw.rectangle((50, 220, 140, 250), fill="white")
    draw.rectangle((370, 250, 460, 280), fill="white")
    exif = Image.Exif()
    exif[274] = orientation
    output = BytesIO()
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()

class SceneDetector:
    model_name = "synthetic-scene"
    def detect(self, image):
        h, w = image.shape[:2]
        return [
            Detection(0, "car", .96, int(w*.03), int(h*.06), int(w*.46), int(h*.76)),
            Detection(1, "truck", .91, int(w*.53), int(h*.11), int(w*.96), int(h*.84)),
            Detection(2, "person", .88, int(w*.47), int(h*.07), int(w*.52), int(h*.42)),
        ]
