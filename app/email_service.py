from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import os

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")



def enviar_correo_recuperacion(email_destino: str, nombre_usuario: str, token: str) -> bool:

    # Construir enlace de recuperacion
    enlace_recuperacion = f"http://4.155.33.198:8000/reset-password?token={token}"

    # Contenido HTML del correo
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="content">
                <h1>Recuperacion de Contraseña</h1>
                <p>Hola <strong>{nombre_usuario}</strong>,</p>
                
                <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en Thermal Monitoring.</p>
                
                <p>Para crear una nueva contraseña, haz clic en el siguiente boton:</p>
                <a href="{enlace_recuperacion}" >Restablecer Contraseña</a>
                
                <p>Si tienes problemas, contacta al administrador del sistema.</p>
                <p>Saludos,<br><strong>Equipo de Thermal Monitoring</strong></p>
            </div>
        </div>
    </body>
    </html>
    """

    # Crear mensaje
    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=email_destino,
        subject='Recuperacion de Contraseña - Thermal Monitoring',
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        print(f"Correo enviado exitosamente. Status code: {response.status_code}")
        return True

    except Exception as e:
        print(f"Error al enviar correo: {str(e)}")
        return False