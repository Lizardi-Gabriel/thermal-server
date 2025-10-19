from fastapi import FastAPI
from app.routers import router as api_router
from app.gallery import router as gallery_router
from app.publicEndpoints import router as public_router

# Crear la instancia de la aplicación FastAPI
app = FastAPI(
    title="Thermal Monitoring API",
    description="API para monitorear calidad del aire y gestionar usuarios e imágenes",
    version="1.0.0"
)

# Registrar los routers
app.include_router(api_router)
app.include_router(gallery_router)
app.include_router(public_router)

# Punto de entrada para ejecutar la aplicación
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)