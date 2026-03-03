"""
Enums auxiliares del dominio S.I.D.I.C.
"""
from enum import Enum


class TipoEsclarecimiento(Enum):
    """Estado de esclarecimiento de un hecho delictivo."""

    SI = "SI"
    NO = "NO"
    PARCIAL = "PARCIAL"

    @classmethod
    def from_text(cls, text: str) -> "TipoEsclarecimiento":
        """Parsea texto libre a tipo de esclarecimiento."""
        if not text:
            return cls.NO
        normalized = text.strip().upper()
        if normalized in ("SI", "SÍ", "S", "TRUE", "1", "RESUELTO"):
            return cls.SI
        if normalized in ("PARCIAL", "PARCIALMENTE"):
            return cls.PARCIAL
        return cls.NO


class ClasificacionAprehendido(Enum):
    """Clasificación de personas aprehendidas por edad y antecedentes."""

    MAYOR_PRIMERIZO = "MAYOR PRIMERIZO"
    MAYOR_CON_ANTECEDENTES = "MAYOR CON ANTECEDENTES"
    MENOR_PRIMERIZO = "MENOR PRIMERIZO"
    MENOR_CON_ANTECEDENTES = "MENOR CON ANTECEDENTES"

    @property
    def es_menor(self) -> bool:
        return self in (
            ClasificacionAprehendido.MENOR_PRIMERIZO,
            ClasificacionAprehendido.MENOR_CON_ANTECEDENTES,
        )

    @property
    def tiene_antecedentes(self) -> bool:
        return self in (
            ClasificacionAprehendido.MAYOR_CON_ANTECEDENTES,
            ClasificacionAprehendido.MENOR_CON_ANTECEDENTES,
        )

    @classmethod
    def inferir(cls, edad: int | None, antecedentes: bool = False) -> "ClasificacionAprehendido":
        """Infiere la clasificación a partir de la edad y antecedentes."""
        es_menor = edad is not None and edad < 18
        if es_menor:
            return cls.MENOR_CON_ANTECEDENTES if antecedentes else cls.MENOR_PRIMERIZO
        return cls.MAYOR_CON_ANTECEDENTES if antecedentes else cls.MAYOR_PRIMERIZO


class FormatoExportacion(Enum):
    """Formatos disponibles para exportación de reportes."""

    EXCEL = "excel"
    WORD = "word"
    PDF = "pdf"

    @property
    def extension(self) -> str:
        ext_map = {
            FormatoExportacion.EXCEL: ".xlsx",
            FormatoExportacion.WORD: ".docx",
            FormatoExportacion.PDF: ".pdf",
        }
        return ext_map[self]


class ModoVariacion(Enum):
    """Modo de cálculo de variación en análisis comparativo."""

    VS_PRINCIPAL = "vs_principal"
    VS_ANTERIOR = "vs_anterior"
    AMBAS = "ambas"


class FormatoGIS(Enum):
    """Formatos de archivos GIS soportados para entrada."""

    SHAPEFILE = "shapefile"
    GEOJSON = "geojson"
    KML = "kml"
    GEOPACKAGE = "geopackage"
    CSV = "csv"

    @classmethod
    def from_extension(cls, extension: str) -> "FormatoGIS":
        """Detecta el formato a partir de la extensión del archivo."""
        ext = extension.lower().lstrip(".")
        mapping = {
            "shp": cls.SHAPEFILE,
            "dbf": cls.SHAPEFILE,
            "geojson": cls.GEOJSON,
            "json": cls.GEOJSON,
            "kml": cls.KML,
            "kmz": cls.KML,
            "gpkg": cls.GEOPACKAGE,
            "csv": cls.CSV,
            "tsv": cls.CSV,
        }
        if ext not in mapping:
            raise ValueError(
                f"Extensión no soportada: .{ext}. "
                f"Formatos válidos: {', '.join(mapping.keys())}"
            )
        return mapping[ext]
