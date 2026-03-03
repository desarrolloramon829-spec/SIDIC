"""
Fixtures compartidas para los tests de S.I.D.I.C v2.0.
"""
from __future__ import annotations

from datetime import date, time
from typing import List

import pytest

from sidic.domain.enums import (
    CategoriaDelito,
    ClasificacionAprehendido,
    FranjaHoraria,
    DiaSemana,
    FormatoExportacion,
    ModoVariacion,
    TipoEsclarecimiento,
)
from sidic.domain.models.crime_record import CrimeRecord
from sidic.domain.models.mentioned_person import MentionedPerson
from sidic.domain.models.apprehended import Apprehended
from sidic.domain.models.report_data import PeriodData, ReportData
from sidic.domain.services.delito_categorizer import DelitoCategorizer


# ═════════════════════════════════════════════════════════════════════════════
# CRIME RECORDS
# ═════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def robo_agravado() -> CrimeRecord:
    """Un robo agravado con todos los campos completos."""
    r = CrimeRecord(
        id="r001",
        nro_sumario="SUM-001",
        fecha=date(2024, 3, 15),  # Viernes
        hora=time(22, 30),
        delito="010-ROBO_AGRAVADO",
        modus_operandi="ASALTANTE",
        ambito="VIA PUBLICA",
        movilidad="A PIE",
        arma_medio="ARMA DE FUEGO",
        esclarecido="SI",
        direccion="Av. San Martín 450",
        jurisdiccion="AMAICHA DEL VALLE",
        dependencia="COMISARÍA AMAICHA",
        coordenadas=(-65.92, -26.59),
        nombre_victima="Juan Pérez",
        sexo_victima="M",
    )
    r.categoria = CategoriaDelito.ROBO
    r._es_robo_agravado = True
    return r


@pytest.fixture
def hurto_oportunista() -> CrimeRecord:
    """Un hurto oportunista."""
    r = CrimeRecord(
        id="h001",
        nro_sumario="SUM-002",
        fecha=date(2024, 3, 18),  # Lunes
        hora=time(14, 0),
        delito="050-HURTO",
        modus_operandi="OPORTUNISTA",
        ambito="DOMICILIO",
        movilidad="A PIE",
        esclarecido="NO",
        direccion="Calle Rivadavia 120",
        jurisdiccion="AMAICHA DEL VALLE",
        dependencia="COMISARÍA AMAICHA",
    )
    r.categoria = CategoriaDelito.HURTO
    return r


@pytest.fixture
def estafa() -> CrimeRecord:
    """Una estafa cuento del tío."""
    r = CrimeRecord(
        id="e001",
        nro_sumario="SUM-003",
        fecha=date(2024, 3, 20),  # Miércoles
        hora=time(10, 15),
        delito="070-ESTAFA",
        modus_operandi="CUENTO DEL TIO",
        ambito="DOMICILIO",
        esclarecido="PARCIAL",
        direccion="Calle Belgrano 800",
        jurisdiccion="AMAICHA DEL VALLE",
        dependencia="COMISARÍA AMAICHA",
    )
    r.categoria = CategoriaDelito.ESTAFA
    return r


@pytest.fixture
def record_sin_fecha() -> CrimeRecord:
    """Registro sin fecha ni hora."""
    return CrimeRecord(
        id="sf001",
        nro_sumario="SUM-004",
        delito="ROBO ARREBATO",
    )


@pytest.fixture
def sample_records(robo_agravado, hurto_oportunista, estafa) -> List[CrimeRecord]:
    """Lista de 3 registros de ejemplo."""
    return [robo_agravado, hurto_oportunista, estafa]


# ═════════════════════════════════════════════════════════════════════════════
# PERSONAS
# ═════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mencionado() -> MentionedPerson:
    return MentionedPerson(
        id="m001",
        nro_sumario="SUM-001",
        alias="Peluca",
        nombre="Roberto Gómez",
        delito="ROBO AGRAVADO",
        fecha=date(2024, 3, 15),
        hora=time(22, 30),
        direccion_hecho="Av. San Martín 450",
    )


@pytest.fixture
def aprehendido() -> Apprehended:
    return Apprehended(
        id="a001",
        nro_sumario="SUM-001",
        nombre="Carlos López",
        edad=25,
        sexo="MASCULINO",
        clasificacion_raw="MAYOR PRIMERIZO",
        delito="ROBO AGRAVADO",
        fecha=date(2024, 3, 15),
    )


@pytest.fixture
def aprehendido_menor() -> Apprehended:
    return Apprehended(
        id="a002",
        nro_sumario="SUM-002",
        nombre="Menor NN",
        edad=16,
        sexo="M",
        clasificacion_raw="MENOR CON ANTECEDENTES",
        delito="HURTO OPORTUNISTA",
        fecha=date(2024, 3, 18),
    )


# ═════════════════════════════════════════════════════════════════════════════
# PERIOD DATA
# ═════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def period_data(sample_records, mencionado, aprehendido) -> PeriodData:
    """PeriodData con un período principal cargado."""
    return PeriodData(
        nombre="Marzo 2024",
        fecha_inicio=date(2024, 3, 1),
        fecha_fin=date(2024, 3, 31),
        hechos=sample_records,
        mencionados=[mencionado],
        aprehendidos=[aprehendido],
    )


@pytest.fixture
def period_data_comparacion() -> PeriodData:
    """Segundo período para comparaciones."""
    r1 = CrimeRecord(
        id="c001",
        nro_sumario="SUM-C01",
        fecha=date(2024, 4, 5),
        hora=time(8, 0),
        delito="010-ROBO_AGRAVADO",
        modus_operandi="ASALTANTE",
    )
    r1.categoria = CategoriaDelito.ROBO
    r1._es_robo_agravado = True

    r2 = CrimeRecord(
        id="c002",
        nro_sumario="SUM-C02",
        fecha=date(2024, 4, 10),
        hora=time(16, 30),
        delito="050-HURTO",
        modus_operandi="OPORTUNISTA",
    )
    r2.categoria = CategoriaDelito.HURTO

    return PeriodData(
        nombre="Abril 2024",
        fecha_inicio=date(2024, 4, 1),
        fecha_fin=date(2024, 4, 30),
        hechos=[r1, r2],
        mencionados=[],
        aprehendidos=[],
    )


# ═════════════════════════════════════════════════════════════════════════════
# REPORT DATA
# ═════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def report_data(period_data) -> ReportData:
    """ReportData con un solo período."""
    return ReportData(
        titulo="INFORME TEST",
        jurisdiccion="AMAICHA DEL VALLE",
        dependencia="COMISARÍA AMAICHA",
        fecha_generacion=date(2024, 4, 1),
        periodos=[period_data],
    )


@pytest.fixture
def report_data_comparativo(period_data, period_data_comparacion) -> ReportData:
    """ReportData comparativo con 2 períodos."""
    return ReportData(
        titulo="INFORME COMPARATIVO TEST",
        jurisdiccion="AMAICHA DEL VALLE",
        dependencia="COMISARÍA AMAICHA",
        fecha_generacion=date(2024, 5, 1),
        periodos=[period_data, period_data_comparacion],
        modo_variacion=ModoVariacion.VS_PRINCIPAL,
    )


# ═════════════════════════════════════════════════════════════════════════════
# CATEGORIZER
# ═════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def categorizer() -> DelitoCategorizer:
    """DelitoCategorizer con defaults."""
    return DelitoCategorizer()
