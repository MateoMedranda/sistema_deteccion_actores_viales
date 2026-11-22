"""Versioned, deterministic transformations. No reconstruction or model calls."""
import math
import cv2
import numpy as np
MAX_SIDE=2048
MAX_PIXELS=2_000_000
MAX_PNG=2*1024*1024
class NotApplicable(ValueError):pass
def _gray(image):
    if image.dtype!=np.uint8 or image.ndim not in (2,3) or min(image.shape[:2])<2:raise NotApplicable("invalid_input")
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY) if image.ndim==3 else image.copy()
    if gray.max()==gray.min():raise NotApplicable("uniform_input")
    return gray
def _scale(gray,padding=0):
    h,w=gray.shape
    desired=max(1,min(4,math.ceil(64/h)))
    for scale in range(desired,0,-1):
        ow,oh=w*scale+padding*2,h*scale+padding*2
        if max(ow,oh)<=MAX_SIDE and ow*oh<=MAX_PIXELS:return scale
    raise NotApplicable("output_limits")
def display_contrast(image):
    gray=_gray(image);s=_scale(gray);h,w=gray.shape
    steps=["grayscale"]
    if s>1:
        gray=cv2.resize(gray,(w*s,h*s),interpolation=cv2.INTER_CUBIC);steps.append("resize_integer")
    output=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8)).apply(gray);steps.append("clahe")
    ok,encoded=cv2.imencode(".png",output)
    if not ok:raise RuntimeError("encode_failed")
    png=encoded.tobytes()
    if len(png)>MAX_PNG:raise NotApplicable("encoded_limit")
    return png,(w*s,h*s),s,steps
def rescue_profile(image,profile):
    gray=_gray(image)
    gray=cv2.bilateralFilter(gray,5,25,3);s=_scale(gray,8)
    h,w=gray.shape
    if s>1:gray=cv2.resize(gray,(w*s,h*s),interpolation=cv2.INTER_CUBIC)
    if profile=="bilateral-clahe-v1":
        output=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8)).apply(gray)
    elif profile=="bilateral-adaptive-v1":
        if min(gray.shape)<11:raise NotApplicable("adaptive_block")
        output=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
    else:raise ValueError("unknown_profile")
    return cv2.cvtColor(cv2.copyMakeBorder(output,8,8,8,8,cv2.BORDER_REPLICATE),cv2.COLOR_GRAY2BGR)
