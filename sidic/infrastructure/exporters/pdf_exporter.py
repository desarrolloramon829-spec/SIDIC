"""
Exportador a PDF.

Genera PDF directamente usando reportlab (sin depender de Word).
También ofrece conversión DOCX → PDF como alternativa.
"""
from __future__ import annotations

import io
import logging
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from sidic.infrastructure.exporters.base_exporter import (
    BaseExporter,
    ExportOptions,
    ExportResult,
)

logger = logging.getLogger(__name__)


class PDFExporter(BaseExporter):
    """
    Exportador nativo a PDF usando reportlab.

    Si reportlab no está disponible, ofrece conversión DOCX → PDF
    usando LibreOffice o docx2pdf.
    """

    def export(
        self,
        output_path: str | Path,
        tables: Dict[str, pd.DataFrame],
        charts: Optional[Dict[str, bytes]] = None,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        output_path = Path(output_path)
        options = options or ExportOptions()
        charts = charts or {}
        self._ensure_dir(output_path)

        # Intentar con reportlab (nativo)
        try:
            return self._export_reportlab(output_path, tables, charts, options)
        except ImportError:
            logger.info("reportlab no disponible, se necesita DOCX → PDF")

        # Fallback: generar DOCX temporal y convertir
        try:
            return self._export_via_docx(output_path, tables, charts, options)
        except Exception as e:
            msg = (
                f"No se pudo generar PDF: {e}. "
                "Instale reportlab ('pip install reportlab') o LibreOffice."
            )
            self._last_error = msg
            return ExportResult(success=False, error=msg)

    def _export_reportlab(
        self,
        output_path: Path,
        tables: Dict[str, pd.DataFrame],
        charts: Dict[str, bytes],
        options: ExportOptions,
    ) -> ExportResult:
        """Genera PDF directamente con reportlab."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Image,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "SidicTitle",
            parent=styles["Heading1"],
            textColor=colors.HexColor("#CC0000"),
            fontSize=16,
            spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            "SidicHeading",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#CC0000"),
            fontSize=13,
            spaceBefore=20,
            spaceAfter=8,
        )

        elements: list = []

        # Título
        elements.append(Paragraph(options.titulo, title_style))
        if options.jurisdiccion:
            elements.append(
                Paragraph(f"Jurisdicción: {options.jurisdiccion}", styles["Normal"])
            )
        elements.append(Spacer(1, 20))

        # Secciones
        _SECTIONS = [
            ("cuadro_referencia", "CUADRO DE REFERENCIA"),
            ("delitos", "DELITOS CON MODALIDADES"),
            ("dias_semana", "DÍAS DE LA SEMANA"),
            ("franja_horaria", "FRANJA HORARIA"),
            ("movilidad", "MEDIOS DE MOVILIDAD"),
            ("armas", "ARMAS / MEDIOS"),
            ("ambito", "ÁMBITO DE OCURRENCIA"),
            ("esclarecimiento", "ÍNDICE DE ESCLARECIMIENTO"),
            ("mencionados", "MENCIONADOS"),
            ("aprehendidos", "APREHENDIDOS"),
            ("comparativa_detallada", "CUADRO COMPARATIVO"),
        ]

        for key, title in _SECTIONS:
            if key not in tables or tables[key].empty:
                continue

            elements.append(PageBreak())
            elements.append(Paragraph(title, heading_style))
            elements.append(Spacer(1, 8))

            # Tabla
            df = tables[key]
            display_cols = [
                c for c in df.columns if c not in ("color_fila", "tendencia", "Color")
            ]
            data = [display_cols]  # header
            for _, row in df.iterrows():
                data.append([str(row[c]) if pd.notna(row[c]) else "" for c in display_cols])

            tbl = Table(data, repeatRows=1)
            tbl_style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#CC0000")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F0F0")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])

            # Detectar fila TOTAL
            for ri, (_, row) in enumerate(df.iterrows(), start=1):
                if "TOTAL" in str(row.iloc[0]).upper():
                    tbl_style.add(
                        "BACKGROUND", (0, ri), (-1, ri), colors.HexColor("#FFFF00")
                    )
                    tbl_style.add(
                        "FONTNAME", (0, ri), (-1, ri), "Helvetica-Bold"
                    )

            tbl.setStyle(tbl_style)
            elements.append(tbl)

            # Gráfico
            if options.incluir_graficos and key in charts:
                elements.append(Spacer(1, 12))
                try:
                    img = Image(io.BytesIO(charts[key]))
                    img.drawWidth = 14 * cm
                    img.drawHeight = 9 * cm
                    elements.append(img)
                except Exception as e:
                    logger.warning(f"Imagen para {key}: {e}")

        doc.build(elements)
        return ExportResult(success=True, output_path=str(output_path))

    def _export_via_docx(
        self,
        output_path: Path,
        tables: Dict[str, pd.DataFrame],
        charts: Dict[str, bytes],
        options: ExportOptions,
    ) -> ExportResult:
        """Genera DOCX temporal y lo convierte a PDF."""
        from sidic.infrastructure.exporters.word_exporter import WordExporter

        docx_path = output_path.with_suffix(".docx")
        word = WordExporter()
        result = word.export(docx_path, tables, charts, options)
        if not result.success:
            return ExportResult(success=False, error=f"Falló DOCX: {result.error}")

        success = _convert_docx_to_pdf(docx_path, output_path)
        if success:
            # Eliminar DOCX temporal
            try:
                docx_path.unlink()
            except Exception:
                pass
            return ExportResult(success=True, output_path=str(output_path))
        else:
            return ExportResult(
                success=False,
                error=(
                    "No se pudo convertir DOCX a PDF. "
                    "Instale LibreOffice o reportlab."
                ),
            )


# ═══════════════════════════════════════════════════════════════════════════
# CONVERSIÓN DOCX → PDF
# ═══════════════════════════════════════════════════════════════════════════


def _convert_docx_to_pdf(docx_path: Path, pdf_path: Path) -> bool:
    """Convierte DOCX a PDF usando docx2pdf o LibreOffice."""
    # 1. docx2pdf (requiere Word en Windows)
    try:
        from docx2pdf import convert

        convert(str(docx_path), str(pdf_path))
        if pdf_path.exists():
            return True
    except (ImportError, Exception) as e:
        logger.debug(f"docx2pdf: {e}")

    # 2. LibreOffice
    soffice = _find_libreoffice()
    if soffice:
        try:
            subprocess.run(
                [
                    soffice,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(pdf_path.parent),
                    str(docx_path),
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
            # LibreOffice usa el nombre original con .pdf
            generated = docx_path.with_suffix(".pdf")
            if generated != pdf_path and generated.exists():
                generated.rename(pdf_path)
            return pdf_path.exists()
        except Exception as e:
            logger.debug(f"LibreOffice: {e}")

    return False


def _find_libreoffice() -> Optional[str]:
    """Busca LibreOffice en el sistema."""
    system = platform.system()
    paths: List[str] = []

    if system == "Windows":
        paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
    elif system == "Darwin":
        paths = ["/Applications/LibreOffice.app/Contents/MacOS/soffice"]
    else:
        paths = ["/usr/bin/libreoffice", "/usr/bin/soffice"]

    for p in paths:
        if Path(p).exists():
            return p
    return None
