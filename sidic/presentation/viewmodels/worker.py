"""
Worker thread para generación de reportes en segundo plano.

Ejecuta los use-cases pesados sin bloquear la UI.
"""
from __future__ import annotations

import logging
import traceback
from typing import Any, Dict, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from sidic.application.dto.dtos import (
    ComparisonInputDTO,
    FilterInputDTO,
    GenerateReportInputDTO,
    LoadDataInputDTO,
)
from sidic.application.use_cases.generate_charts import GenerateChartsUseCase
from sidic.application.use_cases.generate_report import GenerateReportUseCase
from sidic.application.use_cases.generate_tables import GenerateTablesUseCase
from sidic.application.use_cases.load_data import LoadDataUseCase
from sidic.domain.models.report_data import ReportData

logger = logging.getLogger(__name__)


class ReportWorker(QThread):
    """
    Hilo de trabajo para generación de reportes.

    Señales
    -------
    progress(int, str)
        Porcentaje (0-100) y mensaje de estado.
    finished(bool, str, str)
        (éxito, ruta_del_archivo, mensaje).
    error(str)
        Detalle del error.
    data_loaded(object)
        Emite el ReportData cargado para uso posterior.
    """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, str)
    error = pyqtSignal(str)
    data_loaded = pyqtSignal(object)

    def __init__(
        self,
        load_input: LoadDataInputDTO,
        report_input: GenerateReportInputDTO,
        filter_input: FilterInputDTO | None = None,
        comparison_input: ComparisonInputDTO | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._load_input = load_input
        self._report_input = report_input
        self._filter_input = filter_input
        self._comparison_input = comparison_input

    # ── Ejecución principal ──────────────────────────────────────

    def run(self) -> None:  # noqa: C901 — mantenemos el método lineal
        try:
            # 1. Cargar datos ─────────────────────────────────────
            self.progress.emit(5, "Cargando archivos GIS…")
            loader = LoadDataUseCase()
            load_result = loader.execute(self._load_input)

            if not load_result.success:
                errors = "; ".join(load_result.errors)
                self.error.emit(f"Error al cargar datos: {errors}")
                return

            report_data: ReportData = loader.report_data  # type: ignore[assignment]
            self.data_loaded.emit(report_data)
            self.progress.emit(25, "Datos cargados correctamente")

            # 2. Aplicar filtros ──────────────────────────────────
            if self._filter_input and self._filter_input.categorias:
                self.progress.emit(30, "Aplicando filtros…")
                report_data.filter_categories(self._filter_input.categorias)

            # 3. Generar tablas ───────────────────────────────────
            self.progress.emit(35, "Generando tablas estadísticas…")
            table_gen = GenerateTablesUseCase()
            modo = (
                self._comparison_input.modo if self._comparison_input else "vs_principal"
            )
            tables = table_gen.generate_all(report_data, modo_variacion=modo)
            self.progress.emit(55, f"{len(tables)} tablas generadas")

            # 4. Generar gráficos (si aplica) ─────────────────────
            charts: dict[str, bytes] = {}
            if self._report_input.incluir_graficos:
                self.progress.emit(60, "Generando gráficos…")
                chart_gen = GenerateChartsUseCase()
                charts = chart_gen.generate_all(tables)
                self.progress.emit(70, f"{len(charts)} gráficos generados")

            # 5. Exportar ─────────────────────────────────────────
            fmt = self._report_input.formato
            output = self._report_input.output_path

            if fmt == "todos":
                self._export_all_formats(report_data, tables, charts, output)
            else:
                self._export_single_format(
                    fmt, report_data, tables, charts, output,
                )

            self.progress.emit(100, "¡Completado!")

        except Exception:
            tb = traceback.format_exc()
            logger.exception("Error durante generación de reporte")
            self.error.emit(tb)

    # ── Helpers de exportación ───────────────────────────────────

    def _export_single_format(
        self,
        fmt: str,
        report_data: ReportData,
        tables: dict,
        charts: dict,
        output_path: str,
    ) -> None:
        gen = GenerateReportUseCase()

        self.progress.emit(75, f"Exportando a {fmt.upper()}…")
        result = gen.execute(
            report_data=report_data,
            tables=tables,
            charts=charts,
            input_dto=self._report_input,
        )

        if result.success:
            self.finished.emit(True, result.output_path or output_path,
                               f"Reporte {fmt.upper()} generado exitosamente")
        else:
            self.error.emit(result.error or "Error desconocido al exportar")

    def _export_all_formats(
        self,
        report_data: ReportData,
        tables: dict,
        charts: dict,
        base_output: str,
    ) -> None:
        from pathlib import Path

        base = Path(base_output)
        formats = [("excel", ".xlsx", 75), ("word", ".docx", 85), ("pdf", ".pdf", 92)]

        for fmt, ext, pct in formats:
            self.progress.emit(pct, f"Exportando a {fmt.upper()}…")
            dto = GenerateReportInputDTO(
                formato=fmt,
                output_path=str(base.with_suffix(ext)),
                titulo=self._report_input.titulo,
                incluir_graficos=self._report_input.incluir_graficos,
                incluir_cuadro_referencia=self._report_input.incluir_cuadro_referencia,
                incluir_mencionados=self._report_input.incluir_mencionados,
                incluir_aprehendidos=self._report_input.incluir_aprehendidos,
                incluir_matrices=self._report_input.incluir_matrices,
                incluir_comparativos=self._report_input.incluir_comparativos,
            )
            gen = GenerateReportUseCase()
            gen.execute(
                report_data=report_data,
                tables=tables,
                charts=charts,
                input_dto=dto,
            )

        self.finished.emit(
            True,
            str(base.parent),
            "Todos los formatos generados exitosamente",
        )
