"""
Fábrica de lectores GIS.

Selecciona el lector adecuado según la extensión del archivo
y proporciona una interfaz unificada de lectura.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Type

from sidic.domain.enums.common import FormatoGIS
from sidic.infrastructure.readers.base_reader import BaseGISReader, GISReaderError
from sidic.infrastructure.readers.field_mapper import FieldMapper
from sidic.infrastructure.readers.shapefile_reader import CSVReader, ShapefileReader

logger = logging.getLogger(__name__)

# Registro de lectores por extensión
_READER_REGISTRY: Dict[str, Type[BaseGISReader]] = {}


def _register_defaults() -> None:
    """Registra los lectores incluidos."""
    for ext in ShapefileReader().supported_extensions:
        _READER_REGISTRY[ext] = ShapefileReader
    for ext in CSVReader().supported_extensions:
        _READER_REGISTRY[ext] = CSVReader


_register_defaults()


class ReaderFactory:
    """
    Fábrica que instancia el lector correcto para un archivo dado.

    Ejemplo::

        factory = ReaderFactory()
        reader = factory.create("datos/hechos.shp")
        hechos = reader.read_hechos(Path("datos/hechos.shp"))
    """

    def __init__(self, field_mapper: Optional[FieldMapper] = None) -> None:
        self._field_mapper = field_mapper

    def create(self, path: str | Path) -> BaseGISReader:
        """
        Crea un lector para el archivo indicado.

        Args:
            path: Ruta al archivo GIS.

        Returns:
            Instancia del lector apropiado.

        Raises:
            GISReaderError: Si la extensión no está soportada.
        """
        ext = Path(path).suffix.lower()
        reader_cls = _READER_REGISTRY.get(ext)
        if reader_cls is None:
            exts = ", ".join(sorted(_READER_REGISTRY.keys()))
            raise GISReaderError(
                f"Formato no soportado: '{ext}'. "
                f"Extensiones válidas: {exts}"
            )
        return reader_cls(field_mapper=self._field_mapper)

    def create_for_format(self, fmt: FormatoGIS) -> BaseGISReader:
        """Crea un lector a partir de un enum FormatoGIS."""
        ext = fmt.value  # ej: ".shp"
        reader_cls = _READER_REGISTRY.get(ext)
        if reader_cls is None:
            raise GISReaderError(f"No hay lector para formato {fmt.name}")
        return reader_cls(field_mapper=self._field_mapper)

    @staticmethod
    def supported_extensions() -> List[str]:
        """Lista todas las extensiones soportadas."""
        return sorted(_READER_REGISTRY.keys())

    @staticmethod
    def register(ext: str, reader_cls: Type[BaseGISReader]) -> None:
        """
        Registra un lector personalizado para una extensión.

        Permite extender la fábrica con formatos adicionales.
        """
        _READER_REGISTRY[ext.lower()] = reader_cls
        logger.info(
            f"Lector {reader_cls.__name__} registrado para '{ext}'"
        )

    @staticmethod
    def file_filter_string() -> str:
        """
        Retorna un string de filtro para diálogos de archivo Qt.

        Ejemplo: "Archivos GIS (*.shp *.geojson *.gpkg *.kml *.csv)"
        """
        exts = " ".join(f"*{e}" for e in sorted(_READER_REGISTRY.keys()))
        parts = [f"Archivos GIS ({exts})"]

        # Agregar filtros individuales
        format_names = {
            ".shp": "Shapefile",
            ".geojson": "GeoJSON",
            ".json": "GeoJSON",
            ".gpkg": "GeoPackage",
            ".kml": "KML",
            ".csv": "CSV",
        }
        for ext in sorted(_READER_REGISTRY.keys()):
            name = format_names.get(ext, ext.upper().lstrip("."))
            parts.append(f"{name} (*{ext})")

        parts.append("Todos los archivos (*)")
        return ";;".join(parts)
