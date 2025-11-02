import firebase_admin
from firebase_admin import credentials, messaging
import os
from dotenv import load_dotenv

load_dotenv()

FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")

try:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK inicializado correctamente")
except Exception as e:
    print(f"Error al inicializar Firebase Admin SDK: {e}")


def enviar_notificacion_nuevo_evento(token_fcm: str, evento_id: int):
    """Envia notificacion push cuando se crea un nuevo evento"""
    message = messaging.Message(
        notification=messaging.Notification(
            title="Nuevo Evento Detectado",
            body=f"Se ha detectado un nuevo evento #{evento_id}. Requiere revision."
        ),
        data={
            "evento_id": str(evento_id),
            "tipo": "nuevo_evento"
        },
        token=token_fcm
    )

    try:
        response = messaging.send(message)
        print(f"Notificacion enviada exitosamente: {response}")
        return True
    except Exception as e:
        print(f"Error al enviar notificacion: {e}")
        return False


def enviar_notificacion_multiple(tokens_fcm: list, evento_id: int):
    """Envia notificacion a multiples dispositivos (todos los operadores)"""
    if not tokens_fcm:
        print("No hay tokens FCM para enviar notificaciones")
        return False

    # Enviar notificaciones una por una
    exitosos = 0
    fallidos = 0

    for token in tokens_fcm:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Nuevo Evento Detectado",
                    body=f"Se ha detectado un nuevo evento #{evento_id}. Requiere revision."
                ),
                data={
                    "evento_id": str(evento_id),
                    "tipo": "nuevo_evento"
                },
                token=token
            )

            response = messaging.send(message)
            print(f"Notificacion enviada a token: {token[:20]}...")
            exitosos += 1
        except Exception as e:
            print(f"Error al enviar notificacion a token {token[:20]}...: {e}")
            fallidos += 1

    print(f"{exitosos} notificaciones enviadas exitosamente de {len(tokens_fcm)}")
    if fallidos > 0:
        print(f"{fallidos} notificaciones fallaron")

    return exitosos > 0
