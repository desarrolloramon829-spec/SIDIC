"""
Modelo de dominio para personas aprehendidas.

Versión v2.0 — Usa enum ClasificacionAprehendido en lugar de strings.
Incluye nro_sumario para vincular con CrimeRecord.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from sidic.domain.enums import ClasificacionAprehendido


@dataclass
class Apprehended:
    """
    Persona aprehendida con clasificación por edad y antecedentes.
    """

    # ── Identificación ──────────────────────────────────────────────────
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    nro_sumario: str = ""  # Vínculo con CrimeRecord

    # ── Datos personales ────────────────────────────────────────────────
    nombre: str = ""
    edad: Optional[int] = None
    sexo: str = ""

    # ── Clasificación ───────────────────────────────────────────────────
    clasificacion_raw: str = ""  # Valor original del shapefile

    # ── Datos del hecho ─────────────────────────────────────────────────
    delito: str = ""
    fecha: Optional[date] = None
    direccion: str = ""
    descripcion: str = ""

    # ── Campos extra ────────────────────────────────────────────────────
    campos_extra: dict = field(default_factory=dict, repr=False)

    # ═════════════════════════════════════════════════════════════════════
    # PROPIEDADES
    # ═════════════════════════════════════════════════════════════════════

    @property
    def clasificacion(self) -> ClasificacionAprehendido:
        """Clasificación normalizada como enum."""
        if self.clasificacion_raw:
            craw = self.clasificacion_raw.upper()
            es_menor = "MENOR" in craw
            con_antec = "ANTECEDENTES" in craw or "REINCIDENTE" in craw
            if es_menor:
                return (
                    ClasificacionAprehendido.MENOR_CON_ANTECEDENTES
                    if con_antec
                    else ClasificacionAprehendido.MENOR_PRIMERIZO
                )
            return (
                ClasificacionAprehendido.MAYOR_CON_ANTECEDENTES
                if con_antec
                else ClasificacionAprehendido.MAYOR_PRIMERIZO
            )
        # Inferir desde edad
        return ClasificacionAprehendido.inferir(self.edad)

    @property
    def es_menor(self) -> bool:
        """Indica si es menor de edad."""
        return self.clasificacion.es_menor

    @property
    def tiene_antecedentes(self) -> bool:
        """Indica si tiene antecedentes."""
        return self.clasificacion.tiene_antecedentes

    @property
    def sexo_normalizado(self) -> str:
        """Sexo normalizado (M/F/-)."""
        if not self.sexo:
            return "-"
        s = self.sexo.upper().strip()
        if s in ("M", "MASCULINO", "HOMBRE", "VARON", "VARÓN"):
            return "M"
        if s in ("F", "FEMENINO", "MUJER"):
            return "F"
        return self.sexo

    # ═════════════════════════════════════════════════════════════════════
    # MÉTODOS
    # ═════════════════════════════════════════════════════════════════════

    def matches_period(self, start: date, end: date) -> bool:
        """Verifica si la aprehensión está dentro de un período."""
        if self.fecha is None:
            return False
        return start <= self.fecha <= end

    def to_dict(self) -> dict:
        """Serializa a diccionario."""
        return {
            "id": self.id,
            "nro_sumario": self.nro_sumario,
            "nombre": self.nombre,
            "edad": self.edad,
            "sexo": self.sexo_normalizado,
            "clasificacion": self.clasificacion.value,
            "delito": self.delito,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "es_menor": self.es_menor,
            "tiene_antecedentes": self.tiene_antecedentes,
        }

    def to_report_row(self) -> dict:
        """Genera fila para el cuadro de aprehendidos del reporte."""
        return {
            "Nombre/Alias": self.nombre or "NN",
            "Clasificación": self.clasificacion.value,
            "Delito": self.delito,
            "Fecha": self.fecha.strftime("%d/%m/%Y") if self.fecha else "-",
            "Edad": str(self.edad) if self.edad else "-",
            "Sexo": self.sexo_normalizado,
        }

    def __str__(self) -> str:
        nombre = self.nombre or "NN"
        return f"{nombre} - {self.clasificacion.value} - {self.delito}"

    def __repr__(self) -> str:
        return f"Apprehended(nombre={self.nombre!r}, clasificacion={self.clasificacion.value!r})"
