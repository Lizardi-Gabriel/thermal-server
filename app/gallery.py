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


# Mostrar historial de logs del sistema con filtros
@router.get("/historial", response_class=HTMLResponse)
def mostrar_historial_logs(db: Session = Depends(get_db), fecha: Optional[date] = Query(default=None), tipo: Optional[str] = Query(default=None)):

    # Convertir el tipo de string a enum si se proporciona
    tipo_enum = None
    if tipo and tipo != "todos":
        try:
            from app.models import TipoLogEnum
            tipo_enum = TipoLogEnum(tipo)
        except ValueError:
            tipo_enum = None

    # Obtener fecha objetivo
    target_date = fecha if fecha else date.today()

    # Obtener logs filtrados
    logs = crud.get_logs(db=db, fecha_log=target_date, tipo_log=tipo_enum)

    # Mapeo de colores por tipo de log
    tipo_map = {
        'info': ('bg-blue-500', 'text-blue-100', 'border-blue-400'),
        'advertencia': ('bg-yellow-500', 'text-yellow-100', 'border-yellow-400'),
        'error': ('bg-red-500', 'text-red-100', 'border-red-400')
    }

    logs_html = ""
    if not logs:
        logs_html = """
            <div class="col-span-1 text-center text-gray-400 mt-10">
                <svg class="mx-auto h-12 w-12 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p class="text-lg mt-4">No se encontraron logs para esta fecha y filtros.</p>
            </div>
        """
    else:
        for log in logs:
            zona_horaria_mexico = ZoneInfo("America/Mexico_City")
            hora_mexico = log.hora_log.replace(tzinfo=ZoneInfo("UTC")).astimezone(zona_horaria_mexico)
            hora_str = hora_mexico.strftime("%H:%M:%S")
            fecha_str = hora_mexico.strftime("%d/%m/%Y")

            bg_color, text_color, border_color = tipo_map.get(log.tipo.value, ('bg-gray-500', 'text-gray-100', 'border-gray-400'))

            # Icono según tipo de log
            icono = ""
            if log.tipo.value == "info":
                icono = """<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>"""
            elif log.tipo.value == "advertencia":
                icono = """<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>"""
            else:
                icono = """<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>"""

            logs_html += f"""
                <div class="bg-gray-800 rounded-lg p-4 mb-3 shadow-lg border-l-4 {border_color} hover:shadow-xl transition-shadow duration-200">
                    <div class="flex justify-between items-start mb-3">
                        <div class="flex items-center space-x-3">
                            <div class="{bg_color} {text_color} p-2 rounded-full">
                                {icono}
                            </div>
                            <div>
                                <span class="text-sm font-semibold text-gray-300">{fecha_str}</span>
                                <span class="text-sm text-gray-500 ml-2">{hora_str}</span>
                            </div>
                        </div>
                        <span class="px-3 py-1 text-xs font-bold {text_color} {bg_color} rounded-full uppercase">{log.tipo.value}</span>
                    </div>
                    <p class="text-gray-300 leading-relaxed pl-12">{log.mensaje}</p>
                </div>
            """

    # Obtener el valor del filtro actual para mantenerlo seleccionado
    tipo_selected = tipo if tipo else "todos"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Historial de Logs del Sistema</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background-color: #111827; }}
            .filter-transition {{
                transition: all 0.3s ease-in-out;
            }}
        </style>
    </head>
    <body class="text-white">
        <div class="container mx-auto p-4 sm:p-6 lg:p-8">
            <header class="text-center my-6">
                <h1 class="text-3xl font-bold tracking-tight">Historial de Logs del Sistema</h1>
                <p class="text-gray-400">Registros detallados de actividades y eventos</p>
            </header>

            <!-- Filtros -->
            <div class="max-w-4xl mx-auto mb-8 bg-gray-800 rounded-lg p-6 shadow-xl">
                <form id="filterForm" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Filtro de Fecha -->
                    <div>
                        <label for="date-picker" class="block text-sm font-medium text-gray-300 mb-2">
                            <svg class="inline h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            Fecha:
                        </label>
                        <input type="date" id="date-picker" name="fecha" value="{target_date.strftime('%Y-%m-%d')}" 
                               class="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 filter-transition hover:border-blue-400">
                    </div>
                    
                    <!-- Filtro de Tipo -->
                    <div>
                        <label for="tipo-select" class="block text-sm font-medium text-gray-300 mb-2">
                            <svg class="inline h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                            </svg>
                            Tipo de Log:
                        </label>
                        <select id="tipo-select" name="tipo" 
                                class="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 filter-transition hover:border-blue-400">
                            <option value="todos" {"selected" if tipo_selected == "todos" else ""}>Todos</option>
                            <option value="info" {"selected" if tipo_selected == "info" else ""}>Info</option>
                            <option value="advertencia" {"selected" if tipo_selected == "advertencia" else ""}>Advertencia</option>
                            <option value="error" {"selected" if tipo_selected == "error" else ""}>Error</option>
                        </select>
                    </div>
                </form>
                
                <!-- Estadísticas rápidas -->
                <div class="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="text-center p-3 bg-gray-700 rounded-lg">
                        <p class="text-2xl font-bold text-white">{len(logs)}</p>
                        <p class="text-xs text-gray-400">Total Logs</p>
                    </div>
                    <div class="text-center p-3 bg-blue-900 bg-opacity-30 rounded-lg border border-blue-500">
                        <p class="text-2xl font-bold text-blue-400">{sum(1 for log in logs if log.tipo.value == 'info')}</p>
                        <p class="text-xs text-gray-400">Info</p>
                    </div>
                    <div class="text-center p-3 bg-yellow-900 bg-opacity-30 rounded-lg border border-yellow-500">
                        <p class="text-2xl font-bold text-yellow-400">{sum(1 for log in logs if log.tipo.value == 'advertencia')}</p>
                        <p class="text-xs text-gray-400">Advertencias</p>
                    </div>
                    <div class="text-center p-3 bg-red-900 bg-opacity-30 rounded-lg border border-red-500">
                        <p class="text-2xl font-bold text-red-400">{sum(1 for log in logs if log.tipo.value == 'error')}</p>
                        <p class="text-xs text-gray-400">Errores</p>
                    </div>
                </div>
            </div>

            <!-- Contenedor de Logs -->
            <div id="logs-container" class="max-w-4xl mx-auto">
                {logs_html}
            </div>
        </div>

        <script>
            const datePicker = document.getElementById('date-picker');
            const tipoSelect = document.getElementById('tipo-select');
            
            function updateFilters() {{
                const fecha = datePicker.value;
                const tipo = tipoSelect.value;
                const params = new URLSearchParams();
                
                if (fecha) params.append('fecha', fecha);
                if (tipo && tipo !== 'todos') params.append('tipo', tipo);
                
                window.location.href = `/historial?${{params.toString()}}`;
            }}
            
            datePicker.addEventListener('change', updateFilters);
            tipoSelect.addEventListener('change', updateFilters);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)