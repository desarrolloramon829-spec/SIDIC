"""
Lector de Shapefiles (.shp) y formatos de geopandas.

Soporta: Shapefile (.shp), GeoJSON (.geojson), GeoPackage (.gpkg),
KML (.kml), y CSV (.csv) con coordenadas.
Maneja múltiples encodings y detección automática con chardet.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional

from sidic.infrastructure.readers.base_reader import BaseGISReader, GISReaderError

logger = logging.getLogger(__name__)

# Encodings de fallback ordenados por frecuencia en archivos argentinos
_FALLBACK_ENCODINGS = ["utf-8", "latin-1", "cp1252", "iso-8859-1", "ascii"]


class ShapefileReader(BaseGISReader):
    """
    Lector multi-formato GIS basado en geopandas/fiona.

    Detección automática de encoding con chardet (opcionalmente)
    y fallback multi-encoding para archivos QGIS de policías
    argentinas con tildes y caracteres especiales.
    """

    @property
    def supported_extensions(self) -> List[str]:
        return [".shp", ".geojson", ".gpkg", ".kml", ".json"]

    def _read_dataframe(self, path: Path) -> Any:
        """Lee con geopandas intentando múltiples encodings."""
        import geopandas as gpd  # lazy import

        path = Path(path)
        if not path.exists():
            raise GISReaderError(f"Archivo no encontrado: {path}")

        suffix = path.suffix.lower()

        # GeoPackage / GeoJSON / KML no necesitan encoding explícito
        if suffix in (".gpkg", ".geojson", ".json", ".kml"):
            try:
                return self._read_with_driver(gpd, path, suffix)
            except Exception as e:
                raise GISReaderError(
                    f"No se pudo leer {path.name}: {e}"
                ) from e

        # Shapefile: probar encodings
        detected_enc = self._detect_encoding(path)
        encodings_to_try = self._build_encoding_list(detected_enc)

        last_error: Optional[Exception] = None
        for enc in encodings_to_try:
            try:
                df = gpd.read_file(str(path), encoding=enc)
                logger.info(f"Leído {path.name} con encoding {enc}")
                return df
            except (UnicodeDecodeError, UnicodeError):
                logger.debug(f"Encoding {enc} falló para {path.name}")
                last_error = None
                continue
            except Exception as e:
                last_error = e
                break

        if last_error:
            raise GISReaderError(
                f"Error al leer {path.name}: {last_error}"
            ) from last_error

        raise GISReaderError(
            f"No se pudo leer {path.name} con ningún encoding: "
            f"{', '.join(encodings_to_try)}"
        )

    @staticmethod
    def _read_with_driver(gpd: Any, path: Path, suffix: str) -> Any:
        """Lee formatos que no requieren encoding explícito."""
        kwargs = {}
        if suffix == ".kml":
            kwargs["driver"] = "KML"
        return gpd.read_file(str(path), **kwargs)

    @staticmethod
    def _detect_encoding(path: Path) -> Optional[str]:
        """Intenta detectar encoding de los archivos asociados al .shp."""
        try:
            import chardet
        except ImportError:
            return None

        # Verificar .cpg (archivo de encoding ESRI)
        cpg_path = path.with_suffix(".cpg")
        if cpg_path.exists():
            try:
                content = cpg_path.read_text(encoding="ascii").strip()
                if content:
                    logger.debug(f"Encoding de .cpg: {content}")
                    return content
            except Exception:
                pass

        # Si no hay .cpg, muestrear .dbf para detección con chardet
        dbf_path = path.with_suffix(".dbf")
        target = dbf_path if dbf_path.exists() else path
        try:
            with open(target, "rb") as f:
                raw = f.read(min(100_000, target.stat().st_size))
            result = chardet.detect(raw)
            if result and result.get("confidence", 0) >= 0.7:
                enc = result["encoding"]
                logger.debug(
                    f"chardet detectó {enc} "
                    f"(confianza={result['confidence']:.0%})"
                )
                return enc
        except Exception:
            pass

        return None

    @staticmethod
    def _build_encoding_list(detected: Optional[str]) -> List[str]:
        """Construye lista de encodings a probar, priorizando el detectado."""
        result: List[str] = []
        if detected:
            result.append(detected.lower())
        for enc in _FALLBACK_ENCODINGS:
            if enc not in result:
                result.append(enc)
        return result

    def validate_shapefile(self, path: Path) -> dict:
        """
        Valida un archivo y retorna diagnóstico rápido.

        Returns:
            dict con keys: valid, features, fields, encoding, errors, warnings
        """
        result = {
            "valid": False,
            "features": 0,
            "fields": [],
            "encoding": None,
            "errors": [],
            "warnings": [],
        }

        path = Path(path)
        if not path.exists():
            result["errors"].append(f"Archivo no encontrado: {path}")
            return result

        # Verificar archivos complementarios para Shapefile
        if path.suffix.lower() == ".shp":
            for ext in (".dbf", ".shx"):
                companion = path.with_suffix(ext)
                if not companion.exists():
                    result["errors"].append(
                        f"Falta archivo complementario: {companion.name}"
                    )
            prj = path.with_suffix(".prj")
            if not prj.exists():
                result["warnings"].append(
                    f"Falta archivo de proyección: {prj.name}"
                )

        if result["errors"]:
            return result

        try:
            df = self._read_dataframe(path)
            result["valid"] = True
            result["features"] = len(df)
            result["fields"] = [
                c for c in df.columns if c != "geometry"
            ]
            if len(df) == 0:
                result["warnings"].append("El archivo no contiene registros")

        except GISReaderError as e:
            result["errors"].append(str(e))

        return result


class CSVReader(BaseGISReader):
    """
    Lector de archivos CSV con coordenadas opcionales.

    Lee CSV planos usando pandas y, si hay columnas de latitud/longitud,
    los interpreta como puntos geográficos.
    """

    LAT_CANDIDATES = ("lat", "latitud", "latitude", "y")
    LON_CANDIDATES = ("lon", "lng", "longitud", "longitude", "x")

    @property
    def supported_extensions(self) -> List[str]:
        return [".csv"]

    def _read_dataframe(self, path: Path) -> Any:
        import pandas as pd

        path = Path(path)
        if not path.exists():
            raise GISReaderError(f"Archivo no encontrado: {path}")

        detected_enc = self._detect_csv_encoding(path)
        encodings = [detected_enc] if detected_enc else []
        encodings.extend(
            e for e in _FALLBACK_ENCODINGS if e not in encodings
        )

        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(str(path), encoding=enc, dtype=str)
                logger.info(f"CSV leído con encoding {enc}")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                raise GISReaderError(
                    f"Error leyendo CSV {path.name}: {e}"
                ) from e

        if df is None:
            raise GISReaderError(
                f"No se pudo leer CSV {path.name} con ningún encoding"
            )

        # Intentar agregar geometry si hay columnas lat/lon
        df = self._add_geometry_if_possible(df)
        return df

    def _add_geometry_if_possible(self, df: Any) -> Any:
        """Agrega una columna geometry Point si hay lat/lon."""
        import pandas as pd

        cols_lower = {c.lower(): c for c in df.columns}

        lat_col = next(
            (cols_lower[k] for k in self.LAT_CANDIDATES if k in cols_lower),
            None,
        )
        lon_col = next(
            (cols_lower[k] for k in self.LON_CANDIDATES if k in cols_lower),
            None,
        )

        if lat_col and lon_col:
            try:
                import geopandas as gpd
                from shapely.geometry import Point

                df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
                df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
                geometry = [
                    Point(lng, lat)
                    if pd.notna(lat) and pd.notna(lng)
                    else None
                    for lat, lng in zip(df[lat_col], df[lon_col])
                ]
                gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
                logger.info("CSV convertido a GeoDataFrame con geometría")
                return gdf
            except ImportError:
                logger.debug("geopandas no disponible, CSV sin geometría")
            except Exception as e:
                logger.warning(f"No se pudo agregar geometría al CSV: {e}")

        return df

    @staticmethod
    def _detect_csv_encoding(path: Path) -> Optional[str]:
        """Detecta encoding de CSV con chardet."""
        try:
            import chardet

            with open(path, "rb") as f:
                raw = f.read(100_000)
            result = chardet.detect(raw)
            if result and result.get("confidence", 0) >= 0.7:
                return result["encoding"]
        except (ImportError, Exception):
            pass
        return None
