"""
Caso de uso: Cargar datos desde archivos GIS.

Orquesta la lectura de archivos, mapeo de campos, categorización
de delitos y armado de PeriodData.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from sidic.application.dto.dtos import (
    LoadDataInputDTO,
    LoadDataOutputDTO,
    PeriodInputDTO,
    PeriodSummaryDTO,
)
from sidic.domain.models.apprehended import Apprehended
from sidic.domain.models.crime_record import CrimeRecord
from sidic.domain.models.mentioned_person import MentionedPerson
from sidic.domain.models.report_data import PeriodData, ReportData
from sidic.domain.services.delito_categorizer import DelitoCategorizer
from sidic.infrastructure.readers.reader_factory import ReaderFactory

logger = logging.getLogger(__name__)


class LoadDataUseCase:
    """
    Carga datos GIS de múltiples períodos y construye ReportData.

    Flujo:
        1. Para cada período, lee hechos/mencionados/aprehendidos
        2. Categoriza delitos automáticamente
        3. Arma PeriodData con registros y rangos de fecha
        4. Retorna ReportData con todos los períodos listos
    """

    def __init__(
        self,
        reader_factory: Optional[ReaderFactory] = None,
        categorizer: Optional[DelitoCategorizer] = None,
    ) -> None:
        self._reader_factory = reader_factory or ReaderFactory()
        self._categorizer = categorizer or DelitoCategorizer()
        self._report_data: Optional[ReportData] = None

    @property
    def report_data(self) -> Optional[ReportData]:
        """Datos cargados (None si no se ha ejecutado)."""
        return self._report_data

    def execute(self, input_dto: LoadDataInputDTO) -> LoadDataOutputDTO:
        """Ejecuta la carga de datos."""
        errors: List[str] = []
        warnings: List[str] = []
        summaries: List[PeriodSummaryDTO] = []
        periods: List[PeriodData] = []

        for period_input in input_dto.periods:
            summary, period_data, errs, warns = self._load_period(period_input)
            summaries.append(summary)
            errors.extend(errs)
            warnings.extend(warns)
            if period_data:
                periods.append(period_data)

        if not periods:
            errors.append("No se pudo cargar ningún período.")
            return LoadDataOutputDTO(
                success=False,
                errors=errors,
                warnings=warnings,
            )

        self._report_data = ReportData(
            periodos=periods,
            titulo="INFORME DELICTUAL",
            jurisdiccion=input_dto.jurisdiccion,
            dependencia=input_dto.dependencia,
        )

        return LoadDataOutputDTO(
            success=True,
            period_summaries=summaries,
            errors=errors,
            warnings=warnings,
        )

    def _load_period(
        self, p: PeriodInputDTO
    ) -> tuple:
        """Carga un período individual."""
        errors: List[str] = []
        warnings: List[str] = []
        hechos: List[CrimeRecord] = []
        mencionados: List[MentionedPerson] = []
        aprehendidos: List[Apprehended] = []

        # Hechos
        for path_str in p.hechos_paths:
            try:
                reader = self._reader_factory.create(path_str)
                records = reader.read_hechos(Path(path_str))
                hechos.extend(records)
                logger.info(f"[{p.name}] {len(records)} hechos desde {Path(path_str).name}")
            except Exception as e:
                errors.append(f"Error leyendo hechos '{path_str}': {e}")

        # Mencionados
        for path_str in p.mencionados_paths:
            try:
                reader = self._reader_factory.create(path_str)
                records = reader.read_mencionados(Path(path_str))
                mencionados.extend(records)
            except Exception as e:
                errors.append(f"Error leyendo mencionados '{path_str}': {e}")

        # Aprehendidos
        for path_str in p.aprehendidos_paths:
            try:
                reader = self._reader_factory.create(path_str)
                records = reader.read_aprehendidos(Path(path_str))
                aprehendidos.extend(records)
            except Exception as e:
                errors.append(f"Error leyendo aprehendidos '{path_str}': {e}")

        if not hechos:
            warnings.append(f"Período '{p.name}' sin hechos cargados.")

        # Categorizar delitos
        self._categorizer.categorizar_registros(hechos)

        # Detectar campos si es posible
        fields: List[str] = []
        if p.hechos_paths:
            try:
                reader = self._reader_factory.create(p.hechos_paths[0])
                fields = reader.detect_fields(Path(p.hechos_paths[0]))
            except Exception:
                pass

        summary = PeriodSummaryDTO(
            name=p.name,
            start_date=p.start_date,
            end_date=p.end_date,
            total_hechos=len(hechos),
            total_mencionados=len(mencionados),
            total_aprehendidos=len(aprehendidos),
            fields_detected=fields,
        )

        period_data = PeriodData(
            nombre=p.name,
            fecha_inicio=p.start_date,
            fecha_fin=p.end_date,
            hechos=hechos,
            mencionados=mencionados,
            aprehendidos=aprehendidos,
        )

        return summary, period_data, errors, warnings
