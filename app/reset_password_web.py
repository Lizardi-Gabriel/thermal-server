from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app import crud, schemas, security
from app.database import get_db

router = APIRouter()


@router.get("/reset-password", response_class=HTMLResponse)
def mostrar_formulario_reset_password(request: Request, token: str, db: Session = Depends(get_db)):
    """Mostrar formulario para restablecer contraseña."""

    # Validar token
    es_valido, mensaje = crud.validar_token_recuperacion(db, token)

    if not es_valido:
        # Token invalido o expirado
        html_error = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error - Thermal Monitoring</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-900 text-white min-h-screen flex items-center justify-center p-4">
            <div class="max-w-md w-full">
                <div class="bg-gray-800 rounded-lg shadow-2xl p-8">
                    <div class="text-center mb-6">
                        <svg class="mx-auto h-16 w-16 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <h1 class="text-3xl font-bold mt-4">Error</h1>
                    </div>
                    <p class="text-gray-300 text-center mb-6">{mensaje}</p>
                    <div class="text-center">
                        <a href="/" class="text-blue-400 hover:text-blue-300">Volver al inicio</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_error, status_code=400)

    # Formulario para nueva contraseña
    html_formulario = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Restablecer Contraseña - Thermal Monitoring</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 text-white min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full">
            <div class="bg-gray-800 rounded-lg shadow-2xl p-8">
                <div class="text-center mb-8">
                    <h1 class="text-3xl font-bold mb-2">Restablecer Contraseña</h1>
                    <p class="text-gray-400">Ingresa tu nueva contraseña</p>
                </div>
                
                <form method="POST" action="/reset-password-submit" onsubmit="return validarFormulario()" class="space-y-6">
                    <input type="hidden" name="token" value="{token}">
                    
                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-300 mb-2">
                            Nueva Contraseña
                        </label>
                        <input 
                            type="password" 
                            id="password" 
                            name="password" 
                            required
                            minlength="8"
                            class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white"
                            placeholder="Minimo 8 caracteres">
                        <p class="text-xs text-gray-400 mt-1">Debe tener al menos 8 caracteres</p>
                    </div>
                    
                    <div>
                        <label for="confirm_password" class="block text-sm font-medium text-gray-300 mb-2">
                            Confirmar Contraseña
                        </label>
                        <input 
                            type="password" 
                            id="confirm_password" 
                            name="confirm_password" 
                            required
                            minlength="8"
                            class="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white"
                            placeholder="Repite tu contraseña">
                    </div>
                    
                    <div id="error-message" class="hidden bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded-lg">
                    </div>
                    
                    <button 
                        type="submit"
                        class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-colors duration-200">
                        Restablecer Contraseña
                    </button>
                </form>
            </div>
        </div>
        
        <script>
            function validarFormulario() {{
                const password = document.getElementById('password').value;
                const confirmPassword = document.getElementById('confirm_password').value;
                const errorDiv = document.getElementById('error-message');
                
                if (password.length < 8) {{
                    errorDiv.textContent = 'La contraseña debe tener al menos 8 caracteres';
                    errorDiv.classList.remove('hidden');
                    return false;
                }}
                
                if (password !== confirmPassword) {{
                    errorDiv.textContent = 'Las contraseñas no coinciden';
                    errorDiv.classList.remove('hidden');
                    return false;
                }}
                
                errorDiv.classList.add('hidden');
                return true;
            }}
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_formulario)


@router.post("/reset-password-submit", response_class=HTMLResponse)
def procesar_reset_password(
        token: str = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...),
        db: Session = Depends(get_db)
):
    """Procesar el formulario de restablecimiento de contraseña."""

    # Validar que las contraseñas coincidan
    if password != confirm_password:
        return HTMLResponse(
            content=generar_html_error("Las contraseñas no coinciden"),
            status_code=400
        )

    # Validar longitud minima
    if len(password) < 8:
        return HTMLResponse(
            content=generar_html_error("La contraseña debe tener al menos 8 caracteres"),
            status_code=400
        )

    # Validar token
    es_valido, mensaje = crud.validar_token_recuperacion(db, token)

    if not es_valido:
        return HTMLResponse(
            content=generar_html_error(mensaje),
            status_code=400
        )

    # Obtener token y usuario
    db_token = crud.obtener_token_recuperacion(db, token)
    usuario = crud.get_user_by_id(db, db_token.usuario_id)

    if not usuario:
        return HTMLResponse(
            content=generar_html_error("Usuario no encontrado"),
            status_code=404
        )

    # Actualizar contraseña
    nueva_password_hash = security.hashear_password(password)
    usuario.hash_contrasena = nueva_password_hash

    # Marcar token como usado
    crud.marcar_token_como_usado(db, token)

    db.commit()

    # Crear log del sistema
    from app.models import TipoLogEnum
    crud.create_log(db, log=schemas.LogSistemaCreate(
        tipo=TipoLogEnum.info,
        mensaje=f"Contraseña restablecida via web para usuario: {usuario.nombre_usuario}"
    ))

    # Pagina de exito
    html_exito = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Exito - Thermal Monitoring</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 text-white min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full">
            <div class="bg-gray-800 rounded-lg shadow-2xl p-8">
                <div class="text-center mb-6">
                    <svg class="mx-auto h-16 w-16 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <h1 class="text-3xl font-bold mt-4">Contraseña Restablecida</h1>
                </div>
                <p class="text-gray-300 text-center mb-6">
                    Tu contraseña ha sido restablecida exitosamente. Ya puedes iniciar sesion en la aplicacion movil con tu nueva contraseña.
                </p>
                <div class="text-center">
                    <p class="text-sm text-gray-400">Puedes cerrar esta ventana</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_exito)


def generar_html_error(mensaje: str) -> str:
    """Generar HTML de error."""
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error - Thermal Monitoring</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 text-white min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full">
            <div class="bg-gray-800 rounded-lg shadow-2xl p-8">
                <div class="text-center mb-6">
                    <svg class="mx-auto h-16 w-16 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <h1 class="text-3xl font-bold mt-4">Error</h1>
                </div>
                <p class="text-gray-300 text-center mb-6">{mensaje}</p>
                <div class="text-center">
                    <a href="/" class="text-blue-400 hover:text-blue-300">Volver al inicio</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

