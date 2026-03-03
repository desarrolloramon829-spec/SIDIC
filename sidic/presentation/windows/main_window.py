"""
Ventana principal de S.I.D.I.C v2.

Contiene header con estadísticas, tabs de generación/vista-previa,
barra de progreso y menú de acciones.
"""
from __future__ import annotations

import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import sidic
from sidic.application.dto.dtos import (
    ComparisonInputDTO,
    FilterInputDTO,
    GenerateReportInputDTO,
    LoadDataInputDTO,
    PeriodInputDTO,
)
from sidic.presentation.viewmodels.main_viewmodel import (
    AppState,
    MainViewModel,
    PeriodState,
)
from sidic.presentation.viewmodels.worker import ReportWorker
from sidic.presentation.widgets.comparative_periods import ComparativePeriodSelector
from sidic.presentation.widgets.export_options import ExportOptionsPanel
from sidic.presentation.widgets.file_selector import FileSelector
from sidic.presentation.widgets.period_selector import PeriodSelector

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Ventana principal de S.I.D.I.C."""

    def __init__(self) -> None:
        super().__init__()
        self._vm = MainViewModel(self)
        self._worker: Optional[ReportWorker] = None
        self._setup_window()
        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()
        self._load_styles()

    # ═══════════════════════════════════════════════════════════════
    # SETUP
    # ═══════════════════════════════════════════════════════════════

    def _setup_window(self) -> None:
        self.setWindowTitle(
            "S.I.D.I.C — Sistema de Información Delictual e Inteligencia Criminal"
        )
        self.setMinimumSize(1200, 800)
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            self.setGeometry(
                (geo.width() - 1200) // 2,
                (geo.height() - 800) // 2,
                1200, 800,
            )

    def _setup_menu(self) -> None:
        mb = self.menuBar()

        # Archivo
        file_menu = mb.addMenu("&Archivo")
        self._add_action(file_menu, "🆕 Nuevo Reporte", "Ctrl+N", self._on_new)
        self._add_action(file_menu, "📂 Abrir Proyecto", "Ctrl+O", self._on_open_project)
        self._add_action(file_menu, "💾 Guardar Proyecto", "Ctrl+S", self._on_save_project)
        file_menu.addSeparator()
        self._add_action(file_menu, "🚪 Salir", "Ctrl+Q", self.close)

        # Herramientas
        tools_menu = mb.addMenu("&Herramientas")
        self._add_action(tools_menu, "⚙️ Configuración", "", self._on_config)
        self._add_action(tools_menu, "📋 Mapeo de Campos", "", self._on_field_map)

        # Ayuda
        help_menu = mb.addMenu("A&yuda")
        self._add_action(help_menu, "📖 Manual", "F1", self._on_help)
        self._add_action(help_menu, "ℹ️ Acerca de", "", self._on_about)

    @staticmethod
    def _add_action(menu, text: str, shortcut: str, slot) -> None:
        action = QAction(text, menu)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        menu.addAction(action)

    # ── UI Principal ─────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # Header
        root.addWidget(self._build_header())

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_report_tab(), "📊 Generar Informe")
        self.tabs.addTab(self._build_preview_tab(), "👁️ Vista Previa")
        root.addWidget(self.tabs, 1)

        # Footer (progreso + botones)
        root.addWidget(self._build_footer())

    # ── Header ────────────────────────────────────────────────────

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setStyleSheet(
            "QFrame{background:qlineargradient("
            "x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #0a0a12,stop:0.5 #12121c,stop:1 #0a0a12);"
            "border:none;border-bottom:2px solid #00d4ff;padding:16px;}"
        )
        lay = QHBoxLayout(header)
        lay.setContentsMargins(0, 0, 0, 0)

        # Título
        col = QVBoxLayout()
        title = QLabel("S.I.D.I.C")
        title.setStyleSheet(
            "color:#00d4ff;font-size:32pt;font-weight:bold;letter-spacing:8px;"
        )
        col.addWidget(title)
        sub = QLabel("Sistema de Información Delictual e Inteligencia Criminal")
        sub.setStyleSheet("color:#888888;font-size:10pt;letter-spacing:2px;")
        col.addWidget(sub)
        lay.addLayout(col)
        lay.addStretch()

        # Stats
        stats = QHBoxLayout()
        stats.setSpacing(24)
        self.stat_hechos = self._stat_card("0", "Hechos")
        self.stat_mencionados = self._stat_card("0", "Mencionados")
        self.stat_aprehendidos = self._stat_card("0", "Aprehendidos")
        stats.addWidget(self.stat_hechos)
        stats.addWidget(self.stat_mencionados)
        stats.addWidget(self.stat_aprehendidos)
        lay.addLayout(stats)

        return header

    def _stat_card(self, value: str, label: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame{background:#12121c;border:1px solid #333344;"
            "border-radius:8px;padding:8px 16px;}"
            "QFrame:hover{border-color:#00d4ff;}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(8, 8, 8, 8)
        cl.setSpacing(0)

        vlbl = QLabel(value)
        vlbl.setStyleSheet("color:#00d4ff;font-size:20pt;font-weight:bold;")
        vlbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(vlbl)

        tlbl = QLabel(label)
        tlbl.setStyleSheet("color:#888888;font-size:9pt;")
        tlbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(tlbl)

        card.value_label = vlbl  # type: ignore[attr-defined]
        return card

    # ── Tab: Generar Informe ──────────────────────────────────────

    def _build_report_tab(self) -> QWidget:
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(0, 16, 0, 0)
        lay.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setSpacing(16)

        # Selector de archivos
        self.file_selector = FileSelector()
        self.file_selector.files_changed.connect(self._on_files_changed)
        cl.addWidget(self.file_selector)

        # Período principal
        self.period_selector = PeriodSelector()
        self.period_selector.period_changed.connect(self._on_period_changed)
        cl.addWidget(self.period_selector)

        # Toggle comparativo
        self.check_comparative = QCheckBox("📊 INCLUIR ANÁLISIS COMPARATIVO")
        self.check_comparative.setStyleSheet(
            "QCheckBox{color:#00d4ff;font-weight:bold;font-size:11pt;"
            "padding:12px 8px;background:rgba(0,212,255,0.1);"
            "border:1px solid #333344;border-radius:6px;}"
            "QCheckBox:hover{background:rgba(0,212,255,0.2);border-color:#00d4ff;}"
            "QCheckBox::indicator{width:20px;height:20px;}"
            "QCheckBox::indicator:checked{background:#00d4ff;border:2px solid #00d4ff;border-radius:4px;}"
            "QCheckBox::indicator:unchecked{background:#1a1a2e;border:2px solid #333344;border-radius:4px;}"
        )
        self.check_comparative.toggled.connect(self._on_comparative_toggled)
        cl.addWidget(self.check_comparative)

        # Períodos comparativos (inicialmente oculto)
        self.comp_container = QFrame()
        self.comp_container.setStyleSheet(
            "QFrame{border:2px solid #00d4ff;border-radius:8px;"
            "margin-top:12px;padding:12px;}"
        )
        self.comp_container.setVisible(False)
        comp_lay = QVBoxLayout(self.comp_container)

        info = QLabel(
            "Configure los períodos anteriores para comparar.\n"
            "Se generarán cuadros comparativos con variaciones porcentuales."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#888888;padding:4px;")
        comp_lay.addWidget(info)

        self.comparative_periods = ComparativePeriodSelector()
        comp_lay.addWidget(self.comparative_periods)
        cl.addWidget(self.comp_container)

        # Opciones de exportación
        self.export_options = ExportOptionsPanel()
        cl.addWidget(self.export_options)

        cl.addStretch()
        scroll.setWidget(content)
        lay.addWidget(scroll)
        return tab

    # ── Tab: Vista previa ─────────────────────────────────────────

    def _build_preview_tab(self) -> QWidget:
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(0, 16, 0, 0)

        placeholder = QLabel(
            "📋 Vista Previa\n\n"
            "Aquí se mostrará una vista previa del reporte\n"
            "una vez que se carguen los datos."
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color:#666666;font-size:14pt;padding:48px;")
        lay.addWidget(placeholder)
        return tab

    # ── Footer ────────────────────────────────────────────────────

    def _build_footer(self) -> QWidget:
        footer = QFrame()
        footer.setStyleSheet(
            "QFrame{background:#0d0d18;border:1px solid #333344;"
            "border-radius:8px;padding:12px;}"
        )
        fl = QVBoxLayout(footer)
        fl.setSpacing(12)

        # Progreso
        prow = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        prow.addWidget(self.progress_bar)
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color:#00d4ff;")
        self.progress_label.setVisible(False)
        prow.addWidget(self.progress_label)
        fl.addLayout(prow)

        # Botones
        brow = QHBoxLayout()
        brow.addStretch()

        self.btn_preview = QPushButton("👁️ Vista Previa")
        self.btn_preview.setProperty("class", "secondary")
        self.btn_preview.clicked.connect(self._on_preview)
        brow.addWidget(self.btn_preview)

        self.btn_generate = QPushButton("🚀 GENERAR REPORTE")
        self.btn_generate.setMinimumWidth(200)
        self.btn_generate.clicked.connect(self._on_generate)
        brow.addWidget(self.btn_generate)

        fl.addLayout(brow)
        return footer

    # ── Barra de estado y estilos ─────────────────────────────────

    def _setup_statusbar(self) -> None:
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.status_label = QLabel("Listo")
        sb.addWidget(self.status_label)
        sb.addPermanentWidget(QLabel(f"v{sidic.__version__}"))

    def _load_styles(self) -> None:
        qss = Path(__file__).resolve().parent.parent / "styles" / "police_dark.qss"
        if qss.exists():
            self.setStyleSheet(qss.read_text(encoding="utf-8"))

    # ═══════════════════════════════════════════════════════════════
    # SLOTS
    # ═══════════════════════════════════════════════════════════════

    def _on_files_changed(self, files: dict) -> None:
        self._vm.set_files(files)

    def _on_period_changed(self, start: date, end: date) -> None:
        self._vm.set_main_period(start, end)

    def _on_comparative_toggled(self, checked: bool) -> None:
        self.comp_container.setVisible(checked)
        self.export_options.set_comparative_visible(checked)
        self._vm.set_comparative_mode(checked)

    def _on_preview(self) -> None:
        self.tabs.setCurrentIndex(1)
        self.status_label.setText("Vista previa generada")

    def _on_new(self) -> None:
        self.file_selector.clear_all()
        self._vm.reset()
        self.tabs.setCurrentIndex(0)
        self.status_label.setText("Nuevo reporte iniciado")

    # ── Generación de reporte ─────────────────────────────────────

    def _on_generate(self) -> None:
        files = self.file_selector.get_files()
        if not files:
            QMessageBox.warning(
                self, "Sin Datos",
                "No hay archivos cargados para generar el informe.",
            )
            return

        # Validar período
        ok, msg = self.period_selector.validate()
        if not ok:
            QMessageBox.warning(self, "Período Inválido", msg)
            return

        # Validar comparativos
        if self.check_comparative.isChecked():
            ok, msg = self.comparative_periods.validate()
            if not ok:
                QMessageBox.warning(self, "Períodos Inválidos", msg)
                return

        # Sincronizar ViewModel
        self._sync_vm()

        # Elegir archivo de salida
        fmt = self.export_options.get_formato()
        filter_map = {
            "excel": "Excel (*.xlsx)",
            "word": "Word (*.docx)",
            "pdf": "PDF (*.pdf)",
            "todos": "Todos (*.*)",
        }
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte",
            str(
                Path.home()
                / "Documents"
                / f"Informe_Delictual_{datetime.now():%Y%m%d}"
            ),
            filter_map.get(fmt, "Excel (*.xlsx)"),
        )
        if not output_path:
            return

        self._start_generation(output_path)

    def _sync_vm(self) -> None:
        """Sincroniza todos los widgets con el ViewModel."""
        vm = self._vm

        # Archivos
        vm.set_files(self.file_selector.get_files())

        # Período
        s, e = self.period_selector.get_period()
        vm.set_main_period(s, e)

        # Comparativos
        vm.set_comparative_mode(self.check_comparative.isChecked())
        if self.check_comparative.isChecked():
            comp_periods = []
            for name, cs, ce in self.comparative_periods.get_periods():
                comp_periods.append(PeriodState(name=name, start_date=cs, end_date=ce))
            vm.set_comparison_periods(comp_periods)
            vm.set_modo_variacion(self.comparative_periods.get_modo_variacion())

        # Opciones
        opts = self.export_options.get_options()
        for k, v in opts.items():
            vm.set_option(k, v)
        vm.set_formato(self.export_options.get_formato())
        vm.set_categorias(self.export_options.get_categorias_incluidas())

    def _start_generation(self, output_path: str) -> None:
        self.btn_generate.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(True)
        self.progress_label.setText("Iniciando…")

        vm = self._vm
        load_input = vm.build_load_input()
        report_input = vm.build_report_input(output_path)
        filter_input = vm.build_filter_input()
        comp_input = vm.build_comparison_input() if vm.state.comparative_mode else None

        self._worker = ReportWorker(
            load_input=load_input,
            report_input=report_input,
            filter_input=filter_input,
            comparison_input=comp_input,
            parent=self,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.data_loaded.connect(self._on_data_loaded)
        self._worker.start()

    # ── Callbacks del worker ──────────────────────────────────────

    def _on_progress(self, value: int, message: str) -> None:
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        self.status_label.setText(message)

    def _on_finished(self, success: bool, path: str, message: str) -> None:
        self._restore_buttons()
        if success:
            QMessageBox.information(
                self, "Reporte Generado", f"{message}\n\nArchivo: {path}",
            )
            self.status_label.setText(f"✅ {message}")
        else:
            self.status_label.setText("⚠️ Completado con advertencias")

    def _on_error(self, detail: str) -> None:
        self._restore_buttons()
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error en la Generación")
        msg.setText("Ocurrió un error durante la generación del reporte.")
        msg.setDetailedText(detail)
        msg.exec()
        self.status_label.setText("❌ Error en la generación")

    def _on_data_loaded(self, report_data) -> None:
        """Actualiza estadísticas del header cuando se cargan datos."""
        self._vm.report_data = report_data
        try:
            if report_data and report_data.periods:
                p = report_data.periods[0]
                self.stat_hechos.value_label.setText(str(len(p.crime_records)))  # type: ignore[attr-defined]
                self.stat_mencionados.value_label.setText(str(len(p.mentioned_persons)))  # type: ignore[attr-defined]
                self.stat_aprehendidos.value_label.setText(str(len(p.apprehended_persons)))  # type: ignore[attr-defined]
        except Exception:
            pass

    def _restore_buttons(self) -> None:
        self.btn_generate.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

    # ═══════════════════════════════════════════════════════════════
    # MENÚ STUBS
    # ═══════════════════════════════════════════════════════════════

    def _on_open_project(self) -> None:
        QMessageBox.information(self, "Próximamente", "Disponible en futuras versiones.")

    def _on_save_project(self) -> None:
        QMessageBox.information(self, "Próximamente", "Disponible en futuras versiones.")

    def _on_config(self) -> None:
        QMessageBox.information(self, "Próximamente", "Disponible en futuras versiones.")

    def _on_field_map(self) -> None:
        QMessageBox.information(self, "Próximamente", "Disponible en futuras versiones.")

    def _on_help(self) -> None:
        QMessageBox.information(
            self,
            "Ayuda",
            "S.I.D.I.C — Sistema de Información Delictual\n\n"
            "1. Seleccione los archivos GIS\n"
            "2. Configure el período de análisis\n"
            "3. Ajuste las opciones de exportación\n"
            "4. Haga clic en «Generar Reporte»",
        )

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "Acerca de S.I.D.I.C",
            f"<h2>S.I.D.I.C</h2>"
            f"<p><b>Sistema de Información Delictual e Inteligencia Criminal</b></p>"
            f"<p>Versión {sidic.__version__}</p><hr>"
            f"<p>Procesamiento de datos GIS delictuales y generación "
            f"de informes estadísticos profesionales.</p>"
            f"<hr><p>Desarrollado con ❤️ para la seguridad ciudadana.</p>",
        )


# ── Punto de entrada ──────────────────────────────────────────────

def run_app() -> None:
    """Lanza la aplicación GUI."""
    app = QApplication(sys.argv)
    app.setApplicationName("S.I.D.I.C")
    app.setApplicationVersion(sidic.__version__)
    app.setOrganizationName("Policia")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
