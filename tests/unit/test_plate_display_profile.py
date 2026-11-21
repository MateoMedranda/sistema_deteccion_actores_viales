import cv2, numpy as np, pytest
from app.services.plate_profiles import display_contrast, NotApplicable
def test_profile_exact_scale_steps_and_input_immutable():
    original=np.arange(30*80*3,dtype=np.uint8).reshape(30,80,3);copy=original.copy()
    png,size,scale,steps=display_contrast(original)
    decoded=cv2.imdecode(np.frombuffer(png,np.uint8),cv2.IMREAD_UNCHANGED)
    assert scale==3 and size==(240,90) and decoded.shape==(90,240)
    assert steps==["grayscale","resize_integer","clahe"]
    assert np.array_equal(original,copy)
@pytest.mark.parametrize("shape",[(1,30,3),(10,10,3),(2050,2050,3)])
def test_inapplicable(shape):
    with pytest.raises(NotApplicable):display_contrast(np.zeros(shape,np.uint8))

def test_scale_reduced_by_real_dimensions_and_png_has_no_inherited_metadata():
 from io import BytesIO
 from PIL import Image
 image=np.repeat(np.indices((20,1000)).sum(axis=0).astype(np.uint8)[:,:,None],3,axis=2)
 png,size,scale,steps=display_contrast(image)
 assert scale==2 and size==(2000,40)
 decoded=Image.open(BytesIO(png))
 assert not decoded.getexif() and "exif" not in decoded.info and "text" not in decoded.info
@pytest.mark.parametrize("shape",[(2049,2),(1500,1500)])
def test_nonuniform_input_still_obeys_output_limits(shape):
 image=np.indices(shape).sum(axis=0).astype(np.uint8)
 with pytest.raises(NotApplicable):display_contrast(image)
