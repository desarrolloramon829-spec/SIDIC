"""
Tests para el FieldMapper de infraestructura.
"""
from __future__ import annotations

import pytest

from sidic.infrastructure.readers.field_mapper import FieldMapper


class TestFieldMapper:
    """Tests de FieldMapper con mapeo personalizado."""

    @pytest.fixture
    def custom_mapping(self) -> dict:
        return {
            "hechos": {
                "fecha": ["FECHA", "FECHA_HECHO", "date"],
                "delito": ["DELITO", "TIPO_DELITO", "crime_type"],
                "direccion": ["DIRECCION", "DIR", "address"],
                "nro_sumario": ["N_SUMARIO", "NRO"],
            },
            "mencionados": {
                "alias": ["ALIAS", "APODO"],
                "delito": ["DELITO"],
            },
        }

    @pytest.fixture
    def mapper(self, custom_mapping) -> FieldMapper:
        return FieldMapper(mapping=custom_mapping)

    def test_detect_field_exacto(self, mapper):
        result = mapper.detect_field(
            "hechos", "fecha", ["FECHA", "DELITO", "OTROS"]
        )
        assert result == "FECHA"

    def test_detect_field_alias(self, mapper):
        result = mapper.detect_field(
            "hechos", "fecha", ["FECHA_HECHO", "DELITO"]
        )
        assert result == "FECHA_HECHO"

    def test_detect_field_case_insensitive(self, mapper):
        result = mapper.detect_field(
            "hechos", "fecha", ["fecha_hecho", "delito"]
        )
        assert result is not None  # debe encontrar case-insensitive

    def test_detect_field_no_match(self, mapper):
        result = mapper.detect_field(
            "hechos", "fecha", ["COSA", "OTRA"]
        )
        assert result is None

    def test_detect_field_entity_desconocida(self, mapper):
        result = mapper.detect_field(
            "desconocido", "fecha", ["FECHA"]
        )
        assert result is None

    def test_build_field_map(self, mapper):
        available = ["FECHA", "TIPO_DELITO", "OTROS_CAMPO"]
        field_map = mapper.build_field_map("hechos", available)
        assert field_map["fecha"] == "FECHA"
        assert field_map["delito"] == "TIPO_DELITO"
        assert field_map.get("direccion") is None  # no hay "DIRECCION" en available

    def test_detect_mapping(self, mapper):
        available = ["FECHA", "DELITO", "EXTRA"]
        detected = mapper.detect_mapping(available, "hechos")
        assert "fecha" in detected
        assert "delito" in detected
        # Solo campos encontrados
        for v in detected.values():
            assert v in available

    def test_map_row(self, mapper):
        raw = {"FECHA": "15/03/2024", "DELITO": "ROBO", "EXTRA": "X"}
        mapped = mapper.map_row(raw, "hechos")
        assert mapped.get("fecha") == "15/03/2024"
        assert mapped.get("delito") == "ROBO"

    def test_validate_mapping_valid(self, mapper):
        available = ["FECHA", "DELITO", "DIRECCION"]
        validation = mapper.validate_mapping("hechos", available)
        assert validation["valid"] is True
        assert len(validation["critical_missing"]) == 0

    def test_validate_mapping_missing_critical(self, mapper):
        available = ["DIRECCION"]
        validation = mapper.validate_mapping("hechos", available)
        assert validation["valid"] is False
        assert "fecha" in validation["critical_missing"]
        assert "delito" in validation["critical_missing"]

    def test_add_alias(self, mapper):
        mapper.add_alias("hechos", "fecha", "NUEVA_FECHA")
        result = mapper.detect_field("hechos", "fecha", ["NUEVA_FECHA"])
        assert result == "NUEVA_FECHA"

    def test_cache_funciona(self, mapper):
        # Primera llamada
        mapper.detect_field("hechos", "fecha", ["FECHA"])
        # Segunda llamada usa cache
        result = mapper.detect_field("hechos", "fecha", ["FECHA"])
        assert result == "FECHA"

    def test_build_field_map_entidad_desconocida(self, mapper):
        result = mapper.build_field_map("NADA", ["campo"])
        assert result == {}
