"""
Servicio de comparación entre períodos.

Versión v2.0 — Soporta hasta 6 períodos con modos de variación configurables.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from sidic.domain.enums import ModoVariacion
from sidic.domain.models.report_data import PeriodData
from sidic.domain.services.statistics import StatisticsCalculator

logger = logging.getLogger(__name__)


@dataclass
class ComparacionItem:
    """Resultado de comparación para un indicador."""

    nombre: str
    valores: List[int]  # Un valor por período
    variaciones: List[float]  # Variación % respecto al base
    tendencias: List[str]  # "subio", "bajo", "igual" por período


class PeriodComparator:
    """
    Compara estadísticas entre múltiples períodos.

    Soporta 3 modos de variación:
    - VS_PRINCIPAL: todas las variaciones respecto al primer período.
    - VS_ANTERIOR: cada período se compara con el inmediatamente anterior.
    - AMBAS: muestra ambas variaciones.
    """

    def __init__(
        self,
        periodos: List[PeriodData],
        modo: ModoVariacion = ModoVariacion.VS_PRINCIPAL,
    ) -> None:
        if len(periodos) < 2:
            raise ValueError("Se requieren al menos 2 períodos para comparar.")
        self.periodos = periodos
        self.modo = modo
        self._stats = StatisticsCalculator()

    @property
    def labels(self) -> List[str]:
        """Etiquetas cortas de cada período."""
        return [p.label_corto for p in self.periodos]

    def comparar(
        self,
        extractor: Callable[[PeriodData], Dict[str, int]],
        nombre_indicador: str = "",
    ) -> List[ComparacionItem]:
        """
        Compara un indicador extraído de cada período.

        Args:
            extractor: Función que extrae un Dict[str, int] de un PeriodData.
                Ej: lambda p: p.conteo_por_delito()
            nombre_indicador: Nombre descriptivo para logging.

        Returns:
            Lista de ComparacionItem, una por cada clave encontrada.
        """
        conteos = [extractor(p) for p in self.periodos]
        todas_claves = sorted(set().union(*(c.keys() for c in conteos)))

        resultados: List[ComparacionItem] = []

        for clave in todas_claves:
            valores = [c.get(clave, 0) for c in conteos]
            variaciones: List[float] = []
            tendencias: List[str] = []

            for i in range(len(valores)):
                if i == 0:
                    variaciones.append(0.0)
                    tendencias.append("igual")
                else:
                    if self.modo == ModoVariacion.VS_PRINCIPAL:
                        base = valores[0]
                    elif self.modo == ModoVariacion.VS_ANTERIOR:
                        base = valores[i - 1]
                    else:
                        base = valores[0]  # Default a vs_principal

                    var = self._stats.variacion(base, valores[i])
                    variaciones.append(var["porcentaje"])
                    tendencias.append(var["tendencia"])

            resultados.append(
                ComparacionItem(
                    nombre=clave,
                    valores=valores,
                    variaciones=variaciones,
                    tendencias=tendencias,
                )
            )

        logger.debug(
            f"Comparación '{nombre_indicador}': {len(resultados)} ítems, "
            f"{len(self.periodos)} períodos, modo={self.modo.value}"
        )

        return resultados

    def comparar_totales(self) -> ComparacionItem:
        """Compara el total de hechos entre períodos."""
        valores = [p.total_hechos for p in self.periodos]
        variaciones = [0.0]
        tendencias = ["igual"]

        for i in range(1, len(valores)):
            base = valores[0] if self.modo == ModoVariacion.VS_PRINCIPAL else valores[i - 1]
            var = self._stats.variacion(base, valores[i])
            variaciones.append(var["porcentaje"])
            tendencias.append(var["tendencia"])

        return ComparacionItem(
            nombre="TOTAL HECHOS",
            valores=valores,
            variaciones=variaciones,
            tendencias=tendencias,
        )

    def comparar_delitos(self) -> List[ComparacionItem]:
        """Comparación de delitos con modalidad."""
        return self.comparar(
            lambda p: p.conteo_por_delito(), "delitos"
        )

    def comparar_dias_semana(self) -> List[ComparacionItem]:
        """Comparación por día de la semana."""
        return self.comparar(
            lambda p: p.conteo_por_dia_semana(), "días de semana"
        )

    def comparar_franjas_horarias(self) -> List[ComparacionItem]:
        """Comparación por franja horaria."""
        return self.comparar(
            lambda p: p.conteo_por_franja_horaria(), "franjas horarias"
        )

    def comparar_movilidad(self) -> List[ComparacionItem]:
        """Comparación de medios de movilidad."""
        return self.comparar(
            lambda p: p.conteo_por_movilidad(), "movilidad"
        )

    def comparar_armas(self) -> List[ComparacionItem]:
        """Comparación de armas en robos agravados."""
        return self.comparar(
            lambda p: p.conteo_por_arma(), "armas"
        )

    def comparar_ambito(self) -> List[ComparacionItem]:
        """Comparación de ámbito de ocurrencia."""
        return self.comparar(
            lambda p: p.conteo_por_ambito(), "ámbito"
        )
