"""
Tests unitarios para la capa de infraestructura: parse_utils y readers.
"""
from __future__ import annotations

import math
from datetime import date, time, datetime
from typing import Optional, Tuple

import pytest

from sidic.infrastructure.readers.parse_utils import (
    parse_date,
    parse_time,
    extract_coordinates,
    format_coordinates,
    calculate_distance,
    validate_coordinates,
)


# ═════════════════════════════════════════════════════════════════════════════
# parse_date
# ═════════════════════════════════════════════════════════════════════════════


class TestParseDate:
    def test_dd_mm_yyyy_slash(self):
        assert parse_date("15/03/2024") == date(2024, 3, 15)

    def test_dd_mm_yyyy_dash(self):
        assert parse_date("15-03-2024") == date(2024, 3, 15)

    def test_yyyy_mm_dd_dash(self):
        assert parse_date("2024-03-15") == date(2024, 3, 15)

    def test_yyyy_mm_dd_slash(self):
        assert parse_date("2024/03/15") == date(2024, 3, 15)

    def test_dd_mm_yy(self):
        assert parse_date("15/03/24") == date(2024, 3, 15)

    def test_from_datetime(self):
        dt = datetime(2024, 3, 15, 10, 30)
        assert parse_date(dt) == date(2024, 3, 15)

    def test_from_date(self):
        d = date(2024, 3, 15)
        assert parse_date(d) is d

    def test_none(self):
        assert parse_date(None) is None

    def test_empty_string(self):
        assert parse_date("") is None

    def test_invalid_string(self):
        assert parse_date("no_es_fecha") is None

    def test_int_value(self):
        assert parse_date(12345) is None

    def test_whitespace(self):
        assert parse_date("  15/03/2024  ") == date(2024, 3, 15)


# ═════════════════════════════════════════════════════════════════════════════
# parse_time
# ═════════════════════════════════════════════════════════════════════════════


class TestParseTime:
    def test_hh_mm(self):
        assert parse_time("14:30") == time(14, 30)

    def test_hh_mm_ss(self):
        assert parse_time("14:30:45") == time(14, 30, 45)

    def test_dot_separator(self):
        assert parse_time("14.30") == time(14, 30)

    def test_short_hour(self):
        assert parse_time("9:05") == time(9, 5)

    def test_from_datetime(self):
        dt = datetime(2024, 1, 1, 10, 30)
        assert parse_time(dt) == time(10, 30)

    def test_from_time(self):
        t = time(10, 30)
        assert parse_time(t) is t

    def test_none(self):
        assert parse_time(None) is None

    def test_empty_string(self):
        assert parse_time("") is None

    def test_invalid_string(self):
        assert parse_time("no_es_hora") is None


# ═════════════════════════════════════════════════════════════════════════════
# extract_coordinates
# ═════════════════════════════════════════════════════════════════════════════


class TestExtractCoordinates:
    def test_tuple(self):
        assert extract_coordinates((-65.92, -26.59)) == (-65.92, -26.59)

    def test_list(self):
        assert extract_coordinates([-65.92, -26.59]) == (-65.92, -26.59)

    def test_dict_xy(self):
        assert extract_coordinates({"x": -65.92, "y": -26.59}) == (-65.92, -26.59)

    def test_dict_lon_lat(self):
        assert extract_coordinates({"lon": -65.92, "lat": -26.59}) == (-65.92, -26.59)

    def test_dict_longitude_latitude(self):
        result = extract_coordinates({"longitude": -65.92, "latitude": -26.59})
        assert result == (-65.92, -26.59)

    def test_none(self):
        assert extract_coordinates(None) is None

    def test_invalid(self):
        assert extract_coordinates("invalid") is None

    def test_short_tuple(self):
        assert extract_coordinates((1,)) is None

    def test_shapely_like(self):
        """Simula un objeto shapely Point sin importar shapely."""
        class FakePoint:
            x = -65.92
            y = -26.59
        assert extract_coordinates(FakePoint()) == (-65.92, -26.59)


# ═════════════════════════════════════════════════════════════════════════════
# format_coordinates
# ═════════════════════════════════════════════════════════════════════════════


class TestFormatCoordinates:
    def test_default_precision(self):
        result = format_coordinates(-65.92, -26.59)
        assert "-26.590000" in result
        assert "-65.920000" in result

    def test_custom_precision(self):
        result = format_coordinates(-65.92, -26.59, precision=2)
        assert "-26.59" in result


# ═════════════════════════════════════════════════════════════════════════════
# calculate_distance
# ═════════════════════════════════════════════════════════════════════════════


class TestCalculateDistance:
    def test_same_point(self):
        d = calculate_distance((-65.92, -26.59), (-65.92, -26.59))
        assert d == pytest.approx(0, abs=0.01)

    def test_known_distance(self):
        # Buenos Aires → Tucumán ≈ ~1100 km
        ba = (-58.3816, -34.6037)
        tuc = (-65.2226, -26.8083)
        d = calculate_distance(ba, tuc)
        # Tolerancia amplia
        assert 1_000_000 < d < 1_300_000


# ═════════════════════════════════════════════════════════════════════════════
# validate_coordinates
# ═════════════════════════════════════════════════════════════════════════════


class TestValidateCoordinates:
    def test_valid(self):
        assert validate_coordinates(-65.92, -26.59) is True
        assert validate_coordinates(0, 0) is True
        assert validate_coordinates(180, 90) is True
        assert validate_coordinates(-180, -90) is True

    def test_invalid_lon(self):
        assert validate_coordinates(181, 0) is False
        assert validate_coordinates(-181, 0) is False

    def test_invalid_lat(self):
        assert validate_coordinates(0, 91) is False
        assert validate_coordinates(0, -91) is False
