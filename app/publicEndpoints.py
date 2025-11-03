from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, date
from typing import Optional

from app import crud, schemas, security, models
from app.aire import consumir_api_aire
from app.database import get_db

from app.firebase_notifications import enviar_notificacion_multiple

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


# ENDPOINTS DE USUARIOS

@router.post("/usuarios", response_model=schemas.Usuario, status_code=status.HTTP_201_CREATED)
def crear_usuario(user: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """ Crea un nuevo usuario. Este endpoint es público. """
    if crud.get_user_by_username(db, nombre_usuario=user.nombre_usuario):
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso.")
    if crud.get_user_by_email(db, correo_electronico=user.correo_electronico):
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")

    return crud.create_user(db=db, user=user)


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

