"""
Módulo de lectores de archivos GIS.

Provee lectores para Shapefile, GeoJSON, GeoPackage, KML y CSV,
una fábrica de lectores, y utilidades de parseo y mapeo de campos.
"""
from sidic.infrastructure.readers.base_reader import BaseGISReader, GISReaderError
from sidic.infrastructure.readers.field_mapper import FieldMapper
from sidic.infrastructure.readers.reader_factory import ReaderFactory
from sidic.infrastructure.readers.shapefile_reader import CSVReader, ShapefileReader

__all__ = [
    "BaseGISReader",
    "CSVReader",
    "FieldMapper",
    "GISReaderError",
    "ReaderFactory",
    "ShapefileReader",
]
