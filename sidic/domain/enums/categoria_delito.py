"""
Enums de categorías de delitos del sistema S.I.D.I.C.
"""
from enum import Enum


class CategoriaDelito(Enum):
    """Categorías principales de delitos para agrupación en reportes."""

    ROBO = "ROBOS"
    TENTATIVA_ROBO = "TENTATIVA DE ROBOS"
    HURTO = "HURTOS"
    TENTATIVA_HURTO = "TENTATIVA DE HURTOS"
    ESTAFA = "ESTAFAS"
    OTROS = "OTROS DELITOS"

    @property
    def es_tentativa(self) -> bool:
        return self in (
            CategoriaDelito.TENTATIVA_ROBO,
            CategoriaDelito.TENTATIVA_HURTO,
        )

    @property
    def categoria_base(self) -> "CategoriaDelito":
        """Retorna la categoría consumada correspondiente."""
        mapping = {
            CategoriaDelito.TENTATIVA_ROBO: CategoriaDelito.ROBO,
            CategoriaDelito.TENTATIVA_HURTO: CategoriaDelito.HURTO,
        }
        return mapping.get(self, self)

    @property
    def orden(self) -> int:
        """Orden de prioridad para visualización en reportes."""
        orden_map = {
            CategoriaDelito.ROBO: 0,
            CategoriaDelito.TENTATIVA_ROBO: 1,
            CategoriaDelito.HURTO: 2,
            CategoriaDelito.TENTATIVA_HURTO: 3,
            CategoriaDelito.ESTAFA: 4,
            CategoriaDelito.OTROS: 5,
        }
        return orden_map.get(self, 99)

    @property
    def grupo_filtrado(self) -> str:
        """Nombre del grupo para los checkboxes de filtrado en la UI.
        
        Agrupa consumados y tentativas bajo un mismo grupo.
        """
        grupo_map = {
            CategoriaDelito.ROBO: "ROBOS",
            CategoriaDelito.TENTATIVA_ROBO: "ROBOS",
            CategoriaDelito.HURTO: "HURTOS",
            CategoriaDelito.TENTATIVA_HURTO: "HURTOS",
            CategoriaDelito.ESTAFA: "ESTAFAS",
            CategoriaDelito.OTROS: "OTROS",
        }
        return grupo_map.get(self, "OTROS")
