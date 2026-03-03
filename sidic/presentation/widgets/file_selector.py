"""
Selector de archivos GIS con tabla de asignación por tipo.

Incluye drop-zone, tabla de archivos cargados y detección automática
del tipo (hechos / mencionados / aprehendidos / jurisdicción / puntos).
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sidic.presentation.widgets.drop_zone import (
    DropZone,
    _ASSOCIATED_EXTENSIONS,
    _SUPPORTED_EXTENSIONS,
)

# Tipos de archivo reconocidos
FILE_TYPES: Dict[str, Dict] = {
    "hechos": {
        "label": "Hechos Delictuales",
        "description": "Shapefile principal con los hechos delictuales",
        "required": False,
        "patterns": ["hecho", "delito", "delict"],
    },
    "mencionados": {
        "label": "Mencionados",
        "description": "Personas mencionadas como posibles autores",
        "required": False,
        "patterns": ["mencionado", "menc", "autor"],
    },
    "aprehendidos": {
        "label": "Aprehendidos",
        "description": "Personas aprehendidas",
        "required": False,
        "patterns": ["aprehendido", "apreh", "detenido"],
    },
    "jurisdiccion": {
        "label": "Jurisdicción",
        "description": "Límites de la jurisdicción",
        "required": False,
        "patterns": ["jurisdic", "limite", "zona"],
    },
    "puntos_referencia": {
        "label": "Puntos de Referencia",
        "description": "Puntos de interés para el mapa",
        "required": False,
        "patterns": ["referencia", "punto", "poi"],
    },
}


class FileSelector(QWidget):
    """
    Widget para seleccionar y clasificar archivos GIS.

    Signals
    -------
    files_changed(dict)
        Diccionario ``{tipo: ruta}`` actual.
    """

    files_changed = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.file_paths: Dict[str, str] = {}
        self._setup_ui()

    # ── UI ────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        group = QGroupBox("📁 ARCHIVOS GIS")
        glayout = QVBoxLayout(group)
        glayout.setSpacing(12)

        # Drop zone
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        glayout.addWidget(self.drop_zone)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #333344;")
        glayout.addWidget(sep)

        # Tabla de archivos
        self.table = QTableWidget()
        self.table.setObjectName("filesTable")
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Archivo", "Tipo", "Estado", "Quitar"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 70)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(120)
        self.table.setMaximumHeight(200)
        self.table.setAlternatingRowColors(True)
        glayout.addWidget(self.table)

        # Botón limpiar + estado
        btn_row = QHBoxLayout()
        btn_clear = QPushButton("Limpiar Todo")
        btn_clear.setProperty("class", "secondary")
        btn_clear.setMinimumWidth(120)
        btn_clear.clicked.connect(self.clear_all)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()

        self.status_label = QLabel("")
        self.status_label.setObjectName("generalStatus")
        btn_row.addWidget(self.status_label)
        glayout.addLayout(btn_row)

        layout.addWidget(group)
        self._update_status()

    # ── Procesamiento de archivos soltados ────────────────────────

    def _on_files_dropped(self, paths: List[str]) -> None:
        gis_files: list[Path] = []

        for raw in paths:
            p = Path(raw)
            if p.is_dir():
                for ext in _SUPPORTED_EXTENSIONS:
                    gis_files.extend(p.glob(f"*{ext}"))
            elif p.suffix.lower() in _SUPPORTED_EXTENSIONS:
                gis_files.append(p)
            elif p.suffix.lower() in _ASSOCIATED_EXTENSIONS:
                shp = p.with_suffix(".shp")
                if shp.exists() and shp not in gis_files:
                    gis_files.append(shp)

        if not gis_files:
            QMessageBox.warning(
                self,
                "Sin Archivos",
                "No se encontraron archivos GIS válidos.\n\n"
                "Puede arrastrar:\n"
                "• .shp / .geojson / .gpkg / .kml / .csv\n"
                "• Carpetas con archivos GIS",
            )
            return

        added = 0
        for fp in gis_files:
            file_id = self._detect_type(fp.stem)
            if file_id and file_id in self.file_paths:
                reply = QMessageBox.question(
                    self,
                    "Archivo Duplicado",
                    f"Ya existe un archivo para '{FILE_TYPES[file_id]['label']}'.\n\n"
                    f"Actual: {Path(self.file_paths[file_id]).name}\n"
                    f"Nuevo: {fp.name}\n\n¿Reemplazar?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    continue
            if not file_id:
                file_id = self._first_free_type()
            if file_id:
                self._add_file(file_id, str(fp))
                added += 1

        if added:
            self._update_status()
            self.files_changed.emit(self.file_paths)

    def _detect_type(self, stem: str) -> Optional[str]:
        lower = stem.lower()
        for fid, info in FILE_TYPES.items():
            for pat in info["patterns"]:
                if pat in lower:
                    return fid
        return None

    def _first_free_type(self) -> Optional[str]:
        for fid in FILE_TYPES:
            if fid not in self.file_paths:
                return fid
        return None

    # ── Tabla ─────────────────────────────────────────────────────

    def _add_file(self, file_id: str, path: str) -> None:
        self.file_paths[file_id] = path
        row = self._find_row(file_id)
        if row is None:
            row = self.table.rowCount()
            self.table.insertRow(row)

        # Columna 0: nombre
        item = QTableWidgetItem(Path(path).name)
        item.setData(Qt.ItemDataRole.UserRole, file_id)
        item.setToolTip(path)
        self.table.setItem(row, 0, item)

        # Columna 1: tipo combo
        combo = QComboBox()
        for fid, info in FILE_TYPES.items():
            combo.addItem(info["label"], fid)
        idx = combo.findData(file_id)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.currentIndexChanged.connect(lambda _, r=row: self._on_type_changed(r))
        self.table.setCellWidget(row, 1, combo)

        # Columna 2: estado
        valid, msg = self._validate_file(path)
        status = QTableWidgetItem("OK" if valid else "!")
        status.setToolTip(msg)
        status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setForeground(Qt.GlobalColor.green if valid else Qt.GlobalColor.yellow)
        self.table.setItem(row, 2, status)

        # Columna 3: quitar
        btn = QPushButton("X")
        btn.setStyleSheet(
            "QPushButton{background:#ff3b3b;color:#fff;border:none;"
            "border-radius:4px;font-weight:bold;padding:4px 8px;}"
            "QPushButton:hover{background:#ff5555;}"
        )
        btn.setMaximumWidth(50)
        btn.setMinimumHeight(28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda _, r=row: self._remove_row(r))
        self.table.setCellWidget(row, 3, btn)

    def _find_row(self, file_id: str) -> Optional[int]:
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == file_id:
                return r
        return None

    def _on_type_changed(self, row: int) -> None:
        combo = self.table.cellWidget(row, 1)
        item = self.table.item(row, 0)
        if not combo or not item:
            return
        new_id = combo.currentData()
        old_id = item.data(Qt.ItemDataRole.UserRole)
        path = item.toolTip()

        if new_id != old_id and new_id in self.file_paths:
            reply = QMessageBox.question(
                self,
                "Tipo Duplicado",
                f"Ya existe un archivo para '{FILE_TYPES[new_id]['label']}'.\n¿Reemplazar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                idx = combo.findData(old_id)
                combo.blockSignals(True)
                combo.setCurrentIndex(idx)
                combo.blockSignals(False)
                return
            existing = self._find_row(new_id)
            if existing is not None:
                self._remove_row_internal(existing)

        if old_id in self.file_paths:
            del self.file_paths[old_id]
        self.file_paths[new_id] = path
        item.setData(Qt.ItemDataRole.UserRole, new_id)
        self._update_status()
        self.files_changed.emit(self.file_paths)

    def _remove_row(self, row: int) -> None:
        item = self.table.item(row, 0)
        if item:
            fid = item.data(Qt.ItemDataRole.UserRole)
            self.file_paths.pop(fid, None)
        self.table.removeRow(row)
        self._reconnect_buttons()
        self._update_status()
        self.files_changed.emit(self.file_paths)

    def _remove_row_internal(self, row: int) -> None:
        item = self.table.item(row, 0)
        if item:
            self.file_paths.pop(item.data(Qt.ItemDataRole.UserRole), None)
        self.table.removeRow(row)
        self._reconnect_buttons()

    def _reconnect_buttons(self) -> None:
        for r in range(self.table.rowCount()):
            btn = self.table.cellWidget(r, 3)
            if btn:
                try:
                    btn.clicked.disconnect()
                except RuntimeError:
                    pass
                btn.clicked.connect(lambda _, row=r: self._remove_row(row))

    # ── Validación / estado ───────────────────────────────────────

    @staticmethod
    def _validate_file(path: str) -> Tuple[bool, str]:
        p = Path(path)
        if not p.exists():
            return False, "Archivo no encontrado"
        if p.suffix.lower() == ".shp":
            missing = [
                ext for ext in (".dbf", ".shx")
                if not p.with_suffix(ext).exists()
            ]
            if missing:
                return False, f"Faltan: {', '.join(missing)}"
        return True, "Válido"

    def _update_status(self) -> None:
        total = len(self.file_paths)
        if total == 0:
            self.status_label.setText("")
        else:
            self.status_label.setText(f"{total} archivo(s) cargado(s)")
            self.status_label.setStyleSheet("color: #00ff88; font-weight: bold;")

    # ── API pública ───────────────────────────────────────────────

    def get_files(self) -> Dict[str, str]:
        return dict(self.file_paths)

    def clear_all(self) -> None:
        self.file_paths.clear()
        self.table.setRowCount(0)
        self._update_status()
        self.files_changed.emit(self.file_paths)

    def validate(self) -> bool:
        missing = [
            info["label"]
            for fid, info in FILE_TYPES.items()
            if info["required"] and fid not in self.file_paths
        ]
        if missing:
            QMessageBox.warning(
                self,
                "Archivos Requeridos",
                "Faltan:\n" + "\n".join(f"• {m}" for m in missing),
            )
            return False
        return True
