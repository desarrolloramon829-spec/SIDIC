"""
Caso de uso: Generar todas las tablas estadísticas.

Produce DataFrames listos para exportar a partir de ReportData.
Soporta tablas simples (1 período) y comparativas (hasta 6).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from sidic.config import get_section
from sidic.domain.enums.dia_semana import DiaSemana
from sidic.domain.enums.franja_horaria import FranjaHoraria
from sidic.domain.models.report_data import PeriodData, ReportData
from sidic.domain.services.statistics import StatisticsCalculator

logger = logging.getLogger(__name__)


class GenerateTablesUseCase:
    """Genera todas las tablas del reporte a partir de ReportData."""

    def __init__(self, report_data: ReportData) -> None:
        self._rd = report_data
        self._stats = StatisticsCalculator()

    # ─── API principal ─────────────────────────────────────────────────

    def generate_all(self) -> Dict[str, pd.DataFrame]:
        """Genera todas las tablas disponibles y las retorna como dict."""
        tables: Dict[str, pd.DataFrame] = {}
        p = self._rd.periodo_principal
        if p is None:
            return tables

        # Tablas simples / comparativas
        _generators = [
            ("cuadro_referencia", self._cuadro_referencia),
            ("delitos", self._delitos),
            ("dias_semana", self._dias_semana),
            ("franja_horaria", self._franja_horaria),
            ("movilidad", self._movilidad),
            ("armas", self._armas),
            ("ambito", self._ambito),
            ("esclarecimiento", self._esclarecimiento),
            ("matriz_delito_dia", self._matriz_delito_dia),
            ("matriz_delito_franja", self._matriz_delito_franja),
            ("mencionados", self._mencionados),
            ("aprehendidos", self._aprehendidos),
            ("aprehendidos_clasificacion", self._aprehendidos_clasificacion),
        ]

        for key, fn in _generators:
            try:
                df = fn()
                if df is not None and not df.empty:
                    tables[key] = df
            except Exception as e:
                logger.warning(f"Error generando tabla '{key}': {e}")

        # Comparativas (si hay más de 1 período)
        if self._rd.es_comparativo:
            try:
                tables["comparativa_detallada"] = self._comparativa_detallada()
            except Exception as e:
                logger.warning(f"Error en tabla comparativa: {e}")

        return tables

    # ─── Helpers ───────────────────────────────────────────────────────

    def _conteo_a_df(
        self,
        conteo: Dict[str, int],
        col_nombre: str,
        col_valor: str,
        ordenar: bool = True,
        incluir_total: bool = True,
        incluir_pct: bool = True,
    ) -> pd.DataFrame:
        """Convierte dict {nombre: cantidad} a DataFrame con %, total."""
        if not conteo:
            return pd.DataFrame()

        items = sorted(conteo.items(), key=lambda x: x[1], reverse=True) if ordenar else list(conteo.items())
        total = sum(v for _, v in items)

        rows = []
        for nombre, valor in items:
            row: Dict[str, Any] = {col_nombre: nombre.replace("_", " "), col_valor: valor}
            if incluir_pct:
                row["%"] = self._stats.format_porcentaje(
                    self._stats.porcentaje(valor, total)
                )
            rows.append(row)

        if incluir_total:
            row_t: Dict[str, Any] = {col_nombre: "TOTAL", col_valor: total}
            if incluir_pct:
                row_t["%"] = "100.00%"
            rows.append(row_t)

        return pd.DataFrame(rows)

    def _multi_period_df(
        self,
        col_nombre: str,
        extractor,
        labels: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Genera DF comparativo para N períodos."""
        periods = self._rd.periodos
        if labels is None:
            labels = [p.rango_fechas for p in periods]

        all_keys: list = []
        conteos = []
        for p in periods:
            c = extractor(p)
            conteos.append(c)
            for k in c:
                if k not in all_keys:
                    all_keys.append(k)

        rows = []
        totals = {lbl: 0 for lbl in labels}
        for key in all_keys:
            row: Dict[str, Any] = {col_nombre: key.replace("_", " ")}
            for lbl, c in zip(labels, conteos):
                val = c.get(key, 0)
                row[lbl] = val
                totals[lbl] += val
            rows.append(row)

        # Variación respecto al primero
        if len(periods) >= 2:
            for row in rows:
                v1 = row.get(labels[0], 0)
                v2 = row.get(labels[-1], 0)
                var = self._stats.variacion(v1, v2)
                row["Variación"] = var.get("texto", "")

        # Total
        row_t: Dict[str, Any] = {col_nombre: "TOTAL"}
        row_t.update(totals)
        if len(periods) >= 2:
            var = self._stats.variacion(totals[labels[0]], totals[labels[-1]])
            row_t["Variación"] = var.get("texto", "")
        rows.append(row_t)

        return pd.DataFrame(rows)

    # ─── Tablas individuales ──────────────────────────────────────────

    def _cuadro_referencia(self) -> pd.DataFrame:
        """Cuadro de referencia con símbolos."""
        p = self._rd.periodo_principal
        if p is None:
            return pd.DataFrame()

        ref = p.cuadro_referencia()
        if not ref:
            return pd.DataFrame()

        rows = []
        for item in ref:
            rows.append({
                "Símbolo": item.get("simbolo", ""),
                "Tipo": item.get("tipo", ""),
                "Delito": item.get("delito", ""),
                "Cantidad": item.get("cantidad", 0),
                "Color": item.get("color", ""),
            })
        return pd.DataFrame(rows)

    def _delitos(self) -> pd.DataFrame:
        if self._rd.es_comparativo:
            return self._multi_period_df(
                "DELITOS CON MODALIDADES",
                lambda p: p.conteo_por_delito(),
            )
        p = self._rd.periodo_principal
        return self._conteo_a_df(
            p.conteo_por_delito(),
            "DELITOS CON MODALIDADES",
            p.rango_fechas,
        )

    def _dias_semana(self) -> pd.DataFrame:
        if self._rd.es_comparativo:
            return self._multi_period_df(
                "DÍA DE LA SEMANA",
                lambda p: p.conteo_por_dia_semana(),
            )
        p = self._rd.periodo_principal
        return self._conteo_a_df(
            p.conteo_por_dia_semana(),
            "DÍA DE LA SEMANA",
            p.rango_fechas,
        )

    def _franja_horaria(self) -> pd.DataFrame:
        if self._rd.es_comparativo:
            return self._multi_period_df(
                "FRANJA HORARIA",
                lambda p: p.conteo_por_franja_horaria(),
            )
        p = self._rd.periodo_principal
        return self._conteo_a_df(
            p.conteo_por_franja_horaria(),
            "FRANJA HORARIA",
            p.rango_fechas,
        )

    def _movilidad(self) -> pd.DataFrame:
        if self._rd.es_comparativo:
            return self._multi_period_df(
                "MOVILIDAD",
                lambda p: p.conteo_por_movilidad(),
            )
        p = self._rd.periodo_principal
        return self._conteo_a_df(
            p.conteo_por_movilidad(),
            "MOVILIDAD",
            p.rango_fechas,
        )

    def _armas(self) -> pd.DataFrame:
        if self._rd.es_comparativo:
            return self._multi_period_df(
                "ARMA/MEDIO",
                lambda p: p.conteo_por_arma(),
            )
        p = self._rd.periodo_principal
        return self._conteo_a_df(
            p.conteo_por_arma(),
            "ARMA/MEDIO",
            p.rango_fechas,
        )

    def _ambito(self) -> pd.DataFrame:
        if self._rd.es_comparativo:
            return self._multi_period_df(
                "ÁMBITO",
                lambda p: p.conteo_por_ambito(),
            )
        p = self._rd.periodo_principal
        return self._conteo_a_df(
            p.conteo_por_ambito(),
            "ÁMBITO",
            p.rango_fechas,
        )

    def _esclarecimiento(self) -> pd.DataFrame:
        if self._rd.es_comparativo:
            return self._multi_period_df(
                "ESCLARECIMIENTO",
                lambda p: p.conteo_por_esclarecimiento(),
            )
        p = self._rd.periodo_principal
        return self._conteo_a_df(
            p.conteo_por_esclarecimiento(),
            "ESCLARECIMIENTO",
            p.rango_fechas,
        )

    def _matriz_delito_dia(self) -> pd.DataFrame:
        """Matriz cruzada: delito × día de la semana."""
        p = self._rd.periodo_principal
        if p is None:
            return pd.DataFrame()
        matriz = p.matriz_delito_dia()
        if not matriz:
            return pd.DataFrame()
        return pd.DataFrame(matriz).fillna(0).astype(int)

    def _matriz_delito_franja(self) -> pd.DataFrame:
        """Matriz cruzada: delito × franja horaria."""
        p = self._rd.periodo_principal
        if p is None:
            return pd.DataFrame()
        matriz = p.matriz_delito_franja()
        if not matriz:
            return pd.DataFrame()
        return pd.DataFrame(matriz).fillna(0).astype(int)

    def _mencionados(self) -> pd.DataFrame:
        """Tabla de personas mencionadas."""
        p = self._rd.periodo_principal
        if p is None or not p.mencionados:
            return pd.DataFrame()

        rows = []
        for m in p.mencionados:
            rows.append({
                "ALIAS": m.alias,
                "NOMBRE": m.nombre,
                "DESCRIPCIÓN": m.datos_filiatorios,
                "DELITO": m.delito,
                "NRO SUMARIO": m.nro_sumario,
            })
        return pd.DataFrame(rows)

    def _aprehendidos(self) -> pd.DataFrame:
        """Tabla de aprehendidos."""
        p = self._rd.periodo_principal
        if p is None or not p.aprehendidos:
            return pd.DataFrame()

        rows = []
        for a in p.aprehendidos:
            rows.append({
                "NOMBRE": a.nombre,
                "EDAD": a.edad if a.edad else "",
                "SEXO": a.sexo,
                "CLASIFICACIÓN": a.clasificacion.value if a.clasificacion else "",
                "DELITO": a.delito,
                "NRO SUMARIO": a.nro_sumario,
            })
        return pd.DataFrame(rows)

    def _aprehendidos_clasificacion(self) -> pd.DataFrame:
        """Conteo de aprehendidos por clasificación."""
        p = self._rd.periodo_principal
        if p is None or not p.aprehendidos:
            return pd.DataFrame()

        conteo: Dict[str, int] = {}
        for a in p.aprehendidos:
            clas = a.clasificacion.value if a.clasificacion else "SIN CLASIFICAR"
            conteo[clas] = conteo.get(clas, 0) + 1

        if self._rd.es_comparativo:
            return self._multi_period_df(
                "CLASIFICACIÓN",
                lambda per: self._conteo_clasif(per),
            )

        return self._conteo_a_df(
            conteo,
            "CLASIFICACIÓN",
            p.rango_fechas,
        )

    @staticmethod
    def _conteo_clasif(p: PeriodData) -> Dict[str, int]:
        conteo: Dict[str, int] = {}
        for a in p.aprehendidos:
            clas = a.clasificacion.value if a.clasificacion else "SIN CLASIFICAR"
            conteo[clas] = conteo.get(clas, 0) + 1
        return conteo

    def _comparativa_detallada(self) -> pd.DataFrame:
        """
        Tabla comparativa con colores de tendencia.

        Agrega columnas `color_fila` y `tendencia` para
        que los exportadores apliquen estilos.
        """
        if not self._rd.es_comparativo:
            return pd.DataFrame()

        periods = self._rd.periodos
        labels = [p.rango_fechas for p in periods]

        all_delitos: list = []
        conteos = []
        for p in periods:
            c = p.conteo_por_delito()
            conteos.append(c)
            for k in c:
                if k not in all_delitos:
                    all_delitos.append(k)

        rows = []
        totals = {lbl: 0 for lbl in labels}

        for delito in all_delitos:
            row: Dict[str, Any] = {"DELITO": delito.replace("_", " ")}
            vals = []
            for lbl, c in zip(labels, conteos):
                v = c.get(delito, 0)
                row[lbl] = v
                totals[lbl] += v
                vals.append(v)

            v1, v2 = vals[0], vals[-1]
            diff = v2 - v1
            var = self._stats.variacion(v1, v2)
            row["Dif. Cant."] = f"{'+' if diff > 0 else ''}{diff}"
            row["Variación %"] = var.get("texto", "")

            # Colores: rojo = subió (malo), azul = bajó (bueno)
            if diff > 0:
                row["color_fila"] = "#FF0000"
                row["tendencia"] = "up"
            elif diff < 0:
                row["color_fila"] = "#0000FF"
                row["tendencia"] = "down"
            else:
                row["color_fila"] = "#FFFFFF"
                row["tendencia"] = "equal"

            rows.append(row)

        # Total
        diff_t = totals[labels[-1]] - totals[labels[0]]
        var_t = self._stats.variacion(totals[labels[0]], totals[labels[-1]])
        row_t: Dict[str, Any] = {"DELITO": "TOTAL DE HECHOS"}
        row_t.update(totals)
        row_t["Dif. Cant."] = f"{'+' if diff_t > 0 else ''}{diff_t}"
        row_t["Variación %"] = var_t.get("texto", "")
        row_t["color_fila"] = "#FFFF00"
        row_t["tendencia"] = "total"
        rows.append(row_t)

        return pd.DataFrame(rows)
