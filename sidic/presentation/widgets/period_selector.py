"""
Selector de período de análisis.

Permite elegir fecha inicio/fin con atajos rápidos (semana, mes, trimestre).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Tuple

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDateEdit,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PeriodSelector(QWidget):
    """
    Widget para seleccionar el período principal de análisis.

    Signals
    -------
    period_changed(date, date)
        Fechas inicio y fin seleccionadas.
    """

    period_changed = pyqtSignal(object, object)  # date, date

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    # ── UI ────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("📅 PERÍODO DE ANÁLISIS")
        glayout = QVBoxLayout(group)
        glayout.setSpacing(12)

        # Atajos rápidos
        quick = QHBoxLayout()
        quick.setSpacing(8)
        quick.addWidget(QLabel("Período rápido:"))

        for label, days in [
            ("Última Semana", 7),
            ("Último Mes", 30),
            ("Último Trimestre", 90),
        ]:
            btn = QPushButton(label)
            btn.setProperty("class", "secondary")
            btn.clicked.connect(lambda _, d=days: self._set_quick(d))
            quick.addWidget(btn)
        quick.addStretch()
        glayout.addLayout(quick)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #333344;")
        glayout.addWidget(sep)

        # Fechas manuales
        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QLabel("Fecha Inicio:"), 0, 0)
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDisplayFormat("dd/MM/yyyy")
        self.date_start.setMaximumDate(QDate.currentDate())
        self.date_start.setDate(QDate.currentDate().addDays(-30))
        self.date_start.dateChanged.connect(self._on_start_changed)
        grid.addWidget(self.date_start, 0, 1)

        grid.addWidget(QLabel("Fecha Fin:"), 0, 2)
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDisplayFormat("dd/MM/yyyy")
        self.date_end.setMaximumDate(QDate.currentDate())
        self.date_end.setDate(QDate.currentDate())
        self.date_end.dateChanged.connect(self._on_end_changed)
        grid.addWidget(self.date_end, 0, 3)

        self.label_days = QLabel("30 días")
        self.label_days.setStyleSheet("color: #00d4ff; font-weight: bold;")
        grid.addWidget(self.label_days, 0, 4)

        glayout.addLayout(grid)
        layout.addWidget(group)
        self._update_days()

    # ── Atajos ────────────────────────────────────────────────────

    def _set_quick(self, days: int) -> None:
        end = QDate.currentDate()
        start = end.addDays(-days)
        self.date_start.blockSignals(True)
        self.date_end.blockSignals(True)
        self.date_start.setDate(start)
        self.date_end.setDate(end)
        self.date_start.blockSignals(False)
        self.date_end.blockSignals(False)
        self._emit_change()

    # ── Cambios de fecha ──────────────────────────────────────────

    def _on_start_changed(self) -> None:
        if self.date_start.date().daysTo(self.date_end.date()) < 0:
            self.date_end.blockSignals(True)
            self.date_end.setDate(self.date_start.date())
            self.date_end.blockSignals(False)
        self._emit_change()

    def _on_end_changed(self) -> None:
        if self.date_start.date().daysTo(self.date_end.date()) < 0:
            self.date_start.blockSignals(True)
            self.date_start.setDate(self.date_end.date())
            self.date_start.blockSignals(False)
        self._emit_change()

    def _emit_change(self) -> None:
        self._update_days()
        self.period_changed.emit(self.get_start_date(), self.get_end_date())

    def _update_days(self) -> None:
        days = self.date_start.date().daysTo(self.date_end.date())
        if days < 0:
            self.label_days.setText("⚠️ Fechas inválidas")
            self.label_days.setStyleSheet("color: #ff3b3b; font-weight: bold;")
        else:
            self.label_days.setText(f"{days + 1} días")
            self.label_days.setStyleSheet("color: #00d4ff; font-weight: bold;")

    # ── API pública ───────────────────────────────────────────────

    def get_start_date(self) -> date:
        q = self.date_start.date()
        return date(q.year(), q.month(), q.day())

    def get_end_date(self) -> date:
        q = self.date_end.date()
        return date(q.year(), q.month(), q.day())

    def get_period(self) -> Tuple[date, date]:
        return self.get_start_date(), self.get_end_date()

    def validate(self) -> Tuple[bool, str]:
        s = self.date_start.date()
        e = self.date_end.date()
        if s.daysTo(e) < 0:
            return False, "La fecha de inicio es posterior a la fecha fin."
        if e > QDate.currentDate():
            return False, "La fecha fin no puede ser futura."
        return True, ""
