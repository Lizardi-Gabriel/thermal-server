from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional, List
from app.models import RolUsuarioEnum, EstatusEventoEnum, TipoMedicionEnum, TipoLogEnum


# ESQUEMAS PARA USUARIOS

class UsuarioBase(BaseModel):
    """Schema base con los campos comunes de un usuario."""
    nombre_usuario: str = Field(..., max_length=50, description="Nombre de usuario único")
    correo_electronico: EmailStr = Field(..., description="Correo electrónico del usuario")


class UsuarioCreate(UsuarioBase):
    """Schema para la creación de un nuevo usuario."""
    password: str = Field(..., min_length=8, description="Contraseña del usuario (mínimo 8 caracteres)")
    rol: Optional[RolUsuarioEnum] = RolUsuarioEnum.operador


class Usuario(UsuarioBase):
    """Schema para leer los datos de un usuario (respuesta de la API)."""
    usuario_id: int
    rol: RolUsuarioEnum

    class Config:
        from_attributes = True


# ESQUEMAS PARA DETECCION

class DeteccionBase(BaseModel):
    """Schema base para una detección."""
    confianza: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza de la detección (0-1)")
    x1: int
    y1: int
    x2: int
    y2: int


class DeteccionCreate(DeteccionBase):
    """Schema para crear una nueva detección asociada a una imagen."""
    imagen_id: int


class Deteccion(DeteccionBase):
    """Schema para leer los datos de una detección."""
    deteccion_id: int
    imagen_id: int

    class Config:
        from_attributes = True


# ESQUEMAS PARA IMAGENES

class ImagenBase(BaseModel):
    """Schema base para una imagen."""
    ruta_imagen: str = Field(..., max_length=255, description="URL o ruta de la imagen")


class ImagenCreate(ImagenBase):
    """Schema para crear una nueva imagen asociada a un evento."""
    evento_id: int


class Imagen(ImagenBase):
    """Schema para leer los datos de una imagen."""
    imagen_id: int
    evento_id: int
    hora_subida: datetime
    # Relación anidada: Muestra las detecciones de esta imagen
    detecciones: List[Deteccion] = []

    class Config:
        from_attributes = True


# ESQUEMAS PARA calidad de aire

class CalidadAireBase(BaseModel):
    """Schema base para un registro de calidad del aire."""

    temp: float
    humedad: float
    pm2p5: float
    pm10: float
    pm1p0: float
    aqi: float
    descrip: str
    tipo: TipoMedicionEnum = TipoMedicionEnum.pendiente
    hora_medicion: Optional[datetime] = None


class CalidadAireCreate(CalidadAireBase):
    """Schema para crear un nuevo registro de calidad de aire para un evento."""
    evento_id: int


class CalidadAire(CalidadAireBase):
    """Schema para leer un registro de calidad del aire."""
    registro_id: int
    evento_id: int

    class Config:
        from_attributes = True


# ESQUEMAS PARA EVENTOS

class EventoBase(BaseModel):
    """Schema base para un evento."""
    fecha_evento: date
    descripcion: Optional[str] = None
    estatus: EstatusEventoEnum = EstatusEventoEnum.pendiente


class EventoCreate(EventoBase):
    """Schema para crear un nuevo evento."""
    pass # No necesita campos adicionales para la creación básica


class EventoUpdate(BaseModel):
    """Schema para actualizar el estatus de un evento y asignar un usuario."""
    estatus: EstatusEventoEnum
    usuario_id: int
    descripcion: Optional[str] = None


class EventoUpateDescripcion(BaseModel):
    """Schema para actualizar solo la descripcion de un evento."""
    descripcion: str


class Evento(EventoBase):
    """Schema completo para leer un evento, incluyendo sus relaciones."""
    evento_id: int
    usuario_id: Optional[int] = None

    # Relaciones anidadas para una respuesta completa
    usuario: Optional[Usuario] = None
    imagenes: List[Imagen] = []
    registros_calidad_aire: List[CalidadAire] = []

    class Config:
        from_attributes = True


# ESQUEMAS OPTIMIZADOS PARA EVENTOS CON CAMPOS CALCULADOS

class EventoOptimizado(BaseModel):
    """Schema de evento con campos calculados para optimizar el frontend."""
    evento_id: int
    fecha_evento: date
    descripcion: Optional[str] = None
    estatus: EstatusEventoEnum
    usuario_id: Optional[int] = None
    usuario: Optional[Usuario] = None

    # Campos calculados
    total_imagenes: int = 0
    max_detecciones: int = 0
    total_detecciones: int = 0
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None

    # Promedios de calidad del aire (solo registros con horas unicas)
    promedio_pm10: Optional[float] = None
    promedio_pm2p5: Optional[float] = None
    promedio_pm1p0: Optional[float] = None

    # Solo la imagen con mas detecciones para preview
    imagen_preview: Optional[Imagen] = None

    class Config:
        from_attributes = True


class EventoDetalleOptimizado(EventoOptimizado):
    """Schema para detalle de evento con todas las imagenes."""
    # Todas las imagenes para el detalle
    imagenes: List[Imagen] = []
    registros_calidad_aire: List[CalidadAire] = []


class EventosFiltros(BaseModel):
    """Parametros de filtro para listar eventos."""
    estatus: Optional[EstatusEventoEnum] = None
    usuario_id: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    #skip: int = 0
    #limit: int = 50


class EstadisticasEventos(BaseModel):
    """Estadisticas generales de eventos."""
    total_eventos: int
    eventos_pendientes: int
    eventos_confirmados: int
    eventos_descartados: int
    total_detecciones: int
    promedio_detecciones_por_evento: float
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


# ESQUEMAS PARA LOGS

class LogSistemaBase(BaseModel):
    """Schema base para un log del sistema."""
    tipo: TipoLogEnum = TipoLogEnum.info
    mensaje: str


class LogSistemaCreate(LogSistemaBase):
    """Schema para crear un nuevo log."""
    pass


class LogSistema(LogSistemaBase):
    """Schema para leer un log del sistema."""
    log_id: int
    hora_log: datetime

    class Config:
        from_attributes = True


# ESQUEMAS PARA AUTENTICACION

class Token(BaseModel):
    """Schema para la respuesta del token JWT."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema para los datos contenidos dentro de un token JWT (payload)."""
    nombre_usuario: Optional[str] = None


class UsuarioLogin(BaseModel):
    """Schema para el login de usuario."""
    username: str
    password: str


class ImagenConDetecciones(BaseModel):
    """Schema para recibir una imagen con sus detecciones en una sola petición."""
    imagen: ImagenBase
    detecciones: List[DeteccionBase]


# ESQUEMAS PARA TOKEN FCM

class TokenFCMBase(BaseModel):
    """Schema base para un token FCM."""
    token_fcm: str = Field(..., max_length=255, description="Token FCM del dispositivo")
    dispositivo: Optional[str] = Field(None, max_length=100, description="Informacion del dispositivo")


class TokenFCMCreate(TokenFCMBase):
    """Schema para crear un nuevo token FCM."""
    usuario_id: int


class TokenFCM(TokenFCMBase):
    """Schema para leer un token FCM."""
    token_id: int
    usuario_id: int
    fecha_registro: datetime
    activo: bool

    class Config:
        from_attributes = True


class TokenFCMRegistro(BaseModel):
    """Schema para registrar token desde la app."""
    token_fcm: str
    dispositivo: Optional[str] = None


# ESQUEMAS PARA GESTION DE USUARIOS (ADMIN)

class UsuarioUpdate(BaseModel):
    """Schema para actualizar un usuario."""
    nombre_usuario: Optional[str] = Field(None, max_length=50)
    correo_electronico: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    rol: Optional[RolUsuarioEnum] = None


class UsuarioListaAdmin(BaseModel):
    """Schema para listar usuarios (admin)."""
    usuario_id: int
    nombre_usuario: str
    correo_electronico: str
    rol: RolUsuarioEnum
    # Estadisticas del usuario
    total_eventos_gestionados: int = 0
    eventos_confirmados: int = 0
    eventos_descartados: int = 0

    class Config:
        from_attributes = True


class UsuarioCreateAdmin(BaseModel):
    """Schema para que admin cree usuarios."""
    nombre_usuario: str = Field(..., max_length=50)
    correo_electronico: EmailStr
    password: str = Field(..., min_length=8)
    rol: RolUsuarioEnum = RolUsuarioEnum.operador


