"""Synthetic videos; no personal media or recognition-accuracy claims."""

from fractions import Fraction
import av
import numpy as np


def video(path, times=None, width=64, height=48, lossless=True):
    times = times or [Fraction(i, 10) for i in range(12)]
    with av.open(str(path), "w") as out:
        stream = out.add_stream("libx264", rate=30)
        stream.width, stream.height, stream.pix_fmt = width, height, "yuv420p"
        stream.time_base = Fraction(1, 90000)
        stream.options = {"crf": "0" if lossless else "18", "preset": "ultrafast", **({} if lossless else {"profile":"baseline"})}
        for i, time in enumerate(times):
            image = np.full((height, width, 3), i * 12 % 255, dtype=np.uint8)
            frame = av.VideoFrame.from_ndarray(image, format="bgr24")
            frame.pts, frame.time_base = int(time * 90000), Fraction(1, 90000)
            for packet in stream.encode(frame):
                out.mux(packet)
        for packet in stream.encode():
            out.mux(packet)
    return path
