import sys
import os
import numpy as np

from sqlalchemy import func, or_, desc
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ajustar_valor(valor, base=5):
    if valor is None:
        return 0
    return int(round(valor / base) * base)


def _sugerir_limites(promedio, maximo, nombre):
    limiteAmarillo = promedio * 1.5
    limiteRojo = (promedio + maximo) / 2

    print(f"\n[Sugerencia para {nombre}]")
    print(f"  -> Límite Amarillo (Warning): > {limiteAmarillo:.2f}")
    print(f"  -> Límite Rojo (Danger):      > {limiteRojo:.2f}")


class CalculadoraLimitesAire:
    def __init__(self, db: Session):
        self.db = db

    def calcular_estadisticas(self):
        print("--- Iniciando Cálculo de Límites de Calidad del Aire ---")

        self._calcular_por_estatus(models.EstatusEventoEnum.confirmado, "CONFIRMADO")
        self._calcular_por_estatus(models.EstatusEventoEnum.descartado, "DESCARTADO")

    def _obtener_moda(self, columna, estatus, base=5):
        valor_ajustado = (func.round(columna / base) * base).label("valor_ajustado")

        result = (
            self.db.query(
                valor_ajustado,
                func.count("*").label("freq")
            )
            .join(models.Evento, models.CalidadAire.evento_id == models.Evento.evento_id)
            .filter(models.Evento.estatus == estatus)
            .group_by(valor_ajustado)
            .order_by(desc("freq"))
            .first()
        )

        return (result.valor_ajustado, result.freq) if result else (None, 0)

    def _obtener_top_frecuencias(self, columna, estatus, limite=50, base=5):
        valor_ajustado = (func.round(columna / base) * base).label("valor_ajustado")

        results = (
            self.db.query(
                valor_ajustado,
                func.count("*").label("freq")
            )
            .join(models.Evento, models.CalidadAire.evento_id == models.Evento.evento_id)
            .filter(models.Evento.estatus == estatus)
            .group_by(valor_ajustado)
            .order_by(desc("freq"))
            .limit(limite)
            .all()
        )

        return results

    def _obtener_percentiles(self, columna, estatus):
        valores = [
            float(row[0])
            for row in self.db.query(columna)
            .join(models.Evento, models.CalidadAire.evento_id == models.Evento.evento_id)
            .filter(models.Evento.estatus == estatus)
            .all()
        ]

        if not valores:
            return {"p25": 0, "p50": 0, "p75": 0}

        return {
            "p25": float(np.percentile(valores, 25)),
            "p50": float(np.percentile(valores, 50)),
            "p75": float(np.percentile(valores, 75)),
        }

    def _calcular_por_estatus(self, estatus, titulo):
        print(f"\n======= ESTADÍSTICAS PARA EVENTOS {titulo} =======")

        query = self.db.query(
            func.avg(models.CalidadAire.pm1p0).label("avg_pm1"),
            func.max(models.CalidadAire.pm1p0).label("max_pm1"),

            func.avg(models.CalidadAire.pm2p5).label("avg_pm25"),
            func.max(models.CalidadAire.pm2p5).label("max_pm25"),

            func.avg(models.CalidadAire.pm10).label("avg_pm10"),
            func.max(models.CalidadAire.pm10).label("max_pm10"),

            func.count(models.CalidadAire.registro_id).label("total")
        ).join(
            models.Evento, models.CalidadAire.evento_id == models.Evento.evento_id
        ).filter(
            models.Evento.estatus == estatus
        )

        result = query.first()

        if not result or result.total == 0:
            print(f"No hay registros en eventos {titulo.lower()}.")
            return

        (rawPm1, freqPm1) = self._obtener_moda(models.CalidadAire.pm1p0, estatus)
        (rawPm25, freqPm25) = self._obtener_moda(models.CalidadAire.pm2p5, estatus)
        (rawPm10, freqPm10) = self._obtener_moda(models.CalidadAire.pm10, estatus)

        modaPm1 = ajustar_valor(rawPm1)
        modaPm25 = ajustar_valor(rawPm25)
        modaPm10 = ajustar_valor(rawPm10)

        percentilesPm1 = self._obtener_percentiles(models.CalidadAire.pm1p0, estatus)
        percentilesPm25 = self._obtener_percentiles(models.CalidadAire.pm2p5, estatus)
        percentilesPm10 = self._obtener_percentiles(models.CalidadAire.pm10, estatus)

        print(f"\nRegistros analizados: {result.total}")
        print("-" * 120)
        print(
            f"{'Métrica':<10} | {'Avg':<8} | {'Max':<8} | {'Moda (Reps)':<15} | "
            f"{'P25':<8} | {'P50':<8} | {'P75':<8}"
        )
        print("-" * 120)

        def imprimir_linea(nombre, avg, maxv, moda, freq, p):
            textoModa = f"{moda} ({freq})"
            print(
                f"{nombre:<10} | "
                f"{avg:<8} | {maxv:<8} | {textoModa:<15} | "
                f"{round(p['p25'], 2):<8} | {round(p['p50'], 2):<8} | {round(p['p75'], 2):<8}"
            )

        imprimir_linea("PM1.0", round(result.avg_pm1 or 0, 2), round(result.max_pm1 or 0, 2), modaPm1, freqPm1,
                       percentilesPm1)
        imprimir_linea("PM2.5", round(result.avg_pm25 or 0, 2), round(result.max_pm25 or 0, 2), modaPm25, freqPm25,
                       percentilesPm25)
        imprimir_linea("PM10", round(result.avg_pm10 or 0, 2), round(result.max_pm10 or 0, 2), modaPm10, freqPm10,
                       percentilesPm10)

        print("-" * 120)

        print("\n--- Top 5 Valores Más Frecuentes (Valor: Repeticiones) ---")
        topPm1 = self._obtener_top_frecuencias(models.CalidadAire.pm1p0, estatus, 50)
        topPm25 = self._obtener_top_frecuencias(models.CalidadAire.pm2p5, estatus, 50)
        topPm10 = self._obtener_top_frecuencias(models.CalidadAire.pm10, estatus, 50)

        print(f"{'Rank':<5} | {'PM1.0':<20} | {'PM2.5':<20} | {'PM10':<20}")
        print("-" * 75)

        for i in range(50):
            val1 = f"{int(topPm1[i].valor_ajustado)} ({topPm1[i].freq})" if i < len(topPm1) else "-"
            val2 = f"{int(topPm25[i].valor_ajustado)} ({topPm25[i].freq})" if i < len(topPm25) else "-"
            val10 = f"{int(topPm10[i].valor_ajustado)} ({topPm10[i].freq})" if i < len(topPm10) else "-"

            print(f"#{i + 1:<4} | {val1:<20} | {val2:<20} | {val10:<20}")
        print("-" * 75)

        _sugerir_limites(result.avg_pm10, result.max_pm10, "PM 10")
        _sugerir_limites(result.avg_pm25, result.max_pm25, "PM 2.5")
        _sugerir_limites(result.avg_pm1, result.max_pm1, "PM 1.0")


if __name__ == "__main__":
    dbSession = SessionLocal()
    try:
        calculadora = CalculadoraLimitesAire(dbSession)
        calculadora.calcular_estadisticas()
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        dbSession.close()


