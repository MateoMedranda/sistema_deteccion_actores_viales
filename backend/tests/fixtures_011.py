from uuid import uuid4
from tests.fixtures_010 import store_at,frame,observation
NAMES=['Car','Bus','Truck','Big Truck','Motorbike','Van']
def line(name='Línea 1',color='#F59E0B',y=.5):
 return dict(line_id=str(uuid4()),name=name,color=color,segment=dict(point_a=dict(x=.05,y=y),point_b=dict(x=.95,y=y)))

def trajectories():
 return [frame(i,[observation(track=k+1,x=10+k*15,y=(20+i*30 if k%2==0 else 80-i*30),cls=name) for k,name in enumerate(NAMES)],measured=i!=1) for i in range(3)]
