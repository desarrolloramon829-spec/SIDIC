"""
Servicios de filtrado: por período temporal y por categoría de delito.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import List, Optional, Set

from sidic.domain.enums import CategoriaDelito
from sidic.domain.models.crime_record import CrimeRecord
from sidic.domain.models.mentioned_person import MentionedPerson
from sidic.domain.models.apprehended import Apprehended

logger = logging.getLogger(__name__)


class PeriodFilter:
    """Filtra registros por rango de fechas."""

    @staticmethod
    def filter_hechos(
        hechos: List[CrimeRecord],
        inicio: date,
        fin: date,
    ) -> List[CrimeRecord]:
        """Filtra hechos delictuales que caen dentro del período."""
        resultado = [h for h in hechos if h.matches_period(inicio, fin)]
        logger.debug(
            f"PeriodFilter: {len(resultado)}/{len(hechos)} hechos "
            f"en período {inicio} - {fin}"
        )
        return resultado

    @staticmethod
    def filter_mencionados(
        mencionados: List[MentionedPerson],
        inicio: date,
        fin: date,
    ) -> List[MentionedPerson]:
        """Filtra mencionados que caen dentro del período."""
        return [m for m in mencionados if m.matches_period(inicio, fin)]

    @staticmethod
    def filter_aprehendidos(
        aprehendidos: List[Apprehended],
        inicio: date,
        fin: date,
    ) -> List[Apprehended]:
        """Filtra aprehendidos que caen dentro del período."""
        return [a for a in aprehendidos if a.matches_period(inicio, fin)]


class CategoryFilter:
    """Filtra registros por categorías de delito seleccionadas."""

    @staticmethod
    def filter_hechos(
        hechos: List[CrimeRecord],
        categorias: Set[CategoriaDelito] | List[CategoriaDelito] | None = None,
    ) -> List[CrimeRecord]:
        """
        Filtra hechos manteniendo solo los de las categorías indicadas.

        Si categorias es None o vacío, retorna todos los hechos sin filtrar.
        """
        if not categorias:
            return hechos

        cat_set = set(categorias) if not isinstance(categorias, set) else categorias
        resultado = [h for h in hechos if h.categoria in cat_set]

        logger.debug(
            f"CategoryFilter: {len(resultado)}/{len(hechos)} hechos "
            f"en categorías {[c.value for c in cat_set]}"
        )
        return resultado

    @staticmethod
    def filter_mencionados_by_sumario(
        mencionados: List[MentionedPerson],
        nro_sumarios_validos: Set[str],
    ) -> List[MentionedPerson]:
        """
        Filtra mencionados que están vinculados a hechos de categorías válidas,
        usando el nro_sumario como vínculo.
        """
        if not nro_sumarios_validos:
            return mencionados
        return [
            m for m in mencionados
            if not m.nro_sumario or m.nro_sumario in nro_sumarios_validos
        ]

    @staticmethod
    def filter_aprehendidos_by_sumario(
        aprehendidos: List[Apprehended],
        nro_sumarios_validos: Set[str],
    ) -> List[Apprehended]:
        """
        Filtra aprehendidos vinculados a hechos de categorías válidas.
        """
        if not nro_sumarios_validos:
            return aprehendidos
        return [
            a for a in aprehendidos
            if not a.nro_sumario or a.nro_sumario in nro_sumarios_validos
        ]
