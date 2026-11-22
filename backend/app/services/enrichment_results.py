"""Normalize once before any SQLite, JSON or public representation."""
from copy import deepcopy
from app.domain.schemas import EnrichedVehicleResult

def normalize_results(items):
    result, identities = [], set()
    for raw in items:
        item = deepcopy(raw)
        plate = item.get("plate", {})
        status = plate.get("status", "failed")
        if item.get("plate_status") != status:
            raise ValueError("inconsistent_plate_status")
        if status != "read":
            plate["text"] = None
        elif not isinstance(plate.get("text"), str) or not plate["text"].strip():
            plate["status"] = item["plate_status"] = "unreadable"
            plate["text"] = None
        if status == "not_detected":
            plate["bbox_relative"] = None
        if plate.get("provenance") and plate.get("status")!="read":
            plate["provenance"]["selected_variant"]="none"
        item["plate"] = plate
        clean = EnrichedVehicleResult.model_validate(item).model_dump()
        identity = clean["detection_id"]
        if identity in identities:
            raise ValueError("duplicate_detection_identity")
        identities.add(identity)
        result.append(clean)
    return sorted(result, key=lambda item: item["detection_id"])
