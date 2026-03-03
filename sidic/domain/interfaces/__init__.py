"""
Interfaces del dominio S.I.D.I.C.
"""

from sidic.domain.interfaces.protocols import (
    FieldMapper,
    GISReader,
    ProjectRepository,
    ReportExporter,
    SettingsRepository,
)

__all__ = [
    "FieldMapper",
    "GISReader",
    "ProjectRepository",
    "ReportExporter",
    "SettingsRepository",
]
