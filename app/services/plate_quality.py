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


def rectify_plate(image: np.ndarray) -> np.ndarray:
    """Apply only geometric deskew inferred from the crop; no pixels are generated."""
    if image.size == 0:
        return image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    points = cv2.findNonZero(cv2.Canny(gray, 60, 160))
    if points is None or len(points) < 8:
        return image
    angle = cv2.minAreaRect(points)[-1]
    angle = angle + 90 if angle < -45 else angle
    matrix = cv2.getRotationMatrix2D((image.shape[1] / 2, image.shape[0] / 2), angle, 1.0)
    return cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
