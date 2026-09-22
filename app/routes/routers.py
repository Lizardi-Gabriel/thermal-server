from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, models
from app.services import security
from app.database import get_db
from datetime import date

router = APIRouter(
    dependencies=[Depends(security.get_current_user)]
)


# ENDPOINTS DE USUARIOS


@router.get("/usuarios/me", response_model=schemas.Usuario)
def read_users_me(current_user: models.Usuario = Depends(security.get_current_user)):
    """ Devuelve la información del usuario actualmente autenticado. """
    return current_user


# ENDPOINTS DE EVENTOS


@router.put("/eventos/{evento_id}/status", response_model=schemas.Evento)
def actualizar_estatus_evento(evento_id: int, estatus: models.EstatusEventoEnum, db: Session = Depends(get_db), current_user: models.Usuario = Depends(
    security.get_current_user)):
    """ Confirma o descarta un evento, asignando al usuario actual como el que realizó la acción. """
    update_data = schemas.EventoUpdate(estatus=estatus, usuario_id=current_user.usuario_id)
    db_evento = crud.update_evento(db, evento_id=evento_id, evento_update=update_data)
    if db_evento is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado.")
    return db_evento


@router.patch("/eventos/{evento_id}/descripcion", response_model=schemas.Evento)
def actualizar_descripcion_evento(evento_id: int, data: schemas.EventoUpateDescripcion, db: Session = Depends(get_db)):
    """ Actualiza únicamente la descripción de un evento (por ejemplo, con análisis de un LLM). """
    db_evento = crud.update_evento_descripcion(db, evento_id, evento_update=data)
    if db_evento is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado.")
    return db_evento


# ENDPOINTS DE CalidadAire

@router.post("/eventos/{evento_id}/calidad-aire", response_model=schemas.CalidadAire, status_code=status.HTTP_201_CREATED)
def agregar_medicion_calidad_aire(evento_id: int, medicion: schemas.CalidadAireBase, db: Session = Depends(get_db)):
    """ Añade un nuevo registro de calidad del aire a un evento específico. """
    if not crud.get_evento_by_id(db, evento_id):
        raise HTTPException(status_code=404, detail="Evento no encontrado.")

    # Creamos el objeto completo para la función crud
    medicion_data = schemas.CalidadAireCreate(evento_id=evento_id, **medicion.model_dump())
    return crud.create_calidad_aire(db, registro=medicion_data)


@router.patch("/calidad-aire/{registro_id}/tipo", response_model=schemas.CalidadAire)
def actualizar_tipo_de_medicion( registro_id: int, nuevo_tipo: schemas.TipoMedicionEnum, db: Session = Depends(get_db)):
    """ Actualiza el tipo de una medición de calidad del aire específica ('antes', 'durante', 'despues'). """
    db_registro = crud.update_calidad_aire_tipo(
        db=db,
        registro_id=registro_id,
        nuevo_tipo=nuevo_tipo
    )

    if db_registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de calidad del aire no encontrado."
        )

    return db_registro


# ENDPOINTS DE ESTADISTICAS

@router.get("/estadisticas/{usuario_id}")
def obtener_estadisticas_usuario( usuario_id: int, db: Session = Depends(get_db)):
    """Obtener estadisticas de un usuario especifico."""

    success = crud.get_estadisticas_users(db, usuario_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return success
