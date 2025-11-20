import asyncio
import csv
import sqlite3
import random
import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

from PySide6.QtCore import (
    Qt,
    QTimer,
    Signal,
    QObject,
    QSettings,
    QRectF,
    QPointF,
    QSize,
)
from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QColor,
    QFont,
    QPen,
    QBrush,
    QPolygonF,
    QLinearGradient,
)
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QLabel,
    QLineEdit,
    QPushButton,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
    QMessageBox,
    QComboBox,
    QTextEdit,
    QFormLayout,
    QStackedWidget,
    QFrame,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QGraphicsOpacityEffect,
)

import pyqtgraph as pg

# IMPORTAR BACKEND REAL DEL PROYECTO
from telemetria.telemetria import (
    TelemetrySample,
    BackendTelemetria,
    LoRaBackend,
)

# ----------------------------------------------------------------------
# CONFIGURACIÓN DE TEMAS (paleta negro / naranja del equipo)
# ----------------------------------------------------------------------

THEMES = {
    "dark": {
        "bg_main": "#050509",
        "bg_card": "#101018",
        "bg_sidebar": "#08080F",
        "border_color": "#262636",
        "text_main": "#F5F5FF",
        "text_secondary": "#8E8EAA",
        "text_title": "#FFFFFF",
        "accent_color": "#FF8A00",   # naranja principal
        "accent_soft": "#FFB84D",
        "danger_color": "#FF453A",
        "warning_color": "#FFD60A",
        "success_color": "#30D158",
        "nav_hover_bg": "#171723",
        "nav_checked_bg": "#161620",
        "graph_bg": "#060612",
        "graph_grid": "#2A2A3A",
        "console_bg": "#050509",
        "button_secondary_bg": "#191927",
    },
    "light": {
        "bg_main": "#F4F5FB",
        "bg_card": "#FFFFFF",
        "bg_sidebar": "#FFFFFF",
        "border_color": "#E0E0F0",
        "text_main": "#111827",
        "text_secondary": "#6B7280",
        "text_title": "#111111",
        "accent_color": "#FF8A00",
        "accent_soft": "#FFB84D",
        "danger_color": "#FF3B30",
        "warning_color": "#FF9500",
        "success_color": "#34C759",
        "nav_hover_bg": "#E5E7EB",
        "nav_checked_bg": "#FFE7C2",
        "graph_bg": "#FFFFFF",
        "graph_grid": "#E5E7EB",
        "console_bg": "#FFFFFF",
        "button_secondary_bg": "#E5E7EB",
    },
}


def build_stylesheet(theme_name: str) -> str:
    """
    Construye el stylesheet global de Qt en función del tema seleccionado.
    Aquí se ajustan colores, tamaños de fuente y efectos visuales básicos.
    """
    t = THEMES[theme_name]
    return f"""
QMainWindow {{
    background-color: {t["bg_main"]};
    font-family: "Segoe UI", system-ui;
}}

/* Sidebar */
QFrame#Sidebar {{
    background-color: {t["bg_sidebar"]};
    border-right: 1px solid {t["border_color"]};
}}
QLabel#SidebarTitle {{
    color: {t["text_title"]};
    font-weight: 900;
    font-size: 24px;
}}

/* Navegación lateral */
QPushButton[nav="true"] {{
    background-color: transparent;
    color: {t["text_secondary"]};
    border: none;
    text-align: left;
    padding: 10px 18px;
    font-size: 14px;
    font-weight: 600;
    border-radius: 10px;
}}
QPushButton[nav="true"]:hover {{
    background-color: {t["nav_hover_bg"]};
    color: {t["text_title"]};
}}
QPushButton[nav="true"]:checked {{
    background-color: {t["nav_checked_bg"]};
    color: {t["accent_color"]};
    border: 1px solid {t["accent_color"]};
}}

/* Botón cambio de tema */
QPushButton#ThemeToggleButton {{
    background-color: {t["button_secondary_bg"]};
    color: {t["text_main"]};
    border-radius: 999px;
    padding: 6px 12px;
    border: 1px solid {t["border_color"]};
}}

/* Tarjetas (cards) */
QFrame[card="true"] {{
    background-color: {t["bg_card"]};
    border-radius: 16px;
    border: 1px solid {t["border_color"]};
}}

/* Roles de texto */
QLabel[role="title"] {{
    font-size: 26px;
    font-weight: 800;
    color: {t["text_title"]};
}}
QLabel[role="subtitle"] {{
    font-size: 11px;
    letter-spacing: .7px;
    text-transform: uppercase;
    color: {t["text_secondary"]};
}}
QLabel[role="metric"] {{
    font-size: 32px;
    font-weight: 800;
}}
QLabel[role="metricSmall"] {{
    font-size: 22px;
    font-weight: 700;
}}
QLabel[role="unit"] {{
    font-size: 11px;
    color: {t["text_secondary"]};
}}

/* Inputs & botones */
QLineEdit, QComboBox {{
    background-color: {t["button_secondary_bg"]};
    color: {t["text_main"]};
    border-radius: 8px;
    padding: 6px 10px;
    border: 1px solid {t["border_color"]};
}}
QPushButton[action="primary"] {{
    background-color: {t["accent_color"]};
    background-image: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 {t["accent_soft"]},
                                      stop:1 {t["accent_color"]});
    color: white;
    border-radius: 999px;
    padding: 8px 18px;
    border: 1px solid #00000020;
    border-bottom: 3px solid #00000055;
    font-weight: 600;
}}
QPushButton[action="primary"]:hover {{
    background-color: {t["accent_soft"]};
}}
QPushButton[action="primary"]:pressed {{
    margin-top: 2px;
    margin-bottom: -2px;
    border-bottom: 1px solid #00000020;
}}

QPushButton[action="secondary"] {{
    background-color: {t["button_secondary_bg"]};
    color: {t["text_main"]};
    border-radius: 999px;
    padding: 6px 14px;
    border: 1px solid {t["border_color"]};
    font-weight: 500;
}}
QPushButton[action="secondary"]:hover {{
    background-color: {t["nav_hover_bg"]};
}}
QPushButton[action="secondary"]:pressed {{
    margin-top: 2px;
    margin-bottom: -2px;
}}

QPushButton[action="danger"] {{
    background-color: {t["danger_color"]};
    color: white;
    border-radius: 999px;
    padding: 8px 18px;
    border: none;
    font-weight: 600;
}}
QPushButton[action="danger"]:pressed {{
    margin-top: 2px;
    margin-bottom: -2px;
}}

/* Historial */
QTextEdit {{
    background-color: {t["console_bg"]};
    color: {t["text_main"]};
    border-radius: 12px;
    padding: 10px;
    font-family: Consolas, monospace;
    border: 1px solid {t["border_color"]};
}}
QTableWidget {{
    background-color: {t["bg_card"]};
    color: {t["text_main"]};
    border-radius: 12px;
    gridline-color: {t["border_color"]};
    border: 1px solid {t["border_color"]};
}}
QHeaderView::section {{
    background-color: {t["button_secondary_bg"]};
    color: {t["text_main"]};
    padding: 5px;
    border: 1px solid {t["border_color"]};
    font-weight: 600;
}}
QTableWidget::item:selected {{
    background-color: {t["accent_color"]};
    color: white;
}}
"""

pg.setConfigOption("antialias", True)
pg.setConfigOption("background", THEMES["dark"]["graph_bg"])
pg.setConfigOption("foreground", THEMES["dark"]["text_main"])

# ----------------------------------------------------------------------
# WIDGETS PERSONALIZADOS (batería, barras de señal, cámara, HUD)
# ----------------------------------------------------------------------


class BatteryWidget(QWidget):
    """
    Widget que dibuja un icono de batería con nivel y porcentaje dentro.
    El color cambia dinámicamente según el porcentaje restante.
    """

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.setFixedSize(110, 30)
        self.level = 0.0  # 0.0-1.0
        self.theme = theme
        self.percent_text = "0%"

    def set_level(self, pct: float):
        """Actualiza el nivel de la batería (0-100%)."""
        pct = max(0.0, min(100.0, pct))
        self.level = pct / 100.0
        self.percent_text = f"{pct:.0f}%"
        self.update()

    def set_theme(self, theme: str):
        """Actualiza el tema de colores del widget."""
        self.theme = theme
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        t = THEMES[self.theme]
        rect = self.rect().adjusted(4, 6, -14, -6)

        # Color según porcentaje
        if self.level > 0.5:
            fill = QColor(t["success_color"])
        elif self.level > 0.2:
            fill = QColor(t["warning_color"])
        else:
            fill = QColor(t["danger_color"])

        border = QColor(t["text_secondary"])

        # Cuerpo
        p.setPen(QPen(border, 2, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(rect, 6, 6)

        # Polo positivo
        pole_rect = QRectF(rect.right() + 2, rect.center().y() - 5, 6, 10)
        p.setBrush(border)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(pole_rect, 3, 3)

        # Relleno
        w_fill = rect.width() * self.level
        if w_fill > 0:
            inside = QRectF(
                rect.left() + 2, rect.top() + 2, max(0.0, w_fill - 4), rect.height() - 4
            )
            p.setBrush(fill)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(inside, 4, 4)

        # Texto de porcentaje centrado
        p.setPen(QColor(t["text_main"]))
        p.setFont(QFont("Segoe UI", 9, QFont.Medium))
        p.drawText(rect, Qt.AlignCenter, self.percent_text)

        p.end()


class SignalBarsWidget(QWidget):
    """
    Widget que muestra barras de intensidad de señal (0-4 barras).
    Se usa para representar la calidad del enlace.
    """

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.level = 0  # 0 a 4
        self.theme = theme
        self.setFixedSize(40, 20)

    def set_level(self, level: int):
        """Actualiza el número de barras iluminadas."""
        self.level = max(0, min(4, int(level)))
        self.update()

    def set_theme(self, theme: str):
        self.theme = theme
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = THEMES[self.theme]

        w = self.width()
        h = self.height()
        bar_w = w / 6
        spacing = bar_w / 2

        for i in range(4):
            x = spacing + i * (bar_w + spacing)
            frac = (i + 1) / 4.0
            bar_h = h * frac
            y = h - bar_h

            if i < self.level:
                col = QColor(t["accent_color"])
            else:
                col = QColor(t["border_color"])

            r = QRectF(x, y, bar_w, bar_h)
            p.setBrush(col)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(r, 2, 2)

        p.end()


class CameraWidget(QLabel):
    """
    Widget que simula el feed de la cámara del dron.
    - Muestra un degradado animado tipo HUD.
    - Dibuja FPS, resolución y etiqueta de calidad (SD/HD).
    - Permite guardar fotos y grabar “videos” (secuencia de imágenes).
    """

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.theme = theme
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Carpetas de medios: media/fotos y media/videos
        self.media_root = Path("media")
        self.photo_dir = self.media_root / "fotos"
        self.video_dir = self.media_root / "videos"
        for d in (self.media_root, self.photo_dir, self.video_dir):
            d.mkdir(parents=True, exist_ok=True)

        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self._reset_border)

        self.last_frame_time = time.time()
        self.frames_since = 0
        self.fps = 0.0

        # Estado de grabación
        self.is_recording = False
        self.recording_dir: Optional[Path] = None

        self._apply_base_style()

    def set_theme(self, theme: str):
        """Actualiza el tema de la cámara."""
        self.theme = theme
        self._apply_base_style()

    def _apply_base_style(self):
        """Aplica el estilo base del recuadro de cámara."""
        t = THEMES[self.theme]
        self.setStyleSheet(
            f"background-color: {t['bg_card']};"
            f"border-radius: 16px;"
            f"border: 1px solid {t['border_color']};"
            f"color: {t['text_secondary']};"
        )
        if self.pixmap() is None:
            self.setText("NO SIGNAL")

    def update_image(self, active: bool):
        """
        Actualiza el contenido visual de la cámara.
        En modo DEMO genera un fondo degradado y dibuja HUD + textos.
        """
        t = THEMES[self.theme]
        if not active:
            self.setPixmap(QPixmap())
            self.setText("NO SIGNAL")
            self._apply_base_style()
            return

        size = QSize(max(320, self.width()), max(200, self.height()))
        pix = QPixmap(size)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)

        # Degradado de fondo
        grad = QLinearGradient(0, 0, size.width(), size.height())
        grad.setColorAt(0.0, QColor(25, 25, 45))
        grad.setColorAt(0.4, QColor(40, 20, 60))
        grad.setColorAt(1.0, QColor(80, 30, 20))
        p.fillRect(pix.rect(), grad)

        # Cruz central simulando retícula
        p.setPen(QPen(QColor(t["accent_soft"]), 2, Qt.SolidLine, Qt.RoundCap))
        center = pix.rect().center()
        p.drawLine(center.x() - 30, center.y(), center.x() + 30, center.y())
        p.drawLine(center.x(), center.y() - 20, center.x(), center.y() + 20)

        # Cálculo de FPS simple
        now = time.time()
        self.frames_since += 1
        dt = now - self.last_frame_time
        if dt >= 1.0:
            self.fps = self.frames_since / dt
            self.frames_since = 0
            self.last_frame_time = now

        res_text = f"{size.width()}x{size.height()}"
        fps_text = f"{self.fps:4.1f} fps"
        quality = "HD" if size.width() >= 640 else "SD"

        # Etiquetas (timestamp arriba izquierda)
        p.setPen(QColor(t["text_main"]))
        p.setFont(QFont("Segoe UI", 11))
        p.drawText(
            pix.rect().adjusted(12, 8, -12, -8),
            Qt.AlignTop | Qt.AlignLeft,
            datetime.now().strftime("UAV LIVE • %H:%M:%S"),
        )
        # Datos de calidad abajo derecha
        p.drawText(
            pix.rect().adjusted(12, 8, -12, -8),
            Qt.AlignBottom | Qt.AlignRight,
            f"{quality}  {res_text}  •  {fps_text}",
        )

        p.end()
        self.setPixmap(pix)

        # Guardar frames cuando se está grabando
        if self.is_recording and self.recording_dir is not None:
            self.recording_dir.mkdir(parents=True, exist_ok=True)
            fn = self.recording_dir / f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
            pix.save(str(fn))

    def _reset_border(self):
        """Resetea el estilo del borde tras un destello visual."""
        self.flash_timer.stop()
        self._apply_base_style()

    # --- Capturas de foto / video -------------------------------------

    def save_snapshot(self) -> Optional[Path]:
        """Guarda una foto en la carpeta media/fotos y devuelve la ruta."""
        pm = self.pixmap()
        if pm is None:
            return None
        fn = self.photo_dir / f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        pm.save(str(fn))
        return fn

    def start_recording(self):
        """
        Inicia una “grabación” creando una subcarpeta en media/videos y
        guardando allí cada frame como JPG.
        """
        if self.is_recording:
            return
        session = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recording_dir = self.video_dir / f"video_{session}"
        self.is_recording = True

    def stop_recording(self):
        """Detiene la grabación de frames."""
        self.is_recording = False
        self.recording_dir = None


class AttitudeIndicator(QWidget):
    """
    Horizonte artificial que representa roll y pitch.
    Se dibuja un círculo, cielo, tierra y marcas de referencia.
    """

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.theme = theme
        self.roll = 0.0
        self.pitch = 0.0
        self.setMinimumSize(220, 220)

    def set_theme(self, theme: str):
        self.theme = theme
        self.update()

    def set_attitude(self, roll_deg: float, pitch_deg: float):
        """Actualiza los valores de actitud (en grados)."""
        self.roll = roll_deg or 0.0
        self.pitch = pitch_deg or 0.0
        self.update()

    def paintEvent(self, event):
        t = THEMES[self.theme]
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())
        rect = QRectF(0, 0, side, side).adjusted(8, 8, -8, -8)
        center = rect.center()
        radius = rect.width() / 2.0

        # Card exterior
        p.setBrush(QColor(t["bg_card"]))
        p.setPen(QPen(QColor(t["border_color"]), 1.8))
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 16, 16)

        # Transformaciones
        p.save()
        p.translate(center)
        p.rotate(-self.roll)

        # Pitch -> desplazamiento vertical
        pitch_norm = max(-45.0, min(45.0, self.pitch)) / 45.0
        y_offset = pitch_norm * radius * 0.6

        # Cielo y tierra
        sky_color = QColor("#1B4FFF") if self.theme == "dark" else QColor("#7FB3FF")
        ground_color = QColor("#5B3A13") if self.theme == "dark" else QColor("#C49A6C")

        sky_rect = QRectF(-radius * 2, -radius * 2 + y_offset, radius * 4, radius * 2)
        ground_rect = QRectF(-radius * 2, y_offset, radius * 4, radius * 2)

        p.setPen(Qt.NoPen)
        p.setBrush(sky_color)
        p.drawRect(sky_rect)
        p.setBrush(ground_color)
        p.drawRect(ground_rect)

        # Línea de horizonte
        p.setPen(QPen(QColor(t["text_main"]), 2))
        p.drawLine(QPointF(-radius * 2, y_offset), QPointF(radius * 2, y_offset))

        p.restore()
        p.translate(center)

        # Círculo principal
        p.setPen(QPen(QColor(t["border_color"]), 3, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(0, 0), radius * 0.9, radius * 0.9)

        # Avión
        aircraft_pen = QPen(QColor(t["accent_color"]), 3, Qt.SolidLine, Qt.RoundCap)
        p.setPen(aircraft_pen)
        p.drawLine(-radius * 0.4, 0, -radius * 0.1, 0)
        p.drawLine(radius * 0.1, 0, radius * 0.4, 0)
        p.drawEllipse(QPointF(0, 0), 4, 4)

        # Texto de roll/pitch
        p.setPen(QColor(t["text_secondary"]))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(
            QRectF(-radius, radius * 0.55, radius * 2, 20),
            Qt.AlignCenter,
            f"ROLL {self.roll:+.1f}°   PITCH {self.pitch:+.1f}°",
        )

        p.end()


# ----------------------------------------------------------------------
# MANEJO DE BASE DE DATOS PARA HISTORIAL
# ----------------------------------------------------------------------


class HistorialDB:
    """
    Encapsula el acceso a SQLite para guardar y leer historial de telemetría.
    Esta base de datos es propia de la interfaz (independiente del backend).
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute(
            """
        CREATE TABLE IF NOT EXISTS samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_iso TEXT,
            fuente TEXT,
            raw_line TEXT,
            t_s REAL,
            lat REAL,
            lon REAL,
            alt_msl REAL,
            alt_rel REAL,
            roll REAL,
            pitch REAL,
            yaw REAL,
            vn REAL,
            ve REAL,
            vd REAL,
            v REAL,
            vbat REAL,
            bat_pct REAL,
            modo TEXT,
            en_aire INTEGER,
            gps_fix INTEGER,
            sats INTEGER,
            temp REAL,
            hum REAL,
            pres REAL,
            rad REAL,
            acc REAL
        );
        """
        )
        self._buf: List[Tuple] = []

    def append(self, fuente: str, s: TelemetrySample):
        """Añade un nuevo registro al buffer de escritura."""
        row = (
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            fuente,
            getattr(s, "raw_line", "") or "",
            getattr(s, "time_s", 0.0) or 0.0,
            getattr(s, "lat_deg", None),
            getattr(s, "lon_deg", None),
            getattr(s, "abs_alt_m", None),
            getattr(s, "rel_alt_m", None),
            getattr(s, "roll_deg", None),
            getattr(s, "pitch_deg", None),
            getattr(s, "yaw_deg", None),
            getattr(s, "vx_ms", None),
            getattr(s, "vy_ms", None),
            getattr(s, "vz_ms", None),
            getattr(s, "groundspeed_ms", None),
            getattr(s, "voltage_v", None),
            getattr(s, "battery_percent", None),
            getattr(s, "flight_mode", None),
            int(bool(getattr(s, "in_air", False))),
            getattr(s, "gps_fix_type", None),
            getattr(s, "num_sat", None),
            getattr(s, "temp_c", None),
            getattr(s, "hum_pct", None),
            getattr(s, "pres_hpa", None),
            getattr(s, "rad_mwcm2", None),
            getattr(s, "acc_ms2", None),
        )
        self._buf.append(row)

    def flush(self):
        """Escribe en disco todos los registros pendientes en el buffer."""
        if not self._buf:
            return
        self._conn.executemany(
            """
            INSERT INTO samples (
                created_iso, fuente, raw_line, t_s, lat, lon, alt_msl, alt_rel,
                roll, pitch, yaw, vn, ve, vd, v, vbat, bat_pct, modo, en_aire,
                gps_fix, sats, temp, hum, pres, rad, acc
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            self._buf,
        )
        self._conn.commit()
        self._buf.clear()

    def get_all(self):
        """Devuelve todas las filas de la tabla (para exportar)."""
        cur = self._conn.execute("SELECT * FROM samples ORDER BY id ASC")
        cols = [d[0] for d in cur.description]
        return cols, cur.fetchall()

    def get_latest(self, limit: int = 50):
        """Devuelve las últimas `limit` filas (para vista rápida)."""
        cur = self._conn.execute(
            "SELECT * FROM samples ORDER BY id DESC LIMIT ?", (limit,)
        )
        cols = [d[0] for d in cur.description]
        return cols, cur.fetchall()

    def clear(self):
        """Elimina todo el historial."""
        self._conn.execute("DELETE FROM samples")
        self._conn.commit()
        self._conn.execute("VACUUM")
        self._conn.commit()

    def close(self):
        """Cierra la conexión de forma segura."""
        self.flush()
        self._conn.close()


# ----------------------------------------------------------------------
# DIÁLOGOS AUXILIARES (detalle de métrica, detalle de telemetría)
# ----------------------------------------------------------------------


class MetricDetailDialog(QDialog):
    """
    Diálogo que muestra una gráfica ampliada de una métrica específica
    junto con una tabla de sus valores recientes desde la base de datos.
    """

    def __init__(self, parent, db: HistorialDB, theme: str,
                 title: str, db_column: str, unit: str, color: str):
        super().__init__(parent)
        self.db = db
        self.db_column = db_column
        self.unit = unit
        self.color = color
        self.theme = theme

        self.setWindowTitle(title)
        self.resize(900, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        lbl_title = QLabel(title)
        lbl_title.setProperty("role", "title")
        layout.addWidget(lbl_title)

        # Gráfica ampliada
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.plot.setBackground(THEMES[self.theme]["graph_bg"])
        self.curve = self.plot.plot(
            pen=pg.mkPen(self.color, width=2)
        )
        layout.addWidget(self.plot, 2)

        # Tabla con historial de esa métrica
        self.table = QTableWidget()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        layout.addWidget(self.table, 1)

        self._reload_from_db()

    def _reload_from_db(self):
        """Lee las últimas muestras desde la BD y actualiza gráfica + tabla."""
        cols, rows = self.db.get_latest(500)
        if "t_s" not in cols or self.db_column not in cols:
            return
        i_ts = cols.index("t_s")
        i_val = cols.index(self.db_column)

        times = []
        vals = []
        data_rows = []
        for row in reversed(rows):  # más antiguo primero
            t = row[i_ts]
            v = row[i_val]
            if v is None:
                continue
            times.append(t)
            vals.append(v)
            data_rows.append((t, v))

        self.curve.setData(times, vals)

        self.table.setRowCount(len(data_rows))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["t_s [s]", f"Valor [{self.unit}]"])
        for r, (t, v) in enumerate(data_rows):
            self.table.setItem(r, 0, QTableWidgetItem(f"{t:.1f}"))
            self.table.setItem(r, 1, QTableWidgetItem(f"{v:.3f}"))


class TelemetryDetailDialog(QDialog):
    """
    Diálogo que muestra el resumen detallado de una muestra de telemetría
    con el formato de tabla que deseas (estado de vuelo, GPS, entorno, etc.).
    """

    def __init__(self, parent, sample: Optional[TelemetrySample], theme: str):
        super().__init__(parent)
        self.sample = sample
        self.theme = theme
        self.setWindowTitle("Detalle de Telemetría")
        self.resize(800, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        if sample is None:
            layout.addWidget(QLabel("Sin datos de telemetría aún."))
            return

        t = THEMES[theme]

        def card_section(title_text: str, rows_left: List[Tuple[str, str]],
                         rows_right: List[Tuple[str, str]]):
            """
            Construye una tarjeta con dos columnas de texto tipo:
              Etiqueta | Valor
            para agrupar cada categoría (estado, GPS, entorno, etc.).
            """
            card = QFrame()
            card.setProperty("card", True)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 10, 16, 10)
            cl.setSpacing(4)

            title_lbl = QLabel(title_text)
            title_lbl.setStyleSheet(f"color:{t['accent_color']}; font-weight:700;")
            cl.addWidget(title_lbl)

            grid = QGridLayout()
            grid.setHorizontalSpacing(40)
            grid.setVerticalSpacing(2)

            for r, (lbl, val) in enumerate(rows_left):
                l = QLabel(lbl)
                l.setProperty("role", "unit")
                v = QLabel(val)
                grid.addWidget(l, r, 0)
                grid.addWidget(v, r, 1)

            for r, (lbl, val) in enumerate(rows_right):
                l = QLabel(lbl)
                l.setProperty("role", "unit")
                v = QLabel(val)
                grid.addWidget(l, r, 2)
                grid.addWidget(v, r, 3)

            cl.addLayout(grid)
            return card

        # Estado de vuelo
        v_tot = getattr(sample, "groundspeed_ms", 0.0) or 0.0
        alt_rel = getattr(sample, "rel_alt_m", 0.0) or 0.0
        modo = getattr(sample, "flight_mode", "DEMO") or "DEMO"
        en_aire = "Sí" if getattr(sample, "in_air", False) else "No"
        estado_card = card_section(
            "Estado de vuelo",
            [("Modo", modo),
             ("En aire", en_aire),
             ("|V| (m/s)", f"{v_tot:.2f}"),
             ("Alt Rel (m)", f"{alt_rel:.1f}")],
            [],
        )

        # GPS
        lat = getattr(sample, "lat_deg", 0.0) or 0.0
        lon = getattr(sample, "lon_deg", 0.0) or 0.0
        alt_msl = getattr(sample, "abs_alt_m", 0.0) or 0.0
        fix = getattr(sample, "gps_fix_type", 0) or 0
        sats = getattr(sample, "num_sat", 0) or 0
        gps_card = card_section(
            "Posición / GPS",
            [("Lat (deg)", f"{lat:.6f}"),
             ("Lon (deg)", f"{lon:.6f}"),
             ("Alt MSL (m)", f"{alt_msl:.1f}"),
             ("GPS (fix/sats)", f"{fix}/{sats}")],
            [],
        )

        # Actitud / velocidades
        roll = getattr(sample, "roll_deg", 0.0) or 0.0
        pitch = getattr(sample, "pitch_deg", 0.0) or 0.0
        yaw = getattr(sample, "yaw_deg", 0.0) or 0.0
        vn = getattr(sample, "vx_ms", 0.0) or 0.0
        ve = getattr(sample, "vy_ms", 0.0) or 0.0
        vd = getattr(sample, "vz_ms", 0.0) or 0.0
        act_card = card_section(
            "Actitud / Velocidades",
            [("Roll (deg)", f"{roll:.1f}"),
             ("Pitch (deg)", f"{pitch:.1f}"),
             ("Yaw (deg)", f"{yaw:.1f}")],
            [("Vn (m/s)", f"{vn:.2f}"),
             ("Ve (m/s)", f"{ve:.2f}"),
             ("Vd (m/s)", f"{vd:.2f}")],
        )

        # Entorno
        temp = getattr(sample, "temp_c", 0.0) or 0.0
        hum = getattr(sample, "hum_pct", 0.0) or 0.0
        pres = getattr(sample, "pres_hpa", 0.0) or 0.0
        rad = getattr(sample, "rad_mwcm2", 0.0) or 0.0
        acc = getattr(sample, "acc_ms2", 0.0) or 0.0
        env_card = card_section(
            "Entorno",
            [("Temp (°C)", f"{temp:.2f}"),
             ("Hum (%)", f"{hum:.1f}"),
             ("Pres (hPa)", f"{pres:.1f}")],
            [("Rad (mW/cm²)", f"{rad:.3f}"),
             ("Acc (m/s²)", f"{acc:.2f}")],
        )

        layout.addWidget(estado_card)
        layout.addWidget(gps_card)
        layout.addWidget(act_card)
        layout.addWidget(env_card)


# ----------------------------------------------------------------------
# SEÑALES DE TELEMETRÍA Y VENTANA PRINCIPAL
# ----------------------------------------------------------------------


class TelemetrySignals(QObject):
    """Objeto de señales Qt para propagar muestras de telemetría al hilo de UI."""
    sample = Signal(object)


class MainWindow(QMainWindow):
    """
    Ventana principal de la interfaz de telemetría UAV-IASA UNAM.
    Contiene:
      - Dashboard de vuelo (cámara, HUD, estado rápido).
      - Gráficas individuales.
      - Historial de telemetría.
      - Configuración de conexión/backend.
    """

    def __init__(self, logo_path: Optional[str] = None) -> None:
        super().__init__()

        # Tema inicial
        self.current_theme = "dark"
        self.setStyleSheet(build_stylesheet(self.current_theme))
        pg.setConfigOption("background", THEMES[self.current_theme]["graph_bg"])
        pg.setConfigOption("foreground", THEMES[self.current_theme]["text_main"])

        self.setWindowTitle("UAV-IASA UNAM — Ground Control")
        self.setMinimumSize(1280, 800)

        # Configuración persistente
        self.settings = QSettings("UAV-IASA", "GCS")
        if logo_path:
            self.logo_path = logo_path
        else:
            root_logo = Path(__file__).resolve().parent.parent / "uav_iasa_logo.png"
            self.logo_path = str(root_logo) if root_logo.exists() else ""
        self.save_dir = Path("datos_vuelo")
        self.save_dir.mkdir(exist_ok=True)

        # Base de datos local de historial
        self.db = HistorialDB(self.save_dir / "telemetria_ui.db")
        self.db_timer = QTimer(self)
        self.db_timer.timeout.connect(self.db.flush)
        self.db_timer.start(1000)

        self.last_export_path: Optional[str] = None

        # Backend de telemetría
        self.backend = None
        self.backend_task = None
        self.source_name = "DEMO"

        # Buffers para gráficas
        self.time_buf = deque(maxlen=600)
        self.alt_buf = deque(maxlen=600)
        self.spd_buf = deque(maxlen=600)
        self.volt_buf = deque(maxlen=600)
        self.temp_buf = deque(maxlen=600)
        self.pres_buf = deque(maxlen=600)
        self.hum_buf = deque(maxlen=600)

        self.graph_paused = False
        self.graph_smooth = False

        # Tiempo de vuelo acumulado
        self.flight_time_s = 0.0
        self.last_time_s = None

        self.last_sample: Optional[TelemetrySample] = None

        self.signals = TelemetrySignals()
        self.signals.sample.connect(self._handle_sample)

        # Animación de “Conectando...”
        self.connect_anim_timer = QTimer(self)
        self.connect_anim_timer.timeout.connect(self._update_connecting_label)
        self._connecting_phase = 0
        self._is_connecting = False
        self._connecting_fake_level = 0

        # Construcción de UI
        self._build_ui()
        self._setup_button_animations()

        # Cámara simulada (se actualiza aunque sea DEMO)
        self.cam_timer = QTimer(self)
        self.cam_timer.timeout.connect(self._tick_camera)
        self.cam_timer.start(120)

        self.statusBar().hide()

    # ------------------------------------------------------------------
    # CONSTRUCCIÓN DE INTERFAZ
    # ------------------------------------------------------------------

    def _build_ui(self):
        """Crea el layout principal: sidebar + stack de páginas."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- SIDEBAR ---------------------------------------------------
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(270)
        sbl = QVBoxLayout(sidebar)
        sbl.setContentsMargins(22, 26, 22, 26)
        sbl.setSpacing(16)

        # Logo del equipo (más grande) y nombre debajo
        logo_column = QVBoxLayout()
        logo_column.setSpacing(8)
        logo_column.setAlignment(Qt.AlignHCenter)

        self.lbl_logo = QLabel()
        self.lbl_logo.setFixedSize(110, 110)
        self._load_logo()

        title = QLabel("UAV-IASA UNAM")
        title.setObjectName("SidebarTitle")

        logo_column.addWidget(self.lbl_logo, alignment=Qt.AlignHCenter)
        logo_column.addWidget(title, alignment=Qt.AlignHCenter)

        sbl.addLayout(logo_column)
        sbl.addSpacing(20)

        # Botones de navegación
        self.btn_dash = self._nav_button("Dashboard")
        self.btn_graph = self._nav_button("Gráficas")
        self.btn_hist = self._nav_button("Historial")
        self.btn_conn = self._nav_button("Conexión")

        self.btn_dash.setChecked(True)

        sbl.addWidget(self.btn_dash)
        sbl.addWidget(self.btn_graph)
        sbl.addWidget(self.btn_hist)
        sbl.addWidget(self.btn_conn)
        sbl.addStretch()

        # Botón de cambio de tema (oscuro/claro)
        self.btn_theme = QPushButton("Modo claro")
        self.btn_theme.setObjectName("ThemeToggleButton")
        self.btn_theme.clicked.connect(self._toggle_theme)
        sbl.addWidget(self.btn_theme)

        layout.addWidget(sidebar)

        # --- STACK DE PÁGINAS -----------------------------------------
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.page_dashboard = self._build_page_dashboard()
        self.page_graphs = self._build_page_graphs()
        self.page_history = self._build_page_history()
        self.page_connection = self._build_page_connection()

        self.stack.addWidget(self.page_dashboard)
        self.stack.addWidget(self.page_graphs)
        self.stack.addWidget(self.page_history)
        self.stack.addWidget(self.page_connection)

        # Conectar navegación
        self.btn_dash.clicked.connect(lambda: self._set_page(0))
        self.btn_graph.clicked.connect(lambda: self._set_page(1))
        self.btn_hist.clicked.connect(lambda: self._set_page(2))
        self.btn_conn.clicked.connect(lambda: self._set_page(3))

    def _nav_button(self, text: str) -> QPushButton:
        """Crea un botón de navegación lateral."""
        b = QPushButton(text)
        b.setCheckable(True)
        b.setProperty("nav", True)
        return b

    def _set_page(self, idx: int):
        """Cambia la página visible en el stack."""
        self.stack.setCurrentIndex(idx)
        btns = [self.btn_dash, self.btn_graph, self.btn_hist, self.btn_conn]
        for i, b in enumerate(btns):
            b.setChecked(i == idx)
        if idx == 2:
            # Al entrar al historial, recargar tabla
            self._reload_history_table()

    # ------------------------------------------------------------------
    # PÁGINA: DASHBOARD DE VUELO
    # ------------------------------------------------------------------

    def _build_page_dashboard(self) -> QWidget:
        """
        Construye la página principal del dashboard:
        - Encabezado con estado de enlace y “Contrato”.
        - Cámara grande.
        - HUD.
        - Panel de estado rápido.
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Panel de Vuelo")
        title.setProperty("role", "title")
        header.addWidget(title)

        header.addStretch()

        self.signal_widget = SignalBarsWidget(theme=self.current_theme)
        header.addWidget(self.signal_widget)

        self.lbl_conn_status = QLabel("Desconectado")
        self.lbl_conn_status.setProperty("role", "unit")
        header.addWidget(self.lbl_conn_status)

        layout.addLayout(header)

        # Tarjeta de “Contrato” (estado superior)
        status_card = QFrame()
        status_card.setProperty("card", True)
        sc = QVBoxLayout(status_card)
        sc.setContentsMargins(16, 10, 16, 10)
        sc.setSpacing(4)

        self.lbl_status_line1 = QLabel("GPS: -- sats | Modo: -- | En aire: -- | Fuente: --")
        # Hacemos la línea 1 un poco más grande
        accent = THEMES[self.current_theme]["accent_color"]
        self.lbl_status_line1.setStyleSheet(
            f"font-size: 12px; color: {THEMES[self.current_theme]['text_main']};"
        )

        self.lbl_status_line2 = QLabel(
            f"<span style='color:{accent}; font-weight:600;'>Contrato:</span> "
            "temp:--,hum:--,pres:--,rad:--,lat:--,lon:--,speed:--,acc:--,ts:--"
        )
        self.lbl_status_line2.setTextFormat(Qt.RichText)
        self.lbl_status_line2.setStyleSheet(
            f"font-size: 12px; color: {THEMES[self.current_theme]['text_main']};"
        )

        sc.addWidget(self.lbl_status_line1)
        sc.addWidget(self.lbl_status_line2)

        layout.addWidget(status_card)

        # Fila principal: Cámara + columna derecha
        row = QHBoxLayout()
        row.setSpacing(16)

        # --- Cámara grande -------------------------------------------
        cam_card = QFrame()
        cam_card.setProperty("card", True)
        cam_l = QVBoxLayout(cam_card)
        cam_l.setContentsMargins(16, 12, 16, 16)
        cam_l.setSpacing(8)

        # Barra superior: título + modo Foto/Grabar
        cam_top = QHBoxLayout()
        cam_label = QLabel("CÁMARA UAV")
        cam_label.setProperty("role", "subtitle")
        cam_top.addWidget(cam_label)
        cam_top.addStretch()

        # Botones de modo (texto en vez de solo iconos)
        self.btn_mode_photo = QPushButton("Foto")
        self.btn_mode_photo.setCheckable(True)
        self.btn_mode_photo.setProperty("action", "secondary")

        self.btn_mode_video = QPushButton("Grabar")
        self.btn_mode_video.setCheckable(True)
        self.btn_mode_video.setProperty("action", "secondary")

        self.btn_mode_photo.setChecked(True)
        self.capture_mode = "photo"
        self.is_recording = False

        self.btn_mode_photo.clicked.connect(lambda: self._set_capture_mode("photo"))
        self.btn_mode_video.clicked.connect(lambda: self._set_capture_mode("video"))

        # Botón de acción (guardar foto / iniciar-detener grabación)
        self.btn_capture = QPushButton("Guardar foto")
        self.btn_capture.setProperty("action", "primary")
        self.btn_capture.clicked.connect(self._capture_action)

        cam_top.addWidget(self.btn_mode_photo)
        cam_top.addWidget(self.btn_mode_video)
        cam_top.addWidget(self.btn_capture)

        cam_l.addLayout(cam_top)

        self.cam_widget = CameraWidget(theme=self.current_theme)
        cam_l.addWidget(self.cam_widget)

        row.addWidget(cam_card, 2)

        # --- Columna derecha: HUD + estado rápido --------------------
        col_right = QVBoxLayout()
        col_right.setSpacing(12)

        # HUD
        hud_card = QFrame()
        hud_card.setProperty("card", True)
        hud_l = QVBoxLayout(hud_card)
        hud_l.setContentsMargins(16, 12, 16, 16)
        hud_l.setSpacing(8)
        lbl2 = QLabel("HUD / HORIZONTE ARTIFICIAL")
        lbl2.setProperty("role", "subtitle")
        hud_l.addWidget(lbl2)
        self.att_widget = AttitudeIndicator(theme=self.current_theme)
        hud_l.addWidget(self.att_widget, 1)
        col_right.addWidget(hud_card, 2)

        # Estado rápido
        right_card = QFrame()
        right_card.setProperty("card", True)
        rc = QVBoxLayout(right_card)
        rc.setContentsMargins(14, 10, 14, 10)
        rc.setSpacing(10)

        lbl3 = QLabel("ESTADO RÁPIDO")
        lbl3.setProperty("role", "subtitle")
        rc.addWidget(lbl3)

        # Batería
        bat_row = QHBoxLayout()
        self.bat_widget = BatteryWidget(theme=self.current_theme)
        self.lbl_bat_val = QLabel("-- V")
        self.lbl_bat_val.setProperty("role", "metricSmall")
        bat_row.addWidget(QLabel("🔋"))
        bat_row.addWidget(self.bat_widget)
        bat_row.addStretch()
        bat_row.addWidget(self.lbl_bat_val)
        rc.addLayout(bat_row)

        # Altitud
        alt_row = QHBoxLayout()
        alt_label = QLabel("Altitud rel.")
        alt_label.setProperty("role", "unit")
        self.lbl_alt_val = QLabel("--")
        self.lbl_alt_val.setProperty("role", "metricSmall")
        self.lbl_alt_unit = QLabel("m")
        self.lbl_alt_unit.setProperty("role", "unit")
        alt_row.addWidget(QLabel("📡"))
        alt_row.addWidget(alt_label)
        alt_row.addStretch()
        alt_row.addWidget(self.lbl_alt_val)
        alt_row.addWidget(self.lbl_alt_unit)
        rc.addLayout(alt_row)

        # Velocidad
        spd_row = QHBoxLayout()
        spd_label = QLabel("Vel. terreno")
        spd_label.setProperty("role", "unit")
        self.lbl_spd_val = QLabel("--")
        self.lbl_spd_val.setProperty("role", "metricSmall")
        self.lbl_spd_unit = QLabel("m/s")
        self.lbl_spd_unit.setProperty("role", "unit")
        spd_row.addWidget(QLabel("⚡"))
        spd_row.addWidget(spd_label)
        spd_row.addStretch()
        spd_row.addWidget(self.lbl_spd_val)
        spd_row.addWidget(self.lbl_spd_unit)
        rc.addLayout(spd_row)

        # Temperatura
        tmp_row = QHBoxLayout()
        tmp_label = QLabel("Temperatura")
        tmp_label.setProperty("role", "unit")
        self.lbl_tmp_val = QLabel("--")
        self.lbl_tmp_val.setProperty("role", "metricSmall")
        self.lbl_tmp_unit = QLabel("°C")
        self.lbl_tmp_unit.setProperty("role", "unit")
        tmp_row.addWidget(QLabel("🌡️"))
        tmp_row.addWidget(tmp_label)
        tmp_row.addStretch()
        tmp_row.addWidget(self.lbl_tmp_val)
        tmp_row.addWidget(self.lbl_tmp_unit)
        rc.addLayout(tmp_row)

        # Tiempo de vuelo acumulado
        flight_row = QHBoxLayout()
        lbl_ft = QLabel("Tiempo de vuelo")
        lbl_ft.setProperty("role", "unit")
        self.lbl_flight_time_val = QLabel("00:00:00")
        self.lbl_flight_time_val.setProperty("role", "metricSmall")
        flight_row.addWidget(QLabel("⏱️"))
        flight_row.addWidget(lbl_ft)
        flight_row.addStretch()
        flight_row.addWidget(self.lbl_flight_time_val)
        rc.addLayout(flight_row)

        rc.addStretch()
        col_right.addWidget(right_card, 1)

        row.addLayout(col_right, 1)
        layout.addLayout(row, 1)

        return page

    # ------------------------------------------------------------------
    # PÁGINA: GRÁFICAS DE TELEMETRÍA
    # ------------------------------------------------------------------

    def _build_page_graphs(self) -> QWidget:
        """
        Construye la página de gráficas:
        - Cada métrica tiene su propia gráfica y color.
        - Botones para pausar y suavizar la señal.
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Gráficas de Telemetría")
        title.setProperty("role", "title")
        header.addWidget(title)
        header.addStretch()

        self.btn_pause_graphs = QPushButton("Pausar")
        self.btn_pause_graphs.setProperty("action", "secondary")
        self.btn_pause_graphs.setCheckable(True)
        self.btn_pause_graphs.clicked.connect(self._toggle_graph_pause)

        self.btn_smooth_graphs = QPushButton("Suavizar")
        self.btn_smooth_graphs.setProperty("action", "secondary")
        self.btn_smooth_graphs.setCheckable(True)
        self.btn_smooth_graphs.clicked.connect(self._toggle_graph_smooth)

        header.addWidget(self.btn_pause_graphs)
        header.addWidget(self.btn_smooth_graphs)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(16)

        # Colores por métrica
        self.metric_colors = {
            "alt": "#FF8A00",   # naranja
            "spd": "#00D1FF",   # cyan
            "vbat": "#30D158",  # verde
            "tmp": "#FF375F",   # rojo rosado
            "pres": "#8E8EAA",  # gris púrpura
            "hum": "#0A84FF",   # azul
        }

        def create_graph(title_text: str, icon: str, key: str, db_column: str, unit: str):
            """
            Crea una tarjeta de gráfica con:
              - título
              - valor actual
              - botón “Detalle”
              - gráfica pyqtgraph
            """
            card = QFrame()
            card.setProperty("card", True)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 10, 12, 10)
            cl.setSpacing(6)

            header_plot = QHBoxLayout()
            lbl_icon = QLabel(icon)
            lbl_icon.setProperty("role", "unit")
            lbl_title = QLabel(title_text)
            lbl_title.setProperty("role", "subtitle")
            header_plot.addWidget(lbl_icon)
            header_plot.addWidget(lbl_title)
            header_plot.addStretch()
            value_lbl = QLabel("--")
            value_lbl.setProperty("role", "metricSmall")

            btn_expand = QPushButton("Detalle")
            btn_expand.setProperty("action", "secondary")
            btn_expand.clicked.connect(
                lambda _, col=db_column, u=unit, ttl=title_text, k=key: self._open_metric_detail(
                    ttl, col, u, self.metric_colors[k]
                )
            )

            header_plot.addWidget(btn_expand)
            header_plot.addWidget(value_lbl)
            cl.addLayout(header_plot)

            plot = pg.PlotWidget()
            plot.showGrid(x=True, y=True, alpha=0.15)
            plot.setBackground(THEMES[self.current_theme]["graph_bg"])
            curve = plot.plot(
                pen=pg.mkPen(self.metric_colors[key], width=2)
            )
            cl.addWidget(plot)

            return card, plot, curve, value_lbl

        (
            self.card_alt_graph,
            self.plot_alt,
            self.curve_alt,
            self.lbl_alt_graph_val,
        ) = create_graph("Altitud relativa (m)", "📡", "alt", "alt_rel", "m")
        (
            self.card_spd_graph,
            self.plot_spd,
            self.curve_spd,
            self.lbl_spd_graph_val,
        ) = create_graph("Velocidad terreno (m/s)", "⚡", "spd", "v", "m/s")
        (
            self.card_vbat_graph,
            self.plot_vbat,
            self.curve_vbat,
            self.lbl_vbat_graph_val,
        ) = create_graph("Voltaje batería (V)", "🔋", "vbat", "vbat", "V")
        (
            self.card_tmp_graph,
            self.plot_tmp,
            self.curve_tmp,
            self.lbl_tmp_graph_val,
        ) = create_graph("Temperatura (°C)", "🌡️", "tmp", "temp", "°C")
        (
            self.card_pres_graph,
            self.plot_pres,
            self.curve_pres,
            self.lbl_pres_graph_val,
        ) = create_graph("Presión (hPa)", "📈", "pres", "pres", "hPa")
        (
            self.card_hum_graph,
            self.plot_hum,
            self.curve_hum,
            self.lbl_hum_graph_val,
        ) = create_graph("Humedad relativa (%)", "💧", "hum", "hum", "%")

        grid.addWidget(self.card_alt_graph, 0, 0)
        grid.addWidget(self.card_spd_graph, 0, 1)
        grid.addWidget(self.card_vbat_graph, 1, 0)
        grid.addWidget(self.card_tmp_graph, 1, 1)
        grid.addWidget(self.card_pres_graph, 2, 0)
        grid.addWidget(self.card_hum_graph, 2, 1)

        layout.addLayout(grid)

        return page

    def _open_metric_detail(self, title: str, db_column: str, unit: str, color: str):
        """Abre el diálogo de detalle para una métrica específica."""
        dlg = MetricDetailDialog(self, self.db, self.current_theme, title, db_column, unit, color)
        dlg.exec()

    def _toggle_graph_pause(self):
        """Activa o desactiva la pausa de actualización de gráficas."""
        self.graph_paused = self.btn_pause_graphs.isChecked()
        self.btn_pause_graphs.setText("Reanudar" if self.graph_paused else "Pausar")

    def _toggle_graph_smooth(self):
        """Activa o desactiva el suavizado (promedio móvil) de las gráficas."""
        self.graph_smooth = self.btn_smooth_graphs.isChecked()

    # ------------------------------------------------------------------
    # PÁGINA: HISTORIAL
    # ------------------------------------------------------------------

    def _build_page_history(self) -> QWidget:
        """
        Construye la página de historial:
        - Tabla con últimas muestras.
        - Botones para exportar CSV, abrir CSV, ver detalle y borrar todo.
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Historial de Telemetría")
        title.setProperty("role", "title")
        header.addWidget(title)
        header.addStretch()

        btn_detail = QPushButton("Detalles (última muestra)")
        btn_detail.setProperty("action", "secondary")
        btn_detail.clicked.connect(self._open_telemetry_detail)

        btn_export = QPushButton("Exportar CSV")
        btn_export.setProperty("action", "primary")
        btn_export.clicked.connect(self._export_history)

        btn_open_csv = QPushButton("Abrir último CSV")
        btn_open_csv.setProperty("action", "secondary")
        btn_open_csv.clicked.connect(self._open_last_csv)

        btn_clear = QPushButton("Eliminar todo")
        btn_clear.setProperty("action", "danger")
        btn_clear.clicked.connect(self._clear_history)

        header.addWidget(btn_detail)
        header.addWidget(btn_export)
        header.addWidget(btn_open_csv)
        header.addWidget(btn_clear)

        layout.addLayout(header)

        self.table_history = QTableWidget()
        self.table_history.setSortingEnabled(True)
        self.table_history.horizontalHeader().setStretchLastSection(True)
        self.table_history.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        layout.addWidget(self.table_history)

        return page

    def _reload_history_table(self):
        """Recarga la tabla de historial con las últimas muestras."""
        cols, rows = self.db.get_latest(200)
        self.table_history.setRowCount(len(rows))
        self.table_history.setColumnCount(len(cols))
        self.table_history.setHorizontalHeaderLabels(cols)

        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem("" if val is None else str(val))
                self.table_history.setItem(r, c, item)

    def _export_history(self):
        """Exporta el historial completo a un archivo CSV."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar historial como CSV", str(self.save_dir / "telemetria_ui.csv"), "CSV (*.csv)"
        )
        if not path:
            return
        cols, rows = self.db.get_all()
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(cols)
                w.writerows(rows)
            self.last_export_path = path
            QMessageBox.information(self, "Exportado", "Historial exportado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _open_last_csv(self):
        """Abre el último CSV exportado, si existe."""
        if not self.last_export_path or not os.path.exists(self.last_export_path):
            QMessageBox.information(self, "Sin archivo", "Aún no has exportado un CSV.")
            return
        try:
            os.startfile(self.last_export_path)  # Windows
        except Exception:
            QMessageBox.information(self, "Ruta", self.last_export_path)

    def _clear_history(self):
        """Elimina todo el contenido de la base de datos de historial."""
        if (
            QMessageBox.question(
                self, "Confirmar", "¿Eliminar TODO el historial de telemetría?"
            )
            == QMessageBox.Yes
        ):
            self.db.clear()
            self._reload_history_table()

    def _open_telemetry_detail(self):
        """Abre el diálogo de detalle para la última muestra recibida."""
        dlg = TelemetryDetailDialog(self, self.last_sample, self.current_theme)
        dlg.exec()

    # ------------------------------------------------------------------
    # PÁGINA: CONEXIÓN / BACKEND
    # ------------------------------------------------------------------

    def _build_page_connection(self) -> QWidget:
        """
        Construye la página de conexión:
        - Selección de fuente (DEMO / MAVSDK / LoRa).
        - Endpoint o puerto serie.
        - Indicador de intensidad de enlace.
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignTop)

        card = QFrame()
        card.setProperty("card", True)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 24, 24, 24)
        cl.setSpacing(14)

        title = QLabel("Configuración de Enlace")
        title.setProperty("role", "title")
        cl.addWidget(title)

        form = QFormLayout()
        self.combo_source = QComboBox()
        self.combo_source.addItems(["DEMO", "MAVSDK", "LoRa"])
        self.edit_endpoint = QLineEdit("udp://:14540")
        form.addRow("Fuente:", self.combo_source)
        form.addRow("Endpoint / Puerto:", self.edit_endpoint)
        cl.addLayout(form)

        info = QLabel(
            "DEMO: genera datos sintéticos.\n"
            "MAVSDK: conéctate a SITL o dron real vía UDP.\n"
            "LoRa: usa un puerto serie (ej. COM3) hacia el módulo LoRa."
        )
        info.setProperty("role", "unit")
        cl.addWidget(info)

        btn_connect = QPushButton("Conectar")
        btn_connect.setProperty("action", "primary")
        btn_connect.clicked.connect(self._on_connect_clicked)
        cl.addWidget(btn_connect)

        # Intensidad de señal en esta página
        sig_row = QHBoxLayout()
        sig_row.addWidget(QLabel("Intensidad de enlace:"))
        self.signal_widget_conn = SignalBarsWidget(theme=self.current_theme)
        sig_row.addWidget(self.signal_widget_conn)
        sig_row.addStretch()
        cl.addLayout(sig_row)

        layout.addWidget(card, 0)

        return page

    def _set_connection_status(self, connected: bool, extra: str = ""):
        """Actualiza el texto de estado de conexión en el header del dashboard."""
        t = THEMES[self.current_theme]
        if connected:
            self._stop_connecting_animation()
            self.lbl_conn_status.setText(f"Conectado ({extra})")
            self.lbl_conn_status.setStyleSheet(
                f"color:{t['success_color']}; font-weight:600;"
            )
        else:
            self._stop_connecting_animation()
            self.lbl_conn_status.setText("Desconectado")
            self.lbl_conn_status.setStyleSheet(
                f"color:{t['danger_color']}; font-weight:600;"
            )

    def _start_connecting_animation(self):
        """Inicia la animación de “Conectando...” y barras subiendo/bajando."""
        self._is_connecting = True
        self._connecting_phase = 0
        self._connecting_fake_level = 0
        self.connect_anim_timer.start(250)

    def _stop_connecting_animation(self):
        """Detiene la animación de conexión."""
        self._is_connecting = False
        self.connect_anim_timer.stop()

    def _update_connecting_label(self):
        """Actualiza el texto y barras durante el proceso de conexión."""
        if not self._is_connecting:
            return
        phases = ["Conectando", "Conectando.", "Conectando..", "Conectando..."]
        self._connecting_phase = (self._connecting_phase + 1) % len(phases)
        t = THEMES[self.current_theme]
        self.lbl_conn_status.setText(phases[self._connecting_phase])
        self.lbl_conn_status.setStyleSheet(
            f"color:{t['accent_color']}; font-weight:600;"
        )
        # Barras de señal simuladas
        self._connecting_fake_level = (self._connecting_fake_level + 1) % 5
        self.signal_widget.set_level(self._connecting_fake_level)
        self.signal_widget_conn.set_level(self._connecting_fake_level)

    def _on_connect_clicked(self):
        """Manejador del botón Conectar."""
        src = self.combo_source.currentText()
        self.source_name = src
        endpoint = self.edit_endpoint.text().strip()

        # Detener backend previo si existe
        if self.backend is not None and hasattr(self.backend, "stop"):
            try:
                asyncio.create_task(self.backend.stop())
            except RuntimeError:
                # Si no hay loop de asyncio activo, se ignora.
                pass

        # Crear backend según la fuente seleccionada
        if src == "DEMO":
            self.backend = BackendTelemetria(force_demo=True)
        elif src == "MAVSDK":
            self.backend = BackendTelemetria(force_demo=False)
        else:  # LoRa
            self.backend = LoRaBackend(port=endpoint or "COM3", baud=57600)

        self._start_connecting_animation()

        try:
            asyncio.create_task(self._run_backend(endpoint))
        except RuntimeError:
            # Si se ejecuta sin loop de asyncio, el usuario deberá lanzar el backend externamente.
            pass

    async def _run_backend(self, endpoint: str):
        """
        Corrutina que se encarga de conectar el backend y consumir las muestras.
        Va emitiendo señales hacia la interfaz con cada muestra.
        """
        try:
            await self.backend.connect(endpoint)
            self._set_connection_status(True, self.source_name)
            async for sample in self.backend.samples():
                self.signals.sample.emit(sample)
        except Exception as e:
            self._set_connection_status(False, "error")
            QMessageBox.critical(self, "Error de backend", str(e))

    # ------------------------------------------------------------------
    # MANEJO DE TELEMETRÍA ENTRANTE
    # ------------------------------------------------------------------

    def _handle_sample(self, s: TelemetrySample):
        """
        Lógica principal al recibir una muestra:
        - Actualiza buffers de gráficas.
        - Actualiza HUD y estado rápido.
        - Actualiza texto de “Contrato”.
        - Guarda la muestra en la base de datos.
        """
        self.last_sample = s

        # Tiempo relativo de la muestra
        t_val = getattr(s, "time_s", None)
        if t_val is None:
            t_val = self.time_buf[-1] + 1 if self.time_buf else 0.0

        # Cálculo de tiempo de vuelo (suma solo cuando está en aire)
        in_air = bool(getattr(s, "in_air", False))
        if self.last_time_s is not None:
            dt = max(0.0, t_val - self.last_time_s)
            if dt < 10.0 and in_air:
                self.flight_time_s += dt
        self.last_time_s = t_val

        self.time_buf.append(t_val)

        # Variables interesantes
        alt = getattr(s, "rel_alt_m", 0.0) or 0.0
        spd = getattr(s, "groundspeed_ms", 0.0) or 0.0
        vbat = getattr(s, "voltage_v", 0.0) or 0.0
        bat_pct = getattr(s, "battery_percent", 0.0) or 0.0
        tmp = getattr(s, "temp_c", 0.0) or 0.0
        pres = getattr(s, "pres_hpa", 0.0) or 0.0
        hum = getattr(s, "hum_pct", 0.0) or 0.0
        rad = getattr(s, "rad_mwcm2", 0.0) or 0.0
        acc = getattr(s, "acc_ms2", 0.0) or 0.0
        lat = getattr(s, "lat_deg", 0.0) or 0.0
        lon = getattr(s, "lon_deg", 0.0) or 0.0
        sats = getattr(s, "num_sat", 0) or 0

        # Buffers para gráficas
        self.alt_buf.append(alt)
        self.spd_buf.append(spd)
        self.volt_buf.append(vbat)
        self.temp_buf.append(tmp)
        self.pres_buf.append(pres)
        self.hum_buf.append(hum)

        # --- Dashboard: batería --------------------------------------
        self.bat_widget.set_level(bat_pct)
        self.lbl_bat_val.setText(f"{vbat:.2f} V" if vbat > 0 else "-- V")

        # Altitud con color según rango
        t_theme = THEMES[self.current_theme]
        if alt < 5.0:
            color_alt = t_theme["danger_color"]
        elif alt > 120.0:
            color_alt = "#C084FC"
        else:
            color_alt = t_theme["accent_color"]

        self.lbl_alt_val.setText(f"{alt:.1f}")
        self.lbl_alt_val.setStyleSheet(
            f"color:{color_alt}; font-weight:800; font-size:24px;"
        )

        # Velocidad
        self.lbl_spd_val.setText(f"{spd:.1f}")
        self.lbl_spd_val.setStyleSheet(
            f"color:{self.metric_colors['spd']}; font-weight:700; font-size:22px;"
        )

        # Temperatura
        self.lbl_tmp_val.setText(f"{tmp:.1f}")
        self.lbl_tmp_val.setStyleSheet(
            f"color:{self.metric_colors['tmp']}; font-weight:700; font-size:22px;"
        )

        # Tiempo de vuelo en formato hh:mm:ss
        hrs = int(self.flight_time_s // 3600)
        mins = int((self.flight_time_s % 3600) // 60)
        secs = int(self.flight_time_s % 60)
        self.lbl_flight_time_val.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")

        # HUD
        self.att_widget.set_attitude(
            getattr(s, "roll_deg", 0.0) or 0.0,
            getattr(s, "pitch_deg", 0.0) or 0.0,
        )

        # Líneas de estado tipo “Contrato”
        modo = getattr(s, "flight_mode", "--") or "--"
        en_aire_txt = "Sí" if in_air else "No"
        self.lbl_status_line1.setText(
            f"GPS: {sats} sats | Modo: {modo} | En aire: {en_aire_txt} | Fuente: {self.source_name}"
        )

        accent = THEMES[self.current_theme]["accent_color"]
        self.lbl_status_line2.setText(
            f"<span style='color:{accent}; font-weight:600;'>Contrato:</span> "
            f"temp:{tmp:.1f},hum:{hum:.1f},pres:{pres:.1f},rad:{rad:.2f},"
            f"lat:{lat:.4f},lon:{lon:.4f},speed:{spd:.2f},acc:{acc:.2f},ts:{t_val:.1f}"
        )

        # Intensidad de señal (aprox a partir de sats)
        level = 0
        if sats >= 10:
            level = 4
        elif sats >= 7:
            level = 3
        elif sats >= 4:
            level = 2
        elif sats >= 1:
            level = 1
        self.signal_widget.set_level(level)
        self.signal_widget_conn.set_level(level)

        # Gráficas
        self._update_graphs()

        self.lbl_alt_graph_val.setText(f"{alt:.1f} m")
        self.lbl_spd_graph_val.setText(f"{spd:.1f} m/s")
        self.lbl_vbat_graph_val.setText(f"{vbat:.2f} V")
        self.lbl_tmp_graph_val.setText(f"{tmp:.1f} °C")
        self.lbl_pres_graph_val.setText(f"{pres:.1f} hPa")
        self.lbl_hum_graph_val.setText(f"{hum:.1f} %")

        # Guardar en BD (flush inmediato para que siempre haya historial)
        self.db.append(self.source_name, s)
        self.db.flush()

    def _update_graphs(self):
        """Actualiza las curvas de las gráficas en la pestaña correspondiente."""
        if self.graph_paused:
            return

        x = list(self.time_buf)

        def maybe_smooth(data: deque) -> List[float]:
            vals = list(data)
            if not self.graph_smooth or len(vals) < 5:
                return vals
            w = 5
            sm = []
            for i in range(len(vals)):
                i0 = max(0, i - w + 1)
                window = vals[i0:i + 1]
                sm.append(sum(window) / len(window))
            return sm

        self.curve_alt.setData(x, maybe_smooth(self.alt_buf))
        self.curve_spd.setData(x, maybe_smooth(self.spd_buf))
        self.curve_vbat.setData(x, maybe_smooth(self.volt_buf))
        self.curve_tmp.setData(x, maybe_smooth(self.temp_buf))
        self.curve_pres.setData(x, maybe_smooth(self.pres_buf))
        self.curve_hum.setData(x, maybe_smooth(self.hum_buf))

    # ------------------------------------------------------------------
    # CAMBIO DE TEMA (OSC/CLARO)
    # ------------------------------------------------------------------

    def _toggle_theme(self):
        """Alterna entre modo oscuro y claro."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._apply_theme()

    def _apply_theme(self):
        """Aplica el tema actual a todos los widgets."""
        self.setStyleSheet(build_stylesheet(self.current_theme))
        pg.setConfigOption("background", THEMES[self.current_theme]["graph_bg"])
        pg.setConfigOption("foreground", THEMES[self.current_theme]["text_main"])

        self.bat_widget.set_theme(self.current_theme)
        self.att_widget.set_theme(self.current_theme)
        self.cam_widget.set_theme(self.current_theme)
        self.signal_widget.set_theme(self.current_theme)
        self.signal_widget_conn.set_theme(self.current_theme)

        # Actualizar fondos de gráficas y colores de curvas
        plots_curves_colors = [
            (self.plot_alt, self.curve_alt, self.metric_colors["alt"]),
            (self.plot_spd, self.curve_spd, self.metric_colors["spd"]),
            (self.plot_vbat, self.curve_vbat, self.metric_colors["vbat"]),
            (self.plot_tmp, self.curve_tmp, self.metric_colors["tmp"]),
            (self.plot_pres, self.curve_pres, self.metric_colors["pres"]),
            (self.plot_hum, self.curve_hum, self.metric_colors["hum"]),
        ]
        for plot, curve, color in plots_curves_colors:
            plot.setBackground(THEMES[self.current_theme]["graph_bg"])
            curve.setPen(pg.mkPen(color, width=2))

        self.btn_theme.setText(
            "Modo claro" if self.current_theme == "dark" else "Modo oscuro"
        )

        # Actualizar estilos de líneas de estado (Contrato) al cambiar tema
        accent = THEMES[self.current_theme]["accent_color"]
        self.lbl_status_line1.setStyleSheet(
            f"font-size: 12px; color: {THEMES[self.current_theme]['text_main']};"
        )
        self.lbl_status_line2.setStyleSheet(
            f"font-size: 12px; color: {THEMES[self.current_theme]['text_main']};"
        )
        # Forzar re-dibujo de texto “Contrato”
        if self.last_sample is not None:
            self._handle_sample(self.last_sample)

    # ------------------------------------------------------------------
    # CÁMARA: ACTUALIZACIÓN Y CAPTURAS
    # ------------------------------------------------------------------

    def _tick_camera(self):
        """Se llama periódicamente para actualizar el cuadro de la cámara."""
        active = self.backend is not None
        self.cam_widget.update_image(active)

    def _set_capture_mode(self, mode: str):
        """
        Cambia el modo de captura de la cámara:
          - "photo" : botón principal guarda una foto.
          - "video" : botón principal inicia/detiene grabación.
        """
        self.capture_mode = mode
        if mode == "photo":
            self.btn_mode_photo.setChecked(True)
            self.btn_mode_video.setChecked(False)
            self.btn_capture.setText("Guardar foto")
            if self.is_recording:
                self.is_recording = False
                self.cam_widget.stop_recording()
        else:
            self.btn_mode_photo.setChecked(False)
            self.btn_mode_video.setChecked(True)
            self.btn_capture.setText("Iniciar / detener grabación")

    def _capture_action(self):
        """Acción del botón principal de captura (foto o video)."""
        if self.capture_mode == "photo":
            path = self.cam_widget.save_snapshot()
            if path:
                QMessageBox.information(self, "Foto guardada", f"Foto guardada en:\n{path}")
        else:
            # Modo video
            if not self.is_recording:
                self.cam_widget.start_recording()
                self.is_recording = True
                QMessageBox.information(
                    self,
                    "Grabando",
                    "Comenzó la grabación.\nSe guardarán imágenes en media/videos/video_...",
                )
            else:
                self.cam_widget.stop_recording()
                self.is_recording = False
                QMessageBox.information(self, "Grabación detenida", "Se detuvo la grabación.")

    # ------------------------------------------------------------------
    # ANIMACIONES SENCILLAS EN BOTONES (EFECTO “CLICK”)
    # ------------------------------------------------------------------

    def _setup_button_animations(self):
        """Asigna una pequeña animación de opacidad a los botones principales."""
        buttons = [
            self.btn_dash,
            self.btn_graph,
            self.btn_hist,
            self.btn_conn,
            self.btn_theme,
            getattr(self, "btn_pause_graphs", None),
            getattr(self, "btn_smooth_graphs", None),
        ]
        buttons = [b for b in buttons if b is not None]

        def wrap(btn):
            btn.pressed.connect(lambda b=btn: self._animate_button(b))

        for b in buttons:
            wrap(b)

    def _animate_button(self, btn: QPushButton):
        """
        Anima ligeramente el botón reduciendo su opacidad y
        restaurándola después de unos milisegundos.
        """
        effect = btn.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(btn)
            btn.setGraphicsEffect(effect)
        effect.setOpacity(0.6)

        def reset():
            effect.setOpacity(1.0)

        QTimer.singleShot(120, reset)

    # ------------------------------------------------------------------
    # UTILIDADES GENERALES
    # ------------------------------------------------------------------

    def _load_logo(self):
        """
        Carga el logo del equipo desde disco.
        Si no existe, genera un placeholder con una “U”.
        """
        if self.logo_path and os.path.exists(self.logo_path):
            pm = QPixmap(self.logo_path).scaled(
                110, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.lbl_logo.setPixmap(pm)
        else:
            pm = QPixmap(110, 110)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing)
            p.setBrush(QColor("#FF8A00"))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(pm.rect(), 24, 24)
            p.setPen(QColor("white"))
            p.setFont(QFont("Segoe UI", 40, QFont.Bold))
            p.drawText(pm.rect(), Qt.AlignCenter, "U")
            p.end()
            self.lbl_logo.setPixmap(pm)

    def closeEvent(self, event):
        """
        Se llama al cerrar la ventana.
        Cierra la base de datos y detiene el backend de forma ordenada.
        """
        self.db.close()
        try:
            if self.backend is not None and hasattr(self.backend, "stop"):
                asyncio.create_task(self.backend.stop())
        except RuntimeError:
            pass
        event.accept()
