"""
Enum de días de la semana con orden y localización en español.
"""
from enum import Enum


class DiaSemana(Enum):
    """Días de la semana en español, con correspondencia a Python weekday()."""

    LUNES = (0, "LUNES")
    MARTES = (1, "MARTES")
    MIERCOLES = (2, "MIÉRCOLES")
    JUEVES = (3, "JUEVES")
    VIERNES = (4, "VIERNES")
    SABADO = (5, "SÁBADO")
    DOMINGO = (6, "DOMINGO")

    def __init__(self, weekday: int, nombre: str):
        self.weekday = weekday
        self.nombre = nombre

    @classmethod
    def from_weekday(cls, weekday: int) -> "DiaSemana":
        """Convierte Python weekday (0=Lunes) a DiaSemana."""
        for dia in cls:
            if dia.weekday == weekday:
                return dia
        raise ValueError(f"Weekday fuera de rango: {weekday}. Debe ser 0-6.")

    @classmethod
    def from_name(cls, name: str) -> "DiaSemana":
        """Convierte un nombre en texto (case-insensitive) a DiaSemana."""
        normalized = name.strip().upper()
        # Manejar variantes sin acentos
        alias = {
            "MIERCOLES": cls.MIERCOLES,
            "MIÉRCOLES": cls.MIERCOLES,
            "SABADO": cls.SABADO,
            "SÁBADO": cls.SABADO,
        }
        if normalized in alias:
            return alias[normalized]
        for dia in cls:
            if dia.nombre == normalized:
                return dia
        raise ValueError(f"Día no reconocido: {name}")

    @property
    def orden(self) -> int:
        return self.weekday

    @classmethod
    def todos_ordenados(cls) -> list["DiaSemana"]:
        """Retorna todos los días en orden Lunes→Domingo."""
        return sorted(cls, key=lambda d: d.weekday)
