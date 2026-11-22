import numpy as np
from scripts.evaluate_video_presentation import residual_jitter,temporal_lag,channel_pass
def test_residual_not_vehicle_velocity_is_jitter():
 reference=np.array([[x,10,x+80,50] for x in range(20)],dtype=float)
 assert residual_jitter(reference,reference)==(0,0)
 noisy=reference.copy();noisy[::2,[0,2]]+=2
 assert residual_jitter(noisy,reference)[0]>0
 assert channel_pass(0,0) and not channel_pass(0,.001)
 assert channel_pass(1,.8) and not channel_pass(1,.81)
def test_lag_is_measured_independently_and_stationary_is_explicit():
 reference=np.array([[x*x/10,10,x*x/10+80,50] for x in range(30)],dtype=float)
 lagged=np.concatenate((reference[:2],reference[:-2]))
 assert abs(temporal_lag(lagged,reference))==2
 assert temporal_lag(np.tile([10,10,90,50],(20,1)),np.tile([10,10,90,50],(20,1))) is None
