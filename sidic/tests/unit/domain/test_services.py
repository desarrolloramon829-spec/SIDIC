"""
Tests unitarios para servicios del dominio S.I.D.I.C.
"""
from __future__ import annotations

from datetime import date, time
from typing import List

import pytest

from sidic.domain.enums import CategoriaDelito, ModoVariacion
from sidic.domain.models.crime_record import CrimeRecord
from sidic.domain.models.mentioned_person import MentionedPerson
from sidic.domain.models.apprehended import Apprehended
from sidic.domain.models.report_data import PeriodData
from sidic.domain.services.delito_categorizer import DelitoCategorizer
from sidic.domain.services.filters import PeriodFilter, CategoryFilter
from sidic.domain.services.statistics import StatisticsCalculator
from sidic.domain.services.period_comparator import PeriodComparator, ComparacionItem


# ═════════════════════════════════════════════════════════════════════════════
# DelitoCategorizer
# ═════════════════════════════════════════════════════════════════════════════


class TestDelitoCategorizer:
    def test_categorizar_robo_exacto(self, categorizer):
        assert categorizer.categorizar("ROBO AGRAVADO ASALTANTE") == CategoriaDelito.ROBO

    def test_categorizar_hurto_exacto(self, categorizer):
        assert categorizer.categorizar("HURTO OPORTUNISTA") == CategoriaDelito.HURTO

    def test_categorizar_estafa_exacto(self, categorizer):
        assert categorizer.categorizar("ESTAFA CUENTO DEL TIO") == CategoriaDelito.ESTAFA

    def test_categorizar_tentativa_robo(self, categorizer):
        result = categorizer.categorizar("TENTATIVA DE ROBO AGRAVADO ASALTANTE")
        assert result == CategoriaDelito.TENTATIVA_ROBO

    def test_categorizar_tentativa_hurto(self, categorizer):
        result = categorizer.categorizar("TENTATIVA DE HURTO PUNGA")
        assert result == CategoriaDelito.TENTATIVA_HURTO

    def test_categorizar_fallback_robo(self, categorizer):
        # Término desconocido pero contiene "ROBO"
        assert categorizer.categorizar("ROBO NUEVO TIPO") == CategoriaDelito.ROBO

    def test_categorizar_fallback_hurto(self, categorizer):
        assert categorizer.categorizar("HURTO NUEVO TIPO") == CategoriaDelito.HURTO

    def test_categorizar_fallback_tentativa(self, categorizer):
        assert categorizer.categorizar("TENTATIVA DE ROBO NUEVO") == CategoriaDelito.TENTATIVA_ROBO

    def test_categorizar_fallback_otros(self, categorizer):
        assert categorizer.categorizar("DAÑO A PROPIEDAD") == CategoriaDelito.OTROS

    def test_categorizar_vacio(self, categorizer):
        assert categorizer.categorizar("") == CategoriaDelito.OTROS

    def test_categorizar_case_insensitive(self, categorizer):
        assert categorizer.categorizar("robo agravado asaltante") == CategoriaDelito.ROBO

    def test_es_robo_agravado(self, categorizer):
        assert categorizer.es_robo_agravado("ROBO AGRAVADO ASALTANTE") is True
        assert categorizer.es_robo_agravado("ROBO ARREBATO") is False
        assert categorizer.es_robo_agravado("HURTO PUNGA") is False

    def test_categorizar_registros(self, categorizer, sample_records):
        # Resetear categorías para que el categorizer las asigne
        for r in sample_records:
            r._categoria = None
            r._es_robo_agravado = None
        categorizer.categorizar_registros(sample_records)
        # Verificar que todos tienen categoría asignada
        for r in sample_records:
            assert r._categoria is not None

    def test_config_personalizada(self):
        config = {
            "categorias": {
                "ROBOS": ["ATRACO", "ASALTO"],
                "HURTOS": ["MECHERA"],
            },
            "robo_agravado": ["ATRACO"],
            "simbolos": {
                "ATRACO": {
                    "simbolo": "▲",
                    "color": "#FF0000",
                    "descripcion": "Atraco",
                },
            },
        }
        cat = DelitoCategorizer(config=config)
        assert cat.categorizar("ATRACO") == CategoriaDelito.ROBO
        assert cat.categorizar("MECHERA") == CategoriaDelito.HURTO
        assert cat.es_robo_agravado("ATRACO") is True

    def test_get_simbolo(self, categorizer):
        # Los defaults no deberían tener símbolos
        # Pero con config sí
        config = {
            "categorias": {},
            "simbolos": {
                "ROBO ARREBATO": {
                    "simbolo": "★",
                    "color": "#00FF00",
                    "descripcion": "Arrebato",
                },
            },
        }
        cat = DelitoCategorizer(config=config)
        simbolo = cat.get_simbolo("ROBO ARREBATO")
        assert simbolo is not None
        assert simbolo.simbolo == "★"
        assert simbolo.color == "#00FF00"

    def test_get_simbolo_no_encontrado(self, categorizer):
        assert categorizer.get_simbolo("INEXISTENTE") is None


# ═════════════════════════════════════════════════════════════════════════════
# PeriodFilter
# ═════════════════════════════════════════════════════════════════════════════


class TestPeriodFilter:
    def test_filter_hechos(self, sample_records):
        marzo = PeriodFilter.filter_hechos(
            sample_records,
            date(2024, 3, 1),
            date(2024, 3, 31),
        )
        assert len(marzo) == 3

    def test_filter_hechos_parcial(self, sample_records):
        primera_quincena = PeriodFilter.filter_hechos(
            sample_records,
            date(2024, 3, 1),
            date(2024, 3, 16),
        )
        assert len(primera_quincena) == 1  # solo el robo del 15

    def test_filter_hechos_fuera_de_rango(self, sample_records):
        abril = PeriodFilter.filter_hechos(
            sample_records,
            date(2024, 4, 1),
            date(2024, 4, 30),
        )
        assert len(abril) == 0

    def test_filter_mencionados(self, mencionado):
        result = PeriodFilter.filter_mencionados(
            [mencionado],
            date(2024, 3, 1),
            date(2024, 3, 31),
        )
        assert len(result) == 1

    def test_filter_aprehendidos(self, aprehendido):
        result = PeriodFilter.filter_aprehendidos(
            [aprehendido],
            date(2024, 3, 1),
            date(2024, 3, 31),
        )
        assert len(result) == 1


# ═════════════════════════════════════════════════════════════════════════════
# CategoryFilter
# ═════════════════════════════════════════════════════════════════════════════


class TestCategoryFilter:
    def test_filter_hechos_robos(self, sample_records):
        result = CategoryFilter.filter_hechos(
            sample_records,
            {CategoriaDelito.ROBO},
        )
        assert len(result) == 1
        assert result[0].categoria == CategoriaDelito.ROBO

    def test_filter_hechos_multiple(self, sample_records):
        result = CategoryFilter.filter_hechos(
            sample_records,
            {CategoriaDelito.ROBO, CategoriaDelito.HURTO},
        )
        assert len(result) == 2

    def test_filter_hechos_none_retorna_todos(self, sample_records):
        result = CategoryFilter.filter_hechos(sample_records, None)
        assert len(result) == 3

    def test_filter_hechos_vacio_retorna_todos(self, sample_records):
        result = CategoryFilter.filter_hechos(sample_records, set())
        assert len(result) == 3

    def test_filter_mencionados_by_sumario(self, mencionado):
        result = CategoryFilter.filter_mencionados_by_sumario(
            [mencionado],
            {"SUM-001"},
        )
        assert len(result) == 1

    def test_filter_mencionados_no_match(self, mencionado):
        result = CategoryFilter.filter_mencionados_by_sumario(
            [mencionado],
            {"SUM-999"},
        )
        assert len(result) == 0


# ═════════════════════════════════════════════════════════════════════════════
# StatisticsCalculator
# ═════════════════════════════════════════════════════════════════════════════


class TestStatisticsCalculator:
    def test_porcentaje(self):
        assert StatisticsCalculator.porcentaje(25, 100) == 25.0
        assert StatisticsCalculator.porcentaje(1, 3) == 33.33
        assert StatisticsCalculator.porcentaje(0, 0) == 0.0

    def test_format_porcentaje(self):
        assert StatisticsCalculator.format_porcentaje(33.33) == "33.33%"

    def test_variacion_subio(self):
        v = StatisticsCalculator.variacion(10, 15)
        assert v["diferencia"] == 5
        assert v["porcentaje"] == 50.0
        assert v["tendencia"] == "subio"

    def test_variacion_bajo(self):
        v = StatisticsCalculator.variacion(10, 8)
        assert v["diferencia"] == -2
        assert v["porcentaje"] == -20.0
        assert v["tendencia"] == "bajo"

    def test_variacion_igual(self):
        v = StatisticsCalculator.variacion(10, 10)
        assert v["diferencia"] == 0
        assert v["tendencia"] == "igual"

    def test_variacion_desde_cero(self):
        v = StatisticsCalculator.variacion(0, 5)
        assert v["porcentaje"] == 100.0

    def test_variacion_ambos_cero(self):
        v = StatisticsCalculator.variacion(0, 0)
        assert v["porcentaje"] == 0.0
        assert v["tendencia"] == "igual"

    def test_icono_tendencia(self):
        assert StatisticsCalculator.icono_tendencia("subio") == "▲"
        assert StatisticsCalculator.icono_tendencia("bajo") == "▼"
        assert StatisticsCalculator.icono_tendencia("igual") == "─"

    def test_comparar_conteos(self):
        base = {"ROBOS": 10, "HURTOS": 5}
        comp = {"ROBOS": 8, "HURTOS": 7}
        result = StatisticsCalculator.comparar_conteos(base, comp)

        assert result["ROBOS"]["base"] == 10
        assert result["ROBOS"]["comparar"] == 8
        assert result["ROBOS"]["tendencia"] == "bajo"
        assert result["HURTOS"]["tendencia"] == "subio"

    def test_comparar_conteos_multiple(self):
        conteos = [
            {"ROBOS": 10, "HURTOS": 5},
            {"ROBOS": 8, "HURTOS": 7},
            {"ROBOS": 12, "HURTOS": 3},
        ]
        labels = ["P1", "P2", "P3"]
        result = StatisticsCalculator.comparar_conteos_multiple(conteos, labels)
        assert result["ROBOS"]["P1"] == 10
        assert result["ROBOS"]["P2"] == 8
        assert "var_P2" in result["ROBOS"]

    def test_agregar_totales(self):
        conteo = {"ROBOS": 10, "HURTOS": 5}
        original, total = StatisticsCalculator.agregar_totales(conteo)
        assert total == 15
        assert original is conteo


# ═════════════════════════════════════════════════════════════════════════════
# PeriodComparator
# ═════════════════════════════════════════════════════════════════════════════


class TestPeriodComparator:
    def test_min_periodos(self, period_data):
        with pytest.raises(ValueError, match="al menos 2"):
            PeriodComparator([period_data])

    def test_labels(self, period_data, period_data_comparacion):
        comp = PeriodComparator([period_data, period_data_comparacion])
        labels = comp.labels
        assert len(labels) == 2

    def test_comparar_vs_principal(self, period_data, period_data_comparacion):
        comp = PeriodComparator(
            [period_data, period_data_comparacion],
            modo=ModoVariacion.VS_PRINCIPAL,
        )
        resultados = comp.comparar(
            lambda p: p.conteo_por_categoria(),
            "categorías",
        )
        assert isinstance(resultados, list)
        assert all(isinstance(r, ComparacionItem) for r in resultados)
        for item in resultados:
            assert len(item.valores) == 2
            assert len(item.variaciones) == 2
            assert item.variaciones[0] == 0.0  # base siempre 0

    def test_comparar_vs_anterior(self, period_data, period_data_comparacion):
        comp = PeriodComparator(
            [period_data, period_data_comparacion],
            modo=ModoVariacion.VS_ANTERIOR,
        )
        resultados = comp.comparar(lambda p: p.conteo_por_categoria())
        assert len(resultados) > 0
