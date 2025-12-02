import requests
import json
from typing import Optional

# URL por defecto de Ollama en local
OLLAMA_URL = "http://localhost:11434/api/generate"


def obtener_descripcion_de_imagen(imagen_b64: str, prompt: str = "Describe esta imagen detalladamente, enfocándote en cuantos fumadores hay y que parece que estan haciendo.") -> Optional[str]:
    """
    Envía una imagen en Base64 a Ollama (Llava) para obtener una descripción.
    """

    # Limpiamos el header de base64 si viene incluido (ej: "data:image/jpeg;base64,")
    if "," in imagen_b64:
        imagen_b64 = imagen_b64.split(",")[1]

    payload = {
        "model": "llava:7b",
        "prompt": prompt,
        "images": [imagen_b64],
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()

        resultado = response.json()
        descripcion = resultado.get("response", "")

        return descripcion.strip()

    except requests.exceptions.RequestException as e:
        print(f"Error conectando con Ollama: {e}")
        return None
    except Exception as e:
        print(f"Error procesando respuesta de IA: {e}")
        return None
