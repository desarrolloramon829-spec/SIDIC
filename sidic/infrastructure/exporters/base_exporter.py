"""
Exportador base y tipos comunes para todos los formatos de reporte.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ExportOptions:
    """Opciones configurables para la exportación."""

    incluir_graficos: bool = True
    incluir_cuadro_referencia: bool = True
    incluir_mencionados: bool = True
    incluir_aprehendidos: bool = True
    incluir_matrices: bool = True
    incluir_comparativos: bool = True
    incluir_resena: bool = False
    titulo: str = "INFORME DELICTUAL"
    subtitulo: str = ""
    jurisdiccion: str = ""
    dependencia: str = ""
    autor: str = ""
    secciones_habilitadas: List[str] = field(default_factory=list)


@dataclass
class ExportResult:
    """Resultado de una exportación."""

    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    alternative_path: Optional[str] = None  # si el original estaba bloqueado


class BaseExporter(ABC):
    """
    Clase base para todos los exportadores.

    Provee la interfaz común y helpers compartidos.
    """

    def __init__(self) -> None:
        self._last_error: str = ""

    @property
    def last_error(self) -> str:
        return self._last_error

    @abstractmethod
    def export(
        self,
        output_path: str | Path,
        tables: Dict[str, pd.DataFrame],
        charts: Optional[Dict[str, bytes]] = None,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        """
        Exporta las tablas y gráficos al formato de salida.

        Args:
            output_path: Ruta del archivo de salida.
            tables: Dict nombre → DataFrame de cada tabla.
            charts: Dict nombre → bytes PNG de cada gráfico.
            options: Opciones de exportación.

        Returns:
            ExportResult con estado de la operación.
        """
        ...

    @staticmethod
    def _ensure_dir(path: Path) -> None:
        """Crea el directorio de salida si no existe."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_sheet_name(name: str, max_len: int = 31) -> str:
        """Limita nombre de hoja a caracteres válidos."""
        invalid = r'[]:*?/\\'
        clean = "".join(c for c in name if c not in invalid)
        return clean[:max_len]

    def _save_with_retry(
        self,
        save_fn,
        output_path: Path,
    ) -> ExportResult:
        """
        Intenta guardar; si el archivo está bloqueado, usa nombre alternativo.
        """
        try:
            save_fn(str(output_path))
            return ExportResult(success=True, output_path=str(output_path))
        except PermissionError:
            from datetime import datetime

            alt_name = (
                f"{output_path.stem}_{datetime.now().strftime('%H%M%S')}"
                f"{output_path.suffix}"
            )
            alt_path = output_path.parent / alt_name
            try:
                save_fn(str(alt_path))
                return ExportResult(
                    success=True,
                    output_path=str(alt_path),
                    alternative_path=str(alt_path),
                    warnings=[
                        f"Archivo original bloqueado. Guardado como: {alt_name}"
                    ],
                )
            except PermissionError:
                msg = (
                    f"No se puede guardar. Cierre '{output_path.name}' "
                    f"si está abierto en otra aplicación."
                )
                self._last_error = msg
                return ExportResult(success=False, error=msg)
