"""Timestamp-bearing decode; never estimate VFR timestamps from nominal FPS."""

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import av
from av.video.reformatter import VideoReformatter, Colorspace, Interpolation
import numpy as np


@dataclass(frozen=True)
class TimedFrame:
    frame_index: int
    pts: int
    time_base: Fraction
    start_us: int
    end_us: int
    image: np.ndarray


def frame_to_bgr(frame, reformatter):
    """Approved ITU601/BICUBIC conversion and orientation, shared without model imports."""
    # Preserve the approved OpenCV/FFmpeg conversion, including tagged BT.709 sources.
    image = reformatter.reformat(
        frame,
        format="bgr24",
        src_colorspace=Colorspace.ITU601,
        dst_colorspace=Colorspace.ITU601,
        interpolation=Interpolation.BICUBIC,
    ).to_ndarray()
    rotation = int(round(getattr(frame, "rotation", 0) or 0)) % 360
    if rotation:
        if rotation not in (90, 180, 270):
            raise ValueError("timeline_unrepresentable")
        image = np.rot90(image, rotation // 90).copy()
    return image


class TimedVideoDecoder:
    def __init__(self, path: Path):
        self.path = path
        self.timeline = None

    def __iter__(self):
        with av.open(str(self.path)) as container:
            stream = container.streams.video[0]
            origin = stream.start_time or 0
            base = Fraction(stream.time_base)
            reformatter = VideoReformatter()
            pending = None
            index = 0
            for frame in container.decode(stream):
                if frame.pts is None:
                    raise ValueError("timeline_unrepresentable")
                tb = Fraction(frame.time_base)
                start = round((frame.pts * tb - origin * base) * 1_000_000)
                if start < 0:  # preroll is not a presentation interval
                    continue
                image = frame_to_bgr(frame, reformatter)
                h, w = image.shape[:2]
                if self.timeline is None:
                    self.timeline = dict(
                        timebase="source-pts",
                        width=w,
                        height=h,
                        display_width=w,
                        display_height=h,
                        pixel_to_display=[1, 0, 0, 1, 0, 0],
                        duration_us=None,
                        duration_confirmed=False,
                        pts_origin=str(origin),
                        time_base_num=base.numerator,
                        time_base_den=base.denominator,
                        playback_offset_us=0,
                    )
                if pending:
                    if start <= pending[3]:
                        raise ValueError("timeline_unrepresentable")
                    yield TimedFrame(*pending[:3], pending[3], start, pending[4])
                duration = int(getattr(frame, "duration", 0) or 0)
                pending = (index, frame.pts, tb, start, image)
                last_duration = round(duration * tb * 1_000_000)
                index += 1
            if pending:
                end = pending[3] + last_duration
                if last_duration <= 0 and stream.duration is not None:
                    end = round(stream.duration * base * 1_000_000)
                if end <= pending[3]:
                    raise ValueError("timeline_unrepresentable")
                yield TimedFrame(*pending[:3], pending[3], end, pending[4])
