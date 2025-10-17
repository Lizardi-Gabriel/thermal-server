from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db
from sqlalchemy import text


router = APIRouter()


# ============================================================================
# HEALTH CHECK Y DIAGNOSTICO
# ============================================================================
@router.get("/", response_model=schemas.HealthCheckResponse)
def health_check():
    """Verificar estado del servicio"""
    return {
        "status": "ok",
        "message": "API funcionando correctamente"
    }


@router.get("/db-test", response_model=schemas.MessageResponse)
def test_database_connection(db: Session = Depends(get_db)):
    """Probar conexion a base de datos"""
    try:
        db.execute(text('SELECT 1'))
        return {
            "status": "success",
            "message": "Conexion a base de datos exitosa"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de conexion: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE USUARIOS
# ============================================================================

@router.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Crear nuevo usuario en el sistema"""
    # Verificar si username ya existe
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya existe"
        )

    # Verificar si email ya existe
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electronico ya esta registrado"
        )

    return crud.create_user(db=db, user=user)


@router.get("/users/{user_id}", response_model=schemas.UserResponse)
def obtener_usuario(user_id: int, db: Session = Depends(get_db)):
    """Obtener informacion de un usuario especifico"""
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return db_user


@router.get("/users", response_model=List[schemas.UserResponse])
def listar_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar todos los usuarios con paginacion"""
    return crud.get_users(db=db, skip=skip, limit=limit)


# ============================================================================
# ENDPOINT PRINCIPAL: GUARDAR IMAGEN CON DETECCIONES
# ============================================================================

@router.post("/images/with-detections", response_model=schemas.ImageWithDetections, status_code=status.HTTP_201_CREATED)
def guardar_imagen_con_detecciones(
        image_path: str,
        detections: List[schemas.DetectionBase],
        db: Session = Depends(get_db)
):
    """
    Body:
    {
        "image_path": "https://storage.azure.com/container/imagen_20251014_123456.jpg",
        "detections": [
            {
                "confianza": 0.85,
                "x1": 100,
                "y1": 200,
                "x2": 300,
                "y2": 400
            },
            {
                "confianza": 0.92,
                "x1": 500,
                "y1": 150,
                "x2": 650,
                "y2": 350
            }
        ]
    }
    """
    # Crear registro de imagen
    image_create = schemas.ImageCreate(image_path=image_path)
    db_image = crud.create_image(db=db, image=image_create)

    # Guardar todas las detecciones
    created_detections = []
    for detection_data in detections:
        detection_create = schemas.DetectionCreate(
            image_id=db_image.image_id,
            confianza=detection_data.confianza,
            x1=detection_data.x1,
            y1=detection_data.y1,
            x2=detection_data.x2,
            y2=detection_data.y2
        )
        db_detection = crud.create_detection(db=db, detection=detection_create)
        created_detections.append(db_detection)

    # Refrescar imagen para obtener numero actualizado de detecciones
    db.refresh(db_image)

    return {
        **db_image.__dict__,
        "detections": created_detections
    }


# ============================================================================
# ENDPOINTS DE IMAGENES
# ============================================================================

@router.get("/images/{image_id}", response_model=schemas.ImageComplete)
def obtener_imagen(image_id: int, db: Session = Depends(get_db)):
    """Obtener imagen con todas sus detecciones y confirmaciones"""
    db_image = crud.get_image_by_id(db, image_id=image_id)
    if db_image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada"
        )

    # Cargar relaciones
    detections = crud.get_detections_by_image(db, image_id=image_id)
    confirmations = crud.get_confirmations_by_image(db, image_id=image_id)

    return {
        **db_image.__dict__,
        "detections": detections,
        "confirmations": confirmations
    }


@router.get("/images", response_model=List[schemas.ImageResponse])
def listar_imagenes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar todas las imagenes ordenadas por fecha (mas reciente primero)"""
    return crud.get_images(db=db, skip=skip, limit=limit)


@router.get("/images/with-detections/list", response_model=List[schemas.ImageResponse])
def listar_imagenes_con_detecciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar solo imagenes que tienen al menos una deteccion"""
    return crud.get_images_with_detections(db=db, skip=skip, limit=limit)


@router.delete("/images/{image_id}", response_model=schemas.MessageResponse)
def eliminar_imagen(image_id: int, db: Session = Depends(get_db)):
    """Eliminar imagen y todas sus detecciones y confirmaciones asociadas"""
    success = crud.delete_image(db, image_id=image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada"
        )
    return {
        "status": "success",
        "message": f"Imagen {image_id} eliminada correctamente"
    }


# ============================================================================
# ENDPOINTS DE DETECCIONES
# ============================================================================

@router.get("/detections", response_model=List[schemas.DetectionResponse])
def listar_detecciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar todas las detecciones ordenadas por fecha (mas reciente primero)"""
    return crud.get_detections(db=db, skip=skip, limit=limit)


@router.get("/detections/by-confidence/{min_confidence}", response_model=List[schemas.DetectionResponse])
def listar_detecciones_por_confianza(min_confidence: float, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar detecciones con confianza mayor o igual al minimo especificado"""
    if min_confidence < 0.0 or min_confidence > 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La confianza debe estar entre 0.0 y 1.0"
        )
    return crud.get_detections_by_confidence(db=db, min_confidence=min_confidence, skip=skip, limit=limit)


@router.get("/detections/image/{image_id}", response_model=List[schemas.DetectionResponse])
def listar_detecciones_por_imagen(image_id: int, db: Session = Depends(get_db)):
    """Obtener todas las detecciones de una imagen especifica"""
    # Verificar que la imagen existe
    db_image = crud.get_image_by_id(db, image_id=image_id)
    if db_image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada"
        )
    return crud.get_detections_by_image(db=db, image_id=image_id)


@router.get("/detections/{detection_id}", response_model=schemas.DetectionResponse)
def obtener_deteccion(detection_id: int, db: Session = Depends(get_db)):
    """Obtener informacion de una deteccion especifica"""
    db_detection = crud.get_detection_by_id(db, detection_id=detection_id)
    if db_detection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deteccion no encontrada"
        )
    return db_detection


# ============================================================================
# ENDPOINTS DE CONFIRMACIONES
# ============================================================================

@router.post("/confirmations", response_model=schemas.ConfirmationResponse, status_code=status.HTTP_201_CREATED)
def crear_confirmacion(confirmation: schemas.ConfirmationCreate, db: Session = Depends(get_db)):
    """Crear confirmacion (usuario confirma o rechaza una imagen con detecciones)"""
    # Verificar que la imagen existe
    db_image = crud.get_image_by_id(db, image_id=confirmation.image_id)
    if db_image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada"
        )

    # Verificar que el usuario existe
    db_user = crud.get_user_by_id(db, user_id=confirmation.user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return crud.create_confirmation(db=db, confirmation=confirmation)


@router.get("/confirmations", response_model=List[schemas.ConfirmationResponse])
def listar_confirmaciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar todas las confirmaciones ordenadas por fecha (mas reciente primero)"""
    return crud.get_confirmations(db=db, skip=skip, limit=limit)


@router.get("/confirmations/user/{user_id}", response_model=List[schemas.ConfirmationResponse])
def listar_confirmaciones_por_usuario(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtener todas las confirmaciones realizadas por un usuario"""
    # Verificar que el usuario existe
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return crud.get_confirmations_by_user(db=db, user_id=user_id, skip=skip, limit=limit)


@router.get("/confirmations/status/{status}", response_model=List[schemas.ConfirmationResponse])
def listar_confirmaciones_por_estado(status: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtener confirmaciones filtradas por estado (confirmed o rejected)"""
    if status not in ["confirmed", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estado debe ser 'confirmed' o 'rejected'"
        )
    return crud.get_confirmations_by_status(db=db, status=status, skip=skip, limit=limit)


# ============================================================================
# ENDPOINTS DE CALIDAD DEL AIRE
# ============================================================================

@router.post("/air-quality", response_model=schemas.AirQualityResponse, status_code=status.HTTP_201_CREATED)
def crear_registro_calidad_aire(air_quality: schemas.AirQualityCreate, db: Session = Depends(get_db)):
    """Crear nuevo registro de calidad del aire"""
    return crud.create_air_quality(db=db, air_quality=air_quality)


@router.get("/air-quality/latest", response_model=schemas.AirQualityResponse)
def obtener_ultima_calidad_aire(db: Session = Depends(get_db)):
    """Obtener el registro mas reciente de calidad del aire"""
    latest = crud.get_latest_air_quality(db=db)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay registros de calidad del aire"
        )
    return latest


@router.get("/air-quality/averages/{hours}")
def obtener_promedios_calidad_aire(hours: int, db: Session = Depends(get_db)):
    """Calcular promedios de calidad del aire en las ultimas N horas"""
    if hours <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El numero de horas debe ser mayor a 0"
        )
    return crud.get_air_quality_averages(db=db, hours=hours)


@router.get("/air-quality", response_model=List[schemas.AirQualityResponse])
def listar_registros_calidad_aire(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar registros de calidad del aire ordenados por fecha (mas reciente primero)"""
    return crud.get_air_quality_records(db=db, skip=skip, limit=limit)


@router.get("/air-quality/{record_id}", response_model=schemas.AirQualityResponse)
def obtener_registro_calidad_aire(record_id: int, db: Session = Depends(get_db)):
    """Obtener registro especifico de calidad del aire"""
    record = crud.get_air_quality_by_id(db, record_id=record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro no encontrado"
        )
    return record


# ============================================================================
# ENDPOINTS statusIsla
# ============================================================================


@router.post("/statusIsla", status_code=status.HTTP_200_OK)
def recibir_status_isla(payload: schemas.StatusPayload):
    print(f"Status recibido: {payload.status} a las {payload.timestamp}")

    # Guardar el status al final de  archivo de texto
    with open("status_isla.txt", "w") as f:
        f.write(f"status: {payload.status}, timestamp: {payload.timestamp}\n")

    return {"detail": f"Status '{payload.status}' recibido correctamente."}


# ver el status de la isla
@router.get("/statusIsla", response_model=schemas.StatusPayload)
def obtener_status_isla():
    try:
        with open("status_isla.txt", "r") as f:
            lines = f.readlines()
            status_line = lines[0].strip()
            timestamp_line = lines[1].strip()

            status_value = status_line.split(": ")[1]
            timestamp_value = timestamp_line.split(": ")[1]

            return schemas.StatusPayload(status=status_value, timestamp=timestamp_value)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se ha recibido ningun status aun."
        )
