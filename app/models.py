from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class RoleEnum(str, enum.Enum):
    admin = "admin"
    operador = "operador"


class StatusEnum(str, enum.Enum):
    confirmed = "confirmed"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.operador)

    # Relacion con confirmaciones
    confirmations = relationship("Confirmation", back_populates="user")


class Image(Base):
    __tablename__ = "images"

    image_id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(255), nullable=False)
    upload_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    number_of_detections = Column(Integer, default=0)

    # Relaciones
    detections = relationship("Detection", back_populates="image", cascade="all, delete-orphan")
    confirmations = relationship("Confirmation", back_populates="image", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detections"

    detection_id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.image_id", ondelete="CASCADE"))
    detection_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    confianza = Column(Float, nullable=False)
    x1 = Column(Integer, nullable=False)
    y1 = Column(Integer, nullable=False)
    x2 = Column(Integer, nullable=False)
    y2 = Column(Integer, nullable=False)

    # Relacion con imagen
    image = relationship("Image", back_populates="detections")


class Confirmation(Base):
    __tablename__ = "confirmations"

    confirmation_id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.image_id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    confirmation_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    status = Column(Enum(StatusEnum), nullable=False)

    # Relaciones
    image = relationship("Image", back_populates="confirmations")
    user = relationship("User", back_populates="confirmations")


class AirQuality(Base):
    __tablename__ = "air_quality"

    record_id = Column(Integer, primary_key=True, index=True)
    measurement_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    pm25 = Column(Float, nullable=False)
    pm10 = Column(Float, nullable=False)
    pm01 = Column(Float, nullable=False)