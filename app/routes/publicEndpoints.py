import os
import secrets
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, BackgroundTasks, Request, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, date
from typing import Optional
from loguru import logger

from app import crud, schemas, models
from app.database import get_db, SessionLocal
from app.schemas import DescripcionImagenRequest

from app.services import security
from app.services.aire import consumir_api_aire

from app.services.llm_service import obtener_descripcion_de_imagen

router = APIRouter()


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):

    # 1. Busca el usuario en la base de datos
    user = crud.get_user_by_username(db, nombre_usuario=form_data.username)

    # 2. Verifica si el usuario existe y la contraseña es correcta
    if not user or not security.verificar_password(form_data.password, user.hash_contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Crea el token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.crear_access_token(
        data={"sub": user.nombre_usuario}, expires_delta=access_token_expires
    )

    # 4. Devuelve el token
    return {"access_token": access_token, "token_type": "bearer"}


# ENDPOINTS DE EVENTOS

@router.post("/eventos", response_model=schemas.Evento, status_code=status.HTTP_201_CREATED)
def crear_evento(evento: schemas.EventoCreate, db: Session = Depends(get_db)):
    """Crea un nuevo evento. Requiere autenticacion."""

    # Crear el evento
    nuevo_evento = crud.create_evento(db=db, evento=evento)

    # Notificaciones push desactivadas: la infraestructura de Firebase ya no se usa.
    # Se mantiene la creación del evento sin bloquear la respuesta.
    return nuevo_evento


# ENDPOINTS DE LOGS

@router.get("/logs", response_model=list[schemas.LogSistema])
def listar_logs(
    fecha: Optional[date] = Query(default=None),
    tipo: Optional[models.TipoLogEnum] = Query(default=None),
    skip: int = Query(default=0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(default=50, ge=1, le=500, description="Máximo de registros a devolver"),
    db: Session = Depends(get_db),
):
    """Lista logs del más reciente al más antiguo, con filtros y paginación skip/limit."""
    return crud.get_logs(db=db, fecha_log=fecha, tipo_log=tipo, skip=skip, limit=limit)


@router.post("/eventos/{evento_id}/imagenes/upload", status_code=status.HTTP_201_CREATED)
async def subir_imagen_evento(
    evento_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(security.get_current_user),
):
    """Sube una imagen para un evento y devuelve su URL pública local."""
    if not crud.get_evento_by_id(db, evento_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado.")

    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    content_type = file.content_type or ""
    filename = file.filename or "imagen"
    extension = Path(filename).suffix.lower()

    if content_type not in allowed_types and extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no válido. Se aceptan JPG, PNG y WEBP."
        )

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extensión de archivo no válida."
        )

    media_root = Path(os.getenv("MEDIA_ROOT", "/var/data/fotos")).resolve()
    if not media_root.is_absolute():
        media_root = (Path.cwd() / media_root).resolve()

    try:
        media_root.mkdir(parents=True, exist_ok=True)
    except OSError:
        media_root = (Path.cwd() / "media").resolve()
        media_root.mkdir(parents=True, exist_ok=True)

    evento_dir = media_root / "eventos" / str(evento_id)
    if not crud.get_evento_by_id(db, evento_id):
        evento_dir = media_root / "temp" / str(uuid4())

    evento_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid4().hex}{extension}"
    file_path = evento_dir / safe_name

    try:
        with file_path.open("wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)
    except Exception:
        logger.exception("Error guardando imagen en disco para evento_id={}", evento_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo guardar la imagen en el servidor."
        )

    relative_path = file_path.relative_to(media_root)
    public_url = f"/static/{relative_path.as_posix().replace('\\', '/')}"
    file_size = file_path.stat().st_size

    logger.debug(
        "Imagen subida correctamente para evento_id={} | archivo={} | url={} | size={} bytes",
        evento_id,
        file_path.name,
        public_url,
        file_size,
    )

    return {
        "success": True,
        "file_name": file_path.name,
        "url": public_url,
        "size": file_size,
    }


# ENDPOINT COMBINADO para Imagen y Detecciones

@router.post("/eventos/{evento_id}/imagenes", response_model=schemas.Imagen, status_code=status.HTTP_201_CREATED)
def agregar_imagen_con_detecciones(evento_id: int, data: schemas.ImagenConDetecciones, db: Session = Depends(get_db)):
    """
    Añade una nueva imagen a un evento, junto con todas sus detecciones.
    """
    # Verificamos que el evento exista primero
    if not crud.get_evento_by_id(db, evento_id):
        raise HTTPException(status_code=404, detail="Evento no encontrado.")

    datos_aire = consumir_api_aire()

    if datos_aire is not None:
        descripcion = getattr(datos_aire, "descrip", "") or ""
        if not descripcion.startswith("WEATHERLINK_"):
            # Creamos un nuevo registro de calidad del aire asociado al evento
            calidad_aire_data = schemas.CalidadAireCreate(
                evento_id=evento_id,
                temp=datos_aire.temp,
                humedad=datos_aire.humedad,
                pm1p0=datos_aire.pm1p0,
                pm2p5=datos_aire.pm2p5,
                pm10=datos_aire.pm10,
                aqi=datos_aire.aqi,
                descrip=datos_aire.descrip,
                hora_medicion=datos_aire.hora_medicion,
                tipo=schemas.TipoMedicionEnum.durante
            )
            crud.create_calidad_aire(db, registro=calidad_aire_data)


    return crud.create_imagen_con_detecciones(db, evento_id=evento_id, imagen=data.imagen, detecciones=data.detecciones)


# ENDPOINTS DE LOGS

@router.post("/logs", response_model=schemas.LogSistema, status_code=status.HTTP_201_CREATED)
def crear_log(log: schemas.LogSistemaCreate, db: Session = Depends(get_db)):
    """ Crea un nuevo log del sistema. """
    return crud.create_log(db=db, log=log)



@router.post("/auth/forgot-password")
async def solicitar_recuperacion_password( solicitud: schemas.SolicitudRecuperacionPassword, db: Session = Depends(get_db) ):
    """
    Solicitar recuperacion de contraseña.
    Envia un correo con un enlace para restablecer la contraseña.
    """

    # Buscar usuario por correo
    usuario = crud.get_user_by_email(db, correo_electronico=solicitud.correo_electronico)

    # No revelar si el correo existe o no
    mensaje_exito = {
        "mensaje": "Si el correo existe en nuestro sistema, recibiras un enlace de recuperacion"
    }

    if not usuario:
        # Retornar mensaje generico sin revelar que el usuario no existe
        return mensaje_exito

    # Generar token unico
    token = secrets.token_urlsafe(32)

    # Guardar token en BD
    crud.crear_token_recuperacion(db, usuario.usuario_id, token, minutos_expiracion=30)


    # El servicio de correo fue removido; se registra el evento y se devuelve la respuesta genérica.
    crud.create_log(db, log=schemas.LogSistemaCreate(
        tipo=models.TipoLogEnum.info,
        mensaje=f"Solicitud de recuperacion de contraseña para usuario: {usuario.nombre_usuario} (email service deshabilitado)"
    ))

    return mensaje_exito


@router.get("/auth/validate-reset-token/{token}")
async def validar_token_recuperacion(token: str, db: Session = Depends(get_db)):
    """Validar si un token de recuperacion es valido."""

    es_valido, mensaje = crud.validar_token_recuperacion(db, token)

    return schemas.ValidarTokenResponse(
        valido=es_valido,
        mensaje=mensaje
    )


@router.post("/auth/reset-password")
async def restablecer_password(datos: schemas.RestablecerPassword, db: Session = Depends(get_db)):
    """Restablecer contraseña usando un token valido."""

    # Validar token
    es_valido, mensaje = crud.validar_token_recuperacion(db, datos.token)

    if not es_valido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=mensaje
        )

    # Obtener token y usuario
    db_token = crud.obtener_token_recuperacion(db, datos.token)
    usuario = crud.get_user_by_id(db, db_token.usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Actualizar contraseña
    nueva_password_hash = security.hashear_password(datos.nueva_password)
    usuario.hash_contrasena = nueva_password_hash

    # Marcar token como usado
    crud.marcar_token_como_usado(db, datos.token)

    db.commit()

    # Crear log del sistema
    crud.create_log(db, log=schemas.LogSistemaCreate(
        tipo=models.TipoLogEnum.info,
        mensaje=f"Contraseña restablecida para usuario: {usuario.nombre_usuario}"
    ))

    return schemas.RestablecerPasswordResponse(
        exito=True,
        mensaje="Contraseña restablecida exitosamente"
    )


def procesar_y_guardar_descripcion(evento_id: int, imagen_b64: str):
    """
    Función que se ejecuta en segundo plano.
    Crea su propia sesión de BD, llama a Ollama y actualiza el evento.
    """
    logger.debug("Iniciando análisis IA para evento_id={}", evento_id)

    # Crear una nueva sesión de base de datos manual
    db_session = SessionLocal()

    try:
        evento = db_session.query(models.Evento).filter(models.Evento.evento_id == evento_id).first()
        if not evento:
            logger.warning("Evento no encontrado en análisis IA: {}", evento_id)
            return

        descripcion_ia = obtener_descripcion_de_imagen(
            imagen_b64
        )

        if descripcion_ia:
            nueva_descripcion = f"{descripcion_ia}".strip()

            evento.descripcion = nueva_descripcion

            db_session.commit()
            logger.info("Evento actualizado con descripción de IA: {}", evento_id)
        else:

            crud.create_log(
                db_session,
                log=schemas.LogSistemaCreate(
                    tipo=models.TipoLogEnum.error,
                    mensaje=f"error descripción imagen evento_id={evento_id}"
                )
            )

    except Exception:
        logger.exception("Error crítico en background task LLM para evento_id={}", evento_id)
        db_session.rollback()
    finally:
        # Cerrar la sesión
        db_session.close()


@router.post("/eventos/{evento_id}/descripcion", status_code=200)
async def agregar_descripcion_ia(
        evento_id: int,
        request: DescripcionImagenRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """
    Recibe una imagen en Base64, responde inmediatamente al cliente
    y lanza el proceso de Ollama en segundo plano.
    """
    if not crud.get_evento_by_id(db, evento_id):
        raise HTTPException(status_code=404, detail="Evento no encontrado.")

    logger.debug("Solicitado análisis IA en segundo plano para evento_id={}", evento_id)
    # Agendar la tarea en segundo plano
    background_tasks.add_task(
        procesar_y_guardar_descripcion,
        evento_id,
        request.imagen_base64
    )

    return {"mensaje": "Imagen recibida. analisis desc en segundo plano."}
