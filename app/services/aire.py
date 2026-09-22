import requests
import json
import datetime
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
from loguru import logger

from app.schemas import CalidadAireBase

WEATHERLINK_CAIDO = "WEATHERLINK_CAIDO"
WEATHERLINK_SIN_DATOS = "WEATHERLINK_SIN_DATOS"
WEATHERLINK_JSON_INVALIDO = "WEATHERLINK_JSON_INVALIDO"


def retornar_error_general(mensaje: str, estado: str = WEATHERLINK_CAIDO) -> CalidadAireBase:
    """
    Retorna un objeto CalidadAireBase con valores válidos y una categoría explícita
    para distinguir si WeatherLink cayó, respondió sin datos o devolvió JSON inválido.
    """
    logger.warning("API de calidad del aire falló | estado={} | detalle={}", estado, mensaje)
    return CalidadAireBase(
        temp=0.0,
        humedad=0.0,
        pm1p0=0.0,
        pm2p5=0.0,
        pm10=0.0,
        aqi=0.0,
        descrip=f"{estado}: {mensaje}",
        hora_medicion=datetime.datetime.utcnow()
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
                        logger.debug("Calidad del aire recibida: {}", schemaCalidadAire.model_dump_json(indent=4))
                        return schemaCalidadAire

        logger.warning("WeatherLink respondió sin datos válidos para la estación {}", id_station)
        return retornar_error_general(
            f"WeatherLink respondió sin datos para la estación {id_station}",
            estado=WEATHERLINK_SIN_DATOS,
        )

    except requests.exceptions.HTTPError as errHttp:
        logger.warning("WeatherLink caído: respondió con HTTP error: {}", errHttp)
        return retornar_error_general(f"HTTP error: {errHttp}", estado=WEATHERLINK_CAIDO)
    except requests.exceptions.ConnectionError as errCon:
        logger.warning("WeatherLink caído: no disponible (ConnectionError): {}", errCon)
        return retornar_error_general(f"ConnectionError: {errCon}", estado=WEATHERLINK_CAIDO)
    except requests.exceptions.Timeout as errTimeout:
        logger.warning("WeatherLink caído: excedió timeout: {}", errTimeout)
        return retornar_error_general(f"Timeout: {errTimeout}", estado=WEATHERLINK_CAIDO)
    except requests.exceptions.RequestException as err:
        logger.warning("WeatherLink caído: RequestException: {}", err)
        return retornar_error_general(f"RequestException: {err}", estado=WEATHERLINK_CAIDO)
    except json.JSONDecodeError as errJson:
        logger.warning("WeatherLink respondió con JSON inválido: {}", errJson)
        return retornar_error_general(f"JSON inválido: {errJson}", estado=WEATHERLINK_JSON_INVALIDO)
    except KeyError as errKey:
        logger.warning("WeatherLink respondió sin la estructura esperada: {}", errKey)
        return retornar_error_general(
            f"Estructura inesperada en la respuesta: {errKey}",
            estado=WEATHERLINK_SIN_DATOS,
        )
    except Exception as e:
        logger.exception("Error inesperado al consultar WeatherLink: {}", e)
        return retornar_error_general(f"Error inesperado: {e}", estado=WEATHERLINK_CAIDO)


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
                    except Exception:
                        logger.exception("Error parseando un registro histórico de WeatherLink")
                        continue
        return registros_encontrados

    except Exception:
        logger.exception("Error obteniendo históricos WeatherLink")
        return []


# --- BLOQUE MAIN PARA PRUEBAS ---
if __name__ == "__main__":

    import datetime

    logger.info("--- PRUEBA DE HISTÓRICO DE AIRE MANUAL ---")

    fecha_inicio_str = "2025-11-19 04:50:00"
    fecha_fin_str = "2025-11-19 05:10:00"

    try:
        formato = "%Y-%m-%d %H:%M:%S"
        dt_inicio = datetime.datetime.strptime(fecha_inicio_str, formato)
        dt_fin = datetime.datetime.strptime(fecha_fin_str, formato)

        # Convertir a Timestamps requeridos por la API
        ts_start = int(dt_inicio.timestamp())
        ts_end = int(dt_fin.timestamp())

        logger.info("Consultando API WeatherLink...")
        logger.info("Desde: {} (TS: {})", dt_inicio, ts_start)
        logger.info("Hasta: {} (TS: {})", dt_fin, ts_end)

        resultados = obtener_historico_aire(ts_start, ts_end)

        logger.info("--- RESULTADOS ({} registros) ---", len(resultados))

        if not resultados:
            logger.warning("No se encontraron registros de calidad de aire en ese lapso.")
        else:
            # Ordenar por fecha ascendente
            resultados.sort(key=lambda x: x.hora_medicion if x.hora_medicion else datetime.datetime.min)

            # Imprimir tabla
            logger.info("{:<22} | {:<6} | {:<6} | {:<6} | {:<6}", 'HORA', 'PM1.0', 'PM2.5', 'PM10', 'TEMP')
            logger.info("-" * 65)

            for r in resultados:
                # Formateo seguro para evitar errores si algún dato es None
                hora = str(r.hora_medicion) if r.hora_medicion else "N/A"
                pm1 = f"{r.pm1p0:.1f}" if r.pm1p0 is not None else "-"
                pm25 = f"{r.pm2p5:.1f}" if r.pm2p5 is not None else "-"
                pm10 = f"{r.pm10:.1f}" if r.pm10 is not None else "-"
                temp = f"{r.temp:.1f}" if r.temp is not None else "-"

                logger.info("{:<22} | {:<6} | {:<6} | {:<6} | {:<6}", hora, pm1, pm25, pm10, temp)

    except ValueError:
        logger.exception("Error en el formato de fecha")
    except Exception:
        logger.exception("Error inesperado")