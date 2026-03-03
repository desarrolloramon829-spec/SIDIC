"""
Tests unitarios para modelos del dominio S.I.D.I.C.
"""
from __future__ import annotations

from datetime import date, time
from typing import List

import pytest

from sidic.domain.enums import (
    CategoriaDelito,
    ClasificacionAprehendido,
    DiaSemana,
    FranjaHoraria,
    ModoVariacion,
    TipoEsclarecimiento,
)
from sidic.domain.models.crime_record import CrimeRecord
from sidic.domain.models.mentioned_person import MentionedPerson
from sidic.domain.models.apprehended import Apprehended
from sidic.domain.models.report_data import PeriodData, ReportData, MAX_PERIODOS
from sidic.domain.models.simbolo_delito import SimboloDelito


# ═════════════════════════════════════════════════════════════════════════════
# CrimeRecord
# ═════════════════════════════════════════════════════════════════════════════


class TestCrimeRecord:
    def test_defaults(self):
        r = CrimeRecord()
        assert r.delito == ""
        assert r.fecha is None
        assert r.hora is None
        assert r.id  # auto-generated

    def test_dia_semana(self, robo_agravado):
        # 15/03/2024 → Viernes
        assert robo_agravado.dia_semana == DiaSemana.VIERNES

    def test_dia_semana_nombre_sin_fecha(self, record_sin_fecha):
        assert record_sin_fecha.dia_semana_nombre == "#NO_CONSTA"

    def test_franja_horaria(self, robo_agravado):
        # 22:30 → NOCHE
        assert robo_agravado.franja_horaria == FranjaHoraria.NOCHE

    def test_franja_horaria_nombre_sin_hora(self, record_sin_fecha):
        assert record_sin_fecha.franja_horaria_nombre == "#NO_CONSTA"

    def test_fecha_hora(self, robo_agravado):
        dt = robo_agravado.fecha_hora
        assert dt is not None
        assert dt.year == 2024
        assert dt.hour == 22

    def test_fecha_hora_none(self, record_sin_fecha):
        assert record_sin_fecha.fecha_hora is None

    def test_delito_con_modalidad(self, robo_agravado):
        # "010-ROBO_AGRAVADO" + "ASALTANTE" → debe contener ambos
        dcm = robo_agravado.delito_con_modalidad
        assert "ROBO" in dcm
        assert "AGRAVADO" in dcm
        assert "ASALTANTE" in dcm

    def test_delito_con_modalidad_sin_modus(self):
        r = CrimeRecord(delito="HURTO PUNGA")
        assert r.delito_con_modalidad == "HURTO PUNGA"

    def test_delito_con_modalidad_vacio(self):
        r = CrimeRecord()
        assert r.delito_con_modalidad == ""

    def test_categoria_setter(self):
        r = CrimeRecord(delito="X")
        r.categoria = CategoriaDelito.ESTAFA
        assert r.categoria == CategoriaDelito.ESTAFA

    def test_categoria_fallback_robo(self):
        r = CrimeRecord(delito="ROBO ALGO")
        assert r.categoria == CategoriaDelito.ROBO

    def test_categoria_fallback_hurto(self):
        r = CrimeRecord(delito="HURTO PUNGA")
        assert r.categoria == CategoriaDelito.HURTO

    def test_categoria_fallback_estafa(self):
        r = CrimeRecord(delito="ESTAFA CUENTO")
        assert r.categoria == CategoriaDelito.ESTAFA

    def test_categoria_fallback_tentativa(self):
        r = CrimeRecord(delito="TENTATIVA DE ROBO")
        assert r.categoria == CategoriaDelito.TENTATIVA_ROBO

    def test_categoria_fallback_otros(self):
        r = CrimeRecord(delito="DAÑO")
        assert r.categoria == CategoriaDelito.OTROS

    def test_es_robo_agravado(self, robo_agravado):
        assert robo_agravado.es_robo_agravado is True

    def test_tipo_esclarecimiento(self, robo_agravado):
        assert robo_agravado.tipo_esclarecimiento == TipoEsclarecimiento.SI

    def test_es_esclarecido(self, robo_agravado, hurto_oportunista):
        assert robo_agravado.es_esclarecido is True
        assert hurto_oportunista.es_esclarecido is False

    def test_matches_period(self, robo_agravado):
        assert robo_agravado.matches_period(date(2024, 3, 1), date(2024, 3, 31))
        assert not robo_agravado.matches_period(date(2024, 4, 1), date(2024, 4, 30))

    def test_matches_period_sin_fecha(self, record_sin_fecha):
        assert not record_sin_fecha.matches_period(date(2024, 1, 1), date(2024, 12, 31))

    def test_to_dict(self, robo_agravado):
        d = robo_agravado.to_dict()
        assert d["id"] == "r001"
        assert d["nro_sumario"] == "SUM-001"
        assert d["fecha"] == "2024-03-15"
        assert d["hora"] == "22:30"
        assert d["esclarecido"] == "SI"
        assert d["es_robo_agravado"] is True

    def test_str(self, robo_agravado):
        s = str(robo_agravado)
        assert "r001" in s
        assert "15/03/2024" in s

    def test_campos_extra(self):
        r = CrimeRecord(campos_extra={"extra_field": "value"})
        assert r.campos_extra["extra_field"] == "value"


# ═════════════════════════════════════════════════════════════════════════════
# MentionedPerson
# ═════════════════════════════════════════════════════════════════════════════


class TestMentionedPerson:
    def test_alias_formateado(self, mencionado):
        assert mencionado.alias_formateado == 'UN TAL "PELUCA"'

    def test_alias_formateado_vacio(self):
        m = MentionedPerson()
        assert m.alias_formateado == "SIN IDENTIFICAR"

    def test_nombre_display_con_nombre(self, mencionado):
        assert mencionado.nombre_display == "ROBERTO GÓMEZ"

    def test_nombre_display_sin_nombre(self):
        m = MentionedPerson(alias="Topo")
        assert 'UN TAL "TOPO"' in m.nombre_display

    def test_fecha_hora_str(self, mencionado):
        assert "15/03/2024" in mencionado.fecha_hora_str
        assert "22:30" in mencionado.fecha_hora_str

    def test_fecha_hora_str_vacio(self):
        m = MentionedPerson()
        assert m.fecha_hora_str == "Sin fecha/hora"

    def test_matches_period(self, mencionado):
        assert mencionado.matches_period(date(2024, 3, 1), date(2024, 3, 31))
        assert not mencionado.matches_period(date(2024, 4, 1), date(2024, 4, 30))

    def test_matches_period_sin_fecha(self):
        m = MentionedPerson()
        assert not m.matches_period(date(2024, 1, 1), date(2024, 12, 31))

    def test_to_dict(self, mencionado):
        d = mencionado.to_dict()
        assert d["alias"] == "Peluca"
        assert d["nro_sumario"] == "SUM-001"

    def test_to_report_row(self, mencionado):
        row = mencionado.to_report_row()
        assert "Alias" in row
        assert "Delito" in row


# ═════════════════════════════════════════════════════════════════════════════
# Apprehended
# ═════════════════════════════════════════════════════════════════════════════


class TestApprehended:
    def test_clasificacion_desde_raw(self, aprehendido):
        assert aprehendido.clasificacion == ClasificacionAprehendido.MAYOR_PRIMERIZO

    def test_clasificacion_menor_con_antecedentes(self, aprehendido_menor):
        assert aprehendido_menor.clasificacion == ClasificacionAprehendido.MENOR_CON_ANTECEDENTES

    def test_clasificacion_inferida_sin_raw(self):
        a = Apprehended(edad=16)
        assert a.clasificacion == ClasificacionAprehendido.MENOR_PRIMERIZO

    def test_es_menor(self, aprehendido, aprehendido_menor):
        assert aprehendido.es_menor is False
        assert aprehendido_menor.es_menor is True

    def test_tiene_antecedentes(self, aprehendido, aprehendido_menor):
        assert aprehendido.tiene_antecedentes is False
        assert aprehendido_menor.tiene_antecedentes is True

    def test_sexo_normalizado(self, aprehendido):
        assert aprehendido.sexo_normalizado == "M"

    def test_sexo_normalizado_femenino(self):
        a = Apprehended(sexo="FEMENINO")
        assert a.sexo_normalizado == "F"

    def test_sexo_normalizado_vacio(self):
        a = Apprehended()
        assert a.sexo_normalizado == "-"

    def test_matches_period(self, aprehendido):
        assert aprehendido.matches_period(date(2024, 3, 1), date(2024, 3, 31))

    def test_to_dict(self, aprehendido):
        d = aprehendido.to_dict()
        assert d["nombre"] == "Carlos López"
        assert d["edad"] == 25
        assert d["clasificacion"] == "MAYOR PRIMERIZO"

    def test_to_report_row(self, aprehendido):
        row = aprehendido.to_report_row()
        assert "Nombre/Alias" in row
        assert "Clasificación" in row


# ═════════════════════════════════════════════════════════════════════════════
# SimboloDelito
# ═════════════════════════════════════════════════════════════════════════════


class TestSimboloDelito:
    def test_frozen(self):
        s = SimboloDelito(simbolo="▲", color="#FF0000", descripcion="Test")
        with pytest.raises(AttributeError):
            s.simbolo = "X"  # frozen

    def test_hex_color_with_hash(self):
        s = SimboloDelito(simbolo="▲", color="#FF0000", descripcion="Test")
        assert s.hex_color == "#FF0000"

    def test_hex_color_without_hash(self):
        s = SimboloDelito(simbolo="▲", color="FF0000", descripcion="Test")
        assert s.hex_color == "#FF0000"


# ═════════════════════════════════════════════════════════════════════════════
# PeriodData
# ═════════════════════════════════════════════════════════════════════════════


class TestPeriodData:
    def test_propiedades_basicas(self, period_data):
        assert period_data.total_hechos == 3
        assert period_data.total_mencionados == 1
        assert period_data.total_aprehendidos == 1

    def test_rango_fechas(self, period_data):
        assert "01/03/2024" in period_data.rango_fechas
        assert "31/03/2024" in period_data.rango_fechas

    def test_label_corto(self, period_data):
        label = period_data.label_corto
        assert "01/03" in label

    def test_conteo_por_categoria(self, period_data):
        conteo = period_data.conteo_por_categoria()
        assert conteo.get("ROBOS", 0) == 1
        assert conteo.get("HURTOS", 0) == 1
        assert conteo.get("ESTAFAS", 0) == 1

    def test_conteo_por_dia_semana(self, period_data):
        conteo = period_data.conteo_por_dia_semana()
        # Debe tener todos los 7 días
        assert len(conteo) == 7
        assert conteo["VIERNES"] >= 1  # robo el viernes

    def test_conteo_por_franja_horaria(self, period_data):
        conteo = period_data.conteo_por_franja_horaria()
        # Debe tener las 6 franjas
        assert len(conteo) == 6

    def test_conteo_esclarecimiento(self, period_data):
        conteo = period_data.conteo_esclarecimiento()
        assert "SI" in conteo
        assert conteo["SI"] >= 1

    def test_conteo_por_movilidad(self, period_data):
        conteo = period_data.conteo_por_movilidad()
        assert "A PIE" in conteo

    def test_conteo_por_arma_solo_agravados(self, period_data):
        conteo = period_data.conteo_por_arma()
        # Solo robo agravado tiene arma
        assert "ARMA DE FUEGO" in conteo

    def test_conteo_por_ambito(self, period_data):
        conteo = period_data.conteo_por_ambito()
        assert "VIA PUBLICA" in conteo
        assert "DOMICILIO" in conteo

    def test_matriz_delito_dia(self, period_data):
        matriz = period_data.matriz_delito_dia()
        assert isinstance(matriz, dict)
        # Debe tener claves por delito_con_modalidad
        for delito, dias in matriz.items():
            assert len(dias) == 7  # 7 días

    def test_cuadro_referencia(self, period_data):
        cuadro = period_data.cuadro_referencia()
        assert len(cuadro) > 0
        tipos = {f["tipo"] for f in cuadro}
        assert "total" in tipos

    def test_conteo_aprehendidos_clasificacion(self, period_data):
        conteo = period_data.conteo_aprehendidos_clasificacion()
        assert conteo["MAYOR PRIMERIZO"] == 1


# ═════════════════════════════════════════════════════════════════════════════
# ReportData
# ═════════════════════════════════════════════════════════════════════════════


class TestReportData:
    def test_es_comparativo_simple(self, report_data):
        assert report_data.es_comparativo is False

    def test_es_comparativo_multi(self, report_data_comparativo):
        assert report_data_comparativo.es_comparativo is True

    def test_periodo_principal(self, report_data):
        assert report_data.periodo_principal is not None
        assert report_data.periodo_principal.nombre == "Marzo 2024"

    def test_periodos_comparacion(self, report_data_comparativo):
        assert len(report_data_comparativo.periodos_comparacion) == 1

    def test_agregar_periodo_max(self):
        rd = ReportData()
        for i in range(MAX_PERIODOS):
            rd.agregar_periodo(PeriodData(nombre=f"P{i}"))
        with pytest.raises(ValueError, match="Máximo"):
            rd.agregar_periodo(PeriodData(nombre="Extra"))

    def test_comparar_conteos(self):
        a = {"ROBOS": 10, "HURTOS": 5}
        b = {"ROBOS": 8, "HURTOS": 7, "ESTAFAS": 2}
        result = ReportData.comparar_conteos(a, b)

        assert result["ROBOS"]["periodo_a"] == 10
        assert result["ROBOS"]["periodo_b"] == 8
        assert result["ROBOS"]["diferencia"] == -2
        assert result["ROBOS"]["tendencia"] == "bajo"

        assert result["HURTOS"]["diferencia"] == 2
        assert result["HURTOS"]["tendencia"] == "subio"

        assert result["ESTAFAS"]["periodo_a"] == 0
        assert result["ESTAFAS"]["periodo_b"] == 2
        assert result["ESTAFAS"]["tendencia"] == "subio"

    def test_comparar_conteos_iguales(self):
        a = {"X": 5}
        b = {"X": 5}
        result = ReportData.comparar_conteos(a, b)
        assert result["X"]["tendencia"] == "igual"
        assert result["X"]["diferencia"] == 0
