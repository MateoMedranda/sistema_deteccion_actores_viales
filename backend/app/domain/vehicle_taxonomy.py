"""Observation taxonomy; raw detector names and IDs remain unchanged."""
import json
from importlib.resources import files

REGISTRY = json.loads(files('app.domain').joinpath('class_presentation.json').read_text(encoding='utf-8'))
CLASS_ALIASES = REGISTRY['aliases']
VEHICLE_CLASSES = frozenset(REGISTRY['classes']) - {'person'}

def normalize_class(value):
    key = str(value or '').strip().lower() or 'unknown'
    return CLASS_ALIASES.get(key, key)

def is_vehicle(value):
    return normalize_class(value) in VEHICLE_CLASSES

def configured_vehicle_classes(values):
    """Expand spellings for legacy membership/SQL filters without merging counts.

    The configured truck family includes the trained heavy-truck subtype. Other
    explicitly disabled families stay disabled; unknown configured names survive.
    """
    keys = {normalize_class(value) for value in values if str(value).strip()}
    if 'truck' in keys:
        keys.add('big_truck')
    return keys | {alias for alias, key in CLASS_ALIASES.items() if key in keys}
