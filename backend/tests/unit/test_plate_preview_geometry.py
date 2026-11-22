import pytest
from app.services.plate_geometry import plate_roi
def test_roundoff_preserves_same_integer_roi():
    assert plate_roi(dict(x_min=20,y_min=25,x_max=290,y_max=300),dict(x_min=28/270,y_min=180/275,x_max=108/270,y_max=220/275),640,400)==(48,205,128,245)
@pytest.mark.parametrize("relative",[None,dict(x_min=.5,y_min=.2,x_max=.1,y_max=.4),dict(x_min=-.1,y_min=0,x_max=1,y_max=1)])
def test_degenerate_rejected(relative):
    with pytest.raises(ValueError):plate_roi(dict(x_min=0,y_min=0,x_max=20,y_max=20),relative,40,40)
