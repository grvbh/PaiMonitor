from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_admin

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/", response_model=List[schemas.DeviceOut])
def list_devices(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    query = db.query(models.Device)
    if user.role != models.UserRole.admin:
        query = query.filter(models.Device.owner_id == user.id)
    return query.all()


@router.get("/{device_id}", response_model=schemas.DeviceOut)
def get_device(device_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if user.role != models.UserRole.admin and device.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your device")
    return device


@router.post("/", response_model=schemas.DeviceOut)
def register_device(
    payload: schemas.DeviceCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Admin registers a new physical PaiMonitor unit and assigns it to a farmer."""
    owner_id = payload.owner_id
    if not owner_id:
        raise HTTPException(status_code=400, detail="owner_id is required when admin registers a device")

    device = models.Device(
        serial_number=payload.serial_number,
        name=payload.name,
        owner_id=owner_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        crop=payload.crop,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device
