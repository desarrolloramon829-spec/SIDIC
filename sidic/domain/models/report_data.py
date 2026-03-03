"""
Contenedores de datos de período y reporte.

Versión v2.0 — PeriodData y ReportData usan los nuevos enums del dominio
y no dependen de constantes hardcodeadas.
"""
from __future__ import annotations

import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional

from sidic.domain.enums import (
    CategoriaDelito,
    ClasificacionAprehendido,
    DiaSemana,
    FranjaHoraria,
    ModoVariacion,
)
from sidic.domain.models.crime_record import CrimeRecord
from sidic.domain.models.mentioned_person import MentionedPerson
from sidic.domain.models.apprehended import Apprehended

# Máximo de períodos permitidos en análisis comparativo
MAX_PERIODOS = 6


@dataclass
class PeriodData:
    """
    Datos procesados para un período temporal específico.

    Contiene las listas de registros filtrados y métodos de agregación
    que producen los conteos necesarios para la generación de tablas.
    """

    # ── Identificación del período ──────────────────────────────────────
    nombre: str = ""
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

    # ── Registros del período ───────────────────────────────────────────
    hechos: List[CrimeRecord] = field(default_factory=list)
    mencionados: List[MentionedPerson] = field(default_factory=list)
    aprehendidos: List[Apprehended] = field(default_factory=list)

    # ═════════════════════════════════════════════════════════════════════
    # PROPIEDADES BÁSICAS
    # ═════════════════════════════════════════════════════════════════════

    @property
    def rango_fechas(self) -> str:
        """Rango de fechas formateado para display."""
        if self.fecha_inicio and self.fecha_fin:
            fmt = "%d/%m/%Y"
            return f"{self.fecha_inicio.strftime(fmt)} - {self.fecha_fin.strftime(fmt)}"
        return self.nombre

    @property
    def total_hechos(self) -> int:
        return len(self.hechos)

    @property
    def total_mencionados(self) -> int:
        return len(self.mencionados)

    @property
    def total_aprehendidos(self) -> int:
        return len(self.aprehendidos)

    @property
    def label_corto(self) -> str:
        """Etiqueta corta para columnas comparativas."""
        if self.fecha_inicio and self.fecha_fin:
            return (
                f"{self.fecha_inicio.strftime('%d/%m')}-"
                f"{self.fecha_fin.strftime('%d/%m/%y')}"
            )
        return self.nombre[:20]

    # ═════════════════════════════════════════════════════════════════════
    # CONTEOS SIMPLES
    # ═════════════════════════════════════════════════════════════════════

    def conteo_por_delito(self) -> Dict[str, int]:
        """Conteo de hechos por tipo de delito CON MODALIDAD."""
        return dict(
            Counter(h.delito_con_modalidad for h in self.hechos if h.delito_con_modalidad)
        )

    def conteo_por_categoria(self) -> Dict[str, int]:
        """Conteo de hechos por categoría (ROBOS, HURTOS, etc.)."""
        return dict(Counter(h.categoria.value for h in self.hechos))

    def conteo_por_dia_semana(self) -> Dict[str, int]:
        """Conteo de hechos por día de la semana (orden Lunes→Domingo)."""
        result = {dia.nombre: 0 for dia in DiaSemana.todos_ordenados()}
        for h in self.hechos:
            dia = h.dia_semana
            if dia:
                result[dia.nombre] += 1
        return result

    def conteo_por_franja_horaria(self) -> Dict[str, int]:
        """Conteo de hechos por franja horaria."""
        result = {f.display_name: 0 for f in FranjaHoraria}
        for h in self.hechos:
            franja = h.franja_horaria
            if franja:
                result[franja.display_name] += 1
        return result

    def conteo_por_movilidad(self) -> Dict[str, int]:
        """Conteo de hechos por medio de movilidad utilizado."""
        return dict(
            Counter(h.movilidad if h.movilidad else "#NO_CONSTA" for h in self.hechos)
        )

    def conteo_por_arma(self) -> Dict[str, int]:
        """Conteo de armas/medios en robos agravados únicamente."""
        agravados = [h for h in self.hechos if h.es_robo_agravado]
        return dict(
            Counter(h.arma_medio if h.arma_medio else "#NO_CONSTA" for h in agravados)
        )

    def conteo_por_ambito(self) -> Dict[str, int]:
        """Conteo de hechos por ámbito de ocurrencia."""
        return dict(
            Counter(h.ambito if h.ambito else "#NO_CONSTA" for h in self.hechos)
        )

    def conteo_esclarecimiento(self) -> Dict[str, int]:
        """Conteo por tipo de esclarecimiento."""
        return dict(Counter(h.tipo_esclarecimiento.value for h in self.hechos))

    def conteo_aprehendidos_clasificacion(self) -> Dict[str, int]:
        """Conteo de aprehendidos por clasificación normalizada."""
        result = {c.value: 0 for c in ClasificacionAprehendido}
        for a in self.aprehendidos:
            result[a.clasificacion.value] += 1
        return result

    # ═════════════════════════════════════════════════════════════════════
    # MATRICES CRUZADAS
    # ═════════════════════════════════════════════════════════════════════

    def matriz_delito_dia(self) -> Dict[str, Dict[str, int]]:
        """Matriz delito_con_modalidad × día de la semana."""
        dias = [d.nombre for d in DiaSemana.todos_ordenados()]
        delitos = sorted(set(h.delito_con_modalidad for h in self.hechos if h.delito_con_modalidad))
        matriz = {delito: {dia: 0 for dia in dias} for delito in delitos}
        for h in self.hechos:
            if h.delito_con_modalidad and h.dia_semana:
                matriz[h.delito_con_modalidad][h.dia_semana.nombre] += 1
        return matriz

    def matriz_delito_franja(self) -> Dict[str, Dict[str, int]]:
        """Matriz delito_con_modalidad × franja horaria."""
        franjas = [f.display_name for f in FranjaHoraria]
        delitos = sorted(set(h.delito_con_modalidad for h in self.hechos if h.delito_con_modalidad))
        matriz = {delito: {franja: 0 for franja in franjas} for delito in delitos}
        for h in self.hechos:
            if h.delito_con_modalidad and h.franja_horaria:
                matriz[h.delito_con_modalidad][h.franja_horaria.display_name] += 1
        return matriz

    # ═════════════════════════════════════════════════════════════════════
    # CUADRO DE REFERENCIA
    # ═════════════════════════════════════════════════════════════════════

    def cuadro_referencia(self) -> List[Dict[str, Any]]:
        """
        Genera el cuadro de referencia para mapas, agrupado por categoría
        con subtotales por sección y total general.
        """
        conteo = self.conteo_por_delito()
        categorias_conteo = self.conteo_por_categoria()
        esclarecidos = self.conteo_esclarecimiento()

        # Agrupar delitos por categoría
        delitos_por_cat: Dict[CategoriaDelito, List[tuple]] = {}
        for h in self.hechos:
            if h.delito_con_modalidad:
                cat = h.categoria
                if cat not in delitos_por_cat:
                    delitos_por_cat[cat] = []

        for cat in CategoriaDelito:
            if cat in delitos_por_cat:
                delitos_set = set()
                for h in self.hechos:
                    if h.categoria == cat and h.delito_con_modalidad:
                        delitos_set.add(h.delito_con_modalidad)
                delitos_por_cat[cat] = [
                    (d, conteo.get(d, 0)) for d in sorted(delitos_set)
                ]

        filas: List[Dict[str, Any]] = []

        # Generar filas por categoría en orden de prioridad
        for cat in sorted(delitos_por_cat.keys(), key=lambda c: c.orden):
            items = delitos_por_cat[cat]
            if not items:
                continue

            filas.append({"tipo": "categoria", "texto": cat.value, "cantidad": None})
            for delito, cant in sorted(items, key=lambda x: -x[1]):
                filas.append({"tipo": "delito", "texto": delito, "cantidad": cant})
            filas.append({
                "tipo": "subtotal",
                "texto": f"SUBTOTAL - {cat.value}",
                "cantidad": categorias_conteo.get(cat.value, 0),
            })

        # Total general
        filas.append({
            "tipo": "total",
            "texto": "TOTAL DELITOS REGISTRADOS",
            "cantidad": self.total_hechos,
        })

        # Indicadores de esclarecimiento
        total_escl = sum(
            v for k, v in esclarecidos.items() if k != "NO"
        )
        if total_escl > 0:
            filas.append({"tipo": "separador", "texto": "INDICACIONES", "cantidad": None})
            for tipo, cant in esclarecidos.items():
                if cant > 0 and tipo != "NO":
                    filas.append({
                        "tipo": "indicacion",
                        "texto": f"Hechos {tipo.replace('_', ' ').title()}",
                        "cantidad": cant,
                    })
            filas.append({
                "tipo": "subtotal",
                "texto": "TOTAL HECHOS ESCLARECIDOS",
                "cantidad": total_escl,
            })

        return filas


@dataclass
class ReportData:
    """
    Contenedor principal de datos para generación de reportes.

    Soporta de 1 a MAX_PERIODOS períodos para análisis simple o comparativo.
    """

    # ── Información general ─────────────────────────────────────────────
    titulo: str = "INFORME DELICTUAL"
    jurisdiccion: str = ""
    dependencia: str = ""
    fecha_generacion: Optional[date] = None

    # ── Períodos ────────────────────────────────────────────────────────
    periodos: List[PeriodData] = field(default_factory=list)

    # ── Configuración comparativa ───────────────────────────────────────
    modo_variacion: ModoVariacion = ModoVariacion.VS_PRINCIPAL

    # ═════════════════════════════════════════════════════════════════════
    # PROPIEDADES
    # ═════════════════════════════════════════════════════════════════════

    @property
    def es_comparativo(self) -> bool:
        return len(self.periodos) > 1

    @property
    def num_periodos(self) -> int:
        return len(self.periodos)

    @property
    def periodo_principal(self) -> Optional[PeriodData]:
        return self.periodos[0] if self.periodos else None

    @property
    def periodos_comparacion(self) -> List[PeriodData]:
        return self.periodos[1:] if len(self.periodos) > 1 else []

    # ═════════════════════════════════════════════════════════════════════
    # MÉTODOS
    # ═════════════════════════════════════════════════════════════════════

    def agregar_periodo(self, periodo: PeriodData) -> None:
        """Agrega un período al reporte (máximo MAX_PERIODOS)."""
        if len(self.periodos) >= MAX_PERIODOS:
            raise ValueError(
                f"Máximo {MAX_PERIODOS} períodos permitidos. "
                f"Ya hay {len(self.periodos)}."
            )
        self.periodos.append(periodo)

    @staticmethod
    def comparar_conteos(
        conteo_a: Dict[str, int],
        conteo_b: Dict[str, int],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compara dos conteos y calcula variaciones absolutas y porcentuales.

        Args:
            conteo_a: Conteo del período base (referencia).
            conteo_b: Conteo del período a comparar.

        Returns:
            Dict con periodo_a, periodo_b, diferencia, porcentaje, tendencia.
        """
        todas_claves = sorted(set(conteo_a.keys()) | set(conteo_b.keys()))
        resultado = {}

        for clave in todas_claves:
            val_a = conteo_a.get(clave, 0)
            val_b = conteo_b.get(clave, 0)
            diferencia = val_b - val_a

            if val_a > 0:
                porcentaje = ((val_b - val_a) / val_a) * 100
            elif val_b > 0:
                porcentaje = 100.0
            else:
                porcentaje = 0.0

            resultado[clave] = {
                "periodo_a": val_a,
                "periodo_b": val_b,
                "diferencia": diferencia,
                "porcentaje": round(porcentaje, 2),
                "tendencia": (
                    "subio" if diferencia > 0
                    else "bajo" if diferencia < 0
                    else "igual"
                ),
            }

        return resultado
