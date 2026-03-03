"""
ViewModel principal de S.I.D.I.C.

Orquesta la lógica de presentación entre la UI y los use-cases.
Expone señales PyQt que los widgets conectan para reaccionar a cambios.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from sidic.application.dto.dtos import (
    ComparisonInputDTO,
    FilterInputDTO,
    GenerateReportInputDTO,
    LoadDataInputDTO,
    PeriodInputDTO,
    PeriodSummaryDTO,
)
from sidic.domain.enums.common import FormatoExportacion, ModoVariacion
from sidic.domain.models.report_data import ReportData

logger = logging.getLogger(__name__)


# ── Estado observable de la aplicación ────────────────────────────────

@dataclass
class PeriodState:
    """Estado de un período configurado por el usuario."""

    name: str = ""
    start_date: date | None = None
    end_date: date | None = None
    hechos_path: str = ""
    mencionados_path: str = ""
    aprehendidos_path: str = ""


@dataclass
class AppState:
    """Estado completo de la aplicación (fuente de verdad)."""

    # Archivos cargados   {tipo: ruta}
    files: Dict[str, str] = field(default_factory=dict)

    # Período principal
    main_period: PeriodState = field(default_factory=PeriodState)

    # Períodos comparativos (0 a 5)
    comparison_periods: List[PeriodState] = field(default_factory=list)
    comparative_mode: bool = False
    modo_variacion: str = "vs_principal"

    # Opciones de exportación
    formato: str = "excel"
    incluir_graficos: bool = True
    incluir_cuadro_referencia: bool = True
    incluir_mencionados: bool = True
    incluir_aprehendidos: bool = True
    incluir_matrices: bool = True
    incluir_comparativos: bool = True

    # Filtros de categoría
    categorias_incluidas: List[str] = field(
        default_factory=lambda: [
            "ROBOS", "TENTATIVA DE ROBOS",
            "HURTOS", "TENTATIVA DE HURTOS",
            "ESTAFAS", "OTROS DELITOS",
        ]
    )

    # Metadatos
    jurisdiccion: str = ""
    dependencia: str = ""
    titulo: str = "INFORME DELICTUAL"


class MainViewModel(QObject):
    """
    ViewModel central.  Single source of truth para el estado de la app.

    Signals
    -------
    files_updated(dict)
        Archivos cargados cambiaron.
    state_changed()
        Cualquier cambio relevante en el estado.
    validation_result(bool, str)
        Resultado de validación (ok, mensaje).
    """

    files_updated = pyqtSignal(dict)
    state_changed = pyqtSignal()
    validation_result = pyqtSignal(bool, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state = AppState()
        self._report_data: ReportData | None = None

    # ── Propiedades de lectura ────────────────────────────────────

    @property
    def state(self) -> AppState:
        return self._state

    @property
    def report_data(self) -> ReportData | None:
        return self._report_data

    @report_data.setter
    def report_data(self, value: ReportData | None) -> None:
        self._report_data = value

    # ── Mutadores de estado ───────────────────────────────────────

    def set_files(self, files: Dict[str, str]) -> None:
        self._state.files = dict(files)
        self.files_updated.emit(self._state.files)
        self.state_changed.emit()

    def set_main_period(self, start: date, end: date, name: str = "") -> None:
        self._state.main_period.start_date = start
        self._state.main_period.end_date = end
        self._state.main_period.name = name or "Período Principal"
        self.state_changed.emit()

    def set_comparative_mode(self, enabled: bool) -> None:
        self._state.comparative_mode = enabled
        self.state_changed.emit()

    def set_comparison_periods(self, periods: List[PeriodState]) -> None:
        self._state.comparison_periods = list(periods)
        self.state_changed.emit()

    def set_modo_variacion(self, modo: str) -> None:
        self._state.modo_variacion = modo
        self.state_changed.emit()

    def set_formato(self, fmt: str) -> None:
        self._state.formato = fmt
        self.state_changed.emit()

    def set_categorias(self, cats: List[str]) -> None:
        self._state.categorias_incluidas = list(cats)
        self.state_changed.emit()

    def set_option(self, key: str, value: Any) -> None:
        if hasattr(self._state, key):
            setattr(self._state, key, value)
            self.state_changed.emit()

    # ── Validación ────────────────────────────────────────────────

    def validate(self) -> tuple[bool, str]:
        """Valida el estado actual antes de generar reporte."""
        s = self._state

        # Al menos un tipo de archivo cargado
        if not s.files:
            msg = "No hay archivos cargados."
            self.validation_result.emit(False, msg)
            return False, msg

        # Período principal definido
        mp = s.main_period
        if mp.start_date is None or mp.end_date is None:
            msg = "El período principal no está configurado."
            self.validation_result.emit(False, msg)
            return False, msg

        if mp.start_date > mp.end_date:
            msg = "La fecha de inicio es posterior a la fecha fin."
            self.validation_result.emit(False, msg)
            return False, msg

        # Modo comparativo: al menos 1 período extra
        if s.comparative_mode and not s.comparison_periods:
            msg = "Active al menos un período de comparación."
            self.validation_result.emit(False, msg)
            return False, msg

        # Categorías
        if not s.categorias_incluidas:
            msg = "Seleccione al menos una categoría de delitos."
            self.validation_result.emit(False, msg)
            return False, msg

        self.validation_result.emit(True, "")
        return True, ""

    # ── Construcción de DTOs para use-cases ────────────────────────

    def build_load_input(self) -> LoadDataInputDTO:
        """Convierte el estado actual a DTO de carga."""
        s = self._state
        periods: list[PeriodInputDTO] = []

        # Periodo principal
        main_path = s.files.get("hechos", "")
        periods.append(PeriodInputDTO(
            name=s.main_period.name or "Período Principal",
            start_date=s.main_period.start_date or date.today(),
            end_date=s.main_period.end_date or date.today(),
            hechos_paths=[main_path] if main_path else [],
            mencionados_paths=[s.files.get("mencionados", "")] if s.files.get("mencionados") else [],
            aprehendidos_paths=[s.files.get("aprehendidos", "")] if s.files.get("aprehendidos") else [],
        ))

        # Períodos comparativos
        if s.comparative_mode:
            for i, cp in enumerate(s.comparison_periods, 1):
                periods.append(PeriodInputDTO(
                    name=cp.name or f"Período {i}",
                    start_date=cp.start_date or date.today(),
                    end_date=cp.end_date or date.today(),
                    hechos_paths=[main_path] if main_path else [],
                    mencionados_paths=[s.files.get("mencionados", "")] if s.files.get("mencionados") else [],
                    aprehendidos_paths=[s.files.get("aprehendidos", "")] if s.files.get("aprehendidos") else [],
                ))

        return LoadDataInputDTO(
            periods=periods,
            jurisdiccion=s.jurisdiccion,
            dependencia=s.dependencia,
        )

    def build_report_input(self, output_path: str) -> GenerateReportInputDTO:
        """Convierte el estado actual a DTO de generación de reporte."""
        s = self._state
        return GenerateReportInputDTO(
            formato=s.formato,
            output_path=output_path,
            titulo=s.titulo,
            incluir_graficos=s.incluir_graficos,
            incluir_cuadro_referencia=s.incluir_cuadro_referencia,
            incluir_mencionados=s.incluir_mencionados,
            incluir_aprehendidos=s.incluir_aprehendidos,
            incluir_matrices=s.incluir_matrices,
            incluir_comparativos=s.incluir_comparativos,
        )

    def build_filter_input(self) -> FilterInputDTO:
        """Convierte las opciones de filtrado a DTO."""
        return FilterInputDTO(categorias=list(self._state.categorias_incluidas))

    def build_comparison_input(self) -> ComparisonInputDTO:
        """Convierte el modo de variación a DTO."""
        return ComparisonInputDTO(modo=self._state.modo_variacion)

    # ── Reset ─────────────────────────────────────────────────────

    def reset(self) -> None:
        """Restablece el estado a valores iniciales."""
        self._state = AppState()
        self._report_data = None
        self.files_updated.emit({})
        self.state_changed.emit()
