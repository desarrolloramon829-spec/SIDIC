"""
Caso de uso: Generar gráficos estadísticos.

Produce gráficos de barras (PNG bytes) a partir de los DataFrames
generados por GenerateTablesUseCase.
"""
from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from sidic.config import get_section
from sidic.domain.models.report_data import ReportData

logger = logging.getLogger(__name__)

# Paleta para múltiples períodos (hasta 6)
_DEFAULT_COLORS = [
    "#4169E1",  # Azul real
    "#FF6347",  # Rojo tomate
    "#32CD32",  # Verde lima
    "#FFD700",  # Oro
    "#9370DB",  # Púrpura
    "#20B2AA",  # Verde mar
]


class GenerateChartsUseCase:
    """
    Genera gráficos de barras en PNG desde los DataFrames del reporte.

    Soporta gráficos simples (1 período) y agrupados (N períodos).
    """

    def __init__(self, report_data: ReportData) -> None:
        self._rd = report_data
        self._colors = self._load_colors()
        self._setup_style()

    def _load_colors(self) -> List[str]:
        try:
            cfg = get_section("chart_config")
            return cfg.get("colores_periodos", _DEFAULT_COLORS)
        except Exception:
            return _DEFAULT_COLORS

    @staticmethod
    def _setup_style():
        """Configura estilo matplotlib."""
        try:
            import matplotlib.pyplot as plt

            plt.style.use("default")
            plt.rcParams.update({
                "figure.facecolor": "white",
                "axes.facecolor": "white",
                "axes.edgecolor": "#333333",
                "font.family": "sans-serif",
                "font.sans-serif": ["Segoe UI", "Arial", "Helvetica"],
            })
        except ImportError:
            pass

    # ─── API principal ─────────────────────────────────────────────────

    def generate_all(
        self, tables: Dict[str, pd.DataFrame]
    ) -> Dict[str, bytes]:
        """
        Genera todos los gráficos posibles para las tablas dadas.

        Returns:
            Dict nombre → bytes PNG.
        """
        import matplotlib.pyplot as plt

        charts: Dict[str, bytes] = {}

        # Tablas de conteo simple → gráfico de barras
        _CHART_MAP = [
            ("delitos", "DELITOS CON MODALIDADES", "Delitos con modalidades"),
            ("dias_semana", "DÍA DE LA SEMANA", "Días de la semana"),
            ("franja_horaria", "FRANJA HORARIA", "Franja horaria"),
            ("movilidad", "MOVILIDAD", "Medios de movilidad"),
            ("armas", "ARMA/MEDIO", "Armas / medios"),
            ("ambito", "ÁMBITO", "Ámbito de ocurrencia"),
            ("esclarecimiento", "ESCLARECIMIENTO", "Esclarecimiento"),
        ]

        for key, col_cat, titulo in _CHART_MAP:
            if key not in tables:
                continue
            df = tables[key]
            try:
                if self._rd.es_comparativo:
                    fig = self._bar_chart_grouped(df, col_cat, titulo)
                else:
                    fig = self._bar_chart_simple(df, col_cat, titulo)
                if fig:
                    charts[key] = self._fig_to_bytes(fig)
                    plt.close(fig)
            except Exception as e:
                logger.warning(f"Gráfico '{key}': {e}")

        # Comparativa detallada
        if "comparativa_detallada" in tables:
            try:
                fig = self._comparative_chart(tables["comparativa_detallada"])
                if fig:
                    charts["comparativa_delitos"] = self._fig_to_bytes(fig)
                    plt.close(fig)
            except Exception as e:
                logger.warning(f"Gráfico comparativo: {e}")

        return charts

    # ─── Gráficos ──────────────────────────────────────────────────────

    def _bar_chart_simple(
        self,
        df: pd.DataFrame,
        col_cat: str,
        titulo: str,
    ):
        """Gráfico de barras simple (1 período)."""
        import matplotlib.pyplot as plt
        import numpy as np

        if df.empty or col_cat not in df.columns:
            return None

        # Excluir fila TOTAL
        data = df[~df[col_cat].str.upper().str.contains("TOTAL", na=False)].copy()
        if data.empty:
            return None

        # Columna de valores = segunda columna (la de conteo)
        val_cols = [c for c in data.columns if c not in (col_cat, "%", "Color", "color_fila", "tendencia")]
        if not val_cols:
            return None
        val_col = val_cols[0]

        labels = data[col_cat].tolist()
        values = pd.to_numeric(data[val_col], errors="coerce").fillna(0).tolist()

        fig, ax = plt.subplots(figsize=(10, max(5, len(labels) * 0.4)))
        y_pos = np.arange(len(labels))
        bars = ax.barh(y_pos, values, color=self._colors[0], alpha=0.85)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("Cantidad")
        ax.set_title(titulo, fontsize=13, fontweight="bold", color="#CC0000")
        ax.invert_yaxis()

        # Etiquetas de valor
        for bar in bars:
            w = bar.get_width()
            if w > 0:
                ax.annotate(
                    str(int(w)),
                    xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0),
                    textcoords="offset points",
                    va="center",
                    fontsize=8,
                )

        fig.tight_layout()
        return fig

    def _bar_chart_grouped(
        self,
        df: pd.DataFrame,
        col_cat: str,
        titulo: str,
    ):
        """Gráfico de barras agrupadas (N períodos)."""
        import matplotlib.pyplot as plt
        import numpy as np

        if df.empty or col_cat not in df.columns:
            return None

        data = df[~df[col_cat].str.upper().str.contains("TOTAL", na=False)].copy()
        if data.empty:
            return None

        val_cols = [
            c for c in data.columns
            if c not in (col_cat, "%", "Variación", "Color", "color_fila", "tendencia", "Dif. Cant.", "Variación %")
        ]
        if not val_cols:
            return None

        labels = data[col_cat].tolist()
        n_groups = len(labels)
        n_bars = len(val_cols)
        bar_width = 0.8 / n_bars

        fig, ax = plt.subplots(figsize=(12, max(5, n_groups * 0.5)))
        y_pos = np.arange(n_groups)

        for i, vc in enumerate(val_cols):
            offset = (i - n_bars / 2 + 0.5) * bar_width
            vals = pd.to_numeric(data[vc], errors="coerce").fillna(0).tolist()
            color = self._colors[i % len(self._colors)]
            ax.barh(y_pos + offset, vals, bar_width, label=vc, color=color, alpha=0.85)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("Cantidad")
        ax.set_title(titulo, fontsize=13, fontweight="bold", color="#CC0000")
        ax.legend(fontsize=8)
        ax.invert_yaxis()

        fig.tight_layout()
        return fig

    def _comparative_chart(self, df: pd.DataFrame):
        """Gráfico comparativo especial (delitos con tendencia)."""
        import matplotlib.pyplot as plt
        import numpy as np

        if df.empty or "DELITO" not in df.columns:
            return None

        data = df[~df["DELITO"].str.upper().str.contains("TOTAL", na=False)].copy()
        if data.empty:
            return None

        val_cols = [
            c for c in data.columns
            if c not in ("DELITO", "Dif. Cant.", "Variación %", "color_fila", "tendencia")
        ]
        if len(val_cols) < 2:
            return None

        return self._bar_chart_grouped(data.rename(columns={"DELITO": "_DELITO"}), "_DELITO", "Comparativa de delitos")

    # ─── Utilidades ────────────────────────────────────────────────────

    @staticmethod
    def _fig_to_bytes(fig, fmt: str = "png", dpi: int = 150) -> bytes:
        """Convierte Figure a bytes PNG."""
        buf = io.BytesIO()
        fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight")
        buf.seek(0)
        return buf.read()
