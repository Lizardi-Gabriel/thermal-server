from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app import crud
from app.database import get_db

router = APIRouter()


@router.get("/gallery", response_class=HTMLResponse)
def mostrar_galeria(db: Session = Depends(get_db)):
    """mostrar galeria HTML con todas las imagenes detectadas"""

    # obtener todas las imagenes con detecciones
    images = crud.get_images_with_detections(db=db, skip=0, limit=1000)

    # generar HTML dinamico
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Galeria de Detecciones</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            h1 {
                color: white;
                text-align: center;
                margin-bottom: 10px;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .stats {
                text-align: center;
                color: white;
                margin-bottom: 30px;
                font-size: 1.2em;
            }
            
            .gallery {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 25px;
                padding: 20px;
            }
            
            .card {
                background: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .card:hover {
                transform: translateY(-10px);
                box-shadow: 0 15px 40px rgba(0,0,0,0.4);
            }
            
            .card img {
                width: 100%;
                height: 300px;
                object-fit: cover;
                cursor: pointer;
            }
            
            .card-info {
                padding: 15px;
            }
            
            .card-title {
                font-size: 0.9em;
                color: #666;
                margin-bottom: 8px;
            }
            
            .card-detections {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 0.9em;
            }
            
            .card-date {
                color: #999;
                font-size: 0.85em;
                margin-top: 8px;
            }
            
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.9);
                animation: fadeIn 0.3s;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            .modal-content {
                margin: auto;
                display: block;
                max-width: 90%;
                max-height: 90%;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
            }
            
            .close {
                position: absolute;
                top: 20px;
                right: 40px;
                color: #f1f1f1;
                font-size: 50px;
                font-weight: bold;
                cursor: pointer;
                transition: 0.3s;
            }
            
            .close:hover {
                color: #bbb;
            }
            
            .no-images {
                text-align: center;
                color: white;
                font-size: 1.5em;
                margin-top: 50px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Galeria de Detecciones de Cigarros</h1>
            <div class="stats">
                Total de imagenes: """ + str(len(images)) + """
            </div>
            
            <div class="gallery">
    """

    if not images:
        html_content += """
                <div class="no-images">No hay imagenes con detecciones disponibles</div>
        """
    else:
        for img in images:
            # formatear fecha
            fecha = img.upload_time.strftime("%d/%m/%Y %H:%M:%S")

            html_content += f"""
                <div class="card">
                    <img src="{img.image_path}" alt="Deteccion {img.image_id}" onclick="openModal('{img.image_path}')">
                    <div class="card-info">
                        <div class="card-title">ID: {img.image_id}</div>
                        <span class="card-detections">{img.number_of_detections} cigarros detectados</span>
                        <div class="card-date">{fecha}</div>
                    </div>
                </div>
            """

    html_content += """
            </div>
        </div>
        
        <div id="imageModal" class="modal" onclick="closeModal()">
            <span class="close">&times;</span>
            <img class="modal-content" id="modalImage">
        </div>
        
        <script>
            function openModal(imageSrc) {
                const modal = document.getElementById('imageModal');
                const modalImg = document.getElementById('modalImage');
                modal.style.display = 'block';
                modalImg.src = imageSrc;
            }
            
            function closeModal() {
                document.getElementById('imageModal').style.display = 'none';
            }
            
            document.addEventListener('keydown', function(event) {
                if (event.key === 'Escape') {
                    closeModal();
                }
            });
        </script>
    </body>
    </html>
    """

    return html_content