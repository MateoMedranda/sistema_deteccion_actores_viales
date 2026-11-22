from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import yaml

from app.adapters.attribute_extractor_protocol import AttributePrediction


class EfficientNetAttributeExtractor:
    """Loads the evaluated multitask B1 checkpoint once from an external path."""

    def __init__(self, weights_path: Path, manifest_path: Path, device: str = "cpu") -> None:
        if not weights_path.is_file() or not manifest_path.is_file():
            raise RuntimeError("attribute_model_not_configured")
        manifest = self._manifest(manifest_path)
        if manifest.get("architecture") != "MultiTaskEfficientNet":
            raise ValueError("unsupported_attribute_architecture")
        expected = manifest.get("weights_checksum", "")
        if expected and not expected.startswith("replace-"):
            actual = hashlib.sha256(weights_path.read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError("attribute_weights_checksum_mismatch")
        import torch
        import torch.nn as nn
        from torchvision import models, transforms
        class MultiTaskEfficientNet(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.backbone = models.efficientnet_b1(weights=None)
                features = self.backbone.classifier[1].in_features
                self.backbone.classifier = nn.Identity()
                self.color_head = nn.Linear(features, len(manifest["labels"]["color"]))
                self.type_head = nn.Linear(features, len(manifest["labels"]["type"]))
                self.reid_head = nn.Linear(features, 575)
            def forward(self, input_tensor):
                features = self.backbone(input_tensor)
                return self.color_head(features), self.type_head(features)
        self._torch = torch
        self.device = torch.device(device if device != "0" else "cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = MultiTaskEfficientNet().to(self.device)
        state = torch.load(weights_path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(state, strict=True); self.model.eval()
        self.labels = manifest["labels"]
        normalization = manifest["normalization"]; input_spec = manifest["input"]
        self.transform = transforms.Compose([transforms.ToPILImage(), transforms.Resize((input_spec["height"], input_spec["width"])), transforms.ToTensor(), transforms.Normalize(normalization["mean"], normalization["std"])])

    def extract(self, vehicle_crop: np.ndarray) -> list[AttributePrediction]:
        rgb = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2RGB)
        with self._torch.no_grad():
            color, vehicle_type = self.model(self.transform(rgb).unsqueeze(0).to(self.device))
            outputs = []
            for name, logits in (("color", color), ("type", vehicle_type)):
                probabilities = self._torch.softmax(logits, dim=1)[0]
                index = int(self._torch.argmax(probabilities).item())
                outputs.append(AttributePrediction(name, self.labels[name][index], float(probabilities[index].item())))
            return outputs

    @staticmethod
    def _manifest(path: Path) -> dict[str, Any]:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("labels"), dict) or not data["labels"].get("color") or not data["labels"].get("type"):
            raise ValueError("invalid_attribute_manifest")
        return data
