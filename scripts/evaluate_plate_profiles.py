"""Offline, paired OCR evaluation. Public output contains aggregates only.

Manifest stays private. Every test sample needs id, split, group_id, scene_id,
image, detection_id, vehicle_bbox [x1,y1,x2,y2], reference, reference_verified,
verification_source, stratum (degraded|control). Groups/scenes cannot cross splits.
Production continues to compose BaselinePolicy; this script cannot promote it.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from contextlib import redirect_stdout,redirect_stderr
from datetime import UTC,datetime
import hashlib
from importlib.metadata import version
from io import BytesIO
import json
import math
import os
from pathlib import Path
import platform
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
import cv2
import numpy as np
from PIL import Image,ImageOps
import psutil

# Running the file directly must resolve the existing app, without installation.
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app.services.plate_reading_policy import BaselinePolicy,CandidateRescuePolicy,normalize_plate
from app.services.plate_profiles import rescue_profile
from app.services.plate_quality import conservative_enhance,rectify_plate
NORMALIZATION="NFKC-uppercase-remove-whitespace-and-ASCII-hyphen-v1"
def validate_manifest(manifest):
    if manifest.get("version")!=1 or manifest.get("associations_frozen") is not True or manifest.get("reference_independent") is not True:raise ValueError("manifest_not_frozen")
    samples=manifest.get("samples")
    if not isinstance(samples,list):raise ValueError("invalid_samples")
    identities=set();groups={};scenes={};images={};associations=set();test=[]
    for item in samples:
        if not isinstance(item,dict):raise ValueError("invalid_sample")
        for field in ("id","group_id","scene_id","image","reference","verification_source"):
            if not isinstance(item.get(field),str) or not item[field].strip():raise ValueError("missing_reference")
        if item["id"] in identities:raise ValueError("duplicate_identity")
        identities.add(item["id"]);split=item.get("split")
        if split not in ("adjust","test") or item.get("stratum") not in ("degraded","control") or item.get("reference_verified") is not True or not normalize_plate(item["reference"]):raise ValueError("invalid_reference")
        for registry,key in ((groups,item["group_id"]),(scenes,item["scene_id"]),(images,os.path.normcase(os.path.normpath(item["image"])))):
            if key in registry and registry[key]!=split:raise ValueError("split_leakage")
            registry[key]=split
        detection_id=item.get("detection_id")
        if type(detection_id) is not int or detection_id<1:raise ValueError("invalid_association")
        identity=(os.path.normcase(os.path.normpath(item["image"])),detection_id)
        if identity in associations:raise ValueError("duplicate_association")
        associations.add(identity)
        bbox=item.get("vehicle_bbox")
        if not isinstance(bbox,list) or len(bbox)!=4 or not all(type(v) is int and v>=0 for v in bbox) or bbox[2]<=bbox[0] or bbox[3]<=bbox[1]:raise ValueError("invalid_reference_geometry")
        if split=="test":test.append(item)
    strata=Counter(s["stratum"] for s in test)
    if len(test)<60 or strata["degraded"]<30 or strata["control"]<30:raise ValueError("insufficient_holdout")
    return samples
def distance(a,b):
    previous=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        current=[i]
        for j,cb in enumerate(b,1):current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(ca!=cb)))
        previous=current
    return previous[-1]
def metrics(references,predictions):
    if len(references)!=len(predictions) or not references:raise ValueError("invalid_denominator")
    correct=false=read=errors=chars=0;states=Counter()
    for reference,prediction in zip(references,predictions):
        truth=normalize_plate(reference)
        accepted=prediction.get("status")=="read" and bool(prediction.get("text"))
        text=normalize_plate(prediction["text"]) if accepted else ""
        correct+=int(accepted and text==truth);false+=int(accepted and text!=truth);read+=int(accepted)
        errors+=distance(truth,text);chars+=len(truth);states[prediction.get("status","failed")]+=1
    total=len(references)
    return dict(total=total,correct=correct,accuracy=correct/total,false_accepted=false,false_accepted_rate=false/total,read=read,coverage=read/total,character_errors=errors,reference_characters=chars,cer=errors/chars,states=dict(states))
def gate(baseline,candidate):
    a,b=baseline["all"],candidate["all"]
    ad,bd=baseline["degraded"],candidate["degraded"]
    # Count arithmetic avoids accepting/rejecting the exact 5pp boundary by roundoff.
    gain=bd["correct"]*ad["total"]-ad["correct"]*bd["total"]
    return (gain*20>=ad["total"]*bd["total"] and b["correct"]*a["total"]>=a["correct"]*b["total"] and b["false_accepted"]<=a["false_accepted"] and b["character_errors"]*a["reference_characters"]<=a["character_errors"]*b["reference_characters"])
def percentile(values,fraction):
    return sorted(values)[max(0,math.ceil(len(values)*fraction)-1)] if values else 0
def sha(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):digest.update(chunk)
    return digest.hexdigest()
def _iou(actual,reference):
    x1,y1,x2,y2=actual;a,b,c,d=reference
    intersection=max(0,min(x2,c)-max(x1,a))*max(0,min(y2,d)-max(y1,b))
    return intersection/((x2-x1)*(y2-y1)+(c-a)*(d-b)-intersection)
def ocr_hashes(reader):
    args=getattr(reader.ocr,"args",None)
    hashes={}
    for stage in ("det","rec","cls"):
        directory=getattr(args,stage+"_model_dir",None)
        if not directory or not Path(directory).is_dir():raise ValueError("ocr_model_hash_unavailable")
        files=sorted(p for p in Path(directory).rglob("*") if p.is_file() and p.suffix in (".pdmodel",".pdiparams",".json"))
        if not files:raise ValueError("ocr_model_hash_unavailable")
        digest=hashlib.sha256()
        for file in files:digest.update(file.name.encode());digest.update(bytes.fromhex(sha(file)))
        hashes["ocr_"+stage]=digest.hexdigest()
    dictionary=getattr(args,"rec_char_dict_path",None)
    if dictionary and Path(dictionary).is_file():hashes["ocr_dictionary"]=sha(dictionary)
    return hashes
def canonical(path,max_pixels):
    with Image.open(path) as image:
        if image.width*image.height>max_pixels:raise ValueError("image_limit")
        original=ImageOps.exif_transpose(image).convert("RGB")
        return cv2.cvtColor(np.asarray(original),cv2.COLOR_RGB2BGR)
def evaluate(manifest,manifest_path,settings,detector,localizer,reader):
    from app.services.image_geometry import canonical_detections,clip_box
    from app.services.source_artifacts import SourceArtifactStore
    from app.services.inference_metrics import InferenceMetrics
    import logging
    test=[s for s in validate_manifest(manifest) if s["split"]=="test"]
    groups=defaultdict(list)
    for sample in test:groups[sample["group_id"]].append(sample)
    policies={"baseline-v1":BaselinePolicy(),"candidate-rescue-v1":CandidateRescuePolicy()}
    refs=[];strata=[];predictions={p:[] for p in policies};times={p:[] for p in policies};attempts={p:[] for p in policies};selected={p:Counter() for p in policies}
    shared_ms=[];calls=0;started=perf_counter()
    class CounterReader:
        def __call__(self,image):
            nonlocal calls
            calls+=1;return reader.read(image)
    counted=CounterReader()
    # All intermediate files/stores are isolated, removed even on error.
    with TemporaryDirectory(prefix="plate-evaluation-") as temporary:
        artifacts=SourceArtifactStore(Path(temporary)/"sources")
        try:
            for group_index,items in enumerate(groups.values()):
                for sample in items:
                    shared_start=perf_counter();crop=None
                    try:
                        path=Path(sample["image"]);path=path if path.is_absolute() else manifest_path.parent/path
                        image=canonical(path,settings.max_image_pixels)
                        detections=canonical_detections(detector.detect(image),image.shape[1],image.shape[0])
                        ordinal=sample["detection_id"]-1
                        if ordinal>=len(detections):raise ValueError("missed_detection")
                        d=detections[ordinal];actual=(d.x_min,d.y_min,d.x_max,d.y_max)
                        if d.class_name.lower() not in settings.vehicle_class_set() or _iou(actual,sample["vehicle_bbox"])<.5:raise ValueError("association_failed")
                        vehicle=image[d.y_min:d.y_max,d.x_min:d.x_max].copy();del image
                        location=localizer.locate(vehicle)
                        if location is None:raise ValueError("not_localized")
                        box=clip_box(location.x_min,location.y_min,location.x_max,location.y_max,vehicle.shape[1],vehicle.shape[0])
                        if box is None:raise ValueError("not_localized")
                        x1,y1,x2,y2=box;crop=vehicle[y1:y2,x1:x2].copy();del vehicle
                    except Exception:crop=None
                    shared_ms.append((perf_counter()-shared_start)*1000)
                    outputs={}
                    order=list(policies) if group_index%2==0 else list(reversed(policies))
                    for name in order:
                        before=calls;t=perf_counter()
                        output=policies[name].read(crop.copy(),counted,settings.plate_ocr_retry_threshold,settings.plate_ocr_accept_threshold) if crop is not None else {"status":"failed","text":None}
                        outputs[name]=output;times[name].append((perf_counter()-t)*1000);attempts[name].append(calls-before)
                    refs.append(sample["reference"]);strata.append(sample["stratum"])
                    for name,output in outputs.items():
                        predictions[name].append(output)
                        selected[name][output.get("provenance",{}).get("selected_variant","none")]+=1
        finally:artifacts.close()
    summary={}
    for name in policies:
        summary[name]={}
        for stratum in ("all","degraded","control"):
            indexes=[i for i,s in enumerate(strata) if stratum=="all" or s==stratum]
            summary[name][stratum]=metrics([refs[i] for i in indexes],[predictions[name][i] for i in indexes])
        summary[name]["cost"]={"ocr_calls":sum(attempts[name]),"ocr_calls_per_plate":sum(attempts[name])/len(refs),"duration_ms":{"p50":percentile(times[name],.5),"p95":percentile(times[name],.95),"max":max(times[name]),"total":sum(times[name])},"selected_variants":dict(selected[name])}
    return {"arms":summary,"gate_pass":gate(summary["baseline-v1"],summary["candidate-rescue-v1"]),"test_samples":len(refs),"test_groups":len(groups),"shared_detection_localization_ms":{"total":sum(shared_ms),"p95":percentile(shared_ms,.95)},"total_duration_ms":(perf_counter()-started)*1000}

from dataclasses import dataclass,replace
_LOADED_PROFILE_INPUTS={name:sha(ROOT/"app/services"/name) for name in ("plate_profiles.py","plate_quality.py","plate_reading_policy.py")}
from uuid import uuid4

@dataclass(frozen=True)
class InputFingerprint:
    path:Path
    digest:str

@dataclass(frozen=True)
class EvaluationRun:
    """Private immutable run identity and exact input snapshot; never serialize wholesale."""
    run_id:str
    manifest_bytes:bytes
    inputs:tuple[InputFingerprint,...]
    profiles:tuple[tuple[str,str],...]
    models:tuple[tuple[str,str],...]
    conditions_json:str
    def manifest(self):
        return json.loads(self.manifest_bytes)
    def assert_stable(self):
        for item in self.inputs:
            try:stable=sha(item.path)==item.digest
            except OSError:stable=False
            if not stable:raise ValueError("evaluation_inputs_changed")
    def assert_settings(self,settings):
        if json.loads(self.conditions_json)["thresholds"]!=thresholds(settings) or json.loads(self.conditions_json)["device"]!=settings.inference_device:
            raise ValueError("evaluation_parameters_changed")
    def bind_ocr(self,reader):
        paths=[]
        args=getattr(reader.ocr,"args",None)
        for stage in ("det","rec","cls"):
            directory=getattr(args,stage+"_model_dir",None)
            if not directory:raise ValueError("ocr_model_hash_unavailable")
            files=sorted(p for p in Path(directory).rglob("*") if p.is_file() and p.suffix in (".pdmodel",".pdiparams",".json"))
            paths.extend(InputFingerprint(p.resolve(),sha(p)) for p in files)
        dictionary=getattr(args,"rec_char_dict_path",None)
        if dictionary:paths.append(InputFingerprint(Path(dictionary).resolve(),sha(dictionary)))
        result=replace(self,inputs=self.inputs+tuple(paths),models=self.models+tuple(sorted(ocr_hashes(reader).items())))
        result.assert_stable()
        return result
    def public_context(self):
        # A single input commitment adds no per-image identifier to the public report.
        commitment=hashlib.sha256("".join(item.digest for item in self.inputs).encode()).hexdigest()
        return dict(manifest_sha256=hashlib.sha256(self.manifest_bytes).hexdigest(),
                    profile_source_sha256=dict(self.profiles),model_sha256=dict(self.models),
                    input_commitment_sha256=commitment,normalization=NORMALIZATION,
                    conditions=json.loads(self.conditions_json))

def thresholds(settings):
    return dict(detector=settings.model_confidence_threshold,localizer=settings.plate_localizer_threshold,
                retry=settings.plate_ocr_retry_threshold,accept=settings.plate_ocr_accept_threshold)

def cuda_identity(index):
    import torch
    properties=torch.cuda.get_device_properties(index)
    return dict(index=index,name=properties.name,memory_bytes=properties.total_memory,capability=f"{properties.major}.{properties.minor}")

def cuda_inventory():
    import torch
    return [cuda_identity(index) for index in range(torch.cuda.device_count())] if torch.cuda.is_available() else []

def accelerator_description(device):
    # Freeze available hardware even for a CPU detector: the localizer uses auto.
    devices=cuda_inventory()
    requested=device.lower().strip()
    if requested=="cpu":selected="cpu"
    else:
        first=requested.removeprefix("cuda:").split(",")[0]
        if first in ("cuda",""):
            import torch
            first=str(torch.cuda.current_device())
        if not first.isdigit() or int(first) not in {entry["index"] for entry in devices}:
            raise ValueError("requested_accelerator_unavailable")
        selected="cuda:"+str(int(first))
    result=dict(detector_device=device,ocr_device="cpu",devices=devices,
                requested={"detector":selected,"localizer":"auto","ocr":"cpu"},
                selection_policy={"detector":"configured","localizer":"ultralytics-auto","ocr":"fixed-cpu"},
                effective_devices={})
    if devices:
        import torch
        result["cuda_runtime"]=torch.version.cuda
    return result

class DeviceObservations:
    """Bind a frozen selection policy to observed predictors, without moving models."""
    def __init__(self,run):
        self.run=run
        self.hardware=json.loads(run.conditions_json)["accelerator"]
        self.devices={};self.calls={};self.getters={};self.failed=False

    def _observe(self,stage,value):
        try:
            device=str(value).lower()
            if device!="cpu":
                import re
                if not re.fullmatch(r"cuda:[0-9]+",device):raise ValueError()
                index=int(device.split(":")[1]);device="cuda:"+str(index)
                frozen=next((entry for entry in self.hardware["devices"] if entry["index"]==index),None)
                if frozen is None or cuda_identity(index)!=frozen:raise ValueError()
            requested=self.hardware["requested"][stage]
            if requested!="auto" and requested!=device:raise ValueError()
            if stage in self.devices and self.devices[stage]!=device:raise ValueError()
            self.devices[stage]=device
        except Exception:
            self.failed=True
            raise ValueError("evaluation_device_unverified") from None

    def wrap(self,stage,operation,device,*,initialized=False):
        self.getters[stage]=device;self.calls[stage]=0
        if initialized:self._observe(stage,device())
        def call(*args,**kwargs):
            self.calls[stage]+=1
            try:return operation(*args,**kwargs)
            finally:
                try:self._observe(stage,device())
                except Exception:
                    self.failed=True
                    raise ValueError("evaluation_device_unverified") from None
        return call

    def finish(self):
        if self.failed or set(self.getters)!={"detector","localizer","ocr"}:
            raise ValueError("evaluation_device_unverified")
        for stage,getter in self.getters.items():
            if stage in self.devices:
                try:self._observe(stage,getter())
                except Exception:raise ValueError("evaluation_device_unverified") from None
        conditions=json.loads(self.run.conditions_json)
        effective={}
        for stage in self.getters:
            device=self.devices.get(stage)
            row=dict(device=device,status="executed" if self.calls[stage] else "initialized" if device else "not_executed",calls=self.calls[stage])
            if device and device.startswith("cuda:"):
                row["accelerator"]=next(entry for entry in self.hardware["devices"] if entry["index"]==int(device.split(":")[1]))
            effective[stage]=row
        conditions["accelerator"]["effective_devices"]=effective
        return replace(self.run,conditions_json=json.dumps(conditions,sort_keys=True))

def load_observed_reader(factory,language):
    # Observe the final configs actually passed to Paddle, including its CPU hook.
    # Some PaddleOCR components discard Config; predictor identity binds all three.
    from paddle import inference
    from unittest.mock import patch
    original=inference.create_predictor
    created={}
    def create(config):
        if config.use_xpu():raise ValueError("evaluation_device_unverified")
        device="cuda:"+str(config.gpu_device_id()) if config.use_gpu() else "cpu"
        predictor=original(config);created[id(predictor)]=(predictor,device)
        return predictor
    with patch.object(inference,"create_predictor",side_effect=create):
        reader=factory(language)
    def observed():
        devices=[]
        for name in ("text_detector","text_recognizer","text_classifier"):
            predictor=getattr(reader.ocr,name).predictor
            bound=created.get(id(predictor))
            if bound is None or bound[0] is not predictor:raise ValueError("evaluation_device_unverified")
            devices.append(bound[1])
        if len(set(devices))!=1:raise ValueError("evaluation_device_unverified")
        return devices[0]
    return reader,observed

def runtime_conditions(settings):
    dependencies=("numpy","pillow","fastapi","pydantic","psutil","paddleocr","paddlepaddle","ultralytics","torch")
    versions={name:version(name) for name in dependencies}
    versions["opencv"]=cv2.__version__
    return dict(python=platform.python_version(),system=platform.system(),processor=platform.processor(),
                logical_cpus=psutil.cpu_count(),ram_bytes=psutil.virtual_memory().total,
                device=settings.inference_device,accelerator=accelerator_description(settings.inference_device),
                concurrency=1,warmup="none; first call included",arm_order="alternating by group",
                thresholds=thresholds(settings),versions=versions)

def freeze_run(manifest_path,settings,*,profile_paths=None):
    manifest_path=Path(manifest_path).resolve()
    raw=manifest_path.read_bytes();manifest=json.loads(raw);validate_manifest(manifest)
    paths=profile_paths if profile_paths is not None else {
        name:ROOT/"app/services"/name for name in ("plate_profiles.py","plate_quality.py","plate_reading_policy.py")}
    paths={**paths,"evaluate_plate_profiles.py":Path(__file__).resolve()}
    profiles=tuple(sorted((name,sha(path)) for name,path in paths.items()))
    if profile_paths is None and any(dict(profiles)[name]!=digest for name,digest in _LOADED_PROFILE_INPUTS.items()):raise ValueError("evaluation_inputs_changed")
    inputs=[InputFingerprint(manifest_path,hashlib.sha256(raw).hexdigest())]
    inputs.extend(InputFingerprint(Path(paths[name]).resolve(),digest) for name,digest in profiles)
    models=[]
    for name,path in (("detector",settings.model_weights_path),("plate_localizer",settings.plate_model_weights_path)):
        if not path:raise ValueError("models_unavailable")
        fingerprint=InputFingerprint(Path(path).resolve(),sha(path))
        inputs.append(fingerprint);models.append((name,fingerprint.digest))
    # Freeze authorized original bytes as well as the private references.
    seen=set()
    for sample in manifest["samples"]:
        path=Path(sample["image"])
        path=(path if path.is_absolute() else manifest_path.parent/path).resolve()
        if path not in seen:
            seen.add(path);inputs.append(InputFingerprint(path,sha(path)))
    run=EvaluationRun(uuid4().hex,raw,tuple(inputs),profiles,tuple(models),json.dumps(runtime_conditions(settings),sort_keys=True))
    run.assert_stable()
    return run

def main(argv=None):
    parser=argparse.ArgumentParser(description="Paired private plate evaluation; no automatic promotion.")
    parser.add_argument("--manifest",required=True,type=Path);parser.add_argument("--baseline",choices=["baseline-v1"],default="baseline-v1")
    parser.add_argument("--candidate",choices=["candidate-rescue-v1"],default="candidate-rescue-v1");parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        manifest=json.loads(args.manifest.read_bytes());validate_manifest(manifest)
        from app.core.config import Settings
        from app.adapters.yolov10_detector import YOLOv10Detector
        from app.adapters.yolov8_plate_localizer import YOLOv8PlateLocalizer
        from app.adapters.paddle_plate_reader import PaddlePlateReader
        from app.services.inference_metrics import InferenceMetrics
        import logging
        settings=Settings()
        # Freeze exact bytes and conditions before model initialization/inference.
        with open(os.devnull,"w") as sink,redirect_stdout(sink),redirect_stderr(sink):
            run=freeze_run(args.manifest,settings)
            if args.output.resolve() in {item.path for item in run.inputs}:raise ValueError("output_overwrites_input")
            detector=YOLOv10Detector(settings.model_weights_path,settings.model_confidence_threshold,settings.inference_device,settings.ultralytics_path)
            localizer=YOLOv8PlateLocalizer(settings.plate_model_weights_path,settings.plate_localizer_threshold)
            reader,ocr_device=load_observed_reader(PaddlePlateReader,settings.paddle_ocr_lang)
            run=run.bind_ocr(reader)
            from types import SimpleNamespace
            observed=DeviceObservations(run)
            detector_proxy=SimpleNamespace(detect=observed.wrap("detector",detector.detect,lambda:detector._model.predictor.device))
            localizer_proxy=SimpleNamespace(locate=observed.wrap("localizer",localizer.locate,lambda:localizer.model.predictor.device))
            reader_proxy=SimpleNamespace(read=observed.wrap("ocr",reader.read,ocr_device,initialized=True))
            run.assert_stable();run.assert_settings(settings)
            with InferenceMetrics(logging.getLogger("offline-plate-evaluation"),"plate_evaluation") as measurement:
                result=evaluate(run.manifest(),args.manifest,settings,detector_proxy,localizer_proxy,reader_proxy)
            run=observed.finish()
            run.assert_stable();run.assert_settings(settings)
        result.update(protocol_version=1,status="PASS" if result["gate_pass"] else "FAIL",policy_promoted=False,
            **run.public_context(),
            process_rss_mb={"initial":measurement.initial_memory_mb,"final":psutil.Process().memory_info().rss/1024/1024,"peak":measurement._peak})
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2,ensure_ascii=True),encoding="utf-8")
        print("Evaluation complete: "+result["status"]+". Production policy unchanged.")
        return 0
    except Exception:
        print("Evaluation not completed: validate the private manifest, approved models and local resources. No policy was promoted.",file=sys.stderr)
        return 2
if __name__=="__main__":raise SystemExit(main())
