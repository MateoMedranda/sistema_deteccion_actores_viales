"""Compare ALPR runtimes without exporting plate text or changing the source repo."""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.metadata
import json
from pathlib import Path
import sys


def main() -> None:
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--original-repo", type=Path, required=True)
    parser.add_argument("--mode", choices=("original", "backend"), required=True)
    args = parser.parse_args()
    import torch  # Load native Torch DLLs before Paddle on Windows.
    import cv2
    image = cv2.imread(str(args.image))
    if image is None:
        raise ValueError("image_cannot_be_decoded")
    report = {"mode": args.mode, "image_size": list(image.shape[:2]), "versions": {
        p: importlib.metadata.version(p) for p in ("paddlepaddle", "paddleocr", "numpy", "torch")
    }}
    counts = Counter()
    if args.mode == "original":
        sys.path.insert(0, str(args.original_repo))
        from core.yolov10_detector import YOLOv10Detector
        from core.alpr_model import ALPRModel
        detector = YOLOv10Detector(str(args.original_repo / "weights/yolov10s_best.pt"))
        alpr = ALPRModel(str(args.original_repo / "weights/alpr_yolov8n_best.pt"))
        detections = detector.detect(image)
        # The original returns text without applying an application confidence
        # threshold. Observe its raw scores without printing any recognized text.
        original_ocr = alpr.ocr.ocr
        observed = []
        def observe(*a, **kw):
            result = original_ocr(*a, **kw)
            observed[:] = result[0] if result and result[0] else []
            return result
        alpr.ocr.ocr = observe
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            crop = image[max(0, y1):min(image.shape[0], y2), max(0, x1):min(image.shape[1], x2)]
            if not crop.size:
                continue
            observed.clear()
            value = alpr.predict(crop)
            counts[value if value in ("NO_PLATE", "UNREADABLE") else "text_returned"] += 1
            if observed:
                confidence = sum(float(line[1][1]) for line in observed) / len(observed)
                counts["text_confidence_ge_080"] += int(confidence >= .8)
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from app.core.config import Settings
        from app.adapters.yolov10_detector import YOLOv10Detector
        from app.adapters.yolov8_plate_localizer import YOLOv8PlateLocalizer
        from app.adapters.paddle_plate_reader import PaddlePlateReader
        from app.services.enrichment_processing import EnrichmentProcessor
        settings = Settings()
        detector = YOLOv10Detector(settings.model_weights_path, settings.model_confidence_threshold,
                                  settings.inference_device, settings.ultralytics_path)
        processor = EnrichmentProcessor(None, YOLOv8PlateLocalizer(settings.plate_model_weights_path,
            settings.plate_localizer_threshold), PaddlePlateReader(settings.paddle_ocr_lang),
            settings.plate_ocr_retry_threshold, settings.plate_ocr_accept_threshold)
        detections = detector.detect(image)
        for det in detections:
            crop = image[max(0, det.y_min):det.y_max, max(0, det.x_min):det.x_max].copy()
            if crop.size:
                _, result = processor.enrich(crop)
                counts[result["status"]] += 1
    report.update(detections=len(detections), counts=dict(counts))
    print("ALPR_DIAGNOSTIC " + json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
