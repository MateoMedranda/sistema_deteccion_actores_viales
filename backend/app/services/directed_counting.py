"""Finite-segment crossings, measured centers and immutable first eligible event."""
from math import hypot
from app.domain.vehicle_taxonomy import is_vehicle
EPS=1e-6
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return a[0]-b[0],a[1]-b[1]
def side(p,a,b):
 d=cross(sub(b,a),sub(p,a))/hypot(*sub(b,a))
 return 1 if d>EPS else -1 if d < -EPS else 0
def intersects(p,q,a,b):
 r,s=sub(q,p),sub(b,a);den=cross(r,s);v=sub(a,p)
 if abs(den)>1e-12:
  t,u=cross(v,s)/den,cross(v,r)/den
  return -1e-12<=t<=1+1e-12 and -1e-12<=u<=1+1e-12
 if side(p,a,b) or side(q,a,b):return False
 axis=0 if abs(s[0])>=abs(s[1]) else 1
 return max(min(p[axis],q[axis]),min(a[axis],b[axis]))<=min(max(p[axis],q[axis]),max(a[axis],b[axis]))+EPS
def advance(state,point,line,direction,class_name):
 a,b=line;s=side(point,a,b);old_side=state.get('side',0);old=state.get('point');pending=state.get('contact',False);counted=state.get('counted',False)
 touch=old is not None and intersects(old,point,a,b)
 event=False
 if s==0:
  pending=pending or touch
 elif old_side and s!=old_side:
  wanted=1 if direction=='negative_to_positive' else -1
  event=bool(s==wanted and (pending or touch) and not counted and is_vehicle(class_name))
  pending=False
 else:pending=False
 return dict(point=point,side=s or old_side,contact=pending,counted=counted or event),event
