"""
Panel de opciones de exportación y filtros de categoría.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

_FORMATOS = [
    ("Excel (.xlsx)", "excel"),
    ("Word (.docx)", "word"),
    ("PDF (.pdf)", "pdf"),
    ("Todos los formatos", "todos"),
]

_CATEGORIAS = [
    ("Incluir ROBOS", ["ROBOS", "TENTATIVA DE ROBOS"]),
    ("Incluir HURTOS", ["HURTOS", "TENTATIVA DE HURTOS"]),
    ("Incluir ESTAFAS", ["ESTAFAS"]),
    ("Incluir OTROS", ["OTROS DELITOS"]),
]


class ExportOptionsPanel(QWidget):
    """
    Panel con formato de salida, checkboxes de contenido y
    filtros de categorías de delitos.

    Signals
    -------
    options_changed()
        Cualquier opción fue modificada.
    """

    options_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    # ── UI ────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("⚙️ OPCIONES DE EXPORTACIÓN")
        glayout = QVBoxLayout(group)
        glayout.setSpacing(12)

        # Formato
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Formato de salida:"))
        self.combo_format = QComboBox()
        for label, _ in _FORMATOS:
            self.combo_format.addItem(label)
        self.combo_format.currentIndexChanged.connect(lambda _: self.options_changed.emit())
        fmt_row.addWidget(self.combo_format)
        fmt_row.addStretch()
        glayout.addLayout(fmt_row)

        # Opciones de contenido
        content_row = QHBoxLayout()
        self.check_charts = self._cb("Incluir gráficos", True, content_row)
        self.check_cuadro = self._cb("Cuadro de referencia", True, content_row)
        self.check_mencionados = self._cb("Lista de mencionados", True, content_row)
        self.check_matrices = self._cb("Matrices cruzadas", True, content_row)
        self.check_comparativos = self._cb("Cuadros comparativos", True, content_row)
        self.check_comparativos.setVisible(False)
        content_row.addStretch()
        glayout.addLayout(content_row)

        # Categorías
        cat_row = QHBoxLayout()
        self._cat_checks: list[tuple[QCheckBox, list[str]]] = []
        for label, cats in _CATEGORIAS:
            cb = self._cb(label, True, cat_row)
            self._cat_checks.append((cb, cats))
        cat_row.addStretch()
        glayout.addLayout(cat_row)

        layout.addWidget(group)

    def _cb(self, text: str, checked: bool, row: QHBoxLayout) -> QCheckBox:
        cb = QCheckBox(text)
        cb.setChecked(checked)
        cb.toggled.connect(lambda _: self.options_changed.emit())
        row.addWidget(cb)
        return cb

    # ── API pública ───────────────────────────────────────────────

    def get_formato(self) -> str:
        idx = self.combo_format.currentIndex()
        return _FORMATOS[idx][1] if 0 <= idx < len(_FORMATOS) else "excel"

    def get_options(self) -> Dict[str, bool]:
        return {
            "incluir_graficos": self.check_charts.isChecked(),
            "incluir_cuadro_referencia": self.check_cuadro.isChecked(),
            "incluir_mencionados": self.check_mencionados.isChecked(),
            "incluir_matrices": self.check_matrices.isChecked(),
            "incluir_comparativos": self.check_comparativos.isChecked(),
        }

    def get_categorias_incluidas(self) -> List[str]:
        cats: list[str] = []
        for cb, items in self._cat_checks:
            if cb.isChecked():
                cats.extend(items)
        return cats or [
            "ROBOS", "TENTATIVA DE ROBOS",
            "HURTOS", "TENTATIVA DE HURTOS",
            "ESTAFAS", "OTROS DELITOS",
        ]

    def set_comparative_visible(self, visible: bool) -> None:
        self.check_comparativos.setVisible(visible)
        if visible:
            self.check_comparativos.setChecked(True)
        else:
            self.check_comparativos.setChecked(False)
