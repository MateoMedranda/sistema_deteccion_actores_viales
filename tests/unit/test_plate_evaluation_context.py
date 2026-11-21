import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
from scripts.evaluate_plate_profiles import freeze_run
from tests.unit.test_plate_evaluation import manifest

def hardware(monkeypatch):
    import scripts.evaluate_plate_profiles as module
    gpu={"index":0,"name":"Synthetic GPU","memory_bytes":12345,"capability":"9.0"}
    monkeypatch.setattr(module,"cuda_inventory",lambda:[dict(gpu)],raising=False)
    monkeypatch.setattr(module,"cuda_identity",lambda index:dict(gpu),raising=False)
    return module

@pytest.mark.parametrize("localizer",["cpu","cuda:0"])
def test_effective_devices_are_observed_per_stage(tmp_path,monkeypatch,localizer):
    module=hardware(monkeypatch)
    run,*_=fixture_run(tmp_path)
    tracker=module.DeviceObservations(run)
    for stage,device in (("detector","cpu"),("localizer",localizer),("ocr","cpu")):
        call=tracker.wrap(stage,lambda:None,lambda device=device:device,initialized=stage=="ocr")
        call()
    frozen=tracker.finish()
    info=frozen.public_context()["conditions"]["accelerator"]
    assert info["requested"]=={"detector":"cpu","localizer":"auto","ocr":"cpu"}
    assert info["effective_devices"]["localizer"]["device"]==localizer
    assert info["effective_devices"]["localizer"]["calls"]==1
    assert info["effective_devices"]["detector"]["device"]=="cpu"
    assert json.loads(run.conditions_json)["accelerator"]["effective_devices"]=={}
    if localizer=="cuda:0":
        assert info["effective_devices"]["localizer"]["accelerator"]["name"]=="Synthetic GPU"

@pytest.mark.parametrize("stage",["detector","ocr"])
def test_requested_cpu_rejects_observed_cuda(tmp_path,monkeypatch,stage):
    module=hardware(monkeypatch);run,*_=fixture_run(tmp_path)
    tracker=module.DeviceObservations(run)
    call=tracker.wrap(stage,lambda:None,lambda:"cuda:0")
    with pytest.raises(ValueError,match="evaluation_device"):call()
    with pytest.raises(ValueError,match="evaluation_device"):tracker.finish()

def test_observed_device_cannot_change_mid_run(tmp_path,monkeypatch):
    module=hardware(monkeypatch);run,*_=fixture_run(tmp_path)
    tracker=module.DeviceObservations(run);device=["cuda:0"]
    call=tracker.wrap("localizer",lambda:None,lambda:device[0])
    call();device[0]="cpu"
    with pytest.raises(ValueError,match="evaluation_device"):call()
    with pytest.raises(ValueError,match="evaluation_device"):tracker.finish()

def test_changed_hardware_identity_invalidates_the_frozen_run(tmp_path,monkeypatch):
    module=hardware(monkeypatch);run,*_=fixture_run(tmp_path)
    tracker=module.DeviceObservations(run)
    call=tracker.wrap("localizer",lambda:None,lambda:"cuda:0")
    call()
    monkeypatch.setattr(module,"cuda_identity",lambda index:{"index":0,"name":"Other GPU","memory_bytes":12345,"capability":"9.0"})
    with pytest.raises(ValueError,match="evaluation_device"):call()
    with pytest.raises(ValueError,match="evaluation_device"):tracker.finish()

def test_unavailable_identity_and_private_device_strings_are_rejected(tmp_path,monkeypatch):
    module=hardware(monkeypatch);run,*_=fixture_run(tmp_path)
    for device in ("cuda:9","SECRET/private/model",None):
        tracker=module.DeviceObservations(run)
        with pytest.raises(ValueError,match="evaluation_device"):
            tracker.wrap("localizer",lambda:None,lambda:device)()
        with pytest.raises(ValueError):tracker.finish()

def test_unused_lazy_models_are_reported_as_not_executed(tmp_path,monkeypatch):
    module=hardware(monkeypatch);run,*_=fixture_run(tmp_path)
    tracker=module.DeviceObservations(run)
    for stage in ("detector","localizer"):
        tracker.wrap(stage,lambda:None,lambda:None)
    tracker.wrap("ocr",lambda:None,lambda:"cpu",initialized=True)
    actual=tracker.finish().public_context()["conditions"]["accelerator"]["effective_devices"]
    assert actual["localizer"]=={"device":None,"status":"not_executed","calls":0}
    assert actual["ocr"]["device"]=="cpu" and actual["ocr"]["calls"]==0

@pytest.mark.parametrize("nested_hook",[False,True])
def test_paddle_capture_observes_created_predictors_and_detects_replacement(monkeypatch,nested_hook):
    import sys
    import scripts.evaluate_plate_profiles as module
    factory=lambda config:object()
    inference=NS(create_predictor=factory)
    monkeypatch.setitem(sys.modules,"paddle",NS(inference=inference))
    class Reader:
        def __init__(self,language):
            self.ocr=NS()
            def create_components():
                for name in ("text_detector","text_recognizer","text_classifier"):
                    config=NS(use_gpu=lambda:False,use_xpu=lambda:False,
                              disable_mkldnn=lambda:None,switch_ir_optim=lambda enabled:None,enable_new_ir=lambda enabled:None)
                    setattr(self.ocr,name,NS(predictor=inference.create_predictor(config)))
            if nested_hook:
                from unittest.mock import patch
                from app.adapters.paddle_plate_reader import _cpu_predictor
                current=inference.create_predictor
                with patch.object(inference,"create_predictor",side_effect=lambda config:_cpu_predictor(current,config)):
                    create_components()
            else:create_components()
    reader,observed=module.load_observed_reader(Reader,"en")
    assert inference.create_predictor is factory
    assert observed()=="cpu"
    reader.ocr.text_classifier.predictor=object()
    with pytest.raises(ValueError,match="evaluation_device"):observed()

def fixture_run(tmp_path):
    m=manifest()
    for i,item in enumerate(m["samples"]):
        item["image"]="image-"+str(i)+".png"
        (tmp_path/item["image"]).write_bytes(b"synthetic"+bytes([i]))
    path=tmp_path/"SECRET-manifest.json";path.write_text(json.dumps(m),encoding="utf-8")
    detector=tmp_path/"detector.bin";detector.write_bytes(b"approved-detector")
    localizer=tmp_path/"localizer.bin";localizer.write_bytes(b"approved-localizer")
    profile=tmp_path/"profile.py";profile.write_text("frozen recipe")
    settings=NS(model_weights_path=detector,plate_model_weights_path=localizer,inference_device="cpu",model_confidence_threshold=.25,plate_localizer_threshold=.25,plate_ocr_retry_threshold=.7,plate_ocr_accept_threshold=.8)
    run=freeze_run(path,settings,profile_paths={"profile.py":profile})
    return run,path,detector,profile,settings

@pytest.mark.parametrize("changed",["manifest","model","profile","image"])
def test_frozen_run_rejects_changed_inputs(tmp_path,changed):
    run,path,detector,profile,settings=fixture_run(tmp_path)
    target={"manifest":path,"model":detector,"profile":profile,"image":tmp_path/"image-0.png"}[changed]
    target.write_bytes(target.read_bytes()+b"changed")
    with pytest.raises(ValueError,match="evaluation_inputs_changed"):run.assert_stable()
    assert run.manifest()["samples"][0]["reference"]=="ABC123"

def test_context_is_immutable_private_and_public_summary_is_safe(tmp_path):
    run,path,detector,profile,settings=fixture_run(tmp_path)
    with pytest.raises(FrozenInstanceError):run.run_id="other"
    assert run.run_id
    public=run.public_context()
    assert public["manifest_sha256"] and public["profile_source_sha256"]["profile.py"]
    assert public["conditions"]["versions"]["opencv"]
    assert public["conditions"]["accelerator"]["ocr_device"]=="cpu"
    data=json.dumps(public)
    assert run.run_id not in data and str(tmp_path) not in data and "ABC123" not in data and "SECRET" not in data
    edited=run.manifest();edited["samples"][0]["reference"]="ALTERED"
    assert run.manifest()["samples"][0]["reference"]=="ABC123"

def test_source_hash_is_from_the_bytes_parsed_not_a_later_read(tmp_path):
    import hashlib
    run,path,*_=fixture_run(tmp_path)
    expected=hashlib.sha256(path.read_bytes()).hexdigest()
    path.write_text(path.read_text()+" ",encoding="utf-8")
    assert run.public_context()["manifest_sha256"]==expected
    with pytest.raises(ValueError):run.assert_stable()

def test_context_rejects_changed_effective_thresholds(tmp_path):
    run,path,detector,profile,settings=fixture_run(tmp_path)
    settings.plate_ocr_accept_threshold=.99
    with pytest.raises(ValueError,match="evaluation_parameters_changed"):run.assert_settings(settings)

def test_accelerator_description_records_selected_gpu_without_paths(monkeypatch):
    import scripts.evaluate_plate_profiles as module
    fake=NS(cuda=NS(is_available=lambda:True,device_count=lambda:1,get_device_properties=lambda i:NS(name="Synthetic GPU",total_memory=12345,major=9,minor=0)),version=NS(cuda="synthetic-cuda"))
    monkeypatch.setitem(__import__("sys").modules,"torch",fake)
    result=module.accelerator_description("0")
    assert result["devices"]==[{"index":0,"name":"Synthetic GPU","memory_bytes":12345,"capability":"9.0"}]
    assert result["ocr_device"]=="cpu"
