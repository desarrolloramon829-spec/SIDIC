"""
Caso de uso: Validar archivos GIS antes de cargarlos.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from sidic.application.dto.dtos import ValidationResultDTO
from sidic.infrastructure.readers.reader_factory import ReaderFactory
from sidic.infrastructure.readers.shapefile_reader import ShapefileReader

logger = logging.getLogger(__name__)


class ValidateFilesUseCase:
    """Valida uno o más archivos GIS y retorna diagnósticos."""

    def __init__(self, reader_factory: ReaderFactory | None = None) -> None:
        self._factory = reader_factory or ReaderFactory()

    def execute(self, paths: List[str]) -> List[ValidationResultDTO]:
        """Valida cada archivo y retorna lista de resultados."""
        results: List[ValidationResultDTO] = []
        for p in paths:
            results.append(self._validate_one(p))
        return results

    def _validate_one(self, path_str: str) -> ValidationResultDTO:
        path = Path(path_str)
        try:
            reader = self._factory.create(path)
            if isinstance(reader, ShapefileReader):
                info = reader.validate_shapefile(path)
                return ValidationResultDTO(
                    valid=info["valid"],
                    path=path_str,
                    features=info.get("features", 0),
                    fields=info.get("fields", []),
                    encoding=info.get("encoding"),
                    errors=info.get("errors", []),
                    warnings=info.get("warnings", []),
                )
            # Para otros lectores, intentar leer campos
            fields = reader.detect_fields(path)
            return ValidationResultDTO(
                valid=True,
                path=path_str,
                fields=fields,
            )
        except Exception as e:
            return ValidationResultDTO(
                valid=False,
                path=path_str,
                errors=[str(e)],
            )
