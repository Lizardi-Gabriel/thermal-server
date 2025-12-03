import requests
import json
import subprocess
import time
from typing import Optional


def iniciar_servidor_ollama() -> bool:

    print(" iniciar el servidor de Ollama")
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
                print("Servidor Ollama iniciado")
                return True
            except requests.exceptions.ConnectionError:
                time.sleep(1)
                intentos += 1
                print(f"Esperando arranque ({intentos}/10)")

        print("No se pudo iniciar Ollama")
        return False

    except FileNotFoundError:
        print("Error: No se encontró el comando 'ollama'")
        return False
    except Exception as e:
        print(f"Error al intentar iniciar Ollama: {e}")
        return False


def verificar_y_preparar_ollama(modelo: str = "llava:7b") -> bool:

    print('verificar y preparar modelo ollama')

    base_url = "http://localhost:11434"

    servidor_activo = False
    try:
        requests.get(base_url, timeout=2)
        servidor_activo = True
    except requests.exceptions.ConnectionError:
        print("Ollama no responde, iniciando")
        servidor_activo = iniciar_servidor_ollama()

    if not servidor_activo:
        print("ERROR: No se puede conectar con Ollama.")
        return False

    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            modelos = [m['name'] for m in response.json().get('models', [])]
            if not any(modelo in m for m in modelos):
                print('descargando modelo')
                subprocess.run(["ollama", "pull", modelo])
            else:
                print(f"Conexión exitosa con modelo '{modelo}'")
    except Exception as e:
        print(f"verificar lista de modelos: {e}")

    return True


def obtener_descripcion_de_imagen(imagen_b64: str) -> Optional[str]:
    MODELO = "llava:7b"

    if not verificar_y_preparar_ollama(MODELO):
        return None

    prompt: str = (
        "describe esta imagen capturada automaticamente, describe la imagen usando espaniol, enfocate en si hay personas, cuantas personas hay y que estan haciendo"
    )

    if "," in imagen_b64:
        imagen_b64 = imagen_b64.split(",")[1]

    imagen_b64 = imagen_b64.strip()

    url = "http://localhost:11434/api/generate"

    payload = {
        "model": MODELO,
        "prompt": prompt,
        "images": [imagen_b64],
        "stream": False
    }

    try:
        print("Ollama API procesando")

        response = requests.post(url, json=payload, timeout=600)

        response.raise_for_status()
        data = response.json()
        descripcion = data.get("response", "").strip()

        print(descripcion)

        return descripcion

    except requests.exceptions.ConnectionError:
        print("Error: Se perdio la conexión con Ollama.")
        return None
    except requests.exceptions.Timeout:
        print("Error: La petición a Ollama - tiempo de espera (60s).")
        return None
    except Exception as e:
        print(f"Error inesperado ejecutando ollama: {e}")
        return None
