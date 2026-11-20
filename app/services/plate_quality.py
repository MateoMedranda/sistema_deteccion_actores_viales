from __future__ import annotations
import cv2
import numpy as np


def conservative_enhance(image: np.ndarray) -> np.ndarray:
    """Non-generative, deterministic retry image; it never adds plate characters."""
    if image.size == 0: return image
    # Enlarge tiny plate crops before contrast normalization. Interpolation
    # improves OCR input size but does not recover missing character detail.
    height, width = image.shape[:2]
    scale = max(1.0, min(4.0, 64 / height))
    enlarged = cv2.resize(image, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    padded = cv2.copyMakeBorder(gray, 8, 8, 8, 8, cv2.BORDER_REPLICATE)
    return cv2.cvtColor(padded, cv2.COLOR_GRAY2BGR)


def rectify_plate(image: np.ndarray) -> np.ndarray:
    """Apply only geometric deskew inferred from the crop; no pixels are generated."""
    if image.size == 0:
        return image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    points = cv2.findNonZero(cv2.Canny(gray, 60, 160))
    if points is None or len(points) < 8:
        return image
    angle = cv2.minAreaRect(points)[-1]
    angle = (angle + 45) % 90 - 45
    if abs(angle) > 15 or abs(angle) < .5:
        return image
    height, width = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    cosine, sine = abs(matrix[0, 0]), abs(matrix[0, 1])
    new_width = int(np.ceil(height * sine + width * cosine))
    new_height = int(np.ceil(height * cosine + width * sine))
    matrix[0, 2] += (new_width - width) / 2
    matrix[1, 2] += (new_height - height) / 2
    return cv2.warpAffine(image, matrix, (new_width, new_height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
