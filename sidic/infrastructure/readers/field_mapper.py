"""
Mapeador de campos configurable v2.0.

Lee configuración de mapeo desde `defaults.json` o desde un JSON de usuario,
y auto-detecta campos del archivo GIS según múltiples posibles nombres.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from sidic.config.loader import get_section

logger = logging.getLogger(__name__)


class FieldMapper:
    """
    Mapea campos de archivos GIS a campos internos del modelo de dominio.

    Soporta:
    - Múltiples posibles nombres para cada campo (aliases).
    - Coincidencia case-insensitive.
    - Campos requeridos y opcionales.
    - Caché para rendimiento.
    """

    def __init__(self, mapping: Optional[Dict[str, Any]] = None) -> None:
        """
        Args:
            mapping: Diccionario de mapeo personalizado.
                     Si es None, carga desde defaults.json.
        """
        if mapping is not None:
            self._mapping = mapping
        else:
            raw = get_section("field_mappings")
            # Si viene en formato extendido (con source_fields), extraer
            self._mapping = self._normalize_mapping(raw)

        self._cache: Dict[str, Optional[str]] = {}

    @classmethod
    def from_file(cls, path: Path) -> "FieldMapper":
        """Carga mapeo desde un archivo JSON."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
            raw = config.get("mappings", config.get("field_mappings", config))
            return cls(cls._normalize_mapping_static(raw))
        except Exception as e:
            logger.warning(f"Error cargando mapeo desde {path}: {e}. Usando defaults.")
            return cls()

    def save_to_file(self, path: Path) -> bool:
        """Guarda el mapeo actual a archivo JSON."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._mapping, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error guardando mapeo: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════
    # DETECCIÓN DE CAMPOS
    # ═══════════════════════════════════════════════════════════════════════

    def detect_field(
        self,
        entity_type: str,
        internal_field: str,
        available_fields: List[str],
    ) -> Optional[str]:
        """
        Detecta qué campo del archivo corresponde a un campo interno.

        Args:
            entity_type: 'hechos', 'mencionados', 'aprehendidos'
            internal_field: Ej: 'fecha', 'delito'
            available_fields: Campos disponibles en el archivo GIS

        Returns:
            Nombre del campo en el archivo, o None.
        """
        cache_key = f"{entity_type}:{internal_field}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached is None or cached in available_fields:
                return cached

        if entity_type not in self._mapping:
            return None

        possible_names = self._mapping[entity_type].get(internal_field)
        if not possible_names:
            return None

        # Lookup case-insensitive
        avail_upper = {f.upper().strip(): f for f in available_fields}

        for name in possible_names:
            upper = name.upper().strip()
            if upper in avail_upper:
                result = avail_upper[upper]
                self._cache[cache_key] = result
                return result

        self._cache[cache_key] = None
        return None

    def build_field_map(
        self,
        entity_type: str,
        available_fields: List[str],
    ) -> Dict[str, Optional[str]]:
        """
        Construye mapeo completo {campo_interno: campo_archivo o None}.
        """
        if entity_type not in self._mapping:
            return {}
        return {
            internal: self.detect_field(entity_type, internal, available_fields)
            for internal in self._mapping[entity_type]
        }

    def detect_mapping(
        self,
        field_names: List[str],
        entity_type: str,
    ) -> Dict[str, str]:
        """
        Auto-detecta mapeo, retornando solo los campos encontrados.
        Satisface el Protocol FieldMapper de dominio.
        """
        full = self.build_field_map(entity_type, field_names)
        return {k: v for k, v in full.items() if v is not None}

    def map_row(
        self,
        raw_row: Dict[str, Any],
        entity_type: str,
    ) -> Dict[str, Any]:
        """
        Mapea una fila cruda a campos normalizados.
        Satisface el Protocol FieldMapper de dominio.
        """
        available = list(raw_row.keys())
        field_map = self.build_field_map(entity_type, available)

        result: Dict[str, Any] = {}
        for internal, source in field_map.items():
            if source is not None and source in raw_row:
                result[internal] = raw_row[source]
        return result

    def get_required_fields(self, entity_type: str) -> List[str]:
        """Retorna campos requeridos según config. Fallback: fecha, delito."""
        # En defaults.json los required están anotados pero aquí simplificamos
        if entity_type not in self._mapping:
            return []
        return list(self._mapping[entity_type].keys())

    def validate_mapping(
        self,
        entity_type: str,
        available_fields: List[str],
    ) -> Dict[str, Any]:
        """
        Valida el mapeo y reporta campos encontrados/faltantes.
        """
        field_map = self.build_field_map(entity_type, available_fields)
        found = {k: v for k, v in field_map.items() if v is not None}
        missing = [k for k, v in field_map.items() if v is None]
        mapped_set = set(found.values())
        extra = [f for f in available_fields if f not in mapped_set and f != "geometry"]
        critical = ["fecha", "delito"]
        critical_missing = [c for c in critical if c in missing]

        return {
            "found": found,
            "missing": missing,
            "extra": extra,
            "critical_missing": critical_missing,
            "valid": len(critical_missing) == 0,
        }

    def add_alias(self, entity_type: str, internal_field: str, alias: str) -> None:
        """Agrega un alias adicional para un campo."""
        if entity_type not in self._mapping:
            self._mapping[entity_type] = {}
        if internal_field not in self._mapping[entity_type]:
            self._mapping[entity_type][internal_field] = []
        if alias not in self._mapping[entity_type][internal_field]:
            self._mapping[entity_type][internal_field].append(alias)
        # Invalidar cache
        cache_key = f"{entity_type}:{internal_field}"
        self._cache.pop(cache_key, None)

    # ═══════════════════════════════════════════════════════════════════════
    # NORMALIZACIÓN INTERNA
    # ═══════════════════════════════════════════════════════════════════════

    def _normalize_mapping(self, raw: Dict[str, Any]) -> Dict[str, Dict[str, List[str]]]:
        return self._normalize_mapping_static(raw)

    @staticmethod
    def _normalize_mapping_static(raw: Dict[str, Any]) -> Dict[str, Dict[str, List[str]]]:
        """
        Normaliza formato extendido (con source_fields/type/required)
        a formato simple {entity: {campo: [aliases]}}.
        """
        result: Dict[str, Dict[str, List[str]]] = {}
        for entity_type, fields in raw.items():
            if not isinstance(fields, dict):
                continue
            result[entity_type] = {}
            for field_name, field_config in fields.items():
                if isinstance(field_config, dict) and "source_fields" in field_config:
                    result[entity_type][field_name] = field_config["source_fields"]
                elif isinstance(field_config, list):
                    result[entity_type][field_name] = field_config
        return result
