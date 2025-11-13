from fastapi import FastAPI, Request
from app.routes.routers import router as api_router
from app.routes.publicEndpoints import router as public_router
from app.routes.routers_optimizado import router as optimizado_router

from app.routes_hard.privacy_policy import router as privacy_router
from app.routes_hard.gallery import router as gallery_router
from app.routes.routers_admin import router as admin_router
from app.routes_hard.reset_password_web import router as reset_password_router

import time


# Crear la instancia de la aplicación FastAPI
app = FastAPI(
    title="Thermal Monitoring API",
    description="API para monitorear calidad del aire y gestionar usuarios e imágenes",
    version="1.0.0"
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start
    print(f"\nTiempo de respuesta: {process_time:.4f} segundos: {request.url.path}")
    response.headers["X-Process-Time"] = str(f"{process_time:.4f} s")
    return response


# Registrar los routers
app.include_router(api_router)
app.include_router(gallery_router)
app.include_router(public_router)
app.include_router(optimizado_router)
app.include_router(admin_router)
app.include_router(reset_password_router)
app.include_router(privacy_router)


# Punto de entrada para ejecutar la aplicación
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)