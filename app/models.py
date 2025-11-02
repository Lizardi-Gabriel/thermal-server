from sqlalchemy import (Column, Integer, String, Float, DateTime, Enum as SQLAlchemyEnum,
                        ForeignKey, Text, Date)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


import enum
from sqlalchemy import (Column, Integer, String, Float, DateTime, Enum as SQLAlchemyEnum,
                        ForeignKey, Text, Date, Boolean)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RolUsuarioEnum(str, enum.Enum):
    admin = "admin"
    operador = "operador"


class EstatusEventoEnum(str, enum.Enum):
    confirmado = "confirmado"
    descartado = "descartado"
    pendiente = "pendiente"


class TipoMedicionEnum(str, enum.Enum):
    antes = "antes"
    durante = "durante"
    despues = "despues"
    pendiente = "pendiente"


class TipoLogEnum(str, enum.Enum):
    info = "info"
    advertencia = "advertencia"
    error = "error"

# modelos de la base de datos

class Usuario(Base):
    """Modelo para la tabla 'usuarios'"""
    __tablename__ = "usuarios"

    usuario_id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_usuario = Column(String(50), unique=True, nullable=False, index=True)
    correo_electronico = Column(String(100), unique=True, nullable=False)
    hash_contrasena = Column(String(255), nullable=False)
    rol = Column(SQLAlchemyEnum(RolUsuarioEnum), default=RolUsuarioEnum.operador)

    # Relación: Un usuario puede gestionar muchos eventos.
    eventos = relationship("Evento", back_populates="usuario")

    # Relacion: Un usuario puede tener muchos tokens FCM (multiples dispositivos)
    tokens_fcm = relationship("TokenFCM", back_populates="usuario")


class Evento(Base):
    """Modelo para la tabla 'eventos'"""
    __tablename__ = "eventos"

    evento_id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_evento = Column(Date, nullable=False, index=True)
    descripcion = Column(Text)
    estatus = Column(SQLAlchemyEnum(EstatusEventoEnum), default=EstatusEventoEnum.pendiente)

    # Llave foránea que conecta con la tabla de usuarios.
    usuario_id = Column(Integer, ForeignKey("usuarios.usuario_id", ondelete="SET NULL"))

    # Relaciones:
    # Un evento está asociado a un único usuario.
    usuario = relationship("Usuario", back_populates="eventos")
    # Un evento puede tener múltiples imágenes. `cascade` asegura que si se borra un evento, sus imágenes también.
    imagenes = relationship("Imagen", back_populates="evento", cascade="all, delete-orphan")
    # Un evento tiene registros de calidad del aire asociados.
    registros_calidad_aire = relationship("CalidadAire", back_populates="evento", cascade="all, delete-orphan")


class Imagen(Base):
    """Modelo para la tabla 'imagenes'"""
    __tablename__ = "imagenes"

    imagen_id = Column(Integer, primary_key=True, autoincrement=True)
    ruta_imagen = Column(String(255), nullable=False)
    hora_subida = Column(DateTime, default=func.now(), index=True)

    # Llave foránea que conecta con la tabla de eventos.
    evento_id = Column(Integer, ForeignKey("eventos.evento_id", ondelete="CASCADE"), index=True)

    # Relaciones:
    # Una imagen pertenece a un único evento.
    evento = relationship("Evento", back_populates="imagenes")
    # Una imagen puede tener múltiples detecciones.
    detecciones = relationship("Deteccion", back_populates="imagen", cascade="all, delete-orphan")


class Deteccion(Base):
    """Modelo para la tabla 'detecciones'"""
    __tablename__ = "detecciones"

    deteccion_id = Column(Integer, primary_key=True, autoincrement=True)
    confianza = Column(Float, nullable=False)
    x1 = Column(Integer, nullable=False)
    y1 = Column(Integer, nullable=False)
    x2 = Column(Integer, nullable=False)
    y2 = Column(Integer, nullable=False)

    # Llave foránea que conecta con la tabla de imágenes.
    imagen_id = Column(Integer, ForeignKey("imagenes.imagen_id", ondelete="CASCADE"))

    # Relación: Una detección pertenece a una única imagen.
    imagen = relationship("Imagen", back_populates="detecciones")


class CalidadAire(Base):
    """Modelo actualizado para la tabla 'calidad_aire'"""
    __tablename__ = "calidad_aire"

    registro_id = Column(Integer, primary_key=True, autoincrement=True)
    evento_id = Column(Integer, ForeignKey("eventos.evento_id", ondelete="CASCADE"), index=True)
    hora_medicion = Column(DateTime, default=func.now(), index=True)
    temp = Column(Float)
    humedad = Column(Float)
    pm2p5 = Column(Float) # antes pm25
    pm10 = Column(Float)  # antes pm10
    pm1p0 = Column(Float) # antes pm01
    aqi = Column(Float)
    descrip = Column(String(30))
    tipo = Column(SQLAlchemyEnum(TipoMedicionEnum), default=TipoMedicionEnum.pendiente)
    evento = relationship("Evento", back_populates="registros_calidad_aire")


class LogSistema(Base):
    """Modelo para la tabla 'logs_sistema'"""
    __tablename__ = "logs_sistema"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(SQLAlchemyEnum(TipoLogEnum), default=TipoLogEnum.info)
    mensaje = Column(Text, nullable=False)
    hora_log = Column(DateTime, default=func.now(), index=True)


class TokenFCM(Base):
    """Modelo para la tabla 'tokens_fcm'"""
    __tablename__ = "tokens_fcm"

    token_id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.usuario_id", ondelete="CASCADE"))
    token_fcm = Column(String(255), nullable=False)
    dispositivo = Column(String(100))
    fecha_registro = Column(DateTime, default=func.now())
    activo = Column(Boolean, default=True)

    # Relacion: Un token pertenece a un usuario
    usuario = relationship("Usuario", back_populates="tokens_fcm")

