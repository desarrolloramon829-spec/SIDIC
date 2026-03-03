"""
Tests unitarios para enums del dominio S.I.D.I.C.
"""
from __future__ import annotations

import pytest

from sidic.domain.enums import (
    CategoriaDelito,
    ClasificacionAprehendido,
    DiaSemana,
    FormatoExportacion,
    FormatoGIS,
    FranjaHoraria,
    ModoVariacion,
    TipoEsclarecimiento,
)


# ═════════════════════════════════════════════════════════════════════════════
# CategoriaDelito
# ═════════════════════════════════════════════════════════════════════════════


class TestCategoriaDelito:
    def test_values(self):
        assert CategoriaDelito.ROBO.value == "ROBOS"
        assert CategoriaDelito.HURTO.value == "HURTOS"
        assert CategoriaDelito.ESTAFA.value == "ESTAFAS"
        assert CategoriaDelito.OTROS.value == "OTROS DELITOS"

    def test_es_tentativa(self):
        assert CategoriaDelito.TENTATIVA_ROBO.es_tentativa is True
        assert CategoriaDelito.TENTATIVA_HURTO.es_tentativa is True
        assert CategoriaDelito.ROBO.es_tentativa is False
        assert CategoriaDelito.ESTAFA.es_tentativa is False

    def test_categoria_base(self):
        assert CategoriaDelito.TENTATIVA_ROBO.categoria_base == CategoriaDelito.ROBO
        assert CategoriaDelito.TENTATIVA_HURTO.categoria_base == CategoriaDelito.HURTO
        assert CategoriaDelito.ROBO.categoria_base == CategoriaDelito.ROBO
        assert CategoriaDelito.OTROS.categoria_base == CategoriaDelito.OTROS

    def test_orden(self):
        assert CategoriaDelito.ROBO.orden < CategoriaDelito.HURTO.orden
        assert CategoriaDelito.HURTO.orden < CategoriaDelito.ESTAFA.orden
        assert CategoriaDelito.ESTAFA.orden < CategoriaDelito.OTROS.orden

    def test_grupo_filtrado(self):
        assert CategoriaDelito.ROBO.grupo_filtrado == CategoriaDelito.TENTATIVA_ROBO.grupo_filtrado
        assert CategoriaDelito.HURTO.grupo_filtrado == CategoriaDelito.TENTATIVA_HURTO.grupo_filtrado


# ═════════════════════════════════════════════════════════════════════════════
# FranjaHoraria
# ═════════════════════════════════════════════════════════════════════════════


class TestFranjaHoraria:
    def test_from_hour_madrugada(self):
        for h in (0, 1, 2, 3, 4):
            assert FranjaHoraria.from_hour(h) == FranjaHoraria.MADRUGADA

    def test_from_hour_manana(self):
        for h in (5, 6, 7, 8):
            assert FranjaHoraria.from_hour(h) == FranjaHoraria.MANANA

    def test_from_hour_vespertina(self):
        for h in (9, 10, 11, 12):
            assert FranjaHoraria.from_hour(h) == FranjaHoraria.VESPERTINA

    def test_from_hour_siesta(self):
        for h in (13, 14, 15, 16):
            assert FranjaHoraria.from_hour(h) == FranjaHoraria.SIESTA

    def test_from_hour_tarde(self):
        for h in (17, 18, 19):
            assert FranjaHoraria.from_hour(h) == FranjaHoraria.TARDE

    def test_from_hour_noche(self):
        for h in (20, 21, 22, 23):
            assert FranjaHoraria.from_hour(h) == FranjaHoraria.NOCHE

    def test_from_hour_invalid(self):
        with pytest.raises(ValueError):
            FranjaHoraria.from_hour(24)
        with pytest.raises(ValueError):
            FranjaHoraria.from_hour(-1)

    def test_display_name(self):
        assert "MADRUGADA" in FranjaHoraria.MADRUGADA.display_name
        assert "00:00" in FranjaHoraria.MADRUGADA.display_name

    def test_orden_cronologico(self):
        franjas = list(FranjaHoraria)
        sorted_franjas = sorted(franjas, key=lambda f: f.orden)
        assert sorted_franjas[0] == FranjaHoraria.MADRUGADA
        assert sorted_franjas[-1] == FranjaHoraria.NOCHE


# ═════════════════════════════════════════════════════════════════════════════
# DiaSemana
# ═════════════════════════════════════════════════════════════════════════════


class TestDiaSemana:
    def test_from_weekday(self):
        assert DiaSemana.from_weekday(0) == DiaSemana.LUNES
        assert DiaSemana.from_weekday(6) == DiaSemana.DOMINGO

    def test_from_weekday_invalid(self):
        with pytest.raises(ValueError):
            DiaSemana.from_weekday(7)

    def test_from_name(self):
        assert DiaSemana.from_name("LUNES") == DiaSemana.LUNES
        assert DiaSemana.from_name("lunes") == DiaSemana.LUNES
        assert DiaSemana.from_name("MIÉRCOLES") == DiaSemana.MIERCOLES
        assert DiaSemana.from_name("MIERCOLES") == DiaSemana.MIERCOLES  # sin acento
        assert DiaSemana.from_name("SÁBADO") == DiaSemana.SABADO
        assert DiaSemana.from_name("SABADO") == DiaSemana.SABADO  # sin acento

    def test_from_name_invalid(self):
        with pytest.raises(ValueError):
            DiaSemana.from_name("NODIA")

    def test_todos_ordenados(self):
        todos = DiaSemana.todos_ordenados()
        assert len(todos) == 7
        assert todos[0] == DiaSemana.LUNES
        assert todos[-1] == DiaSemana.DOMINGO

    def test_orden(self):
        assert DiaSemana.LUNES.orden == 0
        assert DiaSemana.DOMINGO.orden == 6


# ═════════════════════════════════════════════════════════════════════════════
# TipoEsclarecimiento
# ═════════════════════════════════════════════════════════════════════════════


class TestTipoEsclarecimiento:
    def test_from_text_si(self):
        for text in ("SI", "SÍ", "S", "TRUE", "1", "RESUELTO", " si "):
            assert TipoEsclarecimiento.from_text(text) == TipoEsclarecimiento.SI

    def test_from_text_no(self):
        for text in ("NO", "N", "FALSE", "", "cualquier cosa"):
            assert TipoEsclarecimiento.from_text(text) == TipoEsclarecimiento.NO

    def test_from_text_parcial(self):
        for text in ("PARCIAL", "PARCIALMENTE"):
            assert TipoEsclarecimiento.from_text(text) == TipoEsclarecimiento.PARCIAL

    def test_from_text_empty(self):
        assert TipoEsclarecimiento.from_text("") == TipoEsclarecimiento.NO
        assert TipoEsclarecimiento.from_text(None) == TipoEsclarecimiento.NO


# ═════════════════════════════════════════════════════════════════════════════
# ClasificacionAprehendido
# ═════════════════════════════════════════════════════════════════════════════


class TestClasificacionAprehendido:
    def test_es_menor(self):
        assert ClasificacionAprehendido.MENOR_PRIMERIZO.es_menor is True
        assert ClasificacionAprehendido.MENOR_CON_ANTECEDENTES.es_menor is True
        assert ClasificacionAprehendido.MAYOR_PRIMERIZO.es_menor is False

    def test_tiene_antecedentes(self):
        assert ClasificacionAprehendido.MAYOR_CON_ANTECEDENTES.tiene_antecedentes is True
        assert ClasificacionAprehendido.MENOR_CON_ANTECEDENTES.tiene_antecedentes is True
        assert ClasificacionAprehendido.MAYOR_PRIMERIZO.tiene_antecedentes is False

    def test_inferir_mayor_primerizo(self):
        assert ClasificacionAprehendido.inferir(25) == ClasificacionAprehendido.MAYOR_PRIMERIZO

    def test_inferir_mayor_con_antecedentes(self):
        assert (
            ClasificacionAprehendido.inferir(30, antecedentes=True)
            == ClasificacionAprehendido.MAYOR_CON_ANTECEDENTES
        )

    def test_inferir_menor_primerizo(self):
        assert ClasificacionAprehendido.inferir(16) == ClasificacionAprehendido.MENOR_PRIMERIZO

    def test_inferir_menor_con_antecedentes(self):
        assert (
            ClasificacionAprehendido.inferir(15, antecedentes=True)
            == ClasificacionAprehendido.MENOR_CON_ANTECEDENTES
        )

    def test_inferir_sin_edad(self):
        # Sin edad → asume mayor
        assert ClasificacionAprehendido.inferir(None) == ClasificacionAprehendido.MAYOR_PRIMERIZO


# ═════════════════════════════════════════════════════════════════════════════
# FormatoExportacion
# ═════════════════════════════════════════════════════════════════════════════


class TestFormatoExportacion:
    def test_extension(self):
        assert FormatoExportacion.EXCEL.extension == ".xlsx"
        assert FormatoExportacion.WORD.extension == ".docx"
        assert FormatoExportacion.PDF.extension == ".pdf"


# ═════════════════════════════════════════════════════════════════════════════
# FormatoGIS
# ═════════════════════════════════════════════════════════════════════════════


class TestFormatoGIS:
    def test_from_extension(self):
        assert FormatoGIS.from_extension(".shp") == FormatoGIS.SHAPEFILE
        assert FormatoGIS.from_extension("dbf") == FormatoGIS.SHAPEFILE
        assert FormatoGIS.from_extension(".geojson") == FormatoGIS.GEOJSON
        assert FormatoGIS.from_extension(".kml") == FormatoGIS.KML
        assert FormatoGIS.from_extension("gpkg") == FormatoGIS.GEOPACKAGE
        assert FormatoGIS.from_extension(".csv") == FormatoGIS.CSV

    def test_from_extension_invalid(self):
        with pytest.raises(ValueError, match="Extensión no soportada"):
            FormatoGIS.from_extension(".pdf")


# ═════════════════════════════════════════════════════════════════════════════
# ModoVariacion
# ═════════════════════════════════════════════════════════════════════════════


class TestModoVariacion:
    def test_values(self):
        assert ModoVariacion.VS_PRINCIPAL.value == "vs_principal"
        assert ModoVariacion.VS_ANTERIOR.value == "vs_anterior"
        assert ModoVariacion.AMBAS.value == "ambas"
