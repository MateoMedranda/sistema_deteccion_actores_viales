from app.domain.vehicle_taxonomy import REGISTRY, normalize_class

def class_presentation(name):
    key=normalize_class(name);known=key in REGISTRY['classes']
    entry=REGISTRY['classes'].get(key,{'label':name,'color':REGISTRY['fallback_color']})
    color=entry['color'];rgb=tuple(int(color[i:i+2],16) for i in (1,3,5))
    return {**entry,'key':key,'known':known,'bgr':rgb[::-1]}
