from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app import crud
from app.database import get_db
from datetime import date
from typing import Optional
import json

router = APIRouter()


@router.get("/gallery", response_class=HTMLResponse)
def mostrar_galeria_eventos(db: Session = Depends(get_db), fecha: Optional[date] = Query(default=None)):
    """
    Genera y devuelve una pagina web HTML responsiva con Tailwind CSS, optimizada para moviles.
    Muestra los eventos para una fecha seleccionada, con una tarjeta para cada evento.
    Por defecto, muestra los eventos de la fecha actual.
    """

    # Obtener fecha objetivo
    target_date = fecha if fecha else date.today()

    # Obtener eventos de la base de datos
    eventos = crud.get_eventos_por_fecha(db=db, fecha_evento=target_date)

    # Construir dinamicamente las tarjetas de evento
    cards_html = ""
    if not eventos:
        cards_html = """
            <div class="text-center text-gray-400 mt-10">
                <p class="text-lg">No se encontraron eventos para esta fecha.</p>
            </div>
        """
    else:
        for evento in eventos:
            # Obtener todas las URLs de las imagenes del evento
            imagenes_urls = [img.ruta_imagen for img in evento.imagenes] if evento.imagenes else []
            imagenes_json = json.dumps(imagenes_urls)

            # Imagen de vista previa (la primera del evento)
            preview_image_url = "https://placehold.co/600x400?text=No+Image"
            if evento.imagenes:
                preview_image_url = evento.imagenes[0].ruta_imagen

            # Mapear estado del evento a colores de Tailwind CSS
            status_map = {
                'confirmado': ('bg-green-500', 'Confirmado'),
                'descartado': ('bg-red-500', 'Descartado'),
                'pendiente': ('bg-yellow-500', 'Pendiente')
            }
            status_color, status_text = status_map.get(evento.estatus.value, ('bg-gray-500', 'Desconocido'))

            # Obtener horas de inicio y fin del evento
            hora_inicio_str = "--:--"
            if evento.imagenes:
                hora_inicio_str = evento.imagenes[0].hora_subida.strftime("%H:%M:%S")

            hora_fin_str = ""
            if len(evento.imagenes) > 0:
                hora_fin_str = f"""
                    <div class="flex items-center text-sm text-gray-300">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        <span>Fin: {evento.imagenes[-1].hora_subida.strftime("%H:%M:%S")}</span>
                    </div>
                """

            # Calcular numero maximo de detecciones (fumadores) en una sola imagen del evento
            max_detecciones = 0
            if evento.imagenes:
                max_detecciones = max((len(img.detecciones) for img in evento.imagenes), default=0)

            descripcion = evento.descripcion or "Sin descripcion disponible."

            numero_evento = evento.evento_id

            # Construir HTML para cada tarjeta
            cards_html += f"""
                <div class="bg-gray-800 rounded-lg overflow-hidden shadow-2xl">
                    <img src="{preview_image_url}" alt="Vista previa del evento" class="w-full h-48 object-cover cursor-pointer" onclick='openModal({imagenes_json})'>
                    
                    <div class="p-4">
                        <div class="flex justify-between items-center mb-2">
                            <p class="text-sm text-gray-400">{evento.fecha_evento.strftime("%d/%m/%Y")}</p>
                            <span class="px-3 py-1 text-xs font-semibold text-white {status_color} rounded-full">{status_text}</span>
                        </div>
                        
                        <div class="flex justify-between items-center mb-3">
                           <div class="flex items-center text-sm text-gray-300">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                <span>Inicio: {hora_inicio_str}</span>
                           </div>
                           {hora_fin_str}
                        </div>
                        
                        <div class="flex items-center text-gray-300 mb-4">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor"><path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 001.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" /><path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" /></svg>
                            <span class="font-bold">{max_detecciones} fumadores</span>
                            <span class="text-sm ml-1">(max. detectados)</span>
                        </div>
                        
                        <div>
                            <p class="text-sm text-gray-400 leading-relaxed">{descripcion}</p>
                        </div>
                        
                        <div class="mt-4 text-sm text-gray-500">
                            <span>Número de evento: {numero_evento}</span>
                        </div>
                    </div>
                </div>
            """

    # Plantilla HTML completa
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Galeria de Eventos</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background-color: #111827; }}
        </style>
    </head>
    <body class="text-white">
        <div class="max-w-md mx-auto p-4">
            <header class="text-center my-6">
                <h1 class="text-3xl font-bold tracking-tight">Galeria de Eventos</h1>
                <p class="text-gray-400">Monitorizacion de actividad</p>
            </header>

            <form id="dateForm" class="mb-8">
                <label for="date-picker" class="block text-sm font-medium text-gray-300 mb-2">Seleccionar fecha:</label>
                <input type="date" id="date-picker" name="fecha" value="{target_date.strftime('%Y-%m-%d')}" 
                       class="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5">
            </form>

            <div id="gallery-container" class="space-y-6">
                {cards_html}
            </div>
        </div>

        <div id="imageModal" class="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center p-4 z-50 hidden" onclick="closeModalOnBackground(event)">
            <div class="relative max-w-5xl w-full" onclick="event.stopPropagation()">
                <button onclick="closeModal()" class="absolute top-2 right-2 z-10 bg-gray-800 hover:bg-gray-700 text-white rounded-full p-2 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
                
                <div class="relative flex items-center justify-center">
                    <button id="prevBtn" onclick="previousImage()" class="absolute left-2 z-10 bg-gray-800 hover:bg-gray-700 text-white rounded-full p-3 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                        </svg>
                    </button>
                    
                    <div class="text-center">
                        <img id="modalImage" src="" alt="Imagen ampliada" class="max-w-[90vw] max-h-[80vh] rounded-lg mx-auto">
                        <p id="imageCounter" class="text-gray-300 mt-3 text-sm"></p>
                    </div>
                    
                    <button id="nextBtn" onclick="nextImage()" class="absolute right-2 z-10 bg-gray-800 hover:bg-gray-700 text-white rounded-full p-3 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <script>
            const datePicker = document.getElementById('date-picker');
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');
            const imageCounter = document.getElementById('imageCounter');
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            
            let currentImages = [];
            let currentIndex = 0;

            // Recargar la pagina con la nueva fecha al cambiar el selector
            datePicker.addEventListener('change', function() {{
                window.location.href = `/gallery?fecha=${{this.value}}`;
            }});

            function openModal(images) {{
                currentImages = images;
                currentIndex = 0;
                showImage();
                modal.classList.remove('hidden');
            }}

            function showImage() {{
                if (currentImages.length === 0) return;
                
                modalImg.src = currentImages[currentIndex];
                imageCounter.textContent = `Imagen ${{currentIndex + 1}} de ${{currentImages.length}}`;
                
                // Actualizar estado de botones
                prevBtn.disabled = currentIndex === 0;
                nextBtn.disabled = currentIndex === currentImages.length - 1;
            }}

            function previousImage() {{
                if (currentIndex > 0) {{
                    currentIndex--;
                    showImage();
                }}
            }}

            function nextImage() {{
                if (currentIndex < currentImages.length - 1) {{
                    currentIndex++;
                    showImage();
                }}
            }}

            function closeModal() {{
                modal.classList.add('hidden');
                currentImages = [];
                currentIndex = 0;
            }}

            function closeModalOnBackground(event) {{
                if (event.target === modal) {{
                    closeModal();
                }}
            }}
            
            // Cerrar modal con la tecla Escape
            document.addEventListener('keydown', function(event) {{
                if (!modal.classList.contains('hidden')) {{
                    if (event.key === 'Escape') {{
                        closeModal();
                    }} else if (event.key === 'ArrowLeft') {{
                        previousImage();
                    }} else if (event.key === 'ArrowRight') {{
                        nextImage();
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)