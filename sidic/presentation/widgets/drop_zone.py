"""
Zona de arrastrar y soltar archivos GIS.

Acepta archivos .shp, .geojson, .gpkg, .kml, .csv y carpetas.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_SUPPORTED_EXTENSIONS = {".shp", ".geojson", ".gpkg", ".kml", ".csv"}
_ASSOCIATED_EXTENSIONS = {".dbf", ".shx", ".prj", ".qpj", ".cpg"}


class DropZone(QFrame):
    """
    Zona visual de drag-and-drop.

    Signals
    -------
    files_dropped(list[str])
        Rutas absolutas de archivos/carpetas soltados.
    """

    files_dropped = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("dropZone")
        self._setup_ui()

    # ── UI ────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("⬇")
        icon.setStyleSheet("font-size: 36px; color: #00d4ff;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        self._text = QLabel("Arrastra archivos GIS o una carpeta aquí")
        self._text.setObjectName("dropZoneText")
        self._text.setStyleSheet(
            "font-size: 13pt; color: #888888; font-weight: bold;"
        )
        self._text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._text)

        btn = QPushButton("  Examinar Archivos  ")
        btn.setObjectName("dropZoneBrowse")
        btn.setMinimumWidth(180)
        btn.setMinimumHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._on_browse)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        hint = QLabel(
            "Formatos: .shp .geojson .gpkg .kml .csv | "
            "También puedes arrastrar carpetas"
        )
        hint.setObjectName("dropZoneHint")
        hint.setStyleSheet("font-size: 9pt; color: #555566;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

    # ── Examinar ──────────────────────────────────────────────────

    def _on_browse(self) -> None:
        msg = QMessageBox(self)
        msg.setWindowTitle("Seleccionar")
        msg.setText("¿Qué desea seleccionar?")
        btn_files = msg.addButton("Archivos GIS", QMessageBox.ButtonRole.ActionRole)
        btn_folder = msg.addButton("Carpeta", QMessageBox.ButtonRole.ActionRole)
        msg.addButton(QMessageBox.StandardButton.Cancel)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == btn_files:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Seleccionar archivos GIS",
                str(Path.home()),
                "Archivos GIS (*.shp *.geojson *.gpkg *.kml *.csv);;"
                "Shapefile (*.shp);;GeoJSON (*.geojson);;Todos (*.*)",
            )
            if files:
                self.files_dropped.emit(files)
        elif clicked == btn_folder:
            folder = QFileDialog.getExistingDirectory(
                self, "Seleccionar carpeta con archivos GIS", str(Path.home()),
            )
            if folder:
                self.files_dropped.emit([folder])

    # ── Drag & Drop events ────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:  # noqa: N802
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)

        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.toLocalFile()
        ]
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
