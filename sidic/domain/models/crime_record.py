"""
Modelo de dominio para un hecho delictual.

Versión v2.0 — Inmutable, con clasificación vía servicio externo en lugar de
lógica hardcodeada. Los campos de categoría se asignan post-construcción
por el servicio DelitoCategorizer.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any, Optional, Tuple

from sidic.domain.enums import (
    CategoriaDelito,
    DiaSemana,
    FranjaHoraria,
    TipoEsclarecimiento,
)


@dataclass
class CrimeRecord:
    """
    Hecho delictual individual extraído de un archivo GIS.

    Los campos son los datos crudos normalizados. Las propiedades calculadas
    derivan valores para reportes sin depender de constantes hardcodeadas.
    """

    # ── Identificación ──────────────────────────────────────────────────
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    nro_sumario: str = ""

    # ── Datos temporales ────────────────────────────────────────────────
    fecha: Optional[date] = None
    hora: Optional[time] = None

    # ── Clasificación del delito ────────────────────────────────────────
    delito: str = ""
    modus_operandi: str = ""
    ambito: str = ""

    # ── Medios utilizados ───────────────────────────────────────────────
    movilidad: str = ""
    arma_medio: str = ""

    # ── Estado ──────────────────────────────────────────────────────────
    esclarecido: str = ""
    situacion_causante: str = ""

    # ── Ubicación ───────────────────────────────────────────────────────
    direccion: str = ""
    jurisdiccion: str = ""
    dependencia: str = ""
    barrio: str = ""
    coordenadas: Optional[Tuple[float, float]] = None  # (lon, lat)

    # ── Datos de víctima ────────────────────────────────────────────────
    nombre_victima: str = ""
    sexo_victima: str = ""
    edad_victima: str = ""
    dni_victima: str = ""
    direccion_victima: str = ""

    # ── Datos de causante ───────────────────────────────────────────────
    nombre_causante: str = ""
    sexo_causante: str = ""
    edad_causante: str = ""
    dni_causante: str = ""
    direccion_causante: str = ""
    descripcion_causante: str = ""

    # ── Detalles adicionales ────────────────────────────────────────────
    elemento_sustraido: str = ""
    detalle_lugar: str = ""
    detalle_arma: str = ""
    descripcion_vehiculo: str = ""
    resena_hecho: str = ""
    resolucion_hecho: str = ""
    mes: str = ""

    # ── Geometría GIS ───────────────────────────────────────────────────
    geometry: Any = None

    # ── Categoría asignada (se asigna post-creación por DelitoCategorizer) ──
    _categoria: Optional[CategoriaDelito] = field(
        default=None, repr=False, compare=False
    )
    _es_robo_agravado: Optional[bool] = field(
        default=None, repr=False, compare=False
    )

    # ── Campos extra no mapeados ────────────────────────────────────────
    campos_extra: dict = field(default_factory=dict, repr=False)

    # ═════════════════════════════════════════════════════════════════════
    # PROPIEDADES TEMPORALES
    # ═════════════════════════════════════════════════════════════════════

    @property
    def fecha_hora(self) -> Optional[datetime]:
        """Combina fecha y hora en un datetime."""
        if self.fecha and self.hora:
            return datetime.combine(self.fecha, self.hora)
        return None

    @property
    def dia_semana(self) -> Optional[DiaSemana]:
        """Día de la semana como enum."""
        if self.fecha is None:
            return None
        return DiaSemana.from_weekday(self.fecha.weekday())

    @property
    def dia_semana_nombre(self) -> str:
        """Nombre del día para uso en reportes."""
        dia = self.dia_semana
        return dia.nombre if dia else "#NO_CONSTA"

    @property
    def franja_horaria(self) -> Optional[FranjaHoraria]:
        """Franja horaria del hecho."""
        if self.hora is None:
            return None
        return FranjaHoraria.from_hour(self.hora.hour)

    @property
    def franja_horaria_nombre(self) -> str:
        """Nombre de la franja horaria con rango."""
        franja = self.franja_horaria
        return franja.display_name if franja else "#NO_CONSTA"

    # ═════════════════════════════════════════════════════════════════════
    # PROPIEDADES DE CLASIFICACIÓN
    # ═════════════════════════════════════════════════════════════════════

    @property
    def delito_con_modalidad(self) -> str:
        """
        Combina tipo de delito + modus operandi en un identificador normalizado.

        Ejemplos:
            "050-HURTO" + "OPORTUNISTA" → "HURTO OPORTUNISTA"
            "010-ROBO" + "ARREBATO" → "ROBO ARREBATO"
            "030-ROBO_AGRAVADO" + "ASALTANTE" → "ROBO AGRAVADO ASALTANTE"
        """
        if not self.delito:
            return ""

        # Limpiar prefijo numérico (ej: "050-")
        delito_base = self.delito.upper().strip()
        match = re.match(r"^\d{2,3}[-_]?(.+)$", delito_base)
        if match:
            delito_base = match.group(1).strip()

        # Normalizar: guiones bajos a espacios
        delito_base = delito_base.replace("_", " ").replace("-", " ")
        # Limpiar espacios múltiples
        delito_base = " ".join(delito_base.split())

        if self.modus_operandi and self.modus_operandi.strip():
            modus = self.modus_operandi.upper().strip()
            modus = modus.replace("_", " ").replace("-", " ")
            modus = " ".join(modus.split())

            # Evitar duplicación si el modus ya está en el delito
            if modus not in delito_base:
                return f"{delito_base} {modus}"

        return delito_base

    @property
    def categoria(self) -> CategoriaDelito:
        """Categoría del delito. Debe ser asignada por DelitoCategorizer."""
        if self._categoria is not None:
            return self._categoria
        # Fallback básico si no se asignó categoría
        return self._categorizar_fallback()

    @categoria.setter
    def categoria(self, value: CategoriaDelito) -> None:
        self._categoria = value

    @property
    def es_robo_agravado(self) -> bool:
        """Indica si el delito es un robo agravado (requiere arma)."""
        if self._es_robo_agravado is not None:
            return self._es_robo_agravado
        return "AGRAVADO" in self.delito.upper()

    @es_robo_agravado.setter
    def es_robo_agravado(self, value: bool) -> None:
        self._es_robo_agravado = value

    @property
    def tipo_esclarecimiento(self) -> TipoEsclarecimiento:
        """Tipo de esclarecimiento del hecho."""
        return TipoEsclarecimiento.from_text(self.esclarecido)

    @property
    def es_esclarecido(self) -> bool:
        """Indica si el hecho fue esclarecido (total o parcialmente)."""
        return self.tipo_esclarecimiento != TipoEsclarecimiento.NO

    # ═════════════════════════════════════════════════════════════════════
    # MÉTODOS
    # ═════════════════════════════════════════════════════════════════════

    def matches_period(self, start: date, end: date) -> bool:
        """Verifica si el hecho está dentro de un período dado."""
        if self.fecha is None:
            return False
        return start <= self.fecha <= end

    def to_dict(self) -> dict:
        """Serializa el registro a diccionario."""
        return {
            "id": self.id,
            "nro_sumario": self.nro_sumario,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "hora": self.hora.strftime("%H:%M") if self.hora else None,
            "dia_semana": self.dia_semana_nombre,
            "franja_horaria": self.franja_horaria_nombre,
            "delito": self.delito,
            "delito_con_modalidad": self.delito_con_modalidad,
            "categoria": self.categoria.value,
            "ambito": self.ambito,
            "movilidad": self.movilidad,
            "arma_medio": self.arma_medio,
            "esclarecido": self.esclarecido,
            "tipo_esclarecimiento": self.tipo_esclarecimiento.value,
            "direccion": self.direccion,
            "jurisdiccion": self.jurisdiccion,
            "dependencia": self.dependencia,
            "coordenadas": self.coordenadas,
            "es_robo_agravado": self.es_robo_agravado,
        }

    def _categorizar_fallback(self) -> CategoriaDelito:
        """Categorización básica por palabras clave (fallback)."""
        d = self.delito.upper()
        es_tentativa = "TENTATIVA" in d
        if "ESTAFA" in d:
            return CategoriaDelito.ESTAFA
        if "ROBO" in d:
            return CategoriaDelito.TENTATIVA_ROBO if es_tentativa else CategoriaDelito.ROBO
        if "HURTO" in d:
            return CategoriaDelito.TENTATIVA_HURTO if es_tentativa else CategoriaDelito.HURTO
        return CategoriaDelito.OTROS

    def __str__(self) -> str:
        fecha_str = self.fecha.strftime("%d/%m/%Y") if self.fecha else "S/F"
        hora_str = self.hora.strftime("%H:%M") if self.hora else "S/H"
        return f"[{self.id}] {self.delito} - {fecha_str} {hora_str} - {self.direccion}"

    def __repr__(self) -> str:
        return f"CrimeRecord(id={self.id!r}, delito={self.delito!r}, fecha={self.fecha})"
