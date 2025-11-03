from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app import crud, schemas, models, security
from app.database import get_db

router = APIRouter(
    dependencies=[Depends(security.get_current_user)]
)


@router.get("/eventosfront/estadisticas", response_model=schemas.EstadisticasEventos)
def obtener_estadisticas_eventos(
        fecha_inicio: Optional[date] = Query(None),
        fecha_fin: Optional[date] = Query(None),
        db: Session = Depends(get_db)
):
    """
    Obtiene estadisticas generales de eventos.
    Util para dashboards de admin.
    """
    estadisticas = crud.get_estadisticas_eventos(db, fecha_inicio, fecha_fin)
    return schemas.EstadisticasEventos(**estadisticas)


@router.get("/eventosfront/optimizado", response_model=List[schemas.EventoOptimizado])
def listar_eventos_optimizado(
        estatus: Optional[models.EstatusEventoEnum] = Query(None),
        usuario_id: Optional[int] = Query(None),
        fecha_inicio: Optional[date] = Query(None),
        fecha_fin: Optional[date] = Query(None),
        #skip: int = Query(0, ge=0),
        #limit: int = Query(50, ge=1, le=2000),
        db: Session = Depends(get_db)
):
    """
    Obtiene eventos con filtros y campos calculados optimizados.
    Solo incluye la imagen preview (con mas detecciones).

    Filtros disponibles:
    - estatus: pendiente, confirmado, descartado
    - usuario_id: ID del usuario que gestiono el evento
    - fecha_inicio: Fecha inicio del rango
    - fecha_fin: Fecha fin del rango
    """

    filtros = schemas.EventosFiltros(
        estatus=estatus,
        usuario_id=usuario_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
        #skip=skip,
        #limit=limit
    )

    eventos, total_count = crud.get_eventos_optimizado(db, filtros)

    # Construir respuesta con campos calculados (sin todas las imagenes)
    eventos_optimizados = []
    for evento in eventos:
        campos_calculados = crud.calcular_campos_evento(evento, incluir_todas_imagenes=False)

        evento_dict = {
            "evento_id": evento.evento_id,
            "fecha_evento": evento.fecha_evento,
            "descripcion": evento.descripcion,
            "estatus": evento.estatus,
            "usuario_id": evento.usuario_id,
            "usuario": evento.usuario,
            **campos_calculados
        }

        eventos_optimizados.append(schemas.EventoOptimizado(**evento_dict))

    return eventos_optimizados


@router.get("/eventosfront/{evento_id}/optimizado", response_model=schemas.EventoDetalleOptimizado)
def obtener_evento_optimizado(
        evento_id: int,
        db: Session = Depends(get_db)
):
    """
    Obtiene un evento especifico con campos calculados.
    Incluye TODAS las imagenes para el detalle.
    """
    evento = crud.get_evento_by_id(db, evento_id)

    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )

    campos_calculados = crud.calcular_campos_evento(evento, incluir_todas_imagenes=True)

    evento_dict = {
        "evento_id": evento.evento_id,
        "fecha_evento": evento.fecha_evento,
        "descripcion": evento.descripcion,
        "estatus": evento.estatus,
        "usuario_id": evento.usuario_id,
        "usuario": evento.usuario,
        **campos_calculados
    }

    return schemas.EventoDetalleOptimizado(**evento_dict)
