"""
Selector de períodos comparativos (hasta 6).

Permite agregar/quitar períodos de comparación con sus respectivos rangos
de fecha y elegir el modo de variación (vs_principal / vs_anterior / ambas).
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional, Tuple

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

MAX_PERIODOS = 6


class ComparativePeriodSelector(QWidget):
    """
    Widget para gestionar periodos comparativos.

    Signals
    -------
    periods_changed(list)
        Lista de tuplas ``(name, start_date, end_date)``.
    modo_variacion_changed(str)
        ``"vs_principal"`` | ``"vs_anterior"`` | ``"ambas"``.
    """

    periods_changed = pyqtSignal(list)
    modo_variacion_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self._modo = "vs_principal"
        self._setup_ui()
        self._add_row("Período Anterior")

    # ── UI ────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(8)

        # Contenedor de filas
        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(8)
        self._root.addLayout(self._rows_layout)

        # Controles inferiores
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        self.btn_add = QPushButton("➕ Agregar otro período")
        self.btn_add.setProperty("class", "secondary")
        self.btn_add.clicked.connect(self._on_add)
        ctrl.addWidget(self.btn_add)

        # Selector de modo de variación
        self._var_container = QWidget()
        vl = QHBoxLayout(self._var_container)
        vl.setContentsMargins(10, 0, 0, 0)
        vl.setSpacing(5)
        vl.addWidget(QLabel("Variación:"))
        self._combo_var = QComboBox()
        self._combo_var.addItems(["vs Principal", "vs Anterior", "Ambas"])
        self._combo_var.setToolTip(
            "vs Principal: variación respecto al período principal\n"
            "vs Anterior: variación respecto al período previo\n"
            "Ambas: muestra ambas columnas"
        )
        self._combo_var.currentIndexChanged.connect(self._on_var_changed)
        vl.addWidget(self._combo_var)
        self._var_container.setVisible(False)
        ctrl.addWidget(self._var_container)

        ctrl.addStretch()

        self._label_limit = QLabel("")
        self._label_limit.setStyleSheet("color: #888888; font-size: 11px;")
        ctrl.addWidget(self._label_limit)

        self._root.addLayout(ctrl)
        self._refresh_ui()

    # ── Agregar / quitar filas ────────────────────────────────────

    def _add_row(self, label: str | None = None) -> None:
        if len(self._rows) >= MAX_PERIODOS:
            return

        idx = len(self._rows) + 1
        name = label or f"Período {idx}"

        row_w = QWidget()
        rl = QHBoxLayout(row_w)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)

        lbl = QLabel(f"{idx}. {name}")
        lbl.setMinimumWidth(130)
        rl.addWidget(lbl)

        ds = QDateEdit()
        ds.setCalendarPopup(True)
        ds.setDisplayFormat("dd/MM/yyyy")
        ds.setMaximumDate(QDate.currentDate())
        ds.setDate(QDate.currentDate().addDays(-60 * idx))
        ds.dateChanged.connect(lambda: self._emit_changed())
        rl.addWidget(ds)

        rl.addWidget(QLabel("al"))

        de = QDateEdit()
        de.setCalendarPopup(True)
        de.setDisplayFormat("dd/MM/yyyy")
        de.setMaximumDate(QDate.currentDate())
        de.setDate(QDate.currentDate().addDays(-30 * (idx - 1)))
        de.dateChanged.connect(lambda: self._emit_changed())
        rl.addWidget(de)

        btn_rm = QPushButton("✕")
        btn_rm.setFixedWidth(30)
        btn_rm.setStyleSheet(
            "QPushButton{color:#ff3b3b;font-weight:bold;border:none;}"
            "QPushButton:hover{color:#ff6666;}"
        )
        btn_rm.clicked.connect(lambda _, w=row_w: self._remove_row(w))
        rl.addWidget(btn_rm)

        self._rows_layout.addWidget(row_w)
        self._rows.append({
            "widget": row_w,
            "label": lbl,
            "start": ds,
            "end": de,
        })
        self._refresh_ui()
        self._emit_changed()

    def _remove_row(self, widget: QWidget) -> None:
        for i, r in enumerate(self._rows):
            if r["widget"] is widget:
                self._rows_layout.removeWidget(widget)
                widget.deleteLater()
                self._rows.pop(i)
                break
        self._renumber()
        self._refresh_ui()
        self._emit_changed()

    def _renumber(self) -> None:
        for i, r in enumerate(self._rows, 1):
            r["label"].setText(f"{i}. Período {i}")

    def _on_add(self) -> None:
        self._add_row()

    def _on_var_changed(self, idx: int) -> None:
        modos = ["vs_principal", "vs_anterior", "ambas"]
        self._modo = modos[idx]
        self.modo_variacion_changed.emit(self._modo)

    def _refresh_ui(self) -> None:
        n = len(self._rows)
        self._var_container.setVisible(n >= 2)
        if n >= MAX_PERIODOS:
            self.btn_add.setEnabled(False)
            self.btn_add.setText(f"Máximo {MAX_PERIODOS} períodos")
            self._label_limit.setText("")
        else:
            self.btn_add.setEnabled(True)
            self.btn_add.setText("➕ Agregar otro período")
            self._label_limit.setText(f"({MAX_PERIODOS - n} más disponibles)")

    def _emit_changed(self) -> None:
        self.periods_changed.emit(self.get_periods())

    # ── API pública ───────────────────────────────────────────────

    def get_periods(self) -> List[Tuple[str, date, date]]:
        """Devuelve ``[(name, start, end), …]``."""
        result = []
        for i, r in enumerate(self._rows, 1):
            qs = r["start"].date()
            qe = r["end"].date()
            result.append((
                f"Período {i}",
                date(qs.year(), qs.month(), qs.day()),
                date(qe.year(), qe.month(), qe.day()),
            ))
        return result

    def get_modo_variacion(self) -> str:
        return self._modo

    def validate(self) -> Tuple[bool, str]:
        if not self._rows:
            return False, "Agregue al menos un período de comparación."
        for i, r in enumerate(self._rows, 1):
            s = r["start"].date()
            e = r["end"].date()
            if s.daysTo(e) < 0:
                return False, f"Período {i}: fecha inicio > fecha fin."
        return True, ""
