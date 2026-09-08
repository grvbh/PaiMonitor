from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr

from app.models import UserRole


# ---------- Auth ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    role: UserRole = UserRole.farmer


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole


# ---------- Devices ----------
class DeviceCreate(BaseModel):
    serial_number: str
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    crop: str = "tomato"
    owner_id: Optional[str] = None  # admin can assign; farmer defaults to self


class DeviceOut(BaseModel):
    id: str
    serial_number: str
    name: str
    latitude: Optional[float]
    longitude: Optional[float]
    crop: str
    is_active: bool
    last_seen_at: Optional[datetime]

    class Config:
        from_attributes = True


# ---------- Analytics ----------
class DensityPoint(BaseModel):
    bucket_start: datetime
    species: str
    count: int


class DensitySeries(BaseModel):
    device_id: str
    granularity: str  # "hour" | "day" | "week" | "month"
    points: List[DensityPoint]


class DetectionOut(BaseModel):
    species: str
    confidence: float
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float

    class Config:
        from_attributes = True
