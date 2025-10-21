from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app import crud
from app.database import get_db
from datetime import date
from typing import Optional
import json
from zoneinfo import ZoneInfo

router = APIRouter()


@router.get("/gallery", response_class=HTMLResponse)
def mostrar_galeria_eventos(db: Session = Depends(get_db), fecha: Optional[date] = Query(default=None)):

    target_date = fecha if fecha else date.today()

    eventos = crud.get_eventos_por_fecha(db=db, fecha_evento=target_date)

    # Construir dinamicamente las tarjetas de evento
    cards_html = ""
    if not eventos:
        cards_html = """
            <div class="col-span-1 md:col-span-2 lg:col-span-3 text-center text-gray-400 mt-10">
                <p class="text-lg">No se encontraron eventos para esta fecha.</p>
            </div>
        """
    else:
        contador = 0
        for evento in eventos:
            contador += 1
            # Obtener todas las URLs de las imagenes del evento

            imagenes_con_detecciones = []
            if evento.imagenes:
                for img in evento.imagenes:
                    detecciones_data = [
                        {'x_min': d.x1, 'y_min': d.y1, 'x_max': d.x2, 'y_max': d.y2}
                        for d in img.detecciones
                    ]
                    imagenes_con_detecciones.append({
                        'url': img.ruta_imagen,
                        'detections': detecciones_data
                    })
            imagenes_json = json.dumps(imagenes_con_detecciones)

            # Imagen de vista previa (la primera del evento)
            preview_image_url = "https://placehold.co/600x400?text=No+Image"

            if evento.imagenes:
                # preview_image_url = evento.imagenes[0].ruta_imagen
                # usar la imagen con mayor numero de detecciones como preview
                preview_image = max(evento.imagenes, key=lambda img: len(img.detecciones))
                preview_image_url = preview_image.ruta_imagen

            # Mapear estado del evento a colores de Tailwind CSS
            status_map = {
                'confirmado': ('bg-green-500', 'Confirmado'),
                'descartado': ('bg-red-500', 'Descartado'),
                'pendiente': ('bg-yellow-500', 'Pendiente')
            }
            status_color, status_text = status_map.get(evento.estatus.value, ('bg-gray-500', 'Desconocido'))

            # Obtener horas de inicio y fin del evento
            hora_inicio_str = "--:--"
            hora_fin_str = "--:--"

            if evento.imagenes:
                hora_inicio_naive = evento.imagenes[0].hora_subida
                hora_fin_naive = evento.imagenes[-1].hora_subida

                # Convertir a la zona horaria de la Ciudad de Mexico
                zona_horaria_mexico = ZoneInfo("America/Mexico_City")
                hora_inicio_mexico = hora_inicio_naive.replace(tzinfo=ZoneInfo("UTC")).astimezone(zona_horaria_mexico)
                hora_fin_mexico = hora_fin_naive.replace(tzinfo=ZoneInfo("UTC")).astimezone(zona_horaria_mexico)

                hora_inicio_str = hora_inicio_mexico.strftime("%H:%M:%S")
                hora_fin_str = hora_fin_mexico.strftime("%H:%M:%S")

            max_detecciones = max((len(img.detecciones) for img in evento.imagenes), default=0) if evento.imagenes else 0
            descripcion = evento.descripcion or "Sin descripcion disponible."
            numero_evento = evento.evento_id

            cards_html += f"""
                <div class="bg-gray-800 rounded-lg overflow-hidden shadow-2xl flex flex-col">
                    <img src="{preview_image_url}" alt="Vista previa del evento" class="w-full h-48 object-cover cursor-pointer" onclick='openModal({imagenes_json})'>
                    
                    <div class="p-4 flex flex-col flex-grow">
                        <div class="flex justify-between items-center mb-2">
                            <p class="text-sm text-gray-400">{evento.fecha_evento.strftime("%d/%m/%Y")}</p>
                            <span class="px-3 py-1 text-xs font-semibold text-white {status_color} rounded-full">{status_text}</span>
                        </div>
                        
                        <div class="flex justify-between items-center mb-3">
                           <div class="flex items-center text-sm text-gray-300">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                <span>Inicio: {hora_inicio_str}</span>
                           </div>
                           <div class="flex items-center text-sm text-gray-300">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                <span>Fin: {hora_fin_str}</span>
                           </div>
                        </div>
                        
                        <div class="flex items-center text-gray-300 mb-4">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor"><path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 001.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" /><path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" /></svg>
                            <span class="font-bold">{max_detecciones} fumadores</span>
                            <span class="text-sm ml-1">(max. detectados)</span>
                        </div>
                        
                        <div class="flex-grow">
                            <p class="text-sm text-gray-400 leading-relaxed">{descripcion}</p>
                        </div>
                        
                        <div class="flex justify-between items-center mt-4 pt-4 border-t border-gray-700">
                            <div class="text-sm text-gray-500">
                                <span>Evento del dia: {contador}</span>
                            </div>
                            <div class="text-sm text-gray-500">
                                <button onclick="deleteEvent({numero_evento}, this)" 
                                    class="bg-red-600 hover:bg-red-700 text-white text-xs font-bold py-1 px-3 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50">
                                Borrar
                                </button>
                            </div>
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
            /* Animacion de desvanecimiento para borrar tarjetas */
            .fade-out {{
                transition: opacity 0.5s ease-out;
                opacity: 0;
            }}
        </style>
    </head>
    <body class="text-white">
        <div class="container mx-auto p-4 sm:p-6 lg:p-8">
            <header class="text-center my-6">
                <h1 class="text-3xl font-bold tracking-tight">Galeria de Eventos</h1>
                <p class="text-gray-400">Monitorizacion de actividad</p>
            </header>

            <form id="dateForm" class="mb-8 max-w-sm mx-auto">
                <label for="date-picker" class="block text-sm font-medium text-gray-300 mb-2">Seleccionar fecha:</label>
                <input type="date" id="date-picker" name="fecha" value="{target_date.strftime('%Y-%m-%d')}" 
                       class="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5">
            </form>

            <div id="gallery-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {cards_html}
            </div>
        </div>

        <div id="imageModal" class="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center p-4 z-50 hidden" onclick="closeModalOnBackground(event)">
            <div class="relative max-w-5xl w-full" onclick="event.stopPropagation()">
                <button onclick="closeModal()" class="absolute top-2 right-2 z-10 bg-gray-800 hover:bg-gray-700 text-white rounded-full p-2 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
                <div class="relative flex items-center justify-center">
                    <button id="prevBtn" onclick="previousImage()" class="absolute left-2 z-10 bg-gray-800 hover:bg-gray-700 text-white rounded-full p-3 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
                    </button>
                    <div class="text-center">
                        <canvas id="modalCanvas" class="max-w-[90vw] max-h-[80vh] rounded-lg mx-auto"></canvas>
                        <p id="imageCounter" class="text-gray-300 mt-3 text-sm"></p>
                    </div>
                    <button id="nextBtn" onclick="nextImage()" class="absolute right-2 z-10 bg-gray-800 hover:bg-gray-700 text-white rounded-full p-3 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
                    </button>
                </div>
            </div>
        </div>

        <script>
            const datePicker = document.getElementById('date-picker');
            const modal = document.getElementById('imageModal');
            const modalCanvas = document.getElementById('modalCanvas');
            const imageCounter = document.getElementById('imageCounter');
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            
            let currentImages = [];
            let currentIndex = 0;

            datePicker.addEventListener('change', function() {{
                window.location.href = `/gallery?fecha=${{this.value}}`;
            }});

            // Funciones del Modal
            function openModal(images) {{
                if (!images || images.length === 0) return;
                currentImages = images;
                currentIndex = 0;
                showImage();
                modal.classList.remove('hidden');
            }}
            
            function showImage() {{
                if (currentImages.length === 0) return;
            
                // 1. Obtener datos de la imagen actual (URL y detecciones)
                const imageData = currentImages[currentIndex];
                const detections = imageData.detections || [];
            
                // 2. Preparar el canvas
                const ctx = modalCanvas.getContext('2d');
            
                // 3. Cargar la nueva imagen
                const img = new Image();
                img.src = imageData.url;
            
                // 4. Cuando la imagen esté cargada, dibujarla en el canvas
                img.onload = () => {{
                                   // Ajustar el tamaño del canvas a las dimensiones reales de la imagen
                modalCanvas.width = img.naturalWidth;
                modalCanvas.height = img.naturalHeight;
            
                // Dibujar la imagen de fondo
                ctx.drawImage(img, 0, 0);
            
                // Dibujar cada una de las detecciones sobre la imagen
                detections.forEach(det => {{
                // Calcular ancho y alto del rectángulo
                const width = det.x_max - det.x_min;
                const height = det.y_max - det.y_min;
            
                // Configurar el estilo del rectángulo (color, grosor)
                ctx.strokeStyle = '#01FF01'; // Color rojo vivo
                ctx.lineWidth = 2;
            
                // Dibujar el rectángulo
                ctx.strokeRect(det.x_min, det.y_min, width, height);
            
                ctx.fillStyle = '#FF0000';
                ctx.font = 'bold 18px Arial';
                // Coloca el texto un poco arriba del cuadro
                ctx.fillText('', det.x_min, det.y_min - 10);
                }});
                }};
            
                // Actualizar contador y botones (como antes)
                imageCounter.textContent = `Imagen ${{currentIndex + 1}} de ${{currentImages.length}}`;
                prevBtn.disabled = currentIndex === 0;
                nextBtn.disabled = currentIndex === currentImages.length - 1;
            }}

            

            function previousImage() {{ if (currentIndex > 0) {{ currentIndex--; showImage(); }} }}
            function nextImage() {{ if (currentIndex < currentImages.length - 1) {{ currentIndex++; showImage(); }} }}
            function closeModal() {{ modal.classList.add('hidden'); }}
            function closeModalOnBackground(event) {{ if (event.target === modal) closeModal(); }}

            // Funcion para borrar evento (Ejemplo)
            function deleteEvent(eventId, buttonElement) {{
                if (confirm(`¿Estas seguro de que quieres borrar el evento #${{eventId}}?`)) {{
                    // logica de llamada a la API:
                    // fetch(`/events/${{eventId}}`, {{ method: 'DELETE' }})
                    // .then(response => {{
                    //     if (response.ok) {{
                    //         console.log('Evento borrado');
                    //         // Eliminar la tarjeta del DOM
                    //         const card = buttonElement.closest('.bg-gray-800');
                    //         card.classList.add('fade-out');
                    //         setTimeout(() => card.remove(), 500);
                    //     }} else {{
                    //         alert('Error al borrar el evento.');
                    //     }}
                    // }});
                    
                    // Simulacion:
                    console.log(`Borrando evento con ID: ${{eventId}}`);
                    const card = buttonElement.closest('.bg-gray-800');
                    card.classList.add('fade-out');
                    setTimeout(() => card.remove(), 500);
                }}
            }}
            
            // Navegacion del Modal con teclado
            document.addEventListener('keydown', function(event) {{
                if (modal.classList.contains('hidden')) return;
                if (event.key === 'Escape') closeModal();
                if (event.key === 'ArrowLeft') previousImage();
                if (event.key === 'ArrowRight') nextImage();
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)