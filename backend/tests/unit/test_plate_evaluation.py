import pytest
from scripts.evaluate_plate_profiles import validate_manifest,metrics,gate,normalize_plate
def manifest():
 samples=[]
 for i in range(60):
    samples.append(dict(id=str(i),split="test",group_id="g"+str(i),scene_id="scene"+str(i),image="private"+str(i)+".png",detection_id=1,vehicle_bbox=[0,0,20,20],reference="ABC123",reference_verified=True,verification_source="independent-review",stratum="degraded" if i<30 else "control"))
 return dict(version=1,associations_frozen=True,reference_independent=True,samples=samples)
def test_split_leakage_and_count_denominators():
 m=manifest();assert len(validate_manifest(m))==60
 bad=manifest();bad["samples"].append({**bad["samples"][0],"id":"adjust","split":"adjust"})
 with pytest.raises(ValueError):validate_manifest(bad)
 with pytest.raises(ValueError):validate_manifest({**manifest(),"samples":manifest()["samples"][:59]})
def test_metrics_include_unaccepted_and_false_accepts_and_gate():
 truth=["ABC","XYZ","012"]
 a=metrics(truth,[{"status":"read","text":"ABC"},{"status":"failed"},{"status":"read","text":"O12"}])
 assert a["total"]==3 and a["correct"]==1 and a["false_accepted"]==1
 assert a["character_errors"]==4 and a["reference_characters"]==9
 b=metrics(truth,[{"status":"read","text":s} for s in truth])
 assert gate({"all":a,"degraded":a},{"all":b,"degraded":b})
 assert not gate({"all":b,"degraded":b},{"all":b,"degraded":b})
 assert normalize_plate("ａｂ c-01")=="ABC01" and normalize_plate("O0I1")=="O0I1"

def test_end_to_end_evaluator_keeps_every_failure_and_public_report_aggregate(tmp_path):
 import json,numpy as np
 from PIL import Image
 from app.core.config import Settings
 from tests.conftest import FakeDetector
 from tests.enrichment_fixtures import FakeLocalizer,FakeReader
 from scripts.evaluate_plate_profiles import evaluate
 m=manifest()
 for sample in m["samples"]:
  sample["vehicle_bbox"]=[5,5,30,30]
  sample["image"]=str(tmp_path/(sample["id"]+".png"))
  Image.fromarray(np.indices((40,40)).sum(axis=0).astype(np.uint8)).save(sample["image"])
 m["samples"][0]["detection_id"]=999
 result=evaluate(m,tmp_path/"private.json",Settings(_env_file=None),FakeDetector(),FakeLocalizer(),FakeReader())
 assert result["test_samples"]==60 and not result["gate_pass"]
 assert result["arms"]["baseline-v1"]["all"]["states"]["failed"]==1
 report=json.dumps(result)
 assert "ABC123" not in report and "SYN123" not in report and str(tmp_path) not in report

def test_cli_failure_never_prints_private_path_or_reference(tmp_path,capsys):
 from scripts.evaluate_plate_profiles import main
 private=tmp_path/"SECRET_REFERENCE_CANARY.json"
 private.write_text('{"secret":"PRIVATE_TEXT"}')
 assert main(["--manifest",str(private),"--output",str(tmp_path/"out.json")])==2
 output=capsys.readouterr()
 assert "SECRET_REFERENCE" not in output.err and "PRIVATE_TEXT" not in output.err
 assert not (tmp_path/"out.json").exists()
