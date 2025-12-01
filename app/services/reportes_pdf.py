import io
import os
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image

from app.services.aire import obtener_historico_aire

matplotlib.use('Agg')


def generar_grafica_eventos_por_estatus(eventosStats: dict) -> str:
    # generar grafica de pastel para resumen de estatus
    labels = ['Confirmados', 'Descartados', 'Pendientes']
    sizes = [
        eventosStats.get('eventos_confirmados', 0),
        eventosStats.get('eventos_descartados', 0),
        eventosStats.get('eventos_pendientes', 0)
    ]

    # validar si hay datos para graficar
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


def generar_grafica_diaria(fechaStr: str, eventosDelDia: List[dict]) -> Optional[str]:
    # generar grafica lineal del dia con marcas de eventos
    try:
        # definir rango del dia para contexto historico completo
        fechaBase = datetime.strptime(fechaStr, "%d/%m/%Y")
        inicioDia = fechaBase.replace(hour=0, minute=0, second=0)
        finDia = fechaBase.replace(hour=23, minute=59, second=59)

        tsStart = int(inicioDia.timestamp())
        tsEnd = int(finDia.timestamp())

        # obtener registros de aire para el dia
        registros = obtener_historico_aire(tsStart, tsEnd)

        if not registros:
            print(f"DEBUG: No se encontraron registros para {fechaStr}")
            return None

        # filtrar registros validos
        registrosFiltrados = [
            r for r in registros
            if r.pm1p0 > 0 and r.pm2p5 > 0 and r.pm10 > 0
        ]

        if not registrosFiltrados:
            print(f"DEBUG: Registros encontrados pero filtrados por valores cero para {fechaStr}")
            return None

        registrosFiltrados.sort(key=lambda x: x.hora_medicion)

        # diagnostico de datos
        print(f"DEBUG: Graficando {len(registrosFiltrados)} puntos para {fechaStr}")

        tiempos = [r.hora_medicion for r in registrosFiltrados]
        valoresPm1 = [r.pm1p0 for r in registrosFiltrados]
        valoresPm25 = [r.pm2p5 for r in registrosFiltrados]
        valoresPm10 = [r.pm10 for r in registrosFiltrados]

        fig, ax = plt.subplots(figsize=(12, 6))

        # plotear lineas de historico
        ax.plot(tiempos, valoresPm1, label='PM1', color='#ff6ffb', linewidth=1, alpha=0.7)
        ax.plot(tiempos, valoresPm25, label='PM2.5', color='#FF9800', linewidth=2)
        ax.plot(tiempos, valoresPm10, label='PM10', color='#795548', linewidth=1, linestyle='--')

        # iterar eventos para pintar franjas de duracion
        for evento in eventosDelDia:
            horaInicio = evento.get('hora_inicio')
            horaFin = evento.get('hora_fin')
            eventoId = evento.get('evento_id')

            if horaInicio and horaFin:
                try:
                    dtInicio = datetime.strptime(f"{fechaStr} {horaInicio}", "%d/%m/%Y %H:%M:%S")
                    dtFin = datetime.strptime(f"{fechaStr} {horaFin}", "%d/%m/%Y %H:%M:%S")

                    # validar que el intervalo sea valido > 0 para evitar error de vertices
                    if dtFin > dtInicio:
                        # pintar area sombreada para el evento
                        ax.axvspan(dtInicio, dtFin, color='red', alpha=0.3)
                        # etiquetar el evento en la parte superior
                        ax.text(dtInicio, ax.get_ylim()[1], f"#{eventoId}", rotation=90, verticalalignment='bottom', fontsize=8)
                    else:
                        print(f"DEBUG: Evento {eventoId} ignorado por duracion invalida (Inicio: {dtInicio}, Fin: {dtFin})")
                except Exception as evErr:
                    print(f"DEBUG: Error procesando evento {eventoId}: {evErr}")

        ax.set_title(f'Monitoreo de Calidad del Aire - {fechaStr}', fontsize=12, fontweight='bold')
        ax.set_ylabel('Concentración (μg/m³)')
        ax.set_xlabel('Hora')

        # configurar leyenda y grid
        from matplotlib.lines import Line2D
        customLines = [
            Line2D([0], [0], color='#ff6ffb', lw=1),
            Line2D([0], [0], color='#FF9800', lw=2),
            Line2D([0], [0], color='#795548', lw=1, linestyle='--'),
            matplotlib.patches.Patch(facecolor='red', edgecolor='red', alpha=0.3, label='Evento Detectado')
        ]
        ax.legend(customLines, ['PM1', 'PM2.5', 'PM10', 'Evento'], loc='upper right')

        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.tick_params(axis='x', rotation=45)

        # asegurar limites x validos para evitar division por cero
        if tiempos:
            minTime = min(tiempos)
            maxTime = max(tiempos)

            # verificar si hay un solo punto o rango cero
            if minTime == maxTime:
                minTime = minTime - timedelta(minutes=30)
                maxTime = maxTime + timedelta(minutes=30)

            ax.set_xlim(left=minTime, right=maxTime)

        plt.tight_layout()

        tempPath = f"/tmp/grafica_dia_{fechaBase.strftime('%Y%m%d')}_{datetime.now().timestamp()}.png"
        plt.savefig(tempPath, format='png', bbox_inches='tight', dpi=150)
        plt.close()

        return tempPath

    except Exception as e:
        print(f"error generando grafica diaria: {e}")
        import traceback
        traceback.print_exc()
        return None


def generar_reporte_pdf(
        estadisticas: dict,
        eventos: List[dict],
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        output_path: str = "/tmp/reporte.pdf"
) -> str:
    # inicializar documento pdf
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()

    colorPrincipal = colors.HexColor('#263238')
    colorSecundario = colors.HexColor('#546E7A')
    colorTextoCabecera = colors.whitesmoke

    titleStyle = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colorPrincipal,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitleStyle = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colorSecundario,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    normalStyle = styles['BodyText']
    normalStyle.alignment = TA_LEFT

    # agregar portada y resumen
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("REPORTE DE MONITOREO TÉRMICO", titleStyle))
    story.append(Spacer(1, 0.3*inch))
    fechaReporte = datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(f"Fecha de generación: {fechaReporte}", styles['Normal']))
    if fecha_inicio and fecha_fin:
        story.append(Paragraph(f"Período: {fecha_inicio} a {fecha_fin}", styles['Normal']))
    story.append(PageBreak())

    # seccion 1 resumen ejecutivo
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

    # seccion 2 analisis diario
    story.append(Paragraph("2. ANÁLISIS DIARIO DE CALIDAD DEL AIRE", subtitleStyle))
    story.append(Paragraph("Visualización del comportamiento de partículas PM1, PM2.5 y PM10 agrupado por día. Las áreas sombreadas en rojo indican la duración de los eventos detectados.", normalStyle))
    story.append(Spacer(1, 0.2*inch))

    # agrupar eventos por fecha
    eventosPorDia = defaultdict(list)
    for ev in eventos:
        fecha = ev.get('fecha_evento')
        if fecha:
            eventosPorDia[fecha].append(ev)

    if eventosPorDia:
        # iterar fechas ordenadas
        for fechaStr in sorted(eventosPorDia.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y")):
            eventosDelDia = eventosPorDia[fechaStr]

            story.append(Paragraph(f"Día: {fechaStr}", styles['Heading3']))
            story.append(Paragraph(f"Eventos detectados: {len(eventosDelDia)}", styles['Normal']))

            # generar grafica unica por dia
            graficaDiaPath = generar_grafica_diaria(fechaStr, eventosDelDia)

            if graficaDiaPath and os.path.exists(graficaDiaPath):
                imgDia = Image(graficaDiaPath, width=7*inch, height=3.5*inch)
                story.append(imgDia)
            else:
                story.append(Paragraph("No hay datos históricos disponibles para este día.", styles['Italic']))

            story.append(Spacer(1, 0.4*inch))
    else:
        story.append(Paragraph("No hay eventos registrados para generar gráficas.", normalStyle))

    story.append(PageBreak())

    # seccion 3 detalle tabular
    story.append(Paragraph("3. DETALLE DE EVENTOS", subtitleStyle))

    if eventos:
        eventosData = [['ID', 'Fecha', 'Hora', 'Estatus', 'Max PM2.5']]
        for evento in eventos:
            pm25 = f"{evento.get('promedio_pm2p5', 0):.1f}" if evento.get('promedio_pm2p5') else "N/A"
            eventosData.append([
                str(evento.get('evento_id', '')),
                evento.get('fecha_evento', ''),
                evento.get('hora_inicio', ''),
                evento.get('estatus', '').upper(),
                pm25
            ])

        eventosTable = Table(eventosData, colWidths=[0.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.5*inch])
        eventosTable.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colorPrincipal),
            ('TEXTCOLOR', (0, 0), (-1, 0), colorTextoCabecera),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(eventosTable)

    doc.build(story)
    return output_path