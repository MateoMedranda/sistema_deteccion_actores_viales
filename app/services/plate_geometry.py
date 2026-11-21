"""Canonical half-open ROI, identical to the frontend plateCrop convention."""
import math
import sys
def _field(value,name):
    return value[name] if isinstance(value,dict) else getattr(value,name)
def plate_roi(vehicle,relative,width,height):
    if relative is None: raise ValueError("missing_plate")
    coords=[_field(vehicle,k) for k in ("x_min","y_min","x_max","y_max")]
    if not all(math.isfinite(v) for v in coords):raise ValueError("invalid_vehicle")
    x1,y1,x2,y2=map(math.trunc,coords)
    x1,y1,x2,y2=max(0,x1),max(0,y1),min(width,x2),min(height,y2)
    if x2<=x1 or y2<=y1:raise ValueError("invalid_vehicle")
    ratios=[_field(relative,k) for k in ("x_min","y_min","x_max","y_max")]
    if not all(math.isfinite(v) and 0<=v<=1 for v in ratios) or ratios[0]>=ratios[2] or ratios[1]>=ratios[3]:raise ValueError("invalid_plate")
    def pixel(r,size):
        v=r*size;nearest=math.floor(v+.5)
        return math.trunc(nearest if abs(v-nearest)<=2*sys.float_info.epsilon*max(1,size) else v)
    result=(x1+pixel(ratios[0],x2-x1),y1+pixel(ratios[1],y2-y1),x1+pixel(ratios[2],x2-x1),y1+pixel(ratios[3],y2-y1))
    if result[2]<=result[0] or result[3]<=result[1]:raise ValueError("invalid_plate")
    return result
