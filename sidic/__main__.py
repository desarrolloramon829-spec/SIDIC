"""
Permite ejecutar S.I.D.I.C con: python -m sidic
"""
import sys

from sidic.app import main_gui, main_cli

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        sys.argv.pop(1)
        main_cli()
    else:
        main_gui()
