from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
import os
from typing import List, Optional


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


def generar_grafica_calidad_aire(eventos_con_aire: List[dict]) -> Optional[str]:
    if not eventos_con_aire:
        return None

    pm10_values = [e['promedio_pm10'] for e in eventos_con_aire if e.get('promedio_pm10')]
    pm2p5_values = [e['promedio_pm2p5'] for e in eventos_con_aire if e.get('promedio_pm2p5')]
    pm1p0_values = [e['promedio_pm1p0'] for e in eventos_con_aire if e.get('promedio_pm1p0')]

    if not pm10_values and not pm2p5_values and not pm1p0_values:
        return None

    promedio_pm10 = sum(pm10_values) / len(pm10_values) if pm10_values else 0
    promedio_pm2p5 = sum(pm2p5_values) / len(pm2p5_values) if pm2p5_values else 0
    promedio_pm1p0 = sum(pm1p0_values) / len(pm1p0_values) if pm1p0_values else 0

    limite_pm10 = 45
    limite_pm2p5 = 15
    limite_pm1p0 = 10

    fig, ax = plt.subplots(figsize=(10, 6))

    categories = ['PM10', 'PM2.5', 'PM1.0']
    promedios = [promedio_pm10, promedio_pm2p5, promedio_pm1p0]
    limites = [limite_pm10, limite_pm2p5, limite_pm1p0]

    x = range(len(categories))
    width = 0.35

    bar_colors = []
    for promedio, limite in zip(promedios, limites):
        if promedio > limite:
            bar_colors.append('#D32F2F')
        elif promedio > limite * 0.8:
            bar_colors.append('#FFA000')
        else:
            bar_colors.append('#4CAF50')

    bars1 = ax.bar([i - width/2 for i in x], promedios, width, label='Promedio Medido', color=bar_colors)
    bars2 = ax.bar([i + width/2 for i in x], limites, width, label='Límite OMS', color='#757575', alpha=0.7)

    ax.set_ylabel('Concentración (μg/m³)', fontweight='bold')
    ax.set_title('Calidad del Aire - Comparación con Límites OMS', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()

    temp_path = f"/tmp/grafica_aire_{datetime.now().timestamp()}.png"
    plt.savefig(temp_path, format='png', bbox_inches='tight', dpi=150)
    plt.close()

    return temp_path


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
    story.append(Spacer(1, 0.2*inch))

    resumen_data = [
        ['Métrica', 'Valor'],
        ['Total de Eventos', str(estadisticas.get('total_eventos', 0))],
        ['Eventos Pendientes', str(estadisticas.get('eventos_pendientes', 0))],
        ['Eventos Confirmados', str(estadisticas.get('eventos_confirmados', 0))],
        ['Eventos Descartados', str(estadisticas.get('eventos_descartados', 0))],
        ['Total de Detecciones', str(estadisticas.get('total_detecciones', 0))],
        ['Promedio Detecciones/Evento', f"{estadisticas.get('promedio_detecciones_por_evento', 0):.2f}"]
    ]

    resumen_table = Table(resumen_data, colWidths=[3*inch, 2*inch])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), color_principal),
        ('TEXTCOLOR', (0, 0), (-1, 0), color_texto_cabecera),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))

    story.append(resumen_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("2. DISTRIBUCIÓN DE EVENTOS", subtitle_style))
    grafica_estatus_path = generar_grafica_eventos_por_estatus(estadisticas)
    if grafica_estatus_path and os.path.exists(grafica_estatus_path):
        img = Image(grafica_estatus_path, width=5*inch, height=3.75*inch)
        story.append(img)
        story.append(Spacer(1, 0.2*inch))

    story.append(PageBreak())

    story.append(Paragraph("3. ANÁLISIS DE CALIDAD DEL AIRE", subtitle_style))
    story.append(Spacer(1, 0.2*inch))

    eventos_con_aire = [e for e in eventos if e.get('promedio_pm10') or e.get('promedio_pm2p5') or e.get('promedio_pm1p0')]

    if eventos_con_aire:
        pm10_values = [e['promedio_pm10'] for e in eventos_con_aire if e.get('promedio_pm10')]
        pm2p5_values = [e['promedio_pm2p5'] for e in eventos_con_aire if e.get('promedio_pm2p5')]
        pm1p0_values = [e['promedio_pm1p0'] for e in eventos_con_aire if e.get('promedio_pm1p0')]

        aire_data = [
            ['Parámetro', 'Promedio', 'Máximo', 'Mínimo', 'Límite OMS', 'Estado']
        ]

        if pm10_values:
            promedio_pm10 = sum(pm10_values) / len(pm10_values)
            max_pm10 = max(pm10_values)
            min_pm10 = min(pm10_values)
            limite_pm10 = 45
            estado_pm10 = '⚠ ALTO' if promedio_pm10 > limite_pm10 else '✓ Normal'
            aire_data.append(['PM10', f'{promedio_pm10:.1f}', f'{max_pm10:.1f}', f'{min_pm10:.1f}', f'{limite_pm10}', estado_pm10])

        if pm2p5_values:
            promedio_pm2p5 = sum(pm2p5_values) / len(pm2p5_values)
            max_pm2p5 = max(pm2p5_values)
            min_pm2p5 = min(pm2p5_values)
            limite_pm2p5 = 15
            estado_pm2p5 = '⚠ ALTO' if promedio_pm2p5 > limite_pm2p5 else '✓ Normal'
            aire_data.append(['PM2.5', f'{promedio_pm2p5:.1f}', f'{max_pm2p5:.1f}', f'{min_pm2p5:.1f}', f'{limite_pm2p5}', estado_pm2p5])

        if pm1p0_values:
            promedio_pm1p0 = sum(pm1p0_values) / len(pm1p0_values)
            max_pm1p0 = max(pm1p0_values)
            min_pm1p0 = min(pm1p0_values)
            limite_pm1p0 = 10
            estado_pm1p0 = '⚠ ALTO' if promedio_pm1p0 > limite_pm1p0 else '✓ Normal'
            aire_data.append(['PM1.0', f'{promedio_pm1p0:.1f}', f'{max_pm1p0:.1f}', f'{min_pm1p0:.1f}', f'{limite_pm1p0}', estado_pm1p0])

        aire_table = Table(aire_data, colWidths=[1*inch, 1*inch, 1*inch, 1*inch, 1.2*inch, 1*inch])
        aire_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), color_secundario),
            ('TEXTCOLOR', (0, 0), (-1, 0), color_texto_cabecera),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))

        story.append(aire_table)
        story.append(Spacer(1, 0.3*inch))

        grafica_aire_path = generar_grafica_calidad_aire(eventos_con_aire)
        if grafica_aire_path and os.path.exists(grafica_aire_path):
            img_aire = Image(grafica_aire_path, width=6*inch, height=3.6*inch)
            story.append(img_aire)

        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("<b>Interpretación:</b>", normal_style))
        story.append(Paragraph("• Valores de referencia basados en guías de la OMS para calidad del aire.", normal_style))
        story.append(Paragraph("• PM10: Límite 45 μg/m³ (promedio 24h)", normal_style))
        story.append(Paragraph("• PM2.5: Límite 15 μg/m³ (promedio 24h)", normal_style))
        story.append(Paragraph("• PM1.0: Límite estimado 10 μg/m³", normal_style))
    else:
        story.append(Paragraph("No hay datos suficientes de calidad del aire para análisis.", normal_style))

    story.append(PageBreak())

    story.append(Paragraph("4. DETALLE DE EVENTOS", subtitle_style))
    story.append(Spacer(1, 0.2*inch))

    if eventos:
        eventos_data = [['ID', 'Fecha', 'Estatus', 'Detecciones', 'Operador']]

        for evento in eventos:
            operador = evento.get('usuario', {}).get('nombre_usuario', 'N/A') if evento.get('usuario') else 'N/A'
            eventos_data.append([
                str(evento.get('evento_id', '')),
                evento.get('fecha_evento', ''),
                evento.get('estatus', '').upper(),
                str(evento.get('max_detecciones', 0)),
                operador
            ])

        eventos_table = Table(eventos_data, colWidths=[0.6*inch, 1.2*inch, 1.2*inch, 1.2*inch, 2*inch])
        eventos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), color_principal),
            ('TEXTCOLOR', (0, 0), (-1, 0), color_texto_cabecera),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        story.append(eventos_table)
    else:
        story.append(Paragraph("No hay eventos para mostrar en este período.", normal_style))

    doc.build(story)

    try:
        if grafica_estatus_path and os.path.exists(grafica_estatus_path):
            os.remove(grafica_estatus_path)
        if 'grafica_aire_path' in locals() and grafica_aire_path and os.path.exists(grafica_aire_path):
            os.remove(grafica_aire_path)
    except:
        pass

    return output_path

