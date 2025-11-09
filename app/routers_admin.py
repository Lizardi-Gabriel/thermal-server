from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from fastapi.responses import FileResponse
from app.reportes_pdf import generar_reporte_pdf
from datetime import date as date_type, datetime

from app import crud, schemas, models, security
from app.database import get_db



router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(security.verificar_rol_admin)]
)



@router.get("/reportes/generar-pdf")
def generar_reporte_pdf_endpoint(
        fecha_inicio: Optional[date_type] = Query(None),
        fecha_fin: Optional[date_type] = Query(None),
        db: Session = Depends(get_db)
):
    """
    Genera un reporte PDF completo con estadisticas, graficas y eventos.

    Parametros opcionales:
    - fecha_inicio: Fecha inicio del periodo (YYYY-MM-DD)
    - fecha_fin: Fecha fin del periodo (YYYY-MM-DD)

    Si no se especifican fechas, se generara un reporte con todos los eventos.
    """

    # Obtener estadisticas
    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d") if fecha_inicio else None
    fecha_fin_str = fecha_fin.strftime("%Y-%m-%d") if fecha_fin else None

    estadisticas = crud.get_estadisticas_eventos(db, fecha_inicio, fecha_fin)

    # Obtener eventos con filtro de fechas
    filtros = schemas.EventosFiltros(
        fecha_inicio=fecha_inicio_str,
        fecha_fin=fecha_fin_str,
        skip=0,
        limit=500  # Maximo 500 eventos en el reporte
    )

    eventos_db, total = crud.get_eventos_optimizado(db, filtros)

    # Convertir eventos a dict con campos calculados
    eventos_list = []
    for evento in eventos_db:
        campos_calculados = crud.calcular_campos_evento(evento, incluir_todas_imagenes=False)

        evento_dict = {
            "evento_id": evento.evento_id,
            "fecha_evento": evento.fecha_evento.strftime("%d/%m/%Y"),
            "descripcion": evento.descripcion,
            "estatus": evento.estatus.value,
            "usuario_id": evento.usuario_id,
            "usuario": {
                "nombre_usuario": evento.usuario.nombre_usuario if evento.usuario else None
            },
            **campos_calculados
        }
        eventos_list.append(evento_dict)

    # Generar nombre del archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_thermal_monitoring_{timestamp}.pdf"
    output_path = f"/tmp/{filename}"

    # Generar PDF
    try:
        generar_reporte_pdf(
            estadisticas=estadisticas,
            eventos=eventos_list,
            fecha_inicio=fecha_inicio_str,
            fecha_fin=fecha_fin_str,
            output_path=output_path
        )

        # Devolver el archivo PDF
        return FileResponse(
            path=output_path,
            media_type='application/pdf',
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el reporte: {str(e)}"
        )


@router.get("/usuarios", response_model=List[schemas.UsuarioListaAdmin])
def listar_todos_usuarios(db: Session = Depends(get_db)):
    """Listar todos los usuarios del sistema con estadisticas."""
    usuarios_con_stats = crud.get_all_users_with_stats(db)
    return usuarios_con_stats


@router.post("/usuarios", response_model=schemas.Usuario, status_code=status.HTTP_201_CREATED)
def crear_usuario_admin(
        user: schemas.UsuarioCreateAdmin,
        db: Session = Depends(get_db)
):
    """Crear un nuevo usuario (solo admin puede crear usuarios)."""
    if crud.get_user_by_username(db, nombre_usuario=user.nombre_usuario):
        raise HTTPException(
            status_code=400,
            detail="El nombre de usuario ya esta en uso."
        )
    if crud.get_user_by_email(db, correo_electronico=user.correo_electronico):
        raise HTTPException(
            status_code=400,
            detail="El correo electronico ya esta registrado."
        )

    # Convertir a UsuarioCreate para reutilizar la funcion
    user_create = schemas.UsuarioCreate(
        nombre_usuario=user.nombre_usuario,
        correo_electronico=user.correo_electronico,
        password=user.password,
        rol=user.rol
    )

    return crud.create_user(db=db, user=user_create)


@router.put("/usuarios/{usuario_id}", response_model=schemas.Usuario)
def actualizar_usuario(
        usuario_id: int,
        user_update: schemas.UsuarioUpdate,
        db: Session = Depends(get_db)
):
    """Actualizar un usuario existente."""
    try:
        db_user = crud.update_user(db, usuario_id, user_update)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return db_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
        usuario_id: int,
        db: Session = Depends(get_db),
        current_user: models.Usuario = Depends(security.get_current_user)
):
    """Eliminar un usuario del sistema."""
    # No permitir que el admin se elimine a si mismo
    if usuario_id == current_user.usuario_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta"
        )

    success = crud.delete_user(db, usuario_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return None


@router.get("/usuarios/{usuario_id}", response_model=schemas.Usuario)
def obtener_usuario(
        usuario_id: int,
        db: Session = Depends(get_db)
):
    """Obtener detalles de un usuario especifico."""
    db_user = crud.get_user_by_id(db, usuario_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return db_user


# ENDPOINTS DE ESTADISTICAS

@router.get("/usuarios/{usuario_id}/estadisticas")
def obtener_estadisticas_usuario( usuario_id: int, db: Session = Depends(get_db)):
    """Obtener estadisticas de un usuario especifico."""

    success = crud.get_estadisticas_users(db, usuario_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return success