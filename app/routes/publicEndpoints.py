from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, date
from typing import Optional

from app import crud, schemas, models
from app.database import get_db, SessionLocal
from app.schemas import DescripcionImagenRequest

from app.services import security
from app.services.aire import consumir_api_aire
from app.services.firebase_notifications import enviar_notificacion_multiple
from app.services.email_service import enviar_correo_recuperacion

import secrets

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

    # Obtener tokens FCM de todos los operadores activos
    tokens_operadores = crud.get_tokens_operadores_activos(db)

    # Enviar notificaciones a todos los operadores
    if tokens_operadores:
        try:
            enviar_notificacion_multiple(tokens_operadores, nuevo_evento.evento_id)
        except Exception as e:
            print(f"Error al enviar notificaciones push: {e}")
            # No fallar la creacion del evento si las notificaciones fallan

    return nuevo_evento


# ENDPOINTS DE LOGS

@router.get("/logs", response_model=list[schemas.LogSistema])
def listar_logs(fecha: Optional[date] = Query(default=None), tipo: Optional[models.TipoLogEnum] = Query(default=None), db: Session = Depends(get_db)):
    """ Obtiene una lista de logs del sistema con filtros opcionales por fecha y tipo. """
    return crud.get_logs(db=db, fecha_log=fecha, tipo_log=tipo)


# TODO: agrgarlo a un endpoint protegido

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

    if datos_aire.descrip != "error":
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

        crud.create_log(db, log=schemas.LogSistemaCreate(
            nivel="INFO",
            mensaje=f"Se agrega imagen y detecciones, evento: {evento_id}, calidad de aire: {calidad_aire_data.model_dump_json(indent=4)}"
        ))

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
    print(f"Solicitud de recuperacion de contraseña para correo: {solicitud.correo_electronico}")

    # Buscar usuario por correo
    usuario = crud.get_user_by_email(db, correo_electronico=solicitud.correo_electronico)

    # No revelar si el correo existe o no
    mensaje_exito = {
        "mensaje": "Si el correo existe en nuestro sistema, recibiras un enlace de recuperacion"
    }

    if not usuario:
        print(f"Correo: {solicitud.correo_electronico}, no existe")
        # Retornar mensaje generico sin revelar que el usuario no existe
        return mensaje_exito

    # Generar token unico
    token = secrets.token_urlsafe(32)

    # Guardar token en BD
    crud.crear_token_recuperacion(db, usuario.usuario_id, token, minutos_expiracion=30)

    print(f"se enviara correo a: {usuario.correo_electronico}")
    # Enviar correo
    correo_enviado = enviar_correo_recuperacion(
        email_destino=usuario.correo_electronico,
        nombre_usuario=usuario.nombre_usuario,
        token=token
    )

    if not correo_enviado:
        # Log del error pero no revelar al usuario
        print(f"Error al enviar correo a {usuario.correo_electronico}")

    # Crear log del sistema
    crud.create_log(db, log=schemas.LogSistemaCreate(
        tipo=models.TipoLogEnum.info,
        mensaje=f"Solicitud de recuperacion de contraseña para usuario: {usuario.nombre_usuario}"
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
    print(f"--- Iniciando análisis para evento {evento_id} ---")

    # Crear una nueva sesión de base de datos manual
    db_session = SessionLocal()

    try:
        evento = db_session.query(models.Evento).filter(models.Evento.evento_id == evento_id).first()
        if not evento:
            print(f"Evento {evento_id} no encontrado.")
            return

        descripcion_ia = obtener_descripcion_de_imagen(
            imagen_b64
        )

        if descripcion_ia:
            nueva_descripcion = f"{descripcion_ia}".strip()

            evento.descripcion = nueva_descripcion

            db_session.commit()
            print(f"Evento {evento_id} actualizado con descripción de llm.")
        else:
            print(f"error en llm no descripción para evento {evento_id}.")

            crud.create_log(
                db_session,
                log=schemas.LogSistemaCreate(
                    tipo=models.TipoLogEnum.error,
                    mensaje=f"error descripción imagen evento_id={evento_id}"
                )
            )

    except Exception as e:
        print(f"Error crítico en background task llm: {e}")
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

    print('describirndo la img en 2do plano')
    # Agendar la tarea en segundo plano
    background_tasks.add_task(
        procesar_y_guardar_descripcion,
        evento_id,
        request.imagen_base64
    )

    return {"mensaje": "Imagen recibida. analisis desc en segundo plano."}

