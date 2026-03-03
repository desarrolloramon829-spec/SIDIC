"""
Lector base abstracto para archivos GIS.

Define la interfaz y lógica común de lectura/conversión de filas
a modelos de dominio (CrimeRecord, MentionedPerson, Apprehended).
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sidic.domain.models.apprehended import Apprehended
from sidic.domain.models.crime_record import CrimeRecord
from sidic.domain.models.mentioned_person import MentionedPerson
from sidic.infrastructure.readers.field_mapper import FieldMapper
from sidic.infrastructure.readers.parse_utils import (
    extract_coordinates,
    parse_date,
    parse_time,
)

logger = logging.getLogger(__name__)


class GISReaderError(Exception):
    """Error de lectura/validación de archivo GIS."""
    pass


class BaseGISReader(ABC):
    """
    Clase base para lectores de archivos GIS.

    Cada sub-clase concreta implementa `_read_dataframe` para su formato
    específico (Shapefile, GeoJSON, KML, GPKG, CSV).
    La lógica de conversión de filas a modelos es compartida.
    """

    def __init__(self, field_mapper: Optional[FieldMapper] = None) -> None:
        self.field_mapper = field_mapper or FieldMapper()

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Extensiones soportadas (ej: ['.shp'])."""
        ...

    @abstractmethod
    def _read_dataframe(self, path: Path) -> Any:
        """
        Lee el archivo y retorna un GeoDataFrame (o DataFrame para CSV).

        Debe intentar múltiples encodings si es necesario.
        Lanza GISReaderError si no puede leer.
        """
        ...

    def detect_fields(self, path: Path) -> List[str]:
        """Detecta los nombres de campos disponibles en el archivo."""
        df = self._read_dataframe(path)
        cols = list(df.columns)
        if "geometry" in cols:
            cols.remove("geometry")
        return cols

    # ═══════════════════════════════════════════════════════════════════════
    # LECTURA DE HECHOS
    # ═══════════════════════════════════════════════════════════════════════

    def read_hechos(self, path: Path) -> List[CrimeRecord]:
        """Lee registros de hechos delictuales."""
        import pandas as pd

        df = self._read_dataframe(path)
        fields = [c for c in df.columns if c != "geometry"]
        field_map = self.field_mapper.build_field_map("hechos", fields)

        records: List[CrimeRecord] = []
        for idx, row in df.iterrows():
            try:
                records.append(self._row_to_crime_record(row, field_map, pd))
            except Exception as e:
                logger.warning(f"Error procesando fila {idx} (hechos): {e}")

        logger.info(f"Leídos {len(records)} hechos desde {path.name}")
        return records

    def _row_to_crime_record(
        self,
        row: Any,
        field_map: Dict[str, Optional[str]],
        pd: Any,
    ) -> CrimeRecord:
        """Convierte una fila del DataFrame a CrimeRecord."""

        def get(field: str) -> Any:
            src = field_map.get(field)
            if src and src in row.index:
                val = row[src]
                if pd.isna(val):
                    return None
                return val
            return None

        coords: Optional[Tuple[float, float]] = None
        if hasattr(row, "geometry") and row.geometry is not None:
            coords = extract_coordinates(row.geometry)

        # Campos extra (no mapeados)
        mapped_set = {v for v in field_map.values() if v}
        campos_extra = {
            k: v
            for k, v in row.items()
            if k not in mapped_set and k != "geometry" and not pd.isna(v)
        }

        return CrimeRecord(
            nro_sumario=_s(get("nro_sumario")),
            fecha=parse_date(get("fecha")),
            hora=parse_time(get("hora")),
            delito=_s(get("delito")).upper(),
            modus_operandi=_s(get("modus_operandi")).upper(),
            ambito=_s(get("ambito")).upper(),
            movilidad=_s(get("movilidad")).upper(),
            arma_medio=_s(get("arma_medio")).upper(),
            esclarecido=_s(get("esclarecido")).upper(),
            situacion_causante=_s(get("situacion_causante")).upper(),
            direccion=_s(get("direccion")),
            jurisdiccion=_s(get("jurisdiccion")).upper(),
            dependencia=_s(get("dependencia")).upper(),
            barrio=_s(get("barrio")),
            detalle_lugar=_s(get("detalle_lugar")),
            elemento_sustraido=_s(get("elemento_sustraido")),
            detalle_arma=_s(get("detalle_arma")),
            descripcion_vehiculo=_s(get("descripcion_vehiculo")),
            resena_hecho=_s(get("resena_hecho")),
            resolucion_hecho=_s(get("resolucion_hecho")),
            nombre_victima=_s(get("nombre_victima")),
            sexo_victima=_s(get("sexo_victima")).upper(),
            edad_victima=_s(get("edad_victima")),
            dni_victima=_s(get("dni_victima")),
            direccion_victima=_s(get("direccion_victima")),
            nombre_causante=_s(get("nombre_causante")),
            sexo_causante=_s(get("sexo_causante")).upper(),
            edad_causante=_s(get("edad_causante")),
            dni_causante=_s(get("dni_causante")),
            direccion_causante=_s(get("direccion_causante")),
            descripcion_causante=_s(get("descripcion_causante")),
            mes=_s(get("mes")),
            coordenadas=coords,
            geometry=row.geometry if hasattr(row, "geometry") else None,
            campos_extra=campos_extra,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # LECTURA DE MENCIONADOS
    # ═══════════════════════════════════════════════════════════════════════

    def read_mencionados(self, path: Path) -> List[MentionedPerson]:
        """Lee registros de personas mencionadas."""
        import pandas as pd

        df = self._read_dataframe(path)
        fields = [c for c in df.columns if c != "geometry"]
        field_map = self.field_mapper.build_field_map("mencionados", fields)

        records: List[MentionedPerson] = []
        for idx, row in df.iterrows():
            try:
                records.append(self._row_to_mentioned(row, field_map, pd))
            except Exception as e:
                logger.warning(f"Error procesando fila {idx} (mencionados): {e}")

        logger.info(f"Leídos {len(records)} mencionados desde {path.name}")
        return records

    def _row_to_mentioned(
        self,
        row: Any,
        field_map: Dict[str, Optional[str]],
        pd: Any,
    ) -> MentionedPerson:
        def get(field: str) -> Any:
            src = field_map.get(field)
            if src and src in row.index:
                val = row[src]
                return None if pd.isna(val) else val
            return None

        return MentionedPerson(
            alias=_s(get("alias")),
            nombre=_s(get("nombre")),
            datos_filiatorios=_s(get("descripcion")),
            delito=_s(get("delito")).upper(),
            fecha=parse_date(get("fecha")),
            hora=parse_time(get("hora")),
            direccion_hecho=_s(get("direccion")),
            nro_sumario=_s(get("nro_sumario")),
        )

    # ═══════════════════════════════════════════════════════════════════════
    # LECTURA DE APREHENDIDOS
    # ═══════════════════════════════════════════════════════════════════════

    def read_aprehendidos(self, path: Path) -> List[Apprehended]:
        """Lee registros de aprehendidos."""
        import pandas as pd

        df = self._read_dataframe(path)
        fields = [c for c in df.columns if c != "geometry"]
        field_map = self.field_mapper.build_field_map("aprehendidos", fields)

        records: List[Apprehended] = []
        for idx, row in df.iterrows():
            try:
                records.append(self._row_to_apprehended(row, field_map, pd))
            except Exception as e:
                logger.warning(f"Error procesando fila {idx} (aprehendidos): {e}")

        logger.info(f"Leídos {len(records)} aprehendidos desde {path.name}")
        return records

    def _row_to_apprehended(
        self,
        row: Any,
        field_map: Dict[str, Optional[str]],
        pd: Any,
    ) -> Apprehended:
        def get(field: str) -> Any:
            src = field_map.get(field)
            if src and src in row.index:
                val = row[src]
                return None if pd.isna(val) else val
            return None

        edad_val = get("edad")
        edad: Optional[int] = None
        if edad_val is not None:
            try:
                edad = int(float(edad_val))
            except (ValueError, TypeError):
                pass

        return Apprehended(
            nombre=_s(get("nombre")),
            edad=edad,
            sexo=_s(get("sexo")).upper(),
            clasificacion_raw=_s(get("situacion")).upper(),
            delito=_s(get("delito")).upper(),
            fecha=parse_date(get("fecha_aprehension")),
            direccion=_s(get("direccion")),
            descripcion=_s(get("descripcion")),
            nro_sumario=_s(get("nro_sumario")),
        )


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════


def _s(val: Any) -> str:
    """Convierte a string limpio, None → ""."""
    if val is None:
        return ""
    return str(val).strip()
