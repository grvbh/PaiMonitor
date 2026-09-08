from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/images", tags=["images"])


def _assert_device_access(device: models.Device, user: models.User):
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if user.role != models.UserRole.admin and device.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your device")


@router.get("/device/{device_id}")
def list_images_for_device(
    device_id: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    _assert_device_access(device, user)

    q = db.query(models.TrapImage).filter(models.TrapImage.device_id == device_id)
    if start:
        q = q.filter(models.TrapImage.captured_at >= start)
    if end:
        q = q.filter(models.TrapImage.captured_at <= end)

    images = q.order_by(models.TrapImage.captured_at.desc()).limit(limit).all()
    return [
        {
            "id": img.id,
            "captured_at": img.captured_at,
            "processed": img.processed,
            "temperature_c": img.temperature_c,
            "humidity_pct": img.humidity_pct,
            "image_url": f"https://{img.s3_bucket}.s3.amazonaws.com/{img.s3_key}",
            "detection_count": len(img.detections),
        }
        for img in images
    ]


@router.get("/{image_id}/detections", response_model=List[schemas.DetectionOut])
def get_image_detections(image_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    image = db.query(models.TrapImage).filter(models.TrapImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    _assert_device_access(image.device, user)
    return image.detections
