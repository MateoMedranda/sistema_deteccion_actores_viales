from fractions import Fraction
import av, cv2, numpy as np
from app.adapters.timed_video_decoder import TimedVideoDecoder


def test_tagged_colored_input_preserves_approved_opencv_pixels(tmp_path):
    path = tmp_path / "bt709.mp4"
    with av.open(str(path), "w") as out:
        stream = out.add_stream("libx264", rate=30)
        stream.width = 64
        stream.height = 48
        stream.pix_fmt = "yuv420p"
        stream.codec_context.colorspace = 1
        stream.codec_context.color_primaries = 1
        stream.codec_context.color_trc = 1
        stream.options = {"crf": "0", "preset": "ultrafast"}
        y, x = np.indices((48, 64))
        image = np.stack((x * 3, y * 5, (x + y) * 2), axis=2).astype(np.uint8)
        for i in range(4):
            frame = av.VideoFrame.from_ndarray(image, format="bgr24")
            frame.pts = i
            frame.time_base = Fraction(1, 30)
            frame.colorspace = 1
            for packet in stream.encode(frame):
                out.mux(packet)
        for packet in stream.encode():
            out.mux(packet)
    cap = cv2.VideoCapture(str(path))
    for f in TimedVideoDecoder(path):
        ok, reference = cap.read()
        assert ok and np.array_equal(f.image, reference)
    cap.release()
