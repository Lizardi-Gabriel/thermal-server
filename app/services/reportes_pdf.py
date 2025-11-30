from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
import os
from typing import List, Optional

from app.services.aire import obtener_historico_aire

def generar_grafica_eventos_por_estatus(eventos_stats: dict) -> str:
    labels = ['Confirmados', 'Descartados', 'Pendientes']
    sizes = [
        eventos_stats.get('eventos_confirmados', 0),
        eventos_stats.get('eventos_descartados', 0),
        eventos_stats.get('eventos_pendientes', 0)
    ]
    colors_chart = ['#4CAF50', '#D32F2F', '#1976D2']
    explode = (0.05, 0.05, 0.05)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(sizes, explode=explode, labels=labels, colors=colors_chart,
           autopct='%1.1f%%', shadow=True, startangle=90)
    ax.axis('equal')
    plt.title('Distribución de Eventos por Estatus', fontsize=14, fontweight='bold')

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
    img_buffer.seek(0)
    plt.close()

    temp_path = f"/tmp/grafica_estatus_{datetime.now().timestamp()}.png"
    with open(temp_path, 'wb') as f:
        f.write(img_buffer.getvalue())

    return temp_path


def generar_grafica_comparativa_historico(evento: dict) -> Optional[str]:
    """
    Genera una grafica lineal comparando PM2.5 durante el evento vs historico (1 hora antes/despues).
    """
    try:
        fecha_evento_str = evento.get('fecha_evento')
        hora_inicio_str = evento.get('hora_inicio')

        if not fecha_evento_str or not hora_inicio_str:
            return None

        fecha_hora_evento = datetime.strptime(f"{fecha_evento_str} {hora_inicio_str}", "%d/%m/%Y %H:%M:%S")

        inicio_ventana = fecha_hora_evento - timedelta(minutes=30)
        fin_ventana = fecha_hora_evento + timedelta(minutes=30)

        ts_start = int(inicio_ventana.timestamp())
        ts_end = int(fin_ventana.timestamp())

        registros = obtener_historico_aire(ts_start, ts_end)

        if not registros:
            return None

        registros.sort(key=lambda x: x.hora_medicion)

        tiempos = [r.hora_medicion for r in registros]
        valores_pm25 = [r.pm2p5 for r in registros]
        valores_pm10 = [r.pm10 for r in registros]

        fig, ax = plt.subplots(figsize=(10, 5))

        # Plotear lineas
        ax.plot(tiempos, valores_pm25, label='PM2.5 (Fino)', color='#FF9800', linewidth=2, marker='o', markersize=4)
        ax.plot(tiempos, valores_pm10, label='PM10 (Grueso)', color='#795548', linewidth=1.5, linestyle='--')

        # Marcar el momento del evento
        ax.axvline(x=fecha_hora_evento, color='#D32F2F', linestyle='-', linewidth=2, label='Detección Fumar')

        # Formatear grafica
        ax.set_title(f'Impacto en Calidad del Aire - Evento #{evento.get("evento_id")}', fontsize=12, fontweight='bold')
        ax.set_ylabel('Concentración (μg/m³)')
        ax.set_xlabel('Hora')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Formatear eje X para mostrar horas
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)

        plt.tight_layout()

        temp_path = f"/tmp/grafica_comp_{evento.get('evento_id')}_{datetime.now().timestamp()}.png"
        plt.savefig(temp_path, format='png', bbox_inches='tight', dpi=150)
        plt.close()

        return temp_path
    except Exception as e:
        print(f"Error generando grafica comparativa: {e}")
        return None


def generar_reporte_pdf(
        estadisticas: dict,
        eventos: List[dict],
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        output_path: str = "/tmp/reporte.pdf"
) -> str:
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)

    story = []
    styles = getSampleStyleSheet()

    color_principal = colors.HexColor('#263238')
    color_secundario = colors.HexColor('#546E7A')
    color_texto_cabecera = colors.whitesmoke

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=color_principal,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=color_secundario,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    normal_style = styles['BodyText']
    normal_style.alignment = TA_LEFT

    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("REPORTE DE MONITOREO TÉRMICO", title_style))
    story.append(Spacer(1, 0.3*inch))
    fecha_reporte = datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(f"Fecha de generación: {fecha_reporte}", styles['Normal']))
    if fecha_inicio and fecha_fin:
        story.append(Paragraph(f"Período: {fecha_inicio} a {fecha_fin}", styles['Normal']))
    story.append(PageBreak())

    story.append(Paragraph("1. RESUMEN EJECUTIVO", subtitle_style))
    resumen_data = [
        ['Métrica', 'Valor'],
        ['Total de Eventos', str(estadisticas.get('total_eventos', 0))],
        ['Eventos Pendientes', str(estadisticas.get('eventos_pendientes', 0))],
        ['Eventos Confirmados', str(estadisticas.get('eventos_confirmados', 0))],
        ['Total de Detecciones', str(estadisticas.get('total_detecciones', 0))],
    ]
    resumen_table = Table(resumen_data, colWidths=[3*inch, 2*inch])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), color_principal),
        ('TEXTCOLOR', (0, 0), (-1, 0), color_texto_cabecera),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(resumen_table)
    story.append(Spacer(1, 0.3*inch))

    # Grafica de pastel
    grafica_estatus_path = generar_grafica_eventos_por_estatus(estadisticas)
    if grafica_estatus_path and os.path.exists(grafica_estatus_path):
        img = Image(grafica_estatus_path, width=5*inch, height=3.75*inch)
        story.append(img)
    story.append(PageBreak())

    story.append(Paragraph("2. ANÁLISIS DE IMPACTO AMBIENTAL", subtitle_style))
    story.append(Paragraph("A continuación se muestra el comportamiento de las partículas PM2.5 y PM10 antes, durante y después de los eventos confirmados más relevantes.", normal_style))
    story.append(Spacer(1, 0.2*inch))

    # Filtramos eventos confirmados que tengan datos de aire altos
    eventos_impacto = [e for e in eventos if e.get('estatus') == 'confirmado']
    # Limitamos a los ultimos 3 para no saturar el PDF
    eventos_impacto = eventos_impacto[:3]

    if eventos_impacto:
        for evento in eventos_impacto:
            story.append(Paragraph(f"Evento #{evento.get('evento_id')} - {evento.get('fecha_evento')}", styles['Heading3']))

            # Generar grafica comparativa
            grafica_comp_path = generar_grafica_comparativa_historico(evento)

            if grafica_comp_path and os.path.exists(grafica_comp_path):
                print("inin")
                img_comp = Image(grafica_comp_path, width=6*inch, height=3*inch)
                story.append(img_comp)
                story.append(Paragraph("Nota: La línea roja vertical indica el momento exacto de la detección del fumador.", styles['Italic']))
                story.append(Spacer(1, 0.3*inch))
            else:
                print("on")
                story.append(Paragraph("No hay datos históricos suficientes para generar la gráfica comparativa.", styles['Italic']))
    else:
        story.append(Paragraph("No hay eventos confirmados recientes para analizar el impacto histórico.", normal_style))

    story.append(PageBreak())

    story.append(Paragraph("3. DETALLE DE EVENTOS", subtitle_style))
    if eventos:
        eventos_data = [['ID', 'Fecha', 'Estatus', 'Max PM2.5', 'Operador']]
        for evento in eventos:
            operador = evento.get('usuario', {}).get('nombre_usuario', 'N/A') if evento.get('usuario') else 'N/A'
            pm25 = f"{evento.get('promedio_pm2p5', 0):.1f}" if evento.get('promedio_pm2p5') else "N/A"
            eventos_data.append([
                str(evento.get('evento_id', '')),
                evento.get('fecha_evento', ''),
                evento.get('estatus', '').upper(),
                pm25,
                operador
            ])
        eventos_table = Table(eventos_data, colWidths=[0.6*inch, 1.2*inch, 1.2*inch, 1.2*inch, 2*inch])
        eventos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), color_principal),
            ('TEXTCOLOR', (0, 0), (-1, 0), color_texto_cabecera),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(eventos_table)

    doc.build(story)
    return output_path