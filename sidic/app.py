"""
Punto de entrada principal de S.I.D.I.C v2.0
"""
import sys
import logging
from pathlib import Path


def configure_logging(level: str = "INFO") -> None:
    """Configura el logging global de la aplicación."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main_gui() -> None:
    """Inicia la aplicación con interfaz gráfica PyQt6."""
    configure_logging()
    logger = logging.getLogger(__name__)

    try:
        from PyQt6.QtWidgets import QApplication
        from sidic.presentation.windows.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("S.I.D.I.C")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("Policía de Tucumán")

        window = MainWindow()
        window.show()

        sys.exit(app.exec())
    except ImportError as e:
        logger.error(f"Dependencia faltante: {e}")
        logger.error("Ejecute: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)


def main_cli() -> None:
    """Inicia la aplicación en modo línea de comandos."""
    import argparse

    configure_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        prog="sidic",
        description="S.I.D.I.C — Sistema de Información Delictual e Inteligencia Criminal",
    )
    parser.add_argument("--version", action="version", version="S.I.D.I.C v2.0.0")
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Ruta al archivo GIS de entrada (shapefile, GeoJSON, KML, GeoPackage)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("./output"),
        help="Directorio de salida para los reportes",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["excel", "word", "pdf", "all"],
        default="excel",
        help="Formato de exportación (default: excel)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Fecha de inicio del período (DD-MM-YYYY)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="Fecha de fin del período (DD-MM-YYYY)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="default",
        help="Perfil de comisaría a utilizar",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Modo detallado (debug logging)",
    )

    args = parser.parse_args()

    if args.verbose:
        configure_logging("DEBUG")

    logger.info("S.I.D.I.C v2.0.0 — Modo CLI")
    logger.info(f"Entrada: {args.input}")
    logger.info(f"Salida: {args.output}")
    logger.info(f"Formato: {args.format}")

    # TODO: Implementar pipeline CLI completo en GenerateReportUseCase
    logger.warning("Modo CLI en desarrollo. Use la interfaz gráfica por ahora.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        sys.argv.pop(1)
        main_cli()
    else:
        main_gui()
