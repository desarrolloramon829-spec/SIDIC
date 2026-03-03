"""
Símbolo visual para un tipo de delito en cuadros de referencia.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimboloDelito:
    """Símbolo visual para representar un tipo de delito en mapas."""

    simbolo: str
    color: str
    descripcion: str
    relleno: bool = True

    @property
    def hex_color(self) -> str:
        """Color en formato hex (#RRGGBB)."""
        return self.color if self.color.startswith("#") else f"#{self.color}"
