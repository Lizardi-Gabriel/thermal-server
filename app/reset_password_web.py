from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app import crud, schemas, security
from app.database import get_db

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def pagina_principal():
    """Pagina principal de Thermal Monitoring."""

    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Thermal Monitoring - Sistema de Deteccion Termica</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            'morado-termico': '#4A107B',
                            'amarillo-termico': '#F2B705',
                            'rojo-termico': '#F20505',
                        }
                    }
                }
            }
        </script>
    </head>
    <body class="bg-[#EFEFEF] min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow-md">
            <div class="container mx-auto px-4 py-6">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="bg-morado-termico text-white w-12 h-12 rounded-lg flex items-center justify-center">
                            <svg class="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                        </div>
                        <div>
                            <h1 class="text-2xl font-bold text-black">Thermal Monitoring</h1>
                            <p class="text-sm text-gray-600">Sistema de Deteccion Termica</p>
                        </div>
                    </div>
                </div>
            </div>
        </header>

        <!-- Hero Section -->
        <section class="container mx-auto px-4 py-16">
            <div class="max-w-4xl mx-auto text-center">
                <h2 class="text-4xl md:text-5xl font-bold text-black mb-6">
                    Monitoreo Inteligente de Eventos Termicos
                </h2>
                <p class="text-xl text-gray-700 mb-8">
                    Sistema avanzado para la deteccion, gestion y analisis de eventos termicos con monitoreo de calidad del aire en tiempo real
                </p>
                <div class="flex flex-col sm:flex-row gap-4 justify-center">
                    <a href="/gallery" class="bg-amarillo-termico hover:bg-[#d9a304] text-black font-bold py-3 px-8 rounded-lg transition-colors duration-200 shadow-md">
                        Ver Galeria de Eventos
                    </a>
                    <a href="/historial" class="bg-white hover:bg-gray-100 text-black font-bold py-3 px-8 rounded-lg transition-colors duration-200 shadow-md border-2 border-gray-300">
                        Historial de Logs
                    </a>
                </div>
            </div>
        </section>

        <!-- Features Section -->
        <section class="container mx-auto px-4 py-16">
            <div class="max-w-6xl mx-auto">
                <h3 class="text-3xl font-bold text-center text-black mb-12">Caracteristicas Principales</h3>
                
                <div class="grid md:grid-cols-3 gap-8">
                    <!-- Feature 1 -->
                    <div class="bg-white rounded-lg p-6 shadow-md border-2 border-gray-200">
                        <div class="bg-morado-termico text-white w-14 h-14 rounded-lg flex items-center justify-center mb-4">
                            <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                        </div>
                        <h4 class="text-xl font-bold text-black mb-2">Deteccion Termica</h4>
                        <p class="text-gray-600">
                            Analisis de imagenes termicas con deteccion automatica de eventos y marcado de areas de interes
                        </p>
                    </div>

                    <!-- Feature 2 -->
                    <div class="bg-white rounded-lg p-6 shadow-md border-2 border-gray-200">
                        <div class="bg-amarillo-termico text-black w-14 h-14 rounded-lg flex items-center justify-center mb-4">
                            <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                        </div>
                        <h4 class="text-xl font-bold text-black mb-2">Calidad del Aire</h4>
                        <p class="text-gray-600">
                            Monitoreo continuo de PM10, PM2.5, PM1.0, temperatura, humedad y AQI con analisis comparativo
                        </p>
                    </div>

                    <!-- Feature 3 -->
                    <div class="bg-white rounded-lg p-6 shadow-md border-2 border-gray-200">
                        <div class="bg-morado-termico text-white w-14 h-14 rounded-lg flex items-center justify-center mb-4">
                            <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                        </div>
                        <h4 class="text-xl font-bold text-black mb-2">Reportes PDF</h4>
                        <p class="text-gray-600">
                            Generacion automatica de reportes con graficas, estadisticas y comparacion con limites OMS
                        </p>
                    </div>

                    <!-- Feature 4 -->
                    <div class="bg-white rounded-lg p-6 shadow-md border-2 border-gray-200">
                        <div class="bg-amarillo-termico text-black w-14 h-14 rounded-lg flex items-center justify-center mb-4">
                            <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                            </svg>
                        </div>
                        <h4 class="text-xl font-bold text-black mb-2">Gestion de Usuarios</h4>
                        <p class="text-gray-600">
                            Sistema de roles con administradores y operadores, estadisticas personalizadas por usuario
                        </p>
                    </div>

                    <!-- Feature 5 -->
                    <div class="bg-white rounded-lg p-6 shadow-md border-2 border-gray-200">
                        <div class="bg-morado-termico text-white w-14 h-14 rounded-lg flex items-center justify-center mb-4">
                            <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                            </svg>
                        </div>
                        <h4 class="text-xl font-bold text-black mb-2">Notificaciones Push</h4>
                        <p class="text-gray-600">
                            Alertas en tiempo real via Firebase Cloud Messaging cuando se detectan nuevos eventos
                        </p>
                    </div>

                    <!-- Feature 6 -->
                    <div class="bg-white rounded-lg p-6 shadow-md border-2 border-gray-200">
                        <div class="bg-amarillo-termico text-black w-14 h-14 rounded-lg flex items-center justify-center mb-4">
                            <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                            </svg>
                        </div>
                        <h4 class="text-xl font-bold text-black mb-2">Filtros Avanzados</h4>
                        <p class="text-gray-600">
                            Filtrado por fecha, estatus, operador y navegacion rapida entre fechas para analisis detallado
                        </p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Tech Stack -->
        <section class="bg-white py-16">
            <div class="container mx-auto px-4">
                <div class="max-w-4xl mx-auto text-center">
                    <h3 class="text-3xl font-bold text-black mb-8">Tecnologia</h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
                        <div class="p-4">
                            <p class="font-bold text-black">Backend</p>
                            <p class="text-sm text-gray-600">FastAPI + MySQL</p>
                        </div>
                        <div class="p-4">
                            <p class="font-bold text-black">Mobile</p>
                            <p class="text-sm text-gray-600">Android Kotlin</p>
                        </div>
                        <div class="p-4">
                            <p class="font-bold text-black">Cloud</p>
                            <p class="text-sm text-gray-600">Azure + Firebase</p>
                        </div>
                        <div class="p-4">
                            <p class="font-bold text-black">Reportes</p>
                            <p class="text-sm text-gray-600">ReportLab + Matplotlib</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="bg-morado-termico text-white py-8">
            <div class="container mx-auto px-4 text-center">
                <p class="mb-2">&copy; 2025 Thermal Monitoring. Todos los derechos reservados.</p>
                <p class="text-sm text-gray-300">Sistema de Monitoreo Termico y Calidad del Aire</p>
            </div>
        </footer>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)





@router.get("/reset-password", response_class=HTMLResponse)
def mostrar_formulario_reset_password(
        request: Request,
        token: str,
        db: Session = Depends(get_db)
):
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
            <script>
                tailwind.config = {{
                    theme: {{
                        extend: {{
                            colors: {{
                                'morado-termico': '#4A107B',
                                'amarillo-termico': '#F2B705',
                                'rojo-termico': '#F20505',
                            }}
                        }}
                    }}
                }}
            </script>
        </head>
        <body class="bg-[#EFEFEF] min-h-screen flex items-center justify-center p-4">
            <div class="max-w-md w-full">
                <div class="bg-white rounded-lg shadow-2xl p-8 border-2 border-gray-200">
                    <div class="text-center mb-6">
                        <svg class="mx-auto h-16 w-16 text-rojo-termico" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <h1 class="text-3xl font-bold mt-4 text-black">Error</h1>
                    </div>
                    <p class="text-gray-600 text-center mb-6">{mensaje}</p>
                    <div class="text-center">
                        <a href="/" class="text-morado-termico hover:text-amarillo-termico font-semibold">Volver al inicio</a>
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
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        colors: {{
                            'morado-termico': '#4A107B',
                            'amarillo-termico': '#F2B705',
                            'rojo-termico': '#F20505',
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body class="bg-[#EFEFEF] min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full">
            <div class="bg-white rounded-lg shadow-2xl p-8 border-2 border-gray-200">
                <div class="text-center mb-8">
                    <div class="bg-amarillo-termico text-white w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                    </div>
                    <h1 class="text-3xl font-bold mb-2 text-black">Restablecer Contraseña</h1>
                    <p class="text-gray-600">Ingresa tu nueva contraseña</p>
                </div>
                
                <form method="POST" action="/reset-password-submit" onsubmit="return validarFormulario()" class="space-y-6">
                    <input type="hidden" name="token" value="{token}">
                    
                    <div>
                        <label for="password" class="block text-sm font-semibold text-black mb-2">
                            Nueva Contraseña
                        </label>
                        <input 
                            type="password" 
                            id="password" 
                            name="password" 
                            required
                            minlength="8"
                            class="w-full px-4 py-3 bg-[#EFEFEF] border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-amarillo-termico focus:border-amarillo-termico text-black"
                            placeholder="Minimo 8 caracteres">
                        <p class="text-xs text-gray-500 mt-1">Debe tener al menos 8 caracteres</p>
                    </div>
                    
                    <div>
                        <label for="confirm_password" class="block text-sm font-semibold text-black mb-2">
                            Confirmar Contraseña
                        </label>
                        <input 
                            type="password" 
                            id="confirm_password" 
                            name="confirm_password" 
                            required
                            minlength="8"
                            class="w-full px-4 py-3 bg-[#EFEFEF] border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-amarillo-termico focus:border-amarillo-termico text-black"
                            placeholder="Repite tu contraseña">
                    </div>
                    
                    <div id="error-message" class="hidden bg-red-50 border-2 border-rojo-termico text-rojo-termico px-4 py-3 rounded-lg font-semibold">
                    </div>
                    
                    <button 
                        type="submit"
                        class="w-full bg-amarillo-termico hover:bg-[#d9a304] text-white font-bold py-3 px-4 rounded-lg transition-colors duration-200 shadow-md">
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
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            'morado-termico': '#4A107B',
                            'amarillo-termico': '#F2B705',
                        }
                    }
                }
            }
        </script>
    </head>
    <body class="bg-[#EFEFEF] min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full">
            <div class="bg-white rounded-lg shadow-2xl p-8 border-2 border-gray-200">
                <div class="text-center mb-6">
                    <div class="bg-green-600 text-white w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <h1 class="text-3xl font-bold mt-4 text-black">Contraseña Restablecida</h1>
                </div>
                <p class="text-gray-600 text-center mb-6">
                    Tu contraseña ha sido restablecida exitosamente. Ya puedes iniciar sesion en la aplicacion movil con tu nueva contraseña.
                </p>
                <div class="bg-amarillo-termico bg-opacity-20 border-2 border-amarillo-termico rounded-lg p-4 mb-6">
                    <p class="text-sm text-black font-semibold text-center">
                        Ahora puedes cerrar esta ventana e iniciar sesion en la app
                    </p>
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
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        colors: {{
                            'morado-termico': '#4A107B',
                            'amarillo-termico': '#F2B705',
                            'rojo-termico': '#F20505',
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body class="bg-[#EFEFEF] min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full">
            <div class="bg-white rounded-lg shadow-2xl p-8 border-2 border-gray-200">
                <div class="text-center mb-6">
                    <svg class="mx-auto h-16 w-16 text-rojo-termico" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <h1 class="text-3xl font-bold mt-4 text-black">Error</h1>
                </div>
                <p class="text-gray-600 text-center mb-6">{mensaje}</p>
                <div class="text-center">
                    <a href="/" class="text-morado-termico hover:text-amarillo-termico font-semibold">Volver al inicio</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """