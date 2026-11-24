import json
from types import SimpleNamespace
import numpy as np
import pytest
from app.adapters.yolov10_tracker import YOLOv10ByteTrackAdapter
from tests.unit.test_video_profile import profile
from app.services.video_profile import render_report


def test_native_phase_accounting_is_nested_and_does_not_double_count(tmp_path):
    now=[0.0]
    p=profile(tmp_path,lambda:now[0])
    class Boxes:
        def cpu(self):
            now[0]+=.003
            return self
        def numpy(self):
            now[0]+=.002
            return self
    class Model:
        names={0:"Car"}
        def predict(self,*args,**kwargs):
            now[0]+=.050
            return [SimpleNamespace(boxes=Boxes(),orig_img=args[0],
                speed=dict(preprocess=5.,inference=30.,postprocess=10.))]
    def update(*args):
        now[0]+=.007
        return [[10,10,30,30,1,.9,0,0]]
    tracker=YOLOv10ByteTrackAdapter(Model(),.25,"cpu")
    tracker._tracker=SimpleNamespace(update=update)
    for _ in range(2):tracker.track_profiled(np.zeros((48,64,3),np.uint8),p)
    p.frames=2
    p.end_analysis(complete=True)
    data=p.snapshot()
    detail=data["detection_breakdown"]
    assert detail["native_timing_calls"]==detail["recorded_calls"]==2
    assert detail["unrecorded_detection_calls"]==0
    assert detail["phases"]["preparation"]["total_ms"]==10
    assert detail["phases"]["inference"]["total_ms"]==60
    assert detail["phases"]["postprocessing"]["total_ms"]==20
    assert detail["boxes_transfer"]["total_ms"]==10
    assert detail["unattributed_detection_ms"]==pytest.approx(10)
    assert detail["phases"]["inference"]["mean_call_ms"]==30
    assert detail["phases"]["inference"]["ms_per_processed_frame"]==30
    assert data["stages"]["detection"]["total_ms"]==pytest.approx(110)
    assert data["analysis_wall_ms"]==pytest.approx(124)
    assert data["other_analysis_ms"]==pytest.approx(0)
    assert "Preparacion de entrada" in render_report(data)
    assert "Inferencia de la red" in render_report(data)


@pytest.mark.parametrize("speed,kind",[
    (None,"missing_native_timing_calls"),
    ({"preprocess":"SECRET_PATH","inference":2,"postprocess":3},"invalid_native_timing_calls"),
    ({"preprocess":1e308,"inference":1e308,"postprocess":1e308},"invalid_native_timing_calls"),
    ({"preprocess":1},"missing_native_timing_calls"),
    ({"preprocess":float("nan"),"inference":2,"postprocess":3},"invalid_native_timing_calls"),
    ({"preprocess":1,"inference":-1,"postprocess":3},"invalid_native_timing_calls"),
    ({"preprocess":1,"inference":"SECRET_PATH","postprocess":3},"invalid_native_timing_calls"),
])
def test_missing_or_invalid_native_timings_are_not_invented(tmp_path,speed,kind):
    now=[0.0]
    p=profile(tmp_path,lambda:now[0])
    with p.measure("detection"):now[0]+=.021
    p.record_detection(speed,20,1)
    detail=p.snapshot()["detection_breakdown"]
    assert detail[kind]==1 and detail["native_timing_calls"]==0
    assert detail["phases"]["inference"]["mean_call_ms"] is None
    assert detail["unattributed_detection_ms"]==pytest.approx(20)
    assert "SECRET_PATH" not in json.dumps(detail,allow_nan=False)


def test_native_wall_disagreement_is_reported_without_rescaling(tmp_path):
    now=[0.0]
    p=profile(tmp_path,lambda:now[0])
    with p.measure("detection"):now[0]+=.010
    p.record_detection(dict(preprocess=5,inference=10,postprocess=5),9,1)
    detail=p.snapshot()["detection_breakdown"]
    assert detail["native_exceeds_wall_calls"]==1
    assert detail["phases"]["inference"]["total_ms"]==10
    assert detail["overreported_ms"]==11
    assert detail["unattributed_detection_ms"]==0


def test_failed_prediction_remains_in_parent_and_is_explicitly_unrecorded(tmp_path):
    now=[0.0]
    p=profile(tmp_path,lambda:now[0])
    with pytest.raises(RuntimeError):
        with p.measure("detection"):
            now[0]+=.030
            raise RuntimeError("private error")
    detail=p.snapshot()["detection_breakdown"]
    assert detail["unrecorded_detection_calls"]==1
    assert detail["unattributed_detection_ms"]==pytest.approx(30)


def test_reader_keeps_old_profiles_compatible(tmp_path):
    data=profile(tmp_path).snapshot()
    data.pop("detection_breakdown",None)
    assert "FPS efectivos" in render_report(data)


def test_alternate_prediction_does_not_reuse_previous_native_speed(tmp_path):
    from tests.unit.test_detection_interval import MovingModel,image
    model=MovingModel()
    original=model.predict
    def predict(*args,**kwargs):
        result=original(*args,**kwargs)[0]
        result.speed=dict(preprocess=0,inference=0,postprocess=0)
        return [result]
    model.predict=predict
    tracker=YOLOv10ByteTrackAdapter(model,.25,"cpu")
    tracker.set_detection_interval(2)
    p=profile(tmp_path)
    for i in range(8):tracker.track_profiled(image(i),p)
    assert p.snapshot()["detection_breakdown"]["native_timing_calls"]==4
    assert p.stages["detection"]["calls"]==4


def test_speed_property_failure_does_not_change_a_prediction(tmp_path):
    from tests.unit.test_detection_interval import MovingModel,image
    model=MovingModel()
    original=model.predict
    class Result:
        def __init__(self,source):
            self.boxes,self.orig_img=source.boxes,source.orig_img
        @property
        def speed(self):raise RuntimeError("SECRET_PATH")
    model.predict=lambda *args,**kwargs:[Result(original(*args,**kwargs)[0])]
    tracker=YOLOv10ByteTrackAdapter(model,.25,"cpu")
    p=profile(tmp_path)
    assert len(tracker.track_profiled(image(0),p))==2
    data=p.snapshot()
    assert data["detection_breakdown"]["missing_native_timing_calls"]==1
    assert "SECRET_PATH" not in json.dumps(data)


def test_extreme_finite_telemetry_never_poison_json_percentages(tmp_path):
    now=[0.0]
    p=profile(tmp_path,lambda:now[0])
    with p.measure("detection"):now[0]+=.010
    p.record_detection(dict(preprocess=1e308,inference=0,postprocess=0),9,1)
    data=p.snapshot()
    assert data["detection_breakdown"]["native_exceeds_wall_calls"]==1
    assert data["detection_breakdown"]["phases"]["preparation"]["detection_percent"] is None
    json.dumps(data,allow_nan=False)
