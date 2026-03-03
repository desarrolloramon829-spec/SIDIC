"""
Enum de franjas horarias para clasificación temporal de hechos delictivos.
"""
from enum import Enum


class FranjaHoraria(Enum):
    """Franjas horarias para clasificación de hechos.
    
    Cada valor contiene (nombre_display, hora_inicio, hora_fin, rango_texto).
    """

    MADRUGADA = ("MADRUGADA", 0, 4, "00:00 - 04:59")
    MANANA = ("MAÑANA", 5, 8, "05:00 - 08:59")
    VESPERTINA = ("VESPERTINA", 9, 12, "09:00 - 12:59")
    SIESTA = ("SIESTA", 13, 16, "13:00 - 16:59")
    TARDE = ("TARDE", 17, 19, "17:00 - 19:59")
    NOCHE = ("NOCHE", 20, 23, "20:00 - 23:59")

    def __init__(self, nombre: str, hora_inicio: int, hora_fin: int, rango: str):
        self.nombre = nombre
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.rango = rango

    @classmethod
    def from_hour(cls, hour: int) -> "FranjaHoraria":
        """Determina la franja horaria para una hora dada (0-23)."""
        if not 0 <= hour <= 23:
            raise ValueError(f"Hora fuera de rango: {hour}. Debe ser 0-23.")
        for franja in cls:
            if franja.hora_inicio <= hour <= franja.hora_fin:
                return franja
        return cls.MADRUGADA  # Fallback de seguridad

    @property
    def display_name(self) -> str:
        """Nombre completo con rango horario para mostrar en reportes."""
        return f"{self.nombre} ({self.rango})"

    @property
    def orden(self) -> int:
        """Orden cronológico para visualización."""
        orden_map = {
            FranjaHoraria.MADRUGADA: 0,
            FranjaHoraria.MANANA: 1,
            FranjaHoraria.VESPERTINA: 2,
            FranjaHoraria.SIESTA: 3,
            FranjaHoraria.TARDE: 4,
            FranjaHoraria.NOCHE: 5,
        }
        return orden_map.get(self, 0)
