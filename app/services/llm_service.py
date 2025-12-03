import requests
import json
import subprocess
import time
from typing import Optional


def iniciar_servidor_ollama() -> bool:
    print("iniciar el servidor de Ollama")

    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        intentos = 0
        while intentos < 10:
            try:
                requests.get("http://localhost:11434", timeout=1)
                return True
            except requests.exceptions.ConnectionError:
                time.sleep(1)
                intentos += 1

        print("No se pudo iniciar Ollama")
        return False

    except FileNotFoundError:
        print("Error: No se encontró el comando 'ollama'")
        return False
    except Exception as e:
        print(f"Error al intentar iniciar Ollama: {e}")
        return False


def verificar_y_preparar_ollama(modelo: str = "llava:7b") -> bool:
    base_url = "http://localhost:11434"

    # Verificar si Ollama está activo
    try:
        requests.get(base_url, timeout=2)
        servidor_activo = True
    except requests.exceptions.ConnectionError:
        servidor_activo = iniciar_servidor_ollama()

    if not servidor_activo:
        return False

    # Verificar si el modelo está disponible
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            modelos = [m['name'] for m in response.json().get('models', [])]

            if not any(modelo in m for m in modelos):
                subprocess.run(["ollama", "pull", modelo])
    except Exception:
        return False

    return True


def obtener_descripcion_de_imagen(imagen_b64: str) -> Optional[str]:
    tiempo_total = time.time()
    MODELO = "llava:7b"

    exito = False
    descripcion = None

    # Preparar entorno
    if not verificar_y_preparar_ollama(MODELO):
        tiempo_final = time.time() - tiempo_total
        print(f"[ERROR] No se pudo preparar Ollama | Tiempo total: {tiempo_final:.2f}s")
        return None

    # Limpieza del base64
    if "," in imagen_b64:
        imagen_b64 = imagen_b64.split(",")[1]
    imagen_b64 = imagen_b64.strip()

    url = "http://localhost:11434/api/generate"

    prompt = (
        "describe esta imagen capturada automaticamente, describe la imagen usando espaniol, "
        "enfocate en si hay personas, cuantas personas hay y que estan haciendo"
    )

    payload = {
        "model": MODELO,
        "prompt": prompt,
        "images": [imagen_b64],
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=600)
        response.raise_for_status()

        data = response.json()
        descripcion = data.get("response", "").strip()
        exito = True

    except Exception:
        exito = False

    # --- MENSAJE FINAL ---
    tiempo_final = time.time() - tiempo_total
    estado = "EXITO" if exito else "ERROR"
    print(f"[{estado}] Tiempo total ejecución: {tiempo_final:.2f}s")

    return descripcion if exito else None
