from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import os

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")



def enviar_correo_recuperacion(email_destino: str, nombre_usuario: str, token: str) -> bool:

    # Construir enlace de recuperacion
    enlace_recuperacion = f"thermalapp://reset-password?token={token}"

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
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #6200EE;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .content {{
                background-color: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 5px 5px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: #6200EE;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .warning {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Recuperacion de Contraseña</h1>
            </div>
            <div class="content">
                <p>Hola <strong>{nombre_usuario}</strong>,</p>
                
                <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en Thermal Monitoring.</p>
                
                <p>Para crear una nueva contraseña, haz clic en el siguiente boton:</p>
                
                <div style="text-align: center;">
                    <a href="{enlace_recuperacion}" class="button">Restablecer Contraseña</a>
                </div>
                
                <p>O copia y pega este enlace en la aplicacion:</p>
                <p style="background-color: #e9ecef; padding: 10px; border-radius: 3px; word-break: break-all;">
                    {enlace_recuperacion}
                </p>
                
                <div class="warning">
                    <strong>Importante:</strong>
                    <ul>
                        <li>Este enlace expirara en 30 minutos</li>
                        <li>Solo puede usarse una vez</li>
                        <li>Si no solicitaste este cambio, ignora este correo</li>
                    </ul>
                </div>
                
                <p>Si tienes problemas, contacta al administrador del sistema.</p>
                
                <p>Saludos,<br><strong>Equipo de Thermal Monitoring</strong></p>
            </div>
            <div class="footer">
                <p>Este es un correo automatico, por favor no respondas a este mensaje.</p>
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