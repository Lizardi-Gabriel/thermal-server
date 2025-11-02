from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from typing import List, Optional, Type
from datetime import date
from app import models, schemas
from app.models import LogSistema
from app.security import hashear_password


# OPERACIONES CRUD PARA Usuario

def get_user_by_id(db: Session, usuario_id: int) -> Optional[models.Usuario]:
    """Obtener un usuario por su ID."""
    return db.query(models.Usuario).filter(models.Usuario.usuario_id == usuario_id).first()


def get_user_by_username(db: Session, nombre_usuario: str) -> Optional[models.Usuario]:
    """Obtener un usuario por su nombre de usuario."""
    return db.query(models.Usuario).filter(models.Usuario.nombre_usuario == nombre_usuario).first()


def get_user_by_email(db: Session, correo_electronico: str) -> Optional[models.Usuario]:
    """Obtener un usuario por su correo electrónico."""
    return db.query(models.Usuario).filter(models.Usuario.correo_electronico == correo_electronico).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.Usuario]:
    """Obtener una lista de usuarios con paginación."""
    return db.query(models.Usuario).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UsuarioCreate) -> models.Usuario:
    """Crear un nuevo usuario con la contraseña hasheada."""
    print('-----' *20)
    print('password original: ' + user.password)
    hashed_password = hashear_password(user.password)
    print('password hashed: ' + hashed_password)
    db_user = models.Usuario(
        nombre_usuario=user.nombre_usuario,
        correo_electronico=user.correo_electronico,
        hash_contrasena=hashed_password,
        rol=user.rol
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# OPERACIONES CRUD PARA Evento

def get_evento_by_id(db: Session, evento_id: int) -> Optional[models.Evento]:
    """ Obtener un evento por su ID, cargando también sus relaciones (usuario, imágenes, detecciones y calidad del
    aire)."""
    return (
        db.query(models.Evento)
        .options(
            joinedload(models.Evento.usuario),
            joinedload(models.Evento.imagenes).joinedload(models.Imagen.detecciones),
            joinedload(models.Evento.registros_calidad_aire)
        )
        .filter(models.Evento.evento_id == evento_id)
        .first()
    )


def get_eventos(db: Session, skip: int = 0, limit: int = 100) -> List[models.Evento]:
    """Obtener una lista de eventos ordenados por fecha (más recientes primero)."""
    return (
        db.query(models.Evento)
        .options(
            joinedload(models.Evento.usuario),
            joinedload(models.Evento.imagenes).joinedload(models.Imagen.detecciones),
            joinedload(models.Evento.registros_calidad_aire)
        )
        .order_by(desc(models.Evento.fecha_evento)).offset(skip).limit(limit).all()
    )


def get_eventos_por_fecha(db: Session, fecha_evento) -> List[models.Evento]:
    """Obtener una lista de eventos para una fecha específica."""
    return (
        db.query(models.Evento)
        .options(
            joinedload(models.Evento.usuario),
            joinedload(models.Evento.imagenes).joinedload(models.Imagen.detecciones),
            joinedload(models.Evento.registros_calidad_aire)
        )
        .filter(models.Evento.fecha_evento == fecha_evento)
        .all()
    )



def create_evento(db: Session, evento: schemas.EventoCreate) -> models.Evento:
    """Crear un nuevo evento."""
    db_evento = models.Evento(**evento.model_dump())
    db.add(db_evento)
    db.commit()
    db.refresh(db_evento)
    return db_evento


def update_evento(db: Session, evento_id: int, evento_update: schemas.EventoUpdate) -> Optional[models.Evento]:
    """Actualizar el estatus, usuario y descripción de un evento."""
    db_evento = get_evento_by_id(db, evento_id)
    if db_evento:
        db_evento.estatus = evento_update.estatus
        db_evento.usuario_id = evento_update.usuario_id
        if evento_update.descripcion is not None:
            db_evento.descripcion = evento_update.descripcion
        db.commit()
        db.refresh(db_evento)
    return db_evento


def update_evento_descripcion(db: Session, evento_id: int, evento_update: schemas.EventoUpateDescripcion) -> Optional[models.Evento]:
    """Actualizar únicamente la descripción de un evento."""
    db_evento = get_evento_by_id(db, evento_id)
    if db_evento:
        db_evento.descripcion = evento_update.descripcion
        db.commit()
        db.refresh(db_evento)
    return db_evento


def delete_evento(db: Session, evento_id: int) -> bool:
    """Eliminar un evento por su ID."""
    db_evento = db.query(models.Evento).filter(models.Evento.evento_id == evento_id).first()
    if db_evento:
        db.delete(db_evento)
        db.commit()
        return True
    return False


# OPERACIONES CRUD PARA Imagen Y Deteccion (a menudo se crean juntas)

def create_imagen_con_detecciones(db: Session, evento_id: int, imagen: schemas.ImagenBase, detecciones: List[schemas.DeteccionBase]) -> models.Imagen:
    """Crear una imagen y sus detecciones asociadas dentro de un evento."""

    # 1. Crear la Imagen
    db_imagen = models.Imagen(ruta_imagen=imagen.ruta_imagen, evento_id=evento_id)
    db.add(db_imagen)
    db.commit()
    db.refresh(db_imagen)

    # 2. Crear las Detecciones asociadas a la imagen recién creada
    for det in detecciones:
        db_det = models.Deteccion(**det.model_dump(), imagen_id=db_imagen.imagen_id)
        db.add(db_det)

    db.commit()
    db.refresh(db_imagen)
    return db_imagen


# OPERACIONES CRUD PARA CalidadAire

def create_calidad_aire(db: Session, registro: schemas.CalidadAireCreate) -> models.CalidadAire:
    """Crear un nuevo registro de calidad del aire para un evento."""
    db_registro = models.CalidadAire(**registro.model_dump())
    db.add(db_registro)
    db.commit()
    db.refresh(db_registro)
    return db_registro


def get_registros_calidad_aire_por_evento(db: Session, evento_id: int) -> List[models.CalidadAire]:
    """Obtener todos los registros de calidad de aire de un evento específico."""
    return db.query(models.CalidadAire).filter(models.CalidadAire.evento_id == evento_id).all()


def update_calidad_aire_tipo(db: Session, registro_id: int, nuevo_tipo: schemas.TipoMedicionEnum) -> Optional[models.CalidadAire]:
    """Actualizar el tipo de un registro de calidad del aire."""
    db_registro = db.query(models.CalidadAire).filter(models.CalidadAire.registro_id == registro_id).first()
    if db_registro:
        db_registro.tipo = nuevo_tipo
        db.commit()
        db.refresh(db_registro)
    return db_registro


# OPERACIONES CRUD PARA LogSistema

def create_log(db: Session, log: schemas.LogSistemaCreate) -> models.LogSistema:
    """Crear un nuevo registro de log en el sistema."""
    db_log = models.LogSistema(**log.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_logs(db: Session, fecha_log: Optional[date] = None, tipo_log: Optional[models.TipoLogEnum] = None) -> list[Type[LogSistema]]:
    """Obtener una lista de logs del sistema con filtros opcionales por fecha y tipo."""
    query = db.query(models.LogSistema)

    if fecha_log:
        query = query.filter(func.date(models.LogSistema.hora_log) == fecha_log)

    if tipo_log:
        query = query.filter(models.LogSistema.tipo == tipo_log)

    return query.order_by(desc(models.LogSistema.hora_log)).all()


# OPERACIONES CRUD PARA TokenFCM

def create_token_fcm(db: Session, token: schemas.TokenFCMCreate) -> models.TokenFCM:
    """Crear un nuevo token FCM para un usuario."""
    db_token = models.TokenFCM(**token.model_dump())
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_token_fcm_by_usuario(db: Session, usuario_id: int) -> List[models.TokenFCM]:
    """Obtener todos los tokens FCM activos de un usuario."""
    return db.query(models.TokenFCM).filter(
        models.TokenFCM.usuario_id == usuario_id,
        models.TokenFCM.activo == True
    ).all()


def get_token_fcm_existente(db: Session, usuario_id: int, token_fcm: str) -> Optional[models.TokenFCM]:
    """Verificar si un token FCM ya existe para un usuario."""
    return db.query(models.TokenFCM).filter(
        models.TokenFCM.usuario_id == usuario_id,
        models.TokenFCM.token_fcm == token_fcm
    ).first()


def desactivar_token_fcm(db: Session, token_id: int) -> bool:
    """Desactivar un token FCM."""
    db_token = db.query(models.TokenFCM).filter(models.TokenFCM.token_id == token_id).first()
    if db_token:
        db_token.activo = False
        db.commit()
        return True
    return False


def get_tokens_operadores_activos(db: Session) -> List[str]:
    """Obtener tokens FCM de todos los operadores con sesion activa."""
    tokens = db.query(models.TokenFCM.token_fcm).join(models.Usuario).filter(
        models.Usuario.rol == models.RolUsuarioEnum.operador,
        models.TokenFCM.activo == True
    ).all()
    return [token[0] for token in tokens]