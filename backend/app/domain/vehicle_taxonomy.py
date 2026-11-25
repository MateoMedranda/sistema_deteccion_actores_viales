"""Pure observation taxonomy, independent of enrichment and physical identity claims."""
VEHICLE_CLASSES=frozenset('car truck bus van pickup suv sedan hatchback mpv estate bicycle motorcycle'.split())
def normalize_class(value):return str(value or '').strip().lower() or 'unknown'
def is_vehicle(value):return normalize_class(value) in VEHICLE_CLASSES
