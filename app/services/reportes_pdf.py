import io
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional
import pytz
import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image

from app.services.aire import obtener_historico_aire

matplotlib.use('Agg')

# definir de Zonas Horarias
UTC_TZ = pytz.utc
MEX_TZ = pytz.timezone('America/Mexico_City')


def convertir_utc_a_mexico(fecha_str: str, hora_str: str) -> datetime:
    """Convierte la hora UTC a horario de México, pero PRESERVA la fecha original del evento."""
    try:
        # Parsear fecha original para referencia
        dt_original_date = datetime.strptime(fecha_str, "%d/%m/%Y")

        # Crear datetime completo ingenuo y localizarlo en UTC
        dt_naive = datetime.strptime(f"{fecha_str} {hora_str}", "%d/%m/%Y %H:%M:%S")
        dt_utc = UTC_TZ.localize(dt_naive)

        # Convertir a hora de México
        dt_mex_calculado = dt_utc.astimezone(MEX_TZ)

        # FORZAR la fecha original combinándola con la hora calculada
        # Esto corrige casos donde la conversión de zona horaria podría cambiar el día
        dt_final = dt_mex_calculado.replace(
            year=dt_original_date.year,
            month=dt_original_date.month,
            day=dt_original_date.day
        )

        return dt_final
    except Exception as e:
        print(f"Error convirtiendo fecha: {e}")
        return datetime.now(MEX_TZ)


def generar_grafica_eventos_por_estatus(eventosStats: dict) -> str:
    labels = ['Confirmados', 'Descartados', 'Pendientes']
    sizes = [
        eventosStats.get('eventos_confirmados', 0),
        eventosStats.get('eventos_descartados', 0),
        eventosStats.get('eventos_pendientes', 0)
    ]

    if sum(sizes) == 0:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'Sin eventos registrados',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)
        ax.axis('off')
    else:
        colorsChart = ['#4CAF50', '#D32F2F', '#1976D2']
        explode = (0.05, 0.05, 0.05)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(sizes, explode=explode, labels=labels, colors=colorsChart, autopct='%1.1f%%', shadow=True, startangle=90)
        ax.axis('equal')
        plt.title('Distribución de Eventos por Estatus', fontsize=14, fontweight='bold')

    imgBuffer = io.BytesIO()
    plt.savefig(imgBuffer, format='png', bbox_inches='tight', dpi=150)
    imgBuffer.seek(0)
    plt.close()

    tempPath = f"/tmp/grafica_estatus_{datetime.now().timestamp()}.png"
    with open(tempPath, 'wb') as f:
        f.write(imgBuffer.getvalue())

    return tempPath


def generar_grafica_diaria(fecha_mex_str: str, eventos_del_dia: List[dict], registros: List, start_buffer: datetime, end_buffer: datetime) -> Optional[str]:
    """
    Genera una grafica para un dia usando los registros ya consultados.
    """
    try:
        if not eventos_del_dia:
            return None

        # Procesar eventos para graficar las franjas rojas
        eventos_procesados = []
        for evento in eventos_del_dia:
            inicio_mex = convertir_utc_a_mexico(evento.get('fecha_evento'), evento.get('hora_inicio'))
            fin_mex = convertir_utc_a_mexico(evento.get('fecha_evento'), evento.get('hora_fin'))

            eventos_procesados.append({
                'inicio': inicio_mex,
                'fin': fin_mex,
                'id': evento.get('evento_id')
            })

        # Procesar datos de aire para graficar
        tiempos_mex = []
        valores_pm1 = []
        valores_pm25 = []
        valores_pm10 = []

        if registros:
            # Ordenamos por hora para asegurar lineas correctas
            registros.sort(key=lambda x: x.hora_medicion)

            for r in registros:
                # Convertir timestamp a datetime zona Mexico
                if isinstance(r.hora_medicion, (int, float)):
                    dt_utc = datetime.fromtimestamp(r.hora_medicion, pytz.utc)
                elif isinstance(r.hora_medicion, datetime):
                    dt_utc = r.hora_medicion if r.hora_medicion.tzinfo else pytz.utc.localize(r.hora_medicion)
                else:
                    continue

                dt_mex = dt_utc.astimezone(MEX_TZ)

                tiempos_mex.append(dt_mex)
                valores_pm1.append(r.pm1p0)
                valores_pm25.append(r.pm2p5)
                valores_pm10.append(r.pm10)

        # Configurar Grafica
        fig, ax = plt.subplots(figsize=(12, 6))

        # Plotear lineas si hay datos
        if tiempos_mex:
            ax.plot(tiempos_mex, valores_pm1, label='PM1', color='#ff6ffb', linewidth=1, alpha=0.7)
            ax.plot(tiempos_mex, valores_pm25, label='PM2.5', color='#FF9800', linewidth=2)
            ax.plot(tiempos_mex, valores_pm10, label='PM10', color='#003e79', linewidth=1, linestyle='--')

        # Plotear franjas de eventos
        for ev in eventos_procesados:
            ax.axvspan(ev['inicio'], ev['fin'], color='red', alpha=0.3)

        ax.set_title(f'Monitoreo de Calidad del Aire - {fecha_mex_str}', fontsize=12, fontweight='bold')
        ax.set_ylabel('Concentración (μg/m³)')
        ax.set_xlabel('Hora')

        # Formato de fecha en eje X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=MEX_TZ))
        ax.tick_params(axis='x', rotation=45)

        # Grid y Leyenda
        ax.grid(True, alpha=0.3)
        from matplotlib.lines import Line2D
        customLines = [
            Line2D([0], [0], color='#ff6ffb', lw=1),
            Line2D([0], [0], color='#FF9800', lw=2),
            Line2D([0], [0], color='#003e79', lw=1, linestyle='--'),
            matplotlib.patches.Patch(facecolor='red', edgecolor='red', alpha=0.3, label='Evento')
        ]
        ax.legend(customLines, ['PM1', 'PM2.5', 'PM10', 'Evento'], loc='upper right')

        # Ajustar limites X estrictamente al buffer calculado
        ax.set_xlim(left=start_buffer, right=end_buffer)

        plt.tight_layout()

        # Guardar imagen
        filename_safe = fecha_mex_str.replace('/', '-')
        tempPath = f"/tmp/grafica_dia_{filename_safe}_{datetime.now().timestamp()}.png"
        plt.savefig(tempPath, format='png', bbox_inches='tight', dpi=150)
        plt.close()

        return tempPath

    except Exception as e:
        print(f"Error generando grafica diaria {fecha_mex_str}: {e}")
        import traceback
        traceback.print_exc()
        return None


def calcular_maximos_evento(evento: dict, registros: List) -> dict:
    """
    Calcula el valor máximo de PM1, PM2.5 y PM10 durante el evento y hasta 10 minutos después.
    """
    try:
        if not registros:
            return {'max_pm1': 0.0, 'max_pm25': 0.0, 'max_pm10': 0.0}

        # Calcular ventana de tiempo: Inicio Evento -> Fin Evento + 10 min
        inicio_evento = convertir_utc_a_mexico(evento.get('fecha_evento'), evento.get('hora_inicio'))
        fin_evento = convertir_utc_a_mexico(evento.get('fecha_evento'), evento.get('hora_fin'))

        # Agregamos 10 minutos al final
        fin_ventana = fin_evento + timedelta(minutes=10)

        max_pm1 = 0.0
        max_pm25 = 0.0
        max_pm10 = 0.0

        datos_encontrados = False

        for r in registros:
            # Convertir hora registro a datetime timezone aware (Mexico)
            if isinstance(r.hora_medicion, (int, float)):
                dt_utc = datetime.fromtimestamp(r.hora_medicion, pytz.utc)
            elif isinstance(r.hora_medicion, datetime):
                dt_utc = r.hora_medicion if r.hora_medicion.tzinfo else pytz.utc.localize(r.hora_medicion)
            else:
                continue

            dt_reg = dt_utc.astimezone(MEX_TZ)

            # Verificar si el registro cae dentro de la ventana (Inicio <= Registro <= Fin + 10min)
            if inicio_evento <= dt_reg <= fin_ventana:
                datos_encontrados = True
                if r.pm1p0 > max_pm1: max_pm1 = r.pm1p0
                if r.pm2p5 > max_pm25: max_pm25 = r.pm2p5
                if r.pm10 > max_pm10: max_pm10 = r.pm10

        if not datos_encontrados:
            return {'max_pm1': 0.0, 'max_pm25': 0.0, 'max_pm10': 0.0}

        return {
            'max_pm1': max_pm1,
            'max_pm25': max_pm25,
            'max_pm10': max_pm10
        }

    except Exception as e:
        print(f"Error calculando maximos para evento {evento.get('evento_id')}: {e}")
        return {'max_pm1': 0.0, 'max_pm25': 0.0, 'max_pm10': 0.0}


def generar_reporte_pdf(
        estadisticas: dict,
        eventos: List[dict],
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        output_path: str = "/tmp/reporte.pdf"
) -> str:

    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()

    # Estilos
    colorPrincipal = colors.HexColor('#263238')
    colorSecundario = colors.HexColor('#546E7A')
    colorTextoCabecera = colors.whitesmoke

    titleStyle = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colorPrincipal, spaceAfter=30, alignment=TA_CENTER, fontName='Helvetica-Bold')
    subtitleStyle = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontSize=16, textColor=colorSecundario, spaceAfter=12, spaceBefore=12, fontName='Helvetica-Bold')

    # estilo para la nota
    noteStyle = ParagraphStyle('NoteStyle', parent=styles['BodyText'], fontSize=9, textColor=colors.grey, alignment=TA_JUSTIFY, spaceAfter=10)

    normalStyle = styles['BodyText']
    normalStyle.alignment = TA_LEFT

    # PORTADA Y RESUMEN
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("REPORTE DE MONITOREO TÉRMICO", titleStyle))
    story.append(Spacer(1, 0.3*inch))
    fechaReporte = datetime.now(MEX_TZ).strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(f"Fecha de generación: {fechaReporte} (CDMX)", styles['Normal']))
    if fecha_inicio and fecha_fin:
        story.append(Paragraph(f"Período consultado: {fecha_inicio} a {fecha_fin}", styles['Normal']))
    story.append(PageBreak())

    # SECCION 1
    story.append(Paragraph("1. RESUMEN EJECUTIVO", subtitleStyle))
    resumenData = [
        ['Métrica', 'Valor'],
        ['Total de Eventos', str(estadisticas.get('total_eventos', 0))],
        ['Eventos Pendientes', str(estadisticas.get('eventos_pendientes', 0))],
        ['Eventos Confirmados', str(estadisticas.get('eventos_confirmados', 0))],
        ['Total de Detecciones', str(estadisticas.get('total_detecciones', 0))],
    ]
    resumenTable = Table(resumenData, colWidths=[3*inch, 2*inch])
    resumenTable.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colorPrincipal),
        ('TEXTCOLOR', (0, 0), (-1, 0), colorTextoCabecera),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(resumenTable)
    story.append(Spacer(1, 0.3*inch))

    graficaEstatusPath = generar_grafica_eventos_por_estatus(estadisticas)
    if graficaEstatusPath and os.path.exists(graficaEstatusPath):
        img = Image(graficaEstatusPath, width=5*inch, height=3.75*inch)
        story.append(img)
    story.append(PageBreak())

    story.append(Paragraph("2. ANÁLISIS DIARIO DE CALIDAD DEL AIRE", subtitleStyle))
    story.append(Paragraph("A continuación se grafica el historial de la calidad del aire y el historial de "
                           "detección de eventos confirmados en la isla de datos urbanos en la ESCOM.", normalStyle))
    story.append(Spacer(1, 0.2*inch))

    # Agrupar eventos por día
    eventos_por_dia_local = defaultdict(list)
    for ev in eventos:
        fecha_str_raw = ev.get('fecha_evento')
        estatus = ev.get('estatus')
        if fecha_str_raw and estatus == 'confirmado':
            eventos_por_dia_local[fecha_str_raw].append(ev)

    if eventos_por_dia_local:
        dias_ordenados = sorted(eventos_por_dia_local.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))

        for fecha_str in dias_ordenados:
            eventos_del_dia = eventos_por_dia_local[fecha_str]

            story.append(Paragraph(f"Día: {fecha_str}", styles['Heading3']))
            story.append(Paragraph(f"Eventos en este día: {len(eventos_del_dia)}", styles['Normal']))

            # 1. Calcular Rango de Tiempo para la consulta (Min Inicio - 30m, Max Fin + 30m)
            min_hora_mex = None
            max_hora_mex = None

            for evento in eventos_del_dia:
                inicio_mex = convertir_utc_a_mexico(evento.get('fecha_evento'), evento.get('hora_inicio'))
                fin_mex = convertir_utc_a_mexico(evento.get('fecha_evento'), evento.get('hora_fin'))

                if min_hora_mex is None or inicio_mex < min_hora_mex: min_hora_mex = inicio_mex
                if max_hora_mex is None or fin_mex > max_hora_mex: max_hora_mex = fin_mex

            start_buffer = min_hora_mex - timedelta(minutes=30)
            end_buffer = max_hora_mex + timedelta(minutes=30)

            ts_start = int(start_buffer.timestamp())
            ts_end = int(end_buffer.timestamp())

            # Consultar Histórico UNA VEZ por día
            registros_dia = obtener_historico_aire(ts_start, ts_end)
            if registros_dia:
                registros_filtrados = [r for r in registros_dia if r.pm1p0 > 0]
            else:
                registros_filtrados = []

            # Generar Gráfica pasando los registros
            graficaDiaPath = generar_grafica_diaria(fecha_str, eventos_del_dia, registros_filtrados, start_buffer, end_buffer)

            if graficaDiaPath and os.path.exists(graficaDiaPath):
                imgDia = Image(graficaDiaPath, width=7*inch, height=3.5*inch)
                story.append(imgDia)
            else:
                story.append(Paragraph("No se pudo generar la gráfica (sin datos históricos).", styles['Italic']))

            # CALCULAR MAXIMOS para cada evento usando los registros consultados
            for evento in eventos_del_dia:
                maximos = calcular_maximos_evento(evento, registros_filtrados)
                evento['max_pm1'] = maximos['max_pm1']
                evento['max_pm25'] = maximos['max_pm25']
                evento['max_pm10'] = maximos['max_pm10']

            story.append(Spacer(1, 0.4*inch))
    else:
        story.append(Paragraph("No hay eventos confirmados para graficar en el periodo seleccionado.", normalStyle))

    story.append(PageBreak())

    # SECCION 3: DETALLE DE EVENTOS (TABLA)
    story.append(Paragraph("3. DETALLE DE EVENTOS", subtitleStyle))

    # Nota explicativa solicitada
    nota_texto = "<b>Nota:</b> Las columnas 'Max' representan cuánto subió la contaminación a su punto máximo durante el evento o hasta 10 minutos después de que finalizó."
    story.append(Paragraph(nota_texto, noteStyle))
    story.append(Spacer(1, 0.1*inch))

    if eventos:
        # Headers de tabla actualizados
        # Ajustamos headers para que quepan
        headers = ['ID', 'Fecha', 'Hora', 'Estatus', 'PM1', 'Max\nPM1', 'PM2.5', 'Max\nPM2.5', 'PM10', 'Max\nPM10']
        eventosData = [headers]

        for evento in eventos:
            dt_inicio_mex = convertir_utc_a_mexico(evento.get('fecha_evento'), evento.get('hora_inicio'))

            fecha_local = dt_inicio_mex.strftime("%d/%m") # Formato corto para ahorrar espacio
            hora_local = dt_inicio_mex.strftime("%H:%M")

            # Valores Promedio
            prom_pm1 = f"{evento.get('promedio_pm1p0', 0):.1f}" if evento.get('promedio_pm1p0') else "-"
            prom_pm25 = f"{evento.get('promedio_pm2p5', 0):.1f}" if evento.get('promedio_pm2p5') else "-"
            prom_pm10 = f"{evento.get('promedio_pm10', 0):.1f}" if evento.get('promedio_pm10') else "-"

            # Valores Maximos (calculados arriba, o 0 si no es confirmado/no hubo datos)
            # Si el evento no fue procesado en el loop de graficas (ej. no confirmado), estos keys no existiran
            max_pm1 = f"{evento.get('max_pm1', 0):.1f}" if evento.get('max_pm1') else "-"
            max_pm25 = f"{evento.get('max_pm25', 0):.1f}" if evento.get('max_pm25') else "-"
            max_pm10 = f"{evento.get('max_pm10', 0):.1f}" if evento.get('max_pm10') else "-"

            # Acortar estatus para que quepa mejor
            estatus_corto = evento.get('estatus', '').upper()
            if len(estatus_corto) > 10: estatus_corto = estatus_corto[:9] + "."

            eventosData.append([
                str(evento.get('evento_id', '')),
                fecha_local,
                hora_local,
                estatus_corto,
                prom_pm1,
                max_pm1,
                prom_pm25,
                max_pm25,
                prom_pm10,
                max_pm10
            ])

        # Definir anchos de columnas (Total ~7.5 inch disponible)
        # ID, Fec, Hor, Est, PM1, Max1, PM2.5, Max2.5, PM10, Max10
        col_widths = [0.4*inch, 0.65*inch, 0.65*inch, 0.8*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch]

        eventosTable = Table(eventosData, colWidths=col_widths)
        eventosTable.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colorPrincipal),
            ('TEXTCOLOR', (0, 0), (-1, 0), colorTextoCabecera),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8), # Letra un poco más chica para que quepan datos
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(eventosTable)

    doc.build(story)
    return output_path
