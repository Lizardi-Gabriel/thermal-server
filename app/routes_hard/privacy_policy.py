from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/privacy-policy", response_class=HTMLResponse)
def politica_privacidad():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Política de Privacidad - Thermal Monitoring</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 p-8">
        <div class="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
            <h1 class="text-3xl font-bold mb-6">Política de Privacidad</h1>
            <p class="mb-4"><strong>Última actualización:</strong> 12 de nov 2025</p>
            
            <h2 class="text-2xl font-bold mt-6 mb-4">1. Información que Recopilamos</h2>
            <p class="mb-4">Thermal Monitoring recopila la siguiente información:</p>
            <ul class="list-disc pl-6 mb-4">
                <li>Información de cuenta: nombre de usuario, correo electrónico</li>
                <li>Información de eventos: imágenes térmicas, detecciones, fechas</li>
                <li>Datos de calidad del aire: PM10, PM2.5, PM1.0, temperatura, humedad</li>
                <li>Tokens de notificaciones push (Firebase Cloud Messaging)</li>
            </ul>
            
            <h2 class="text-2xl font-bold mt-6 mb-4">2. Uso de la Información</h2>
            <p class="mb-4">Utilizamos la información recopilada para:</p>
            <ul class="list-disc pl-6 mb-4">
                <li>Proporcionar y mantener el servicio</li>
                <li>Enviar notificaciones sobre eventos</li>
                <li>Generar reportes y estadísticas</li>
                <li>Mejorar la experiencia del usuario</li>
            </ul>
            
            <h2 class="text-2xl font-bold mt-6 mb-4">3. Almacenamiento de Datos</h2>
            <p class="mb-4">Los datos se almacenan de forma segura en servidores Microsoft Azure con cifrado.</p>
            
            <h2 class="text-2xl font-bold mt-6 mb-4">4. Compartir Información</h2>
            <p class="mb-4">No compartimos información personal con terceros excepto:</p>
            <ul class="list-disc pl-6 mb-4">
                <li>Firebase (Google) para notificaciones push</li>
                <li>SendGrid para correos de recuperación de contraseña</li>
            </ul>
            
            <h2 class="text-2xl font-bold mt-6 mb-4">5. Seguridad</h2>
            <p class="mb-4">Implementamos medidas de seguridad para proteger su información, incluyendo autenticación JWT y cifrado de datos.</p>
            
            <h2 class="text-2xl font-bold mt-6 mb-4">6. Sus Derechos</h2>
            <p class="mb-4">Tiene derecho a:</p>
            <ul class="list-disc pl-6 mb-4">
                <li>Acceder a su información personal</li>
                <li>Solicitar la eliminación de su cuenta</li>
                <li>Corregir información incorrecta</li>
            </ul>
            
            <h2 class="text-2xl font-bold mt-6 mb-4">7. Contacto</h2>
            <p class="mb-4">Para preguntas sobre esta política, contacte a: lizardigabriel9@gmail.com</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)