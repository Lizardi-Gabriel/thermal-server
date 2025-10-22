import requests
import json
import datetime
from dotenv import load_dotenv
import os


def consumir_api_aire():

    load_dotenv()

    apikey = os.getenv("API_KEY")
    XApiSecret = os.getenv("X_API_SECRET")
    id_station = os.getenv("ID_STATION")

    urlApi = f"https://api.weatherlink.com/v2/current/{id_station}?api-key={apikey}"

    headers = {
        'X-Api-Secret': f'{XApiSecret}',
        'Content-Type': 'application/json'
    }

    try:
        respuesta = requests.get(urlApi, headers=headers, timeout=10)
        respuesta.raise_for_status()
        datos = respuesta.json()

        # print(f"datos en pretty json:\n{json.dumps(datos, indent=4)}")

        print(f"--- Datos Generales de la Estación ---")
        print(f"ID de Estación: {datos.get('station_id')}")
        print(f"UUID: {datos.get('station_id_uuid')}")

        tsGenerado = datos.get('generated_at', 0)
        fechaGenerado = datetime.datetime.fromtimestamp(tsGenerado)

        print(f"Datos generados el: {fechaGenerado}")

        print("\n--- Procesando Sensores ---")

        for sensor in datos.get('sensors', []):

            lsid = sensor.get('lsid')
            tipoSensor = sensor.get('sensor_type')

            if lsid == 794536 or lsid == 794537:

                if sensor.get('data'):
                    datosSensor = sensor['data'][0]
                    tsLectura = datetime.datetime.fromtimestamp(datosSensor.get('ts', 0))

                    print(f"\n[Sensor LSID: {lsid} - Tipo: {tipoSensor}]")
                    print(f"  Fecha de lectura: {tsLectura}")

                    # Identificar qué tipo de sensor es para mostrar datos relevantes
                    # Tipo 506 (Salud del dispositivo)
                    if tipoSensor == 506:
                        print(f"  Tipo: Salud del Dispositivo")
                        print(f"  - IP: {datosSensor.get('ip_v4_address')}")
                        print(f"  - Señal WiFi: {datosSensor.get('wifi_rssi')} dBm")
                        print(f"  - Uptime (seg): {datosSensor.get('uptime')}")

                    # Tipos 323 o 326 (Ambiental)
                    elif tipoSensor == 323 or tipoSensor == 326:
                        print(f"  Tipo: Ambiental / Calidad de Aire")
                        print(f"  - Temperatura: {datosSensor.get('temp')} °F")
                        print(f"  - Humedad: {datosSensor.get('hum')} %")
                        print(f"  - PM 01: {datosSensor.get('pm_1')}")
                        print(f"  - PM 2.5: {datosSensor.get('pm_2p5')}")
                        print(f"  - PM 10: {datosSensor.get('pm_10')}")
                        print(f"  - AQI: {datosSensor.get('aqi_val')}")
                        print(f"  - Descripción: {datosSensor.get('aqi_desc')}")

                    else:
                        print(f"  Tipo: No reconocido ({tipoSensor})")

                else:
                    print(f"\n[Sensor LSID: {lsid}] - Sin datos (lista 'data' vacía).")

    except requests.exceptions.HTTPError as errHttp:
        print(f"Error HTTP: {errHttp}")
        if errHttp.response.status_code == 401 or errHttp.response.status_code == 403:
            print("Verifica tu API Key o Token en el 'Authorization' header.")
    except requests.exceptions.ConnectionError as errCon:
        print(f"Error de Conexión: No se pudo conectar a {urlApi}")
    except requests.exceptions.Timeout as errTimeout:
        print(f"Error: La solicitud a {urlApi} tardó demasiado (Timeout).")
    except requests.exceptions.RequestException as err:
        print(f"Error Inesperado: {err}")
    except json.JSONDecodeError:
        print("Error: La respuesta no es un JSON válido.")
    except KeyError as errKey:
        print(f"Error: El JSON no tiene la estructura esperada. Falta la llave: {errKey}")


# Ejecutar la función
if __name__ == "__main__":
    consumir_api_aire()