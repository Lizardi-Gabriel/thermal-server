from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_, or_
from typing import List, Optional, Type, Tuple
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


def calcular_campos_evento(evento: models.Evento, incluir_todas_imagenes: bool = False) -> dict:
    """
    Calcula campos derivados de un evento para optimizar el frontend.

    Args:
        evento: Modelo del evento
        incluir_todas_imagenes: Si es True, incluye todas las imagenes. Si es False, solo la preview.
    """

    # Calcular campos de imagenes
    total_imagenes = len(evento.imagenes)
    max_detecciones = max((len(img.detecciones) for img in evento.imagenes), default=0)
    total_detecciones = sum(len(img.detecciones) for img in evento.imagenes)

    # Obtener imagen con mas detecciones para preview
    imagen_preview = None
    if evento.imagenes:
        imagen_preview = max(evento.imagenes, key=lambda img: len(img.detecciones))

    # Calcular horas de inicio y fin
    hora_inicio = None
    hora_fin = None
    if evento.imagenes:
        hora_inicio = evento.imagenes[0].hora_subida.strftime("%H:%M:%S") if evento.imagenes[0].hora_subida else None
        hora_fin = evento.imagenes[-1].hora_subida.strftime("%H:%M:%S") if evento.imagenes[-1].hora_subida else None

    # Calcular promedios de calidad del aire (solo registros con horas unicas)
    registros_unicos = {}
    for registro in evento.registros_calidad_aire:
        if registro.hora_medicion:
            hora = registro.hora_medicion.strftime("%Y-%m-%d %H:%M")
            if hora not in registros_unicos:
                registros_unicos[hora] = registro

    registros_lista = list(registros_unicos.values())

    pm10_values = [r.pm10 for r in registros_lista if r.pm10 is not None]
    pm2p5_values = [r.pm2p5 for r in registros_lista if r.pm2p5 is not None]
    pm1p0_values = [r.pm1p0 for r in registros_lista if r.pm1p0 is not None]

    promedio_pm10 = sum(pm10_values) / len(pm10_values) if pm10_values else None
    promedio_pm2p5 = sum(pm2p5_values) / len(pm2p5_values) if pm2p5_values else None
    promedio_pm1p0 = sum(pm1p0_values) / len(pm1p0_values) if pm1p0_values else None

    resultado = {
        "total_imagenes": total_imagenes,
        "max_detecciones": max_detecciones,
        "total_detecciones": total_detecciones,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "promedio_pm10": promedio_pm10,
        "promedio_pm2p5": promedio_pm2p5,
        "promedio_pm1p0": promedio_pm1p0,
        "imagen_preview": imagen_preview
    }

    # Solo incluir todas las imagenes si se solicita (para detalle)
    if incluir_todas_imagenes:
        resultado["imagenes"] = evento.imagenes
        resultado["registros_calidad_aire"] = evento.registros_calidad_aire

    return resultado


def get_eventos_optimizado(db: Session, filtros: schemas.EventosFiltros ) -> Tuple[List[models.Evento], int]:
    """ Obtiene eventos con filtros y ordenamiento optimizado. Retorna una tupla (eventos, total_count) """
    query = db.query(models.Evento).options(
        joinedload(models.Evento.usuario),
        joinedload(models.Evento.imagenes).joinedload(models.Imagen.detecciones),
        joinedload(models.Evento.registros_calidad_aire)
    )

    # Aplicar filtros
    conditions = []

    if filtros.estatus:
        conditions.append(models.Evento.estatus == filtros.estatus)

    if filtros.usuario_id:
        conditions.append(models.Evento.usuario_id == filtros.usuario_id)

    if filtros.fecha_inicio and filtros.fecha_fin:
        conditions.append(
            and_(
                models.Evento.fecha_evento >= filtros.fecha_inicio,
                models.Evento.fecha_evento <= filtros.fecha_fin
            )
        )
    elif filtros.fecha_inicio:
        conditions.append(models.Evento.fecha_evento >= filtros.fecha_inicio)
    elif filtros.fecha_fin:
        conditions.append(models.Evento.fecha_evento <= filtros.fecha_fin)

    if conditions:
        query = query.filter(and_(*conditions))

    # Contar total sin paginacion
    total_count = query.count()

    # Ordenar por fecha descendente y aplicar paginacion
    eventos = query.order_by(desc(models.Evento.fecha_evento)).all()

    return eventos, total_count


def get_estadisticas_eventos(db: Session, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None) -> dict:
    """Obtiene estadisticas generales de eventos."""

    query = db.query(models.Evento)

    # Aplicar filtros de fecha
    if fecha_inicio and fecha_fin:
        query = query.filter(
            and_(
                models.Evento.fecha_evento >= fecha_inicio,
                models.Evento.fecha_evento <= fecha_fin
            )
        )
    elif fecha_inicio:
        query = query.filter(models.Evento.fecha_evento >= fecha_inicio)
    elif fecha_fin:
        query = query.filter(models.Evento.fecha_evento <= fecha_fin)

    total_eventos = query.count()
    eventos_pendientes = query.filter(models.Evento.estatus == models.EstatusEventoEnum.pendiente).count()
    eventos_confirmados = query.filter(models.Evento.estatus == models.EstatusEventoEnum.confirmado).count()
    eventos_descartados = query.filter(models.Evento.estatus == models.EstatusEventoEnum.descartado).count()

    # Calcular total de detecciones
    eventos = query.options(
        joinedload(models.Evento.imagenes).joinedload(models.Imagen.detecciones)
    ).all()

    total_detecciones = sum(
        len(imagen.detecciones)
        for evento in eventos
        for imagen in evento.imagenes
    )

    promedio_detecciones = total_detecciones / total_eventos if total_eventos > 0 else 0

    return {
        "total_eventos": total_eventos,
        "eventos_pendientes": eventos_pendientes,
        "eventos_confirmados": eventos_confirmados,
        "eventos_descartados": eventos_descartados,
        "total_detecciones": total_detecciones,
        "promedio_detecciones_por_evento": round(promedio_detecciones, 2),
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    }


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


# OPERACIONES CRUD PARA GESTION DE USUARIOS (ADMIN)

def get_all_users_with_stats(db: Session) -> List[dict]:
    """Obtener todos los usuarios con sus estadisticas."""
    usuarios = db.query(models.Usuario).all()

    usuarios_con_stats = []
    for usuario in usuarios:
        # Contar eventos gestionados
        eventos_gestionados = db.query(models.Evento).filter(
            models.Evento.usuario_id == usuario.usuario_id
        ).all()

        total_gestionados = len(eventos_gestionados)
        confirmados = sum(1 for e in eventos_gestionados if e.estatus == models.EstatusEventoEnum.confirmado)
        descartados = sum(1 for e in eventos_gestionados if e.estatus == models.EstatusEventoEnum.descartado)

        usuarios_con_stats.append({
            "usuario_id": usuario.usuario_id,
            "nombre_usuario": usuario.nombre_usuario,
            "correo_electronico": usuario.correo_electronico,
            "rol": usuario.rol,
            "total_eventos_gestionados": total_gestionados,
            "eventos_confirmados": confirmados,
            "eventos_descartados": descartados
        })

    return usuarios_con_stats


def update_user(db: Session, usuario_id: int, user_update: schemas.UsuarioUpdate) -> Optional[models.Usuario]:
    """Actualizar un usuario (solo admin)."""
    db_user = get_user_by_id(db, usuario_id)

    if not db_user:
        return None

    if user_update.nombre_usuario is not None:
        # Verificar que el nuevo nombre no este en uso
        existing = db.query(models.Usuario).filter(
            models.Usuario.nombre_usuario == user_update.nombre_usuario,
            models.Usuario.usuario_id != usuario_id
        ).first()
        if existing:
            raise ValueError("El nombre de usuario ya esta en uso")
        db_user.nombre_usuario = user_update.nombre_usuario

    if user_update.correo_electronico is not None:
        # Verificar que el nuevo correo no este en uso
        existing = db.query(models.Usuario).filter(
            models.Usuario.correo_electronico == user_update.correo_electronico,
            models.Usuario.usuario_id != usuario_id
        ).first()
        if existing:
            raise ValueError("El correo electronico ya esta en uso")
        db_user.correo_electronico = user_update.correo_electronico

    if user_update.password is not None:
        from app.security import hashear_password
        db_user.hash_contrasena = hashear_password(user_update.password)

    if user_update.rol is not None:
        db_user.rol = user_update.rol

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, usuario_id: int) -> bool:
    """Eliminar un usuario (solo admin)."""
    db_user = get_user_by_id(db, usuario_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False