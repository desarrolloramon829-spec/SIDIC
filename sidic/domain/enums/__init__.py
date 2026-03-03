"""
Enums del dominio S.I.D.I.C.

Exporta todos los enums para uso conveniente:
    from sidic.domain.enums import CategoriaDelito, FranjaHoraria, DiaSemana
"""

from sidic.domain.enums.categoria_delito import CategoriaDelito
from sidic.domain.enums.franja_horaria import FranjaHoraria
from sidic.domain.enums.dia_semana import DiaSemana
from sidic.domain.enums.common import (
    ClasificacionAprehendido,
    FormatoExportacion,
    FormatoGIS,
    ModoVariacion,
    TipoEsclarecimiento,
)

__all__ = [
    "CategoriaDelito",
    "ClasificacionAprehendido",
    "DiaSemana",
    "FormatoExportacion",
    "FormatoGIS",
    "FranjaHoraria",
    "ModoVariacion",
    "TipoEsclarecimiento",
]
