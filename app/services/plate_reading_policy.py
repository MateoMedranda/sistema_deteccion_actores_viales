"""Image-only policies. Baseline is production; rescue is offline/evaluation only."""
from copy import deepcopy
from time import monotonic
import unicodedata
from app.services.plate_quality import conservative_enhance,rectify_plate
from app.services.plate_profiles import rescue_profile,NotApplicable
def normalize_plate(text):
    return "".join(c for c in unicodedata.normalize("NFKC",text).upper() if not c.isspace() and c!="-")
def provenance(policy,attempts,selected="none"):
    return dict(version=1,policy_id=policy,attempted_variants=list(attempts),selected_variant=selected)
class BaselinePolicy:
    policy_id="baseline-v1"
    def read(self,image,reader,retry_threshold,accept_threshold,should_continue=lambda:True):
        attempts=[];selected="raw";enhanced=False
        try:
            if not should_continue():raise RuntimeError("cancelled")
            attempts.append("raw");reading=reader(image)
            if reading is None or reading.confidence<retry_threshold:
                if not should_continue():raise RuntimeError("cancelled")
                prepared=conservative_enhance(rectify_plate(image))
                attempts.append("legacy-retry-v1");enhanced=True;retried=reader(prepared)
                if retried is not None and (reading is None or retried.confidence>reading.confidence):
                    reading=retried;selected="legacy-retry-v1"
            result=dict(status="unreadable",text=None,ocr_confidence=reading.confidence if reading else None,used_enhancement=enhanced)
            if reading is not None and reading.confidence>=accept_threshold and reading.text:
                result.update(status="read",text=reading.text)
            result["provenance"]=provenance(self.policy_id,attempts,selected if result["status"]=="read" else "none")
            return result
        except Exception as exc:
            return dict(status="failed",text=None,used_enhancement=enhanced,error_code="plate_processing_failed",_exception_type=type(exc).__name__,provenance=provenance(self.policy_id,attempts))
class CandidateRescuePolicy:
    policy_id="candidate-rescue-v1"
    def __init__(self,*,timer=monotonic):self.timer=timer
    def read(self,image,reader,retry_threshold,accept_threshold,should_continue=lambda:True):
        baseline=BaselinePolicy().read(image,reader,retry_threshold,accept_threshold,should_continue)
        result=deepcopy(baseline);result["provenance"]["policy_id"]=self.policy_id
        if result["status"]!="unreadable":return result
        attempts=result["provenance"]["attempted_variants"];deadline=self.timer()+10;accepted=[]
        def active():return self.timer()<deadline and should_continue()
        for profile in ("bilateral-clahe-v1","bilateral-adaptive-v1"):
            if not active():return result
            try:prepared=rescue_profile(image,profile)
            except NotApplicable:continue
            if not active():return result
            attempts.append(profile);result["used_enhancement"]=True
            try:reading=reader(prepared)
            except Exception:continue
            if not active():return result
            if reading is not None and reading.text and reading.confidence>=accept_threshold:accepted.append((profile,reading))
        if not active() or not accepted:return result
        if len({normalize_plate(reading.text) for _,reading in accepted})!=1:
            result.update(status="unreadable",text=None);result["provenance"]["selected_variant"]="none";return result
        selected,reading=max(accepted,key=lambda pair:pair[1].confidence)
        result.update(status="read",text=reading.text,ocr_confidence=reading.confidence)
        result["provenance"]["selected_variant"]=selected
        return result
