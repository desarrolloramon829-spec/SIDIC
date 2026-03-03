"""
Tests para DTOs y casos de uso de la capa de aplicación.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from sidic.application.dto.dtos import (
    ComparisonInputDTO,
    FieldMappingDTO,
    FileInfoDTO,
    FilterInputDTO,
    GenerateReportInputDTO,
    GenerateReportOutputDTO,
    LoadDataInputDTO,
    LoadDataOutputDTO,
    PeriodInputDTO,
    PeriodSummaryDTO,
    TableDataDTO,
    ValidationResultDTO,
)


# ═════════════════════════════════════════════════════════════════════════════
# DTOs — instanciación correcta
# ═════════════════════════════════════════════════════════════════════════════


class TestDTOs:
    def test_period_input_dto(self):
        dto = PeriodInputDTO(
            name="Marzo",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 31),
            hechos_paths=["a.shp", "b.shp"],
        )
        assert dto.name == "Marzo"
        assert len(dto.hechos_paths) == 2
        assert dto.mencionados_paths == []

    def test_load_data_input_dto(self):
        period = PeriodInputDTO("P1", date(2024, 1, 1), date(2024, 1, 31))
        dto = LoadDataInputDTO(
            periods=[period],
            jurisdiccion="AMAICHA DEL VALLE",
        )
        assert len(dto.periods) == 1
        assert dto.dependencia == ""

    def test_load_data_output_dto(self):
        dto = LoadDataOutputDTO(success=True)
        assert dto.success is True
        assert dto.errors == []

    def test_period_summary_dto(self):
        dto = PeriodSummaryDTO(
            name="P1",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 31),
            total_hechos=42,
        )
        assert dto.total_hechos == 42
        assert dto.total_mencionados == 0

    def test_filter_input_dto(self):
        dto = FilterInputDTO(categorias=["ROBOS", "HURTOS"])
        assert len(dto.categorias) == 2
        assert dto.delitos is None

    def test_generate_report_input_dto(self):
        dto = GenerateReportInputDTO(
            formato="excel",
            output_path="/tmp/report.xlsx",
            titulo="TEST",
        )
        assert dto.formato == "excel"
        assert dto.incluir_graficos is True

    def test_generate_report_output_dto(self):
        dto = GenerateReportOutputDTO(
            success=True,
            output_path="/tmp/report.xlsx",
            tables_generated=["tabla_general", "tabla_dias"],
        )
        assert len(dto.tables_generated) == 2

    def test_validation_result_dto(self):
        dto = ValidationResultDTO(
            valid=True,
            path="datos.shp",
            features=150,
            fields=["FECHA", "DELITO"],
        )
        assert dto.valid is True
        assert dto.features == 150

    def test_file_info_dto(self):
        dto = FileInfoDTO(
            path="/data/file.shp",
            name="file.shp",
            extension=".shp",
            size_bytes=1024,
        )
        assert dto.supported is True
        assert dto.size_bytes == 1024

    def test_comparison_input_dto(self):
        dto = ComparisonInputDTO(modo="vs_anterior")
        assert dto.modo == "vs_anterior"

    def test_comparison_input_dto_default(self):
        dto = ComparisonInputDTO()
        assert dto.modo == "vs_principal"

    def test_field_mapping_dto(self):
        dto = FieldMappingDTO(
            entity_type="hechos",
            available_fields=["FECHA", "DELITO"],
            detected_mapping={"fecha": "FECHA", "delito": "DELITO"},
            confidence=1.0,
        )
        assert dto.entity_type == "hechos"
        assert dto.confidence == 1.0
        assert dto.unmapped_required == []
