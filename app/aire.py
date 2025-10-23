import requests
import json
import datetime
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from enum import Enum

from schemas import CalidadAireBase


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

        tsGenerado = datos.get('generated_at', 0)
        fechaGenerado = datetime.datetime.fromtimestamp(tsGenerado)

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
                            'pm1p0': datosSensor.get('pm_1'),   # API 'pm_1' -> Schema 'pm1p0'
                            'pm2p5': datosSensor.get('pm_2p5'), # API 'pm_2p5' -> Schema 'pm2p5'
                            'pm10': datosSensor.get('pm_10'),  # API 'pm_10' -> Schema 'pm10'
                            'aqi': datosSensor.get('aqi_val'),  # API 'aqi_val' -> Schema 'aqi'
                            'descrip': datosSensor.get('aqi_desc'), # API 'aqi_desc' -> Schema 'descrip'
                            'hora_medicion': horaLectura

                        }

                        schemaCalidadAire = CalidadAireBase(**datosParaSchema)

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
