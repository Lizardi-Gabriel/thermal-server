# Criterios de logs

- INFO: operaciones importantes completadas (creación de eventos, cambios reales de estatus, análisis IA y generación de PDF).
- DEBUG: consultas correctas del panel, subida de imágenes y respuestas HTTP rápidas. Activar con LOG_LEVEL=DEBUG y reiniciar el servidor.
- WARNING: respuestas HTTP 4xx, solicitudes de al menos 2 segundos, fallos recuperables de servicios externos y registros históricos inválidos resumidos por consulta.
- ERROR: respuestas HTTP 5xx y excepciones no controladas. El middleware registra las excepciones propagadas; las capas que recuperan un fallo registran su propio diagnóstico.

Consola y archivo usan el mismo nivel. Cada solicitud tiene un request_id generado por el servidor, también disponible en X-Request-ID. Los campos adicionales, incluido reporte_pdf, aparecen en el formato. Las rutas HTTP se registran como plantillas para evitar imprimir tokens en las URL. No se vuelcan variables locales en las trazas.

Se retiraron los registros por imagen de la bitácora que duplicaban los datos de calidad del aire ya persistidos. WeatherLink emite un aviso por consulta fallida sin imprimir URLs con credenciales y resume los registros inválidos. Las consultas rutinarias del panel ya no llenan INFO con datos y mensajes de inicio y fin.

Los logs de PDF conservan el rango solicitado, días incluidos, ventanas horarias y cantidades por día. La creación y cambio de estatus se registran después de confirmar la escritura en base de datos.

GET /logs sigue consultando exclusivamente logs_sistema; no lee el archivo de Loguru. POST /logs conserva cada mensaje enviado: no se descartan textos iguales automáticamente, porque pueden corresponder a incidentes diferentes. Esta mejora no borra registros anteriores ni implementa deduplicación de reintentos del cliente.
