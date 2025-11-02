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

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title="Nuevo Evento Detectado",
            body=f"Se ha detectado un nuevo evento #{evento_id}. Requiere revision."
        ),
        data={
            "evento_id": str(evento_id),
            "tipo": "nuevo_evento"
        },
        tokens=tokens_fcm
    )

    try:
        response = messaging.send_multicast(message)
        print(f"{response.success_count} notificaciones enviadas exitosamente de {len(tokens_fcm)}")
        if response.failure_count > 0:
            print(f"{response.failure_count} notificaciones fallaron")
        return True
    except Exception as e:
        print(f"Error al enviar notificaciones: {e}")
        return False