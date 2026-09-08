"""
Thin wrapper around a trained YOLOv8 model for counting/classifying insects
on a yellow sticky-trap image.

The model is trained separately (see /ml-training) and the resulting
weights file is mounted into the backend container at
app.config.settings.model_weights_path.
"""
from functools import lru_cache
from typing import List, Dict
from io import BytesIO

from PIL import Image

from app.config import settings


@lru_cache(maxsize=1)
def get_model():
    # Imported lazily so the API can boot even before a model file exists
    # (e.g. during early development, before training is done).
    from ultralytics import YOLO
    return YOLO(settings.model_weights_path)


def run_inference(image_bytes: bytes) -> List[Dict]:
    """
    Returns a list of detections:
    [{"species": str, "confidence": float, "bbox": (x, y, w, h)}]  # bbox normalized 0-1
    """
    model = get_model()
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    width, height = img.size

    results = model.predict(img, conf=settings.detection_confidence, verbose=False)
    detections = []
    for r in results:
        names = r.names
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "species": names[cls_id],
                "confidence": conf,
                "bbox": (
                    x1 / width,
                    y1 / height,
                    (x2 - x1) / width,
                    (y2 - y1) / height,
                ),
            })
    return detections
