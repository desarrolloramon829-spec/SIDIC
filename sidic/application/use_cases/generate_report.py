"""
Caso de uso: Generar reporte completo.

Orquesta la generación de tablas, gráficos y exportación
al formato seleccionado (Excel, Word, PDF).
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

import pandas as pd

from sidic.application.dto.dtos import (
    GenerateReportInputDTO,
    GenerateReportOutputDTO,
)
from sidic.domain.models.report_data import ReportData
from sidic.infrastructure.exporters.base_exporter import ExportOptions

logger = logging.getLogger(__name__)


class GenerateReportUseCase:
    """
    Genera el reporte completo en el formato solicitado.

    Flujo:
        1. Genera todas las tablas requeridas (via TableGenerator)
        2. Genera gráficos correspondientes (via ChartGenerator)
        3. Exporta al formato seleccionado
    """

    def __init__(self, report_data: ReportData) -> None:
        self._report_data = report_data

    def execute(self, input_dto: GenerateReportInputDTO) -> GenerateReportOutputDTO:
        """Ejecuta la generación del reporte."""
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Generar tablas
        try:
            from sidic.application.use_cases.generate_tables import GenerateTablesUseCase

            tables_uc = GenerateTablesUseCase(self._report_data)
            tables = tables_uc.generate_all()
            tables_generated = list(tables.keys())
        except Exception as e:
            msg = f"Error generando tablas: {e}"
            logger.exception(msg)
            return GenerateReportOutputDTO(success=False, error=msg)

        # 2. Generar gráficos (si se requieren)
        charts: Dict[str, bytes] = {}
        charts_generated: List[str] = []
        if input_dto.incluir_graficos:
            try:
                from sidic.application.use_cases.generate_charts import GenerateChartsUseCase

                charts_uc = GenerateChartsUseCase(self._report_data)
                charts = charts_uc.generate_all(tables)
                charts_generated = list(charts.keys())
            except Exception as e:
                warnings.append(f"Gráficos no generados: {e}")

        # 3. Exportar
        options = ExportOptions(
            incluir_graficos=input_dto.incluir_graficos,
            incluir_cuadro_referencia=input_dto.incluir_cuadro_referencia,
            incluir_mencionados=input_dto.incluir_mencionados,
            incluir_aprehendidos=input_dto.incluir_aprehendidos,
            incluir_matrices=input_dto.incluir_matrices,
            incluir_comparativos=input_dto.incluir_comparativos,
            titulo=input_dto.titulo,
            jurisdiccion=self._report_data.jurisdiccion,
            dependencia=self._report_data.dependencia,
        )

        exporter = self._create_exporter(input_dto.formato)
        if exporter is None:
            return GenerateReportOutputDTO(
                success=False,
                error=f"Formato '{input_dto.formato}' no soportado.",
            )

        result = exporter.export(
            input_dto.output_path,
            tables,
            charts,
            options,
        )

        return GenerateReportOutputDTO(
            success=result.success,
            output_path=result.output_path,
            error=result.error,
            warnings=warnings + (result.warnings or []),
            tables_generated=tables_generated,
            charts_generated=charts_generated,
        )

    @staticmethod
    def _create_exporter(formato: str):
        """Crea el exportador según el formato."""
        fmt = formato.lower().strip()
        if fmt in ("excel", "xlsx", ".xlsx"):
            from sidic.infrastructure.exporters.excel_exporter import ExcelExporter
            return ExcelExporter()
        elif fmt in ("word", "docx", ".docx"):
            from sidic.infrastructure.exporters.word_exporter import WordExporter
            return WordExporter()
        elif fmt in ("pdf", ".pdf"):
            from sidic.infrastructure.exporters.pdf_exporter import PDFExporter
            return PDFExporter()
        return None
