from sqlalchemy.orm import Session
from sqlalchemy import desc
from app import models, schemas
from passlib.context import CryptContext
from typing import List, Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# OPERACIONES CRUD PARA USUARIOS
# ============================================================================

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Obtener usuario por nombre de usuario"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Obtener usuario por correo electronico"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Obtener usuario por ID"""
    return db.query(models.User).filter(models.User.user_id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Obtener lista de usuarios con paginacion"""
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Crear nuevo usuario con password hasheado"""
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar que la contrasena coincida con el hash"""
    return pwd_context.verify(plain_password, hashed_password)


def delete_user(db: Session, user_id: int) -> bool:
    """Eliminar usuario por ID"""
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


# ============================================================================
# OPERACIONES CRUD PARA IMAGENES
# ============================================================================

def create_image(db: Session, image: schemas.ImageCreate) -> models.Image:
    """Crear nuevo registro de imagen"""
    db_image = models.Image(image_path=image.image_path)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


def get_image_by_id(db: Session, image_id: int) -> Optional[models.Image]:
    """Obtener imagen por ID"""
    return db.query(models.Image).filter(models.Image.image_id == image_id).first()


def get_images(db: Session, skip: int = 0, limit: int = 100) -> List[models.Image]:
    """Obtener lista de imagenes ordenadas por fecha de carga (mas reciente primero)"""
    return db.query(models.Image).order_by(desc(models.Image.upload_time)).offset(skip).limit(limit).all()


def get_images_with_detections(db: Session, skip: int = 0, limit: int = 100) -> List[models.Image]:
    """Obtener imagenes que tienen al menos una deteccion"""
    return db.query(models.Image).filter(models.Image.number_of_detections > 0).order_by(desc(models.Image.upload_time)).offset(skip).limit(limit).all()


def update_image_detection_count(db: Session, image_id: int) -> Optional[models.Image]:
    """Actualizar contador de detecciones de una imagen"""
    image = get_image_by_id(db, image_id)
    if image:
        detection_count = db.query(models.Detection).filter(models.Detection.image_id == image_id).count()
        image.number_of_detections = detection_count
        db.commit()
        db.refresh(image)
    return image


def delete_image(db: Session, image_id: int) -> bool:
    """Eliminar imagen (cascade delete eliminara detecciones y confirmaciones)"""
    image = get_image_by_id(db, image_id)
    if image:
        db.delete(image)
        db.commit()
        return True
    return False


# ============================================================================
# OPERACIONES CRUD PARA DETECCIONES
# ============================================================================

def create_detection(db: Session, detection: schemas.DetectionCreate) -> models.Detection:
    """Crear nueva deteccion y actualizar contador en imagen"""
    db_detection = models.Detection(
        image_id=detection.image_id,
        confianza=detection.confianza,
        x1=detection.x1,
        y1=detection.y1,
        x2=detection.x2,
        y2=detection.y2
    )
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)

    # Actualizar contador de detecciones en la imagen
    update_image_detection_count(db, detection.image_id)

    return db_detection


def get_detection_by_id(db: Session, detection_id: int) -> Optional[models.Detection]:
    """Obtener deteccion por ID"""
    return db.query(models.Detection).filter(models.Detection.detection_id == detection_id).first()


def get_detections(db: Session, skip: int = 0, limit: int = 100) -> List[models.Detection]:
    """Obtener lista de detecciones ordenadas por fecha (mas reciente primero)"""
    return db.query(models.Detection).order_by(desc(models.Detection.detection_time)).offset(skip).limit(limit).all()


def get_detections_by_image(db: Session, image_id: int) -> List[models.Detection]:
    """Obtener todas las detecciones de una imagen especifica"""
    return db.query(models.Detection).filter(models.Detection.image_id == image_id).order_by(desc(models.Detection.detection_time)).all()


def get_detections_by_confidence(db: Session, min_confidence: float, skip: int = 0, limit: int = 100) -> List[models.Detection]:
    """Obtener detecciones con confianza mayor o igual al minimo especificado"""
    return db.query(models.Detection).filter(models.Detection.confianza >= min_confidence).order_by(desc(models.Detection.detection_time)).offset(skip).limit(limit).all()


def delete_detection(db: Session, detection_id: int) -> bool:
    """Eliminar deteccion y actualizar contador en imagen"""
    detection = get_detection_by_id(db, detection_id)
    if detection:
        image_id = detection.image_id
        db.delete(detection)
        db.commit()
        update_image_detection_count(db, image_id)
        return True
    return False


# ============================================================================
# OPERACIONES CRUD PARA CONFIRMACIONES
# ============================================================================

def create_confirmation(db: Session, confirmation: schemas.ConfirmationCreate) -> models.Confirmation:
    """Crear nueva confirmacion (usuario confirma o rechaza una imagen)"""
    db_confirmation = models.Confirmation(
        image_id=confirmation.image_id,
        user_id=confirmation.user_id,
        status=confirmation.status
    )
    db.add(db_confirmation)
    db.commit()
    db.refresh(db_confirmation)
    return db_confirmation


def get_confirmation_by_id(db: Session, confirmation_id: int) -> Optional[models.Confirmation]:
    """Obtener confirmacion por ID"""
    return db.query(models.Confirmation).filter(models.Confirmation.confirmation_id == confirmation_id).first()


def get_confirmations(db: Session, skip: int = 0, limit: int = 100) -> List[models.Confirmation]:
    """Obtener lista de confirmaciones ordenadas por fecha (mas reciente primero)"""
    return db.query(models.Confirmation).order_by(desc(models.Confirmation.confirmation_time)).offset(skip).limit(limit).all()


def get_confirmations_by_image(db: Session, image_id: int) -> List[models.Confirmation]:
    """Obtener todas las confirmaciones de una imagen especifica"""
    return db.query(models.Confirmation).filter(models.Confirmation.image_id == image_id).order_by(desc(models.Confirmation.confirmation_time)).all()


def get_confirmations_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Confirmation]:
    """Obtener todas las confirmaciones realizadas por un usuario"""
    return db.query(models.Confirmation).filter(models.Confirmation.user_id == user_id).order_by(desc(models.Confirmation.confirmation_time)).offset(skip).limit(limit).all()


def get_confirmations_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[models.Confirmation]:
    """Obtener confirmaciones filtradas por estado (confirmed o rejected)"""
    return db.query(models.Confirmation).filter(models.Confirmation.status == status).order_by(desc(models.Confirmation.confirmation_time)).offset(skip).limit(limit).all()


def delete_confirmation(db: Session, confirmation_id: int) -> bool:
    """Eliminar confirmacion"""
    confirmation = get_confirmation_by_id(db, confirmation_id)
    if confirmation:
        db.delete(confirmation)
        db.commit()
        return True
    return False


# ============================================================================
# OPERACIONES CRUD PARA CALIDAD DEL AIRE
# ============================================================================

def create_air_quality(db: Session, air_quality: schemas.AirQualityCreate) -> models.AirQuality:
    """Crear nuevo registro de calidad del aire"""
    db_air_quality = models.AirQuality(
        pm25=air_quality.pm25,
        pm10=air_quality.pm10,
        pm01=air_quality.pm01
    )
    db.add(db_air_quality)
    db.commit()
    db.refresh(db_air_quality)
    return db_air_quality


def get_air_quality_by_id(db: Session, record_id: int) -> Optional[models.AirQuality]:
    """Obtener registro de calidad del aire por ID"""
    return db.query(models.AirQuality).filter(models.AirQuality.record_id == record_id).first()


def get_air_quality_records(db: Session, skip: int = 0, limit: int = 100) -> List[models.AirQuality]:
    """Obtener registros de calidad del aire ordenados por fecha (mas reciente primero)"""
    return db.query(models.AirQuality).order_by(desc(models.AirQuality.measurement_time)).offset(skip).limit(limit).all()


def get_latest_air_quality(db: Session) -> Optional[models.AirQuality]:
    """Obtener el registro mas reciente de calidad del aire"""
    return db.query(models.AirQuality).order_by(desc(models.AirQuality.measurement_time)).first()


def get_air_quality_averages(db: Session, hours: int = 24) -> dict:
    """Calcular promedios de calidad del aire en las ultimas N horas"""
    from sqlalchemy import func
    from datetime import datetime, timedelta

    time_threshold = datetime.now() - timedelta(hours=hours)

    result = db.query(
        func.avg(models.AirQuality.pm25).label('avg_pm25'),
        func.avg(models.AirQuality.pm10).label('avg_pm10'),
        func.avg(models.AirQuality.pm01).label('avg_pm01')
    ).filter(models.AirQuality.measurement_time >= time_threshold).first()

    return {
        'avg_pm25': float(result.avg_pm25) if result.avg_pm25 else 0.0,
        'avg_pm10': float(result.avg_pm10) if result.avg_pm10 else 0.0,
        'avg_pm01': float(result.avg_pm01) if result.avg_pm01 else 0.0,
        'period_hours': hours
    }


def delete_air_quality(db: Session, record_id: int) -> bool:
    """Eliminar registro de calidad del aire"""
    record = get_air_quality_by_id(db, record_id)
    if record:
        db.delete(record)
        db.commit()
        return True
    return False

