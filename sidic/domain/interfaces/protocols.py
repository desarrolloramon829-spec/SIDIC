"""
Interfaces (Protocols) del dominio S.I.D.I.C.

Define contratos que deben cumplir las implementaciones concretas
de la capa de infraestructura, sin acoplar el dominio a dependencias externas.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from sidic.domain.models.crime_record import CrimeRecord
from sidic.domain.models.mentioned_person import MentionedPerson
from sidic.domain.models.apprehended import Apprehended


# ═════════════════════════════════════════════════════════════════════════════
# LECTURA DE DATOS GIS
# ═════════════════════════════════════════════════════════════════════════════


@runtime_checkable
class GISReader(Protocol):
    """Protocolo para lectores de archivos GIS."""

    def read_hechos(self, path: Path) -> List[CrimeRecord]:
        """Lee registros de hechos delictuales desde un archivo GIS."""
        ...

    def read_mencionados(self, path: Path) -> List[MentionedPerson]:
        """Lee registros de personas mencionadas."""
        ...

    def read_aprehendidos(self, path: Path) -> List[Apprehended]:
        """Lee registros de personas aprehendidas."""
        ...

    def detect_fields(self, path: Path) -> List[str]:
        """Detecta los nombres de campos disponibles en el archivo."""
        ...

    @property
    def supported_extensions(self) -> List[str]:
        """Extensiones de archivo soportadas por este reader."""
        ...


# ═════════════════════════════════════════════════════════════════════════════
# MAPEO DE CAMPOS
# ═════════════════════════════════════════════════════════════════════════════


@runtime_checkable
class FieldMapper(Protocol):
    """Protocolo para mapeo de campos entre formato GIS y modelo de dominio."""

    def map_row(self, raw_row: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """
        Mapea una fila cruda del archivo GIS a campos normalizados.

        Args:
            raw_row: Diccionario con nombres de campo originales.
            entity_type: Tipo de entidad ('hechos', 'mencionados', 'aprehendidos').

        Returns:
            Diccionario con nombres de campo normalizados.
        """
        ...

    def detect_mapping(self, field_names: List[str], entity_type: str) -> Dict[str, str]:
        """
        Auto-detecta el mapeo entre campos del archivo y campos del modelo.

        Args:
            field_names: Nombres de campo disponibles en el archivo.
            entity_type: Tipo de entidad a mapear.

        Returns:
            Diccionario {campo_modelo: campo_archivo}.
        """
        ...

    def get_required_fields(self, entity_type: str) -> List[str]:
        """Retorna los nombres de campos requeridos para un tipo de entidad."""
        ...


# ═════════════════════════════════════════════════════════════════════════════
# EXPORTACIÓN DE REPORTES
# ═════════════════════════════════════════════════════════════════════════════


@runtime_checkable
class ReportExporter(Protocol):
    """Protocolo para exportadores de reportes."""

    def export(
        self,
        output_path: Path,
        tables: Dict[str, Any],
        charts: Dict[str, bytes],
        options: Dict[str, Any],
    ) -> Path:
        """
        Exporta un reporte al formato correspondiente.

        Args:
            output_path: Ruta del archivo de salida.
            tables: Diccionario de DataFrames con las tablas generadas.
            charts: Diccionario de imágenes de gráficos (como bytes PNG).
            options: Opciones de exportación (secciones a incluir, etc.).

        Returns:
            Ruta del archivo generado.
        """
        ...


# ═════════════════════════════════════════════════════════════════════════════
# PERSISTENCIA DE PROYECTOS
# ═════════════════════════════════════════════════════════════════════════════


@runtime_checkable
class ProjectRepository(Protocol):
    """Protocolo para persistencia de proyectos."""

    def save(self, project_data: Dict[str, Any], path: Path) -> None:
        """Guarda un proyecto en disco."""
        ...

    def load(self, path: Path) -> Dict[str, Any]:
        """Carga un proyecto desde disco."""
        ...

    def exists(self, path: Path) -> bool:
        """Verifica si un archivo de proyecto existe."""
        ...


@runtime_checkable
class SettingsRepository(Protocol):
    """Protocolo para persistencia de configuraciones de usuario."""

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Establece un valor de configuración."""
        ...

    def save(self) -> None:
        """Persiste los cambios a disco."""
        ...

    def load(self) -> None:
        """Carga configuraciones desde disco."""
        ...
