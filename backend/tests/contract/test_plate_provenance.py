import pytest
from app.domain.schemas import EnrichmentPlate
from pydantic import ValidationError
def test_old_absent_and_new_provenance_contract():
    assert EnrichmentPlate(status="read",text="SYN",used_enhancement=True).provenance is None
    p=EnrichmentPlate(status="unreadable",text="DO_NOT_STORE",provenance={"version":1,"policy_id":"baseline-v1","attempted_variants":["raw"],"selected_variant":"none"})
    assert p.text is None and p.provenance.selected_variant=="none"
    with pytest.raises(ValidationError):EnrichmentPlate(status="read",text="SYN",provenance={"version":1,"policy_id":"baseline-v1","attempted_variants":["raw"],"selected_variant":"legacy-retry-v1"})
