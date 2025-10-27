from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, date
from typing import Optional

from app import crud, schemas, security, models
from app.database import get_db

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
    """ Crea un nuevo evento. Requiere autenticación. """
    return crud.create_evento(db=db, evento=evento)


# ENDPOINTS DE LOGS

@router.get("/logs", response_model=list[schemas.LogSistema])
def listar_logs(fecha: Optional[date] = Query(default=None), tipo: Optional[models.TipoLogEnum] = Query(default=None), db: Session = Depends(get_db)):
    """ Obtiene una lista de logs del sistema con filtros opcionales por fecha y tipo. """
    return crud.get_logs(db=db, fecha_log=fecha, tipo_log=tipo)