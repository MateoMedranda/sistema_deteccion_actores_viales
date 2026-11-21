import cv2,numpy as np,pytest
from app.services.plate_profiles import rescue_profile,NotApplicable
def test_exact_candidate_recipes():
    image=np.arange(20*50*3,dtype=np.uint8).reshape(20,50,3)
    gray=cv2.bilateralFilter(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),5,25,3)
    enlarged=cv2.resize(gray,(200,80),interpolation=cv2.INTER_CUBIC)
    for profile in ("bilateral-clahe-v1","bilateral-adaptive-v1"):
        expected=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8)).apply(enlarged) if "clahe" in profile else cv2.adaptiveThreshold(enlarged,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
        expected=cv2.cvtColor(cv2.copyMakeBorder(expected,8,8,8,8,cv2.BORDER_REPLICATE),cv2.COLOR_GRAY2BGR)
        assert np.array_equal(rescue_profile(image,profile),expected)
def test_small_adaptive_is_not_silently_changed():
    image=np.arange(2*2*3,dtype=np.uint8).reshape(2,2,3)
    with pytest.raises(NotApplicable):rescue_profile(image,"bilateral-adaptive-v1")
