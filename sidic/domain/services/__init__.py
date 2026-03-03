"""
Servicios del dominio — lógica de negocio pura.
"""

from sidic.domain.services.delito_categorizer import DelitoCategorizer
from sidic.domain.services.filters import CategoryFilter, PeriodFilter
from sidic.domain.services.period_comparator import (
    ComparacionItem,
    PeriodComparator,
)
from sidic.domain.services.statistics import StatisticsCalculator

__all__ = [
    "DelitoCategorizer",
    "PeriodFilter",
    "CategoryFilter",
    "StatisticsCalculator",
    "PeriodComparator",
    "ComparacionItem",
]
