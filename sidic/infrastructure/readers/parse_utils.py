"""
Utilidades de parseo de fechas, horas y geometría.

Versión v2.0 — Funciones puras sin dependencias de constantes hardcodeadas.
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime, time
from typing import Any, Optional, Tuple, Union


# ═════════════════════════════════════════════════════════════════════════════
# FECHAS
# ═════════════════════════════════════════════════════════════════════════════


def parse_date(value: Union[str, datetime, date, None]) -> Optional[date]:
    """
    Convierte un valor a objeto date.

    Soporta formatos: dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd, yyyy/mm/dd,
    datetime, date.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    if isinstance(value, (int, float)):
        return None

    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%y",
        "%d-%m-%y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    # Fallback: regex
    match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", value)
    if match:
        day, month, year = match.groups()
        if len(year) == 2:
            year = ("20" + year) if int(year) < 50 else ("19" + year)
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            pass

    return None


def parse_time(value: Union[str, datetime, time, None]) -> Optional[time]:
    """
    Convierte un valor a objeto time.

    Soporta formatos: HH:MM, HH:MM:SS, HH.MM, H:MM
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value

    if not isinstance(value, str):
        return None

    value = value.strip().replace(".", ":")
    if not value:
        return None

    formats = ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue

    # Fallback: regex
    match = re.match(r"(\d{1,2}):(\d{2})", value)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        if 0 <= h <= 23 and 0 <= m <= 59:
            return time(h, m)

    return None


# ═════════════════════════════════════════════════════════════════════════════
# GEOMETRÍA
# ═════════════════════════════════════════════════════════════════════════════


def extract_coordinates(geometry: Any) -> Optional[Tuple[float, float]]:
    """
    Extrae coordenadas (lon, lat) de un objeto geometría.

    Soporta shapely Point, tuple/list [x, y], dict {x, y | lon, lat}.
    """
    if geometry is None:
        return None

    # shapely Point
    if hasattr(geometry, "x") and hasattr(geometry, "y"):
        return (geometry.x, geometry.y)

    if isinstance(geometry, (tuple, list)) and len(geometry) >= 2:
        try:
            return (float(geometry[0]), float(geometry[1]))
        except (ValueError, TypeError):
            return None

    if isinstance(geometry, dict):
        for xk, yk in [("x", "y"), ("lon", "lat"), ("longitude", "latitude")]:
            if xk in geometry and yk in geometry:
                try:
                    return (float(geometry[xk]), float(geometry[yk]))
                except (ValueError, TypeError):
                    return None

    return None


def format_coordinates(lon: float, lat: float, precision: int = 6) -> str:
    """Formatea coordenadas para display."""
    return f"{lat:.{precision}f}, {lon:.{precision}f}"


def calculate_distance(
    point1: Tuple[float, float],
    point2: Tuple[float, float],
) -> float:
    """Distancia en metros entre dos puntos (lon, lat) usando Haversine."""
    R = 6_371_000  # Radio de la Tierra en metros
    lon1, lat1 = math.radians(point1[0]), math.radians(point1[1])
    lon2, lat2 = math.radians(point2[0]), math.radians(point2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def validate_coordinates(lon: float, lat: float) -> bool:
    """Valida que las coordenadas estén en rangos válidos."""
    return -180 <= lon <= 180 and -90 <= lat <= 90
