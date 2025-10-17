from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


# Schemas para Usuario
class UserBase(BaseModel):
    """Schema base para usuario"""
    username: str = Field(..., description="Nombre de usuario unico")
    email: EmailStr = Field(..., description="Correo electronico del usuario")


class UserCreate(UserBase):
    """Schema para crear nuevo usuario"""
    password: str = Field(..., min_length=8, description="Contrasena del usuario (minimo 8 caracteres)")
    role: Optional[str] = Field("operador", description="Rol del usuario: admin u operador")


class UserResponse(UserBase):
    """Schema de respuesta con datos del usuario"""
    user_id: int = Field(..., description="ID unico del usuario")
    role: str = Field(..., description="Rol asignado al usuario")

    class Config:
        from_attributes = True


# Schemas para Imagen
class ImageBase(BaseModel):
    """Schema base para imagen"""
    image_path: str = Field(..., description="Ruta donde se almacena la imagen")


class ImageCreate(ImageBase):
    """Schema para registrar nueva imagen"""
    pass


class ImageResponse(ImageBase):
    """Schema de respuesta con datos de la imagen"""
    image_id: int = Field(..., description="ID unico de la imagen")
    upload_time: datetime = Field(..., description="Fecha y hora de carga")
    number_of_detections: int = Field(..., description="Numero total de detecciones en esta imagen")

    class Config:
        from_attributes = True


# Schemas para Deteccion
class DetectionBase(BaseModel):
    """Schema base para deteccion"""
    confianza: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza de la deteccion (0-1)")
    x1: int = Field(..., description="Coordenada X1 del bounding box")
    y1: int = Field(..., description="Coordenada Y1 del bounding box")
    x2: int = Field(..., description="Coordenada X2 del bounding box")
    y2: int = Field(..., description="Coordenada Y2 del bounding box")



class DetectionCreate(DetectionBase):
    """Schema para crear nueva deteccion"""
    image_id: int = Field(..., description="ID de la imagen donde se realizo la deteccion")


class DetectionResponse(DetectionBase):
    """Schema de respuesta con datos de la deteccion"""
    detection_id: int = Field(..., description="ID unico de la deteccion")
    image_id: int = Field(..., description="ID de la imagen asociada")
    detection_time: datetime = Field(..., description="Fecha y hora de la deteccion")

    class Config:
        from_attributes = True


class DetectionWithImage(DetectionResponse):
    """Schema de deteccion con informacion de la imagen"""
    image: ImageResponse = Field(..., description="Datos de la imagen asociada")


# Schemas para Confirmacion
class ConfirmationBase(BaseModel):
    """Schema base para confirmacion"""
    status: str = Field(..., description="Estado de la confirmacion: confirmed o rejected")


class ConfirmationCreate(ConfirmationBase):
    """Schema para crear nueva confirmacion"""
    image_id: int = Field(..., description="ID de la imagen a confirmar/rechazar")
    user_id: int = Field(..., description="ID del usuario que realiza la confirmacion")


class ConfirmationResponse(ConfirmationBase):
    """Schema de respuesta con datos de la confirmacion"""
    confirmation_id: int = Field(..., description="ID unico de la confirmacion")
    image_id: int = Field(..., description="ID de la imagen confirmada/rechazada")
    user_id: int = Field(..., description="ID del usuario que realizo la confirmacion")
    confirmation_time: datetime = Field(..., description="Fecha y hora de la confirmacion")

    class Config:
        from_attributes = True


class ConfirmationWithDetails(ConfirmationResponse):
    """Schema de confirmacion con detalles de usuario e imagen"""
    user: UserResponse = Field(..., description="Datos del usuario que confirmo")
    image: ImageResponse = Field(..., description="Datos de la imagen confirmada")


# Schemas para Calidad del Aire
class AirQualityBase(BaseModel):
    """Schema base para calidad del aire"""
    pm25: float = Field(..., ge=0, description="Particulas PM2.5 (microgramos por metro cubico)")
    pm10: float = Field(..., ge=0, description="Particulas PM10 (microgramos por metro cubico)")
    pm01: float = Field(..., ge=0, description="Particulas PM0.1 (microgramos por metro cubico)")


class AirQualityCreate(AirQualityBase):
    """Schema para registrar nueva medicion de calidad del aire"""
    pass


class AirQualityResponse(AirQualityBase):
    """Schema de respuesta con datos de calidad del aire"""
    record_id: int = Field(..., description="ID unico del registro")
    measurement_time: datetime = Field(..., description="Fecha y hora de la medicion")

    class Config:
        from_attributes = True


# Schemas compuestos para endpoints especificos
class ImageWithDetections(ImageResponse):
    """Schema de imagen con todas sus detecciones"""
    detections: List[DetectionResponse] = Field(default=[], description="Lista de detecciones en esta imagen")


class ImageWithConfirmations(ImageResponse):
    """Schema de imagen con todas sus confirmaciones"""
    confirmations: List[ConfirmationResponse] = Field(default=[], description="Lista de confirmaciones de esta imagen")


class ImageComplete(ImageResponse):
    """Schema completo de imagen con detecciones y confirmaciones"""
    detections: List[DetectionResponse] = Field(default=[], description="Lista de detecciones en esta imagen")
    confirmations: List[ConfirmationResponse] = Field(default=[], description="Lista de confirmaciones de esta imagen")


# Schema para respuestas de API
class MessageResponse(BaseModel):
    """Schema para mensajes de respuesta genericos"""
    message: str = Field(..., description="Mensaje de respuesta")
    status: str = Field("success", description="Estado de la operacion: success o error")


class HealthCheckResponse(BaseModel):
    """Schema para verificacion de estado del sistema"""
    status: str = Field(..., description="Estado del servicio")
    message: str = Field(..., description="Mensaje descriptivo")
    timestamp: datetime = Field(default_factory=datetime.now, description="Fecha y hora de la verificacion")


# statusIsla
class StatusPayload(BaseModel):
    """Define el cuerpo esperado para la peticion de status"""
    status: str
    timestamp: str
