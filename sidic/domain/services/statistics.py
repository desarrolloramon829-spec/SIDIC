"""
Servicio de cálculos estadísticos agregados.

Centraliza la lógica de cálculo de porcentajes, variaciones y tendencias
que antes estaba dispersa entre TableGenerator y PeriodComparator.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


class StatisticsCalculator:
    """Calculadora de estadísticas para reportes."""

    @staticmethod
    def porcentaje(parte: int, total: int) -> float:
        """Calcula porcentaje con división segura."""
        if total == 0:
            return 0.0
        return round((parte / total) * 100, 2)

    @staticmethod
    def format_porcentaje(valor: float) -> str:
        """Formatea un porcentaje a string con 2 decimales."""
        return f"{valor:.2f}%"

    @staticmethod
    def variacion(anterior: int, actual: int) -> Dict[str, Any]:
        """
        Calcula variación entre dos valores.

        Returns:
            { diferencia, porcentaje, tendencia }
        """
        diferencia = actual - anterior
        if anterior > 0:
            pct = ((actual - anterior) / anterior) * 100
        elif actual > 0:
            pct = 100.0
        else:
            pct = 0.0

        return {
            "diferencia": diferencia,
            "porcentaje": round(pct, 2),
            "tendencia": (
                "subio" if diferencia > 0
                else "bajo" if diferencia < 0
                else "igual"
            ),
        }

    @staticmethod
    def icono_tendencia(tendencia: str) -> str:
        """Retorna ícono visual para la tendencia."""
        iconos = {
            "subio": "▲",
            "bajo": "▼",
            "igual": "─",
            "nuevo": "★",
        }
        return iconos.get(tendencia, "─")

    @staticmethod
    def comparar_conteos(
        conteo_base: Dict[str, int],
        conteo_comparar: Dict[str, int],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compara dos diccionarios de conteos y calcula variaciones.

        Returns:
            {clave: {base, comparar, diferencia, porcentaje, tendencia, icono}}
        """
        todas_claves = sorted(set(conteo_base.keys()) | set(conteo_comparar.keys()))
        resultado = {}

        for clave in todas_claves:
            val_base = conteo_base.get(clave, 0)
            val_comp = conteo_comparar.get(clave, 0)
            var = StatisticsCalculator.variacion(val_base, val_comp)

            resultado[clave] = {
                "base": val_base,
                "comparar": val_comp,
                **var,
                "icono": StatisticsCalculator.icono_tendencia(var["tendencia"]),
            }

        return resultado

    @staticmethod
    def comparar_conteos_multiple(
        conteos: List[Dict[str, int]],
        labels: List[str],
        indice_base: int = 0,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compara N diccionarios de conteos contra un período base.

        Args:
            conteos: Lista de diccionarios de conteos (uno por período).
            labels: Etiquetas de cada período.
            indice_base: Índice del período base para variaciones.

        Returns:
            {clave: {label_0: val, label_1: val, ..., var_1: %, var_2: %, ...}}
        """
        todas_claves = sorted(
            set().union(*(c.keys() for c in conteos))
        )
        resultado = {}
        base = conteos[indice_base]

        for clave in todas_claves:
            fila: Dict[str, Any] = {}
            for i, (conteo, label) in enumerate(zip(conteos, labels)):
                val = conteo.get(clave, 0)
                fila[label] = val

                if i != indice_base:
                    val_base = base.get(clave, 0)
                    var = StatisticsCalculator.variacion(val_base, val)
                    fila[f"var_{label}"] = var["porcentaje"]
                    fila[f"tend_{label}"] = var["tendencia"]

            resultado[clave] = fila

        return resultado

    @staticmethod
    def agregar_totales(conteo: Dict[str, int]) -> Tuple[Dict[str, int], int]:
        """
        Agrega fila de total a un conteo.

        Returns:
            (conteo_original, total)
        """
        total = sum(conteo.values())
        return conteo, total
