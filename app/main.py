import os
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.logging import logger as app_logger
from app.routes.routers import router as api_router
from app.routes.publicEndpoints import router as public_router
from app.routes.routers_optimizado import router as optimizado_router
from app.routes.routers_admin import router as admin_router


allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS").split(",")
    if origin.strip()
]

MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT"))
if not MEDIA_ROOT.is_absolute():
    MEDIA_ROOT = Path.cwd() / MEDIA_ROOT

try:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
except OSError:
    MEDIA_ROOT = Path.cwd() / "media"
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)


# Crear la instancia de la aplicación FastAPI
app = FastAPI(
    title="Thermal Monitoring API",
    description="API para monitorear calidad del aire y gestionar usuarios e imágenes",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(MEDIA_ROOT)), name="static")


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start
    app_logger.info(f"Tiempo de respuesta: {process_time:.4f} segundos | path={request.url.path}")
    response.headers["X-Process-Time"] = str(f"{process_time:.4f} s")
    return response


# Registrar los routers
# La capa de presentación se mueve a Angular. El backend queda como API REST JSON pura.
app.include_router(api_router)
app.include_router(public_router)
app.include_router(optimizado_router)
app.include_router(admin_router)


# Punto de entrada para ejecutar la aplicación
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)