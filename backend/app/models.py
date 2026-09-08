import enum
import uuid

from sqlalchemy import (
    Column, String, Float, Integer, ForeignKey, DateTime, Enum, Boolean, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    farmer = "farmer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.farmer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    devices = relationship("Device", back_populates="owner")


class Device(Base):
    """A single PaiMonitor unit deployed in a farmer's field."""
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    serial_number = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)  # e.g. "North Field Trap 1"
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    crop = Column(String, default="tomato")

    is_active = Column(Boolean, default=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="devices")
    images = relationship("TrapImage", back_populates="device")


class TrapImage(Base):
    """One hourly capture uploaded by a device to S3."""
    __tablename__ = "trap_images"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    device_id = Column(UUID(as_uuid=False), ForeignKey("devices.id"), nullable=False)

    s3_key = Column(String, nullable=False)
    s3_bucket = Column(String, nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False)  # from device/EXIF or upload time

    temperature_c = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)

    processed = Column(Boolean, default=False)
    processing_error = Column(String, nullable=True)

    device = relationship("Device", back_populates="images")
    detections = relationship("Detection", back_populates="image")


class Detection(Base):
    """One detected insect instance within a trap image (model output)."""
    __tablename__ = "detections"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    image_id = Column(UUID(as_uuid=False), ForeignKey("trap_images.id"), nullable=False)

    species = Column(String, nullable=False, index=True)
    confidence = Column(Float, nullable=False)

    # bounding box, normalized 0-1, for drawing overlays in the UI
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_w = Column(Float, nullable=False)
    bbox_h = Column(Float, nullable=False)

    image = relationship("TrapImage", back_populates="detections")
