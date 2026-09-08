from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

GRANULARITY_TO_TRUNC = {
    "day": "day",
    "week": "week",
    "month": "month",
}


@router.get("/density/{device_id}", response_model=schemas.DensitySeries)
def density_series(
    device_id: str,
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    species: Optional[str] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if user.role != models.UserRole.admin and device.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your device")

    trunc_unit = GRANULARITY_TO_TRUNC[granularity]
    bucket = func.date_trunc(trunc_unit, models.TrapImage.captured_at).label("bucket_start")

    q = (
        db.query(bucket, models.Detection.species, func.count(models.Detection.id).label("count"))
        .join(models.TrapImage, models.Detection.image_id == models.TrapImage.id)
        .filter(models.TrapImage.device_id == device_id)
    )
    if start:
        q = q.filter(models.TrapImage.captured_at >= start)
    if end:
        q = q.filter(models.TrapImage.captured_at <= end)
    if species:
        q = q.filter(models.Detection.species == species)

    q = q.group_by(bucket, models.Detection.species).order_by(bucket)
    rows = q.all()

    points = [
        schemas.DensityPoint(bucket_start=row.bucket_start, species=row.species, count=row.count)
        for row in rows
    ]
    return schemas.DensitySeries(device_id=device_id, granularity=granularity, points=points)


@router.get("/summary/{device_id}")
def summary(device_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Quick-glance card data: total insects this week, trend vs last week, top species."""
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if user.role != models.UserRole.admin and device.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your device")

    top_species = (
        db.query(models.Detection.species, func.count(models.Detection.id).label("count"))
        .join(models.TrapImage, models.Detection.image_id == models.TrapImage.id)
        .filter(models.TrapImage.device_id == device_id)
        .group_by(models.Detection.species)
        .order_by(func.count(models.Detection.id).desc())
        .limit(5)
        .all()
    )
    total = sum(r.count for r in top_species)
    return {
        "device_id": device_id,
        "total_detections": total,
        "top_species": [{"species": r.species, "count": r.count} for r in top_species],
    }
