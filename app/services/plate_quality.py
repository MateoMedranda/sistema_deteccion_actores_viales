from __future__ import annotations
import cv2
import numpy as np


def conservative_enhance(image: np.ndarray) -> np.ndarray:
    """Non-generative, deterministic retry image; it never adds plate characters."""
    if image.size == 0: return image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    gray = cv2.fastNlMeansDenoising(gray, None, 5, 7, 21)
    gray = cv2.GaussianBlur(gray, (0, 0), 1.0)
    sharp = cv2.addWeighted(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 1.4, gray, -0.4, 0)
    scaled = cv2.resize(sharp, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
