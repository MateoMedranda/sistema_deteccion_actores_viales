import logging,json
from app.services.inference_metrics import InferenceMetrics
from app.core.logging import JsonFormatter
def test_explicit_safe_outcome_is_not_overwritten_by_exception(caplog):
    logger=logging.getLogger("preview-test")
    with caplog.at_level(logging.INFO,logger="preview-test"):
        try:
            with InferenceMetrics(logger,"plate_preview",request_id="safe",job_id="job",profile_id="display-contrast-v1") as m:
                m.status="expired";m.error_code="source_expired"
                raise ValueError("SECRET_PLATE_OR_PATH")
        except ValueError:pass
    record=caplog.records[-1];output=json.loads(JsonFormatter().format(record))
    assert output["status"]=="expired" and output["profile_id"]=="display-contrast-v1"
    assert output["peak_memory_mb"]>=output["initial_memory_mb"]
    assert "SECRET" not in json.dumps(output)

def test_rejected_publication_records_actual_expiry_not_completed(caplog):
 from datetime import UTC,datetime,timedelta
 from app.services.plate_preview_store import PlatePreviewStore,PreviewValue
 from app.api.error_handlers import ApiError
 import pytest,time
 logger=logging.getLogger("preview-test")
 expiry=datetime.now(UTC)+timedelta(seconds=30);store=PlatePreviewStore();calls=[]
 def validate():
  calls.append(1)
  if len(calls)>1:raise ApiError(410,"source_expired","safe")
 with caplog.at_level(logging.INFO,logger="preview-test"):
  c=store.acquire((1,),expiry,lambda check:PreviewValue(b"png","{}",expiry),validate,measure=lambda:InferenceMetrics(logger,"plate_preview",profile_id="display-contrast-v1"))
  with pytest.raises(ApiError):c.future.result(2)
  for _ in range(100):
   if caplog.records:break
   time.sleep(.01)
 store.close()
 record=next(r for r in caplog.records if r.msg=="inference_measurement")
 assert record.status=="expired" and store.entry_count==0
