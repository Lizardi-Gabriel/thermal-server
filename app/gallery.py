from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app import crud
from app.database import get_db
from datetime import date
from typing import Optional

router = APIRouter()


@router.get("/gallery", response_class=HTMLResponse)
def mostrar_galeria_eventos(db: Session = Depends(get_db), fecha: Optional[date] = Query(default=None)):
    """
    Genera y devuelve una página web HTML responsiva con Tailwind CSS, optimizada para móviles.
    Muestra los eventos para una fecha seleccionada, con una tarjeta para cada evento.
    Por defecto, muestra los eventos de la fecha actual.
    """

    # Si no se proporciona una fecha en la URL (?fecha=YYYY-MM-DD), se usa la del día de hoy.
    target_date = fecha if fecha else date.today()

    # Se obtienen los eventos de la base de datos usando la función CRUD existente.
    eventos = crud.get_eventos_por_fecha(db=db, fecha_evento=target_date)

    # --- Construcción dinámica de las tarjetas de evento ---
    cards_html = ""
    if not eventos:
        cards_html = """
            <div class="text-center text-gray-400 mt-10">
                <p class="text-lg">No se encontraron eventos para esta fecha.</p>
            </div>
        """
    else:
        for evento in eventos:
            # Lógica para procesar y calcular los datos de cada evento.

            # Imagen de vista previa (la primera del evento).
            preview_image_url = "https://placehold.co/600x400?text=No+Image"
            if evento.imagenes:
                preview_image_url = evento.imagenes[0].ruta_imagen

            # Mapeo del estado del evento a colores de Tailwind CSS.
            status_map = {
                'confirmado': ('bg-green-500', 'Confirmado'),
                'descartado': ('bg-red-500', 'Descartado'),
                'pendiente': ('bg-yellow-500', 'Pendiente')
            }
            status_color, status_text = status_map.get(evento.estatus.value, ('bg-gray-500', 'Desconocido'))

            # Horas de inicio y fin del evento.
            hora_inicio_str = "--:--"
            if evento.imagenes:
                hora_inicio_str = evento.imagenes[0].hora_subida.strftime("%H:%M:%S")

            hora_fin_str = ""
            # La hora de fin solo se muestra si el evento no está 'pendiente'.
            if evento.estatus.value != 'pendiente' and len(evento.imagenes) > 0:
                hora_fin_str = f"""
                    <div class="flex items-center text-sm text-gray-300">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        <span>Fin: {evento.imagenes[-1].hora_subida.strftime("%H:%M:%S")}</span>
                    </div>
                """

            # Cálculo del número máximo de detecciones (fumadores) en una sola imagen del evento.
            max_detecciones = 0
            if evento.imagenes:
                max_detecciones = max((len(img.detecciones) for img in evento.imagenes), default=0)

            descripcion = evento.descripcion or "Sin descripción disponible."

            # Construcción del HTML para cada tarjeta.
            cards_html += f"""
                <div class="bg-gray-800 rounded-lg overflow-hidden shadow-2xl">
                    <img src="{preview_image_url}" alt="Vista previa del evento" class="w-full h-48 object-cover cursor-pointer" onclick="openModal('{preview_image_url}')">
                    
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
                            <span class="text-sm ml-1">(máx. detectados)</span>
                        </div>
                        
                        <div>
                            <p class="text-sm text-gray-400 leading-relaxed">{descripcion}</p>
                        </div>
                    </div>
                </div>
            """

    # --- Plantilla HTML Completa ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Galería de Eventos</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background-color: #111827; }}
        </style>
    </head>
    <body class="text-white">
        <div class="max-w-md mx-auto p-4">
            <header class="text-center my-6">
                <h1 class="text-3xl font-bold tracking-tight">Galería de Eventos</h1>
                <p class="text-gray-400">Monitorización de actividad</p>
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

        <div id="imageModal" class="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center p-4 z-50 hidden" onclick="closeModal()">
            <div class="relative">
                <img id="modalImage" src="" alt="Imagen ampliada" class="max-w-[90vw] max-h-[90vh] rounded-lg">
            </div>
        </div>

        <script>
            const datePicker = document.getElementById('date-picker');
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');

            // Recargar la página con la nueva fecha al cambiar el selector.
            datePicker.addEventListener('change', function() {{
                window.location.href = `/gallery?fecha=${{this.value}}`;
            }});

            function openModal(imageSrc) {{
                modalImg.src = imageSrc;
                modal.classList.remove('hidden');
            }}

            function closeModal() {{
                modal.classList.add('hidden');
            }}
            
            // Cerrar modal con la tecla Escape.
            document.addEventListener('keydown', function(event) {{
                if (event.key === 'Escape' && !modal.classList.contains('hidden')) {{
                    closeModal();
                }}
            }});
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)