import asyncio
import sys
from pathlib import Path

from PySide6.QtGui import QPalette, QColor, QIcon
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from interfaz.main_window import MainWindow


def resource_path(relative: str) -> Path:
    """
    Devuelve la ruta absoluta a un recurso, tanto en modo normal
    como cuando el programa está empacado con PyInstaller (onefile).
    """
    # OJO: siempre convertimos a Path, aunque _MEIPASS sea str
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative


def tema_negro_naranja(app: QApplication):
    app.setStyle("Fusion")
    pal = QPalette()
    negro = QColor(15, 15, 16)
    gris  = QColor(28, 28, 30)
    texto = QColor(235, 235, 235)
    acento = QColor(255, 122, 24)

    pal.setColor(QPalette.Window, gris)
    pal.setColor(QPalette.WindowText, texto)
    pal.setColor(QPalette.Base, negro)
    pal.setColor(QPalette.AlternateBase, gris)
    pal.setColor(QPalette.Button, gris)
    pal.setColor(QPalette.ButtonText, texto)
    pal.setColor(QPalette.Text, texto)
    pal.setColor(QPalette.Highlight, acento)
    pal.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(pal)

    app.setStyleSheet("""
        QGroupBox {
            font-weight: 600; border: 1px solid #2b2b2e;
            border-radius: 6px; margin-top: 12px;
        }
        QGroupBox::title { color:#ff7a18; padding:0 6px; }
        QPushButton { border:1px solid #444; padding:6px 10px; border-radius:4px; }
        QPushButton:hover { border:1px solid #ff7a18; }
        QToolBar { spacing: 8px; }
    """)


def main():
    app = QApplication(sys.argv)
    tema_negro_naranja(app)

    # Event loop async de qasync
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Logo (asegúrate de que uav_iasa_logo.png está junto a main.py)
    logo_file = resource_path("uav_iasa_logo.png")
    logo_path = str(logo_file) if logo_file.exists() else None

    win = MainWindow(logo_path=logo_path)

    # Icono de la ventana / barra de tareas
    if logo_path:
        app.setWindowIcon(QIcon(logo_path))

    win.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
    