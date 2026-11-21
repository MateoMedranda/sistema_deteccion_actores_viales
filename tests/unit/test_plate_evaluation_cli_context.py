import json
from types import SimpleNamespace as NS
import pytest
from scripts import evaluate_plate_profiles as module
from tests.unit.test_plate_evaluation_context import fixture_run,hardware

@pytest.mark.parametrize("change",["none","mixed","device","missing-device","not-called","manifest","profile","model","image","threshold"])
def test_cli_uses_frozen_context_and_never_exports_private_identity(tmp_path,monkeypatch,capsys,change):
    hardware(monkeypatch)
    _,manifest,detector,profile,settings=fixture_run(tmp_path)
    settings.ultralytics_path=None;settings.paddle_ocr_lang="en"
    import app.core.config as config
    import app.adapters.yolov10_detector as detection
    import app.adapters.yolov8_plate_localizer as localization
    import app.adapters.paddle_plate_reader as reading
    monkeypatch.setattr(config,"Settings",lambda:settings)
    calls=[]
    def adapter(name,obj):
        def load(*args):calls.append(name);return obj
        return load
    directories={}
    for stage in ("det","rec","cls"):
        p=tmp_path/stage;p.mkdir();(p/"inference.pdmodel").write_bytes(b"approved")
        directories[stage+"_model_dir"]=str(p)
    detector_adapter=NS(_model=NS(predictor=NS(device="cpu")),detect=lambda image:[])
    localizer_adapter=NS(model=NS(predictor=NS(device="cuda:0" if change=="mixed" else "cpu")),locate=lambda image:None)
    reader=NS(ocr=NS(args=NS(**directories,rec_char_dict_path=None)),read=lambda image:None)
    monkeypatch.setattr(detection,"YOLOv10Detector",adapter("detector",detector_adapter))
    monkeypatch.setattr(localization,"YOLOv8PlateLocalizer",adapter("localizer",localizer_adapter))
    monkeypatch.setattr(reading,"PaddlePlateReader",adapter("reader",reader))
    def observed_reader(factory,language):return factory(language),lambda:"cpu"
    monkeypatch.setattr(module,"load_observed_reader",observed_reader,raising=False)
    freeze=module.freeze_run;identities=[]
    def frozen(path,current):
        run=freeze(path,current,profile_paths={"profile.py":profile});identities.append(run.run_id);return run
    monkeypatch.setattr(module,"freeze_run",frozen)
    def evaluate(manifest_data,path,current,detector_proxy,localizer_proxy,reader_proxy):
        if change!="not-called":
            detector_proxy.detect(None)
            if change=="missing-device":localizer_adapter.model.predictor.device=None
            localizer_proxy.locate(None);reader_proxy.read(None)
        if change=="device":detector_adapter._model.predictor.device="cuda:0"
        elif change=="threshold":settings.plate_ocr_accept_threshold=.99
        elif change in ("manifest","profile","model","image"):
            target={"manifest":manifest,"profile":profile,"model":detector,"image":tmp_path/"image-0.png"}[change]
            target.write_bytes(target.read_bytes()+b"changed")
        return {"gate_pass":False,"test_samples":60}
    monkeypatch.setattr(module,"evaluate",evaluate)
    output=tmp_path/"aggregate.json"
    status=module.main(["--manifest",str(manifest),"--output",str(output)])
    assert calls==["detector","localizer","reader"]
    captured=capsys.readouterr()
    assert str(tmp_path) not in captured.err and "ABC123" not in captured.out
    if change in ("none","mixed","not-called"):
        assert status==0
        data=output.read_text();result=json.loads(data)
        assert result["status"]=="FAIL" and result["policy_promoted"] is False
        assert result["conditions"]["versions"]["opencv"]
        assert "ocr_rec" in result["model_sha256"]
        assert identities[0] not in data and str(tmp_path) not in data and "ABC123" not in data
        actual=result["conditions"]["accelerator"]["effective_devices"]
        if change=="not-called":
            assert actual["localizer"]["device"] is None and actual["localizer"]["status"]=="not_executed"
        else:
            assert actual["localizer"]["device"]==("cuda:0" if change=="mixed" else "cpu")
            assert actual["detector"]["device"]==actual["ocr"]["device"]=="cpu"
            assert actual["localizer"]["calls"]==1
            if change=="mixed":assert actual["localizer"]["accelerator"]["name"]=="Synthetic GPU"
    else:assert status==2 and not output.exists()
