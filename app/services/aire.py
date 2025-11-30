import requests
import json
import datetime
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from enum import Enum
from typing import List, Optional


from app.schemas import CalidadAireBase


def retornar_error_general(mensaje: str) -> CalidadAireBase:
    """
    Retorna un objeto CalidadAireBase con valores None y un mensaje de error.
    """
    return CalidadAireBase(
        temp=None,
        humedad=None,
        pm1p0=None,
        pm2p5=None,
        pm10=None,
        aqi=None,
        descrip=mensaje
    )


def consumir_api_aire() -> CalidadAireBase:
    """
    Consumir la API de WeatherLink y retornar un schema CalidadAireBase.
    Retorna None si hay un error o no se encuentran datos.
    """

    # TODO: manejar errores
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

        for sensor in datos.get('sensors', []):

            lsid = sensor.get('lsid')
            tipoSensor = sensor.get('sensor_type')

            if lsid == 794536 or lsid == 794537:

                if sensor.get('data'):

                    if tipoSensor == 323 or tipoSensor == 326:

                        datosSensor = sensor['data'][0]
                        tsLectura = datosSensor.get('ts', 0)
                        horaLectura = datetime.datetime.fromtimestamp(tsLectura)

                        datosParaSchema = {
                            'temp': datosSensor.get('temp'),
                            'humedad': datosSensor.get('hum'),
                            'pm1p0': datosSensor.get('pm_1'),
                            'pm2p5': datosSensor.get('pm_2p5'),
                            'pm10': datosSensor.get('pm_10'),
                            'aqi': datosSensor.get('aqi_val'),
                            'descrip': datosSensor.get('aqi_desc'),
                            'hora_medicion': horaLectura

                        }

                        schemaCalidadAire = CalidadAireBase(**datosParaSchema)

                        print(schemaCalidadAire.model_dump_json(indent=4))

                        return schemaCalidadAire

        return retornar_error_general("error")

    except requests.exceptions.HTTPError as errHttp:
        return retornar_error_general("error")
    except requests.exceptions.ConnectionError as errCon:
        return retornar_error_general("error")
    except requests.exceptions.Timeout as errTimeout:
        return retornar_error_general("error")
    except requests.exceptions.RequestException as err:
        return retornar_error_general("error")
    except json.JSONDecodeError:
        return retornar_error_general("error")
    except KeyError as errKey:
        return retornar_error_general("error")
    except Exception as e:
        return retornar_error_general("error")


def obtener_historico_aire(start_timestamp: int, end_timestamp: int) -> List[CalidadAireBase]:
    load_dotenv()

    apikey = os.getenv("API_KEY")
    XApiSecret = os.getenv("X_API_SECRET")
    id_station = os.getenv("ID_STATION")

    urlApi = f"https://api.weatherlink.com/v2/historic/{id_station}"

    params = {
        "api-key": apikey,
        "start-timestamp": start_timestamp,
        "end-timestamp": end_timestamp
    }

    headers = {
        'X-Api-Secret': f'{XApiSecret}',
        'Content-Type': 'application/json'
    }

    registros_encontrados = []

    try:
        respuesta = requests.get(urlApi, headers=headers, params=params, timeout=15)
        respuesta.raise_for_status()
        datos = respuesta.json()

        for sensor in datos.get('sensors', []):
            lsid = sensor.get('lsid')

            if lsid == 794536 or lsid == 794537:

                lista_datos = sensor.get('data', [])

                for punto_dato in lista_datos:
                    ts_lectura = punto_dato.get('ts')
                    hora_lectura = datetime.datetime.fromtimestamp(ts_lectura) if ts_lectura else None

                    # print(f"punto dato con prettyjson: {json.dumps(punto_dato, indent=4)}")

                    datos_para_schema = {
                        'temp': punto_dato.get('temp_last'),
                        'humedad': punto_dato.get('hum_last'),
                        'pm1p0': punto_dato.get('pm_1_hi'),
                        'pm2p5': punto_dato.get('pm_2p5_hi'),
                        'pm10': punto_dato.get('pm_10_hi'),
                        'aqi': punto_dato.get('aqi_hi_val'),
                        'descrip': punto_dato.get('aqi_avg_desc'),
                        'hora_medicion': hora_lectura
                    }

                    try:
                        registro = CalidadAireBase(
                            temp=datos_para_schema['temp'] or 0.0,
                            humedad=datos_para_schema['humedad'] or 0.0,
                            pm1p0=datos_para_schema['pm1p0'] or 0.0,
                            pm2p5=datos_para_schema['pm2p5'] or 0.0,
                            pm10=datos_para_schema['pm10'] or 0.0,
                            aqi=datos_para_schema['aqi'] or 0.0,
                            descrip=str(datos_para_schema['descrip']),
                            hora_medicion=hora_lectura
                        )
                        registros_encontrados.append(registro)
                    except Exception as e:
                        print(f"Error parseando un registro histórico: {e}")
                        continue
        return registros_encontrados

    except Exception as e:
        print(f"Error obteniendo históricos WeatherLink: {e}")
        return []


# --- BLOQUE MAIN PARA PRUEBAS ---
if __name__ == "__main__":

    """
    Inicio: 2025-11-19 04:50:00 
    Fin:    2025-11-19 05:10:00
    """
    import datetime

    print("--- PRUEBA DE HISTÓRICO DE AIRE MANUAL ---")

    # 1. DEFINE AQUÍ TU RANGO DE FECHAS (Año-Mes-Dia Hora:Minuto:Segundo)
    fecha_inicio_str = "2025-11-19 04:50:00"
    fecha_fin_str = "2025-11-19 05:10:00"

    try:
        # 2. Convertir strings a objetos datetime
        formato = "%Y-%m-%d %H:%M:%S"
        dt_inicio = datetime.datetime.strptime(fecha_inicio_str, formato)
        dt_fin = datetime.datetime.strptime(fecha_fin_str, formato)

        # 3. Convertir a Timestamps UNIX (enteros) requeridos por la API
        ts_start = int(dt_inicio.timestamp())
        ts_end = int(dt_fin.timestamp())

        print(f"Consultando API WeatherLink...")
        print(f"Desde: {dt_inicio} (TS: {ts_start})")
        print(f"Hasta: {dt_fin} (TS: {ts_end})")

        # 4. Llamar a la función
        resultados = obtener_historico_aire(ts_start, ts_end)

        print(f"\n--- RESULTADOS ({len(resultados)} registros) ---")

        if not resultados:
            print("No se encontraron registros de calidad de aire en ese lapso.")
        else:
            # Ordenar por fecha ascendente
            resultados.sort(key=lambda x: x.hora_medicion if x.hora_medicion else datetime.datetime.min)

            # Imprimir tabla
            print(f"{'HORA':<22} | {'PM1.0':<6} | {'PM2.5':<6} | {'PM10':<6} | {'TEMP':<6}")
            print("-" * 65)

            for r in resultados:
                # Formateo seguro para evitar errores si algún dato es None
                hora = str(r.hora_medicion) if r.hora_medicion else "N/A"
                pm1 = f"{r.pm1p0:.1f}" if r.pm1p0 is not None else "-"
                pm25 = f"{r.pm2p5:.1f}" if r.pm2p5 is not None else "-"
                pm10 = f"{r.pm10:.1f}" if r.pm10 is not None else "-"
                temp = f"{r.temp:.1f}" if r.temp is not None else "-"

                print(f"{hora:<22} | {pm1:<6} | {pm25:<6} | {pm10:<6} | {temp}")

    except ValueError as e:
        print(f"Error en el formato de fecha: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")