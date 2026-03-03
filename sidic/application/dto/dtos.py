"""
Data Transfer Objects para la capa de aplicación.

Los DTOs son objetos simples que transportan datos entre capas
sin lógica de negocio. Sirven como contrato entre la UI y los
use cases.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class PeriodInputDTO:
    """Entrada para definir un período de análisis."""

    name: str
    start_date: date
    end_date: date
    hechos_paths: List[str] = field(default_factory=list)
    mencionados_paths: List[str] = field(default_factory=list)
    aprehendidos_paths: List[str] = field(default_factory=list)
    color: Optional[str] = None


@dataclass
class LoadDataInputDTO:
    """Entrada general para carga de datos."""

    periods: List[PeriodInputDTO] = field(default_factory=list)
    jurisdiccion: str = ""
    dependencia: str = ""


@dataclass
class LoadDataOutputDTO:
    """Resultado de la carga de datos."""

    success: bool
    period_summaries: List[PeriodSummaryDTO] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class PeriodSummaryDTO:
    """Resumen de datos cargados en un período."""

    name: str
    start_date: date
    end_date: date
    total_hechos: int = 0
    total_mencionados: int = 0
    total_aprehendidos: int = 0
    fields_detected: List[str] = field(default_factory=list)


@dataclass
class FilterInputDTO:
    """Filtros a aplicar sobre los datos cargados."""

    categorias: Optional[List[str]] = None  # None = todas
    delitos: Optional[List[str]] = None
    dias_semana: Optional[List[str]] = None
    franjas_horarias: Optional[List[str]] = None
    jurisdiccion: Optional[str] = None
    esclarecido: Optional[str] = None


@dataclass
class GenerateReportInputDTO:
    """Entrada para generar el reporte."""

    formato: str  # "excel" | "word" | "pdf"
    output_path: str
    titulo: str = "INFORME DELICTUAL"
    incluir_graficos: bool = True
    incluir_cuadro_referencia: bool = True
    incluir_mencionados: bool = True
    incluir_aprehendidos: bool = True
    incluir_matrices: bool = True
    incluir_comparativos: bool = True
    secciones: List[str] = field(default_factory=list)


@dataclass
class GenerateReportOutputDTO:
    """Resultado de la generación del reporte."""

    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    tables_generated: List[str] = field(default_factory=list)
    charts_generated: List[str] = field(default_factory=list)


@dataclass
class TableDataDTO:
    """Transporta datos de una tabla generada."""

    name: str
    title: str
    dataframe: pd.DataFrame = field(default_factory=pd.DataFrame)
    chart_bytes: Optional[bytes] = None


@dataclass
class ValidationResultDTO:
    """Resultado de validar archivos de entrada."""

    valid: bool
    path: str
    features: int = 0
    fields: List[str] = field(default_factory=list)
    encoding: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class FileInfoDTO:
    """Información básica de un archivo GIS."""

    path: str
    name: str
    extension: str
    size_bytes: int = 0
    supported: bool = True


@dataclass
class ComparisonInputDTO:
    """Entrada para comparación entre períodos."""

    modo: str = "vs_principal"  # "vs_principal" | "vs_anterior" | "ambas"


@dataclass
class FieldMappingDTO:
    """Mapeo de campos para un tipo de entidad."""

    entity_type: str  # "hechos" | "mencionados" | "aprehendidos"
    available_fields: List[str] = field(default_factory=list)
    detected_mapping: Dict[str, Optional[str]] = field(default_factory=dict)
    confidence: float = 0.0
    unmapped_required: List[str] = field(default_factory=list)
