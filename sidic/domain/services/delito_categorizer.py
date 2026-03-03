"""
Servicio de categorización de delitos.

Versión v2.0 — Las reglas de categorización se cargan desde configuración JSON,
no están hardcodeadas en el código. Esto permite que cada comisaría defina
sus propios tipos de delito sin modificar código fuente.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from sidic.domain.enums import CategoriaDelito
from sidic.domain.models.crime_record import CrimeRecord
from sidic.domain.models.simbolo_delito import SimboloDelito

logger = logging.getLogger(__name__)


class DelitoCategorizer:
    """
    Clasifica delitos en categorías usando reglas configurables.

    Las reglas se cargan desde un JSON de configuración y determinan
    a qué categoría pertenece cada delito según su nombre.
    """

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        """
        Args:
            config: Configuración con claves:
                - categorias: {ROBOS: [...], HURTOS: [...], ...}
                - robo_agravado: [lista de patrones]
                - simbolos: {nombre: {simbolo, color, descripcion, relleno}}
        """
        self._categorias: Dict[CategoriaDelito, List[str]] = {}
        self._robo_agravado: Set[str] = set()
        self._simbolos: Dict[str, SimboloDelito] = {}
        self._aliases: Dict[str, str] = {}

        if config:
            self._load_config(config)
        else:
            self._load_defaults()

    def _load_config(self, config: Dict[str, Any]) -> None:
        """Carga reglas desde configuración JSON."""
        cat_map = {
            "ROBOS": CategoriaDelito.ROBO,
            "TENTATIVA_ROBOS": CategoriaDelito.TENTATIVA_ROBO,
            "TENTATIVA DE ROBOS": CategoriaDelito.TENTATIVA_ROBO,
            "HURTOS": CategoriaDelito.HURTO,
            "TENTATIVA_HURTOS": CategoriaDelito.TENTATIVA_HURTO,
            "TENTATIVA DE HURTOS": CategoriaDelito.TENTATIVA_HURTO,
            "ESTAFAS": CategoriaDelito.ESTAFA,
        }

        categorias = config.get("categorias", {})
        for nombre_cat, patrones in categorias.items():
            cat_enum = cat_map.get(nombre_cat.upper())
            if cat_enum:
                self._categorias[cat_enum] = [p.upper() for p in patrones]

        self._robo_agravado = set(
            p.upper() for p in config.get("robo_agravado", [])
        )

        simbolos_raw = config.get("simbolos", {})
        for nombre, datos in simbolos_raw.items():
            self._simbolos[nombre.upper()] = SimboloDelito(
                simbolo=datos.get("simbolo", "?"),
                color=datos.get("color", "#000000"),
                descripcion=datos.get("descripcion", nombre),
                relleno=datos.get("relleno", True),
            )

        self._aliases = {
            k.upper(): v.upper() for k, v in config.get("aliases", {}).items()
        }

    def _load_defaults(self) -> None:
        """Carga reglas por defecto (fallback sin configuración)."""
        self._categorias = {
            CategoriaDelito.ROBO: [
                "ROBO AGRAVADO ASALTANTE",
                "ROBO AGRAVADO ASALTANTE EN BANDA",
                "ROBO AGRAVADO DE MOTOVEHICULO",
                "ROBO AGRAVADO PIRAÑA DE MOTOVEHICULO",
                "ROBO AGRAVADO DE AUTOMOTOR",
                "ROBO AGRAVADO ENTRADERA",
                "ROBO AGRAVADO ARIETE",
                "ROBO PIRAÑA DE MOTOVEHICULOS",
                "ROBO PIRAÑA",
                "ROBO ARREBATO",
                "ROBO CLAVERO DE AUTOS",
                "ROBO DE MOTOVEHICULOS",
                "ROBO DE AUTOMOTOR",
                "ROBO ESCRUCHE",
                "ROBO BOQUETERO",
                "ROBO ROMPE VIDRIO",
                "ROBO OPORTUNISTA",
            ],
            CategoriaDelito.TENTATIVA_ROBO: [
                "TENTATIVA DE ROBO AGRAVADO ASALTANTE",
                "TENTATIVA DE ROBO AGRAVADO ASALTANTE EN BANDA",
                "TENTATIVA DE ROBO AGRAVADO DE MOTOVEHICULO",
                "TENTATIVA DE ROBO AGRAVADO PIRAÑA DE MOTOVEHICULO",
                "TENTATIVA DE ROBO AGRAVADO DE AUTOMOTOR",
                "TENTATIVA DE ROBO AGRAVADO ENTRADERA",
                "TENTATIVA DE ROBO AGRAVADO ARIETE",
                "TENTATIVA DE ROBO PIRAÑA DE MOTOVEHICULOS",
                "TENTATIVA DE ROBO PIRAÑA",
                "TENTATIVA DE ROBO ARREBATO",
                "TENTATIVA DE ROBO CLAVERO DE AUTOS",
                "TENTATIVA DE ROBO DE MOTOVEHICULOS",
                "TENTATIVA DE ROBO DE AUTOMOTOR",
                "TENTATIVA DE ROBO ESCRUCHE",
                "TENTATIVA DE ROBO BOQUETERO",
                "TENTATIVA DE ROBO ROMPE VIDRIO",
                "TENTATIVA DE ROBO OPORTUNISTA",
            ],
            CategoriaDelito.HURTO: [
                "HURTO PUNGA",
                "HURTO MECHERA",
                "HURTO OPORTUNISTA",
                "HURTO DE MOTOVEHICULO",
                "HURTO DE AUTOMOTOR",
                "HURTO INHIBIDOR DE ALARMAS",
                "HURTO ESCALAMIENTO",
                "HURTO VIUDA NEGRA",
            ],
            CategoriaDelito.TENTATIVA_HURTO: [
                "TENTATIVA DE HURTO PUNGA",
                "TENTATIVA DE HURTO MECHERA",
                "TENTATIVA DE HURTO OPORTUNISTA",
                "TENTATIVA DE HURTO DE MOTOVEHICULO",
                "TENTATIVA DE HURTO DE AUTOMOTOR",
                "TENTATIVA DE HURTO INHIBIDOR DE ALARMAS",
                "TENTATIVA DE HURTO ESCALAMIENTO",
                "TENTATIVA DE HURTO VIUDA NEGRA",
            ],
            CategoriaDelito.ESTAFA: [
                "ESTAFA CUENTO DEL TIO",
                "TENTATIVA DE ESTAFA CUENTO DEL TIO",
            ],
        }

        self._robo_agravado = {
            "ROBO AGRAVADO ASALTANTE",
            "ROBO AGRAVADO ASALTANTE EN BANDA",
            "ROBO AGRAVADO DE MOTOVEHICULO",
            "ROBO AGRAVADO PIRAÑA DE MOTOVEHICULO",
            "ROBO AGRAVADO DE AUTOMOTOR",
            "ROBO AGRAVADO ENTRADERA",
            "ROBO AGRAVADO ARIETE",
        }

    # ═════════════════════════════════════════════════════════════════════
    # CLASIFICACIÓN
    # ═════════════════════════════════════════════════════════════════════

    def categorizar(self, nombre_delito: str) -> CategoriaDelito:
        """
        Determina la categoría de un delito por su nombre.

        1. Busca coincidencia exacta en las listas de cada categoría.
        2. Busca coincidencia parcial (el patrón está contenido en el nombre).
        3. Aplica fallback por palabras clave genéricas.
        """
        if not nombre_delito:
            return CategoriaDelito.OTROS

        normalizado = nombre_delito.upper().strip()

        # Resolver alias
        if normalizado in self._aliases:
            normalizado = self._aliases[normalizado]

        # 1. Coincidencia exacta
        for cat, patrones in self._categorias.items():
            if normalizado in patrones:
                return cat

        # 2. Coincidencia parcial
        for cat, patrones in self._categorias.items():
            for patron in patrones:
                if patron in normalizado or normalizado in patron:
                    return cat

        # 3. Fallback por palabra clave
        es_tentativa = "TENTATIVA" in normalizado
        if "ESTAFA" in normalizado:
            return CategoriaDelito.ESTAFA
        if "ROBO" in normalizado:
            return CategoriaDelito.TENTATIVA_ROBO if es_tentativa else CategoriaDelito.ROBO
        if "HURTO" in normalizado:
            return CategoriaDelito.TENTATIVA_HURTO if es_tentativa else CategoriaDelito.HURTO

        return CategoriaDelito.OTROS

    def es_robo_agravado(self, nombre_delito: str) -> bool:
        """Determina si un delito es robo agravado."""
        normalizado = nombre_delito.upper().strip()
        if normalizado in self._robo_agravado:
            return True
        return any(p in normalizado for p in self._robo_agravado)

    def get_simbolo(self, nombre_delito: str) -> Optional[SimboloDelito]:
        """Obtiene el símbolo visual para un tipo de delito."""
        normalizado = nombre_delito.upper().strip()

        # Búsqueda exacta
        if normalizado in self._simbolos:
            return self._simbolos[normalizado]

        # Búsqueda con guiones bajos → espacios
        alternativo = normalizado.replace("_", " ")
        if alternativo in self._simbolos:
            return self._simbolos[alternativo]

        # Búsqueda parcial
        for nombre, simbolo in self._simbolos.items():
            if nombre in normalizado or normalizado in nombre:
                return simbolo

        return None

    # ═════════════════════════════════════════════════════════════════════
    # APLICACIÓN MASIVA
    # ═════════════════════════════════════════════════════════════════════

    def categorizar_registros(self, registros: List[CrimeRecord]) -> None:
        """
        Asigna categoría y flag de robo agravado a una lista de CrimeRecord.

        Modifica los registros in-place.
        """
        for registro in registros:
            nombre = registro.delito_con_modalidad or registro.delito
            registro.categoria = self.categorizar(nombre)
            registro.es_robo_agravado = self.es_robo_agravado(nombre)

        logger.info(
            f"Categorizados {len(registros)} registros: "
            + ", ".join(
                f"{cat.value}={sum(1 for r in registros if r.categoria == cat)}"
                for cat in CategoriaDelito
                if any(r.categoria == cat for r in registros)
            )
        )
