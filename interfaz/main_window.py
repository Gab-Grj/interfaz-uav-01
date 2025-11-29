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
from math import sqrt, atan2, radians, sin, cos, pi  # <- para HUD/energía/FPV

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
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
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
        "accent_color": "#FF8A00",   # se sobreescribe según configuración
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

# paletas de color principal configurables
ACCENT_COLOR_OPTIONS = {
    "Rojo": ("#FF3B30", "#FF6961"),
    "Azul": ("#0A84FF", "#5AC8FA"),
    "Amarillo": ("#FFD60A", "#FFE566"),
    "Verde": ("#30D158", "#5CD85C"),
    "Naranja": ("#FF8A00", "#FFB84D"),
    "Morado": ("#BF5AF2", "#D0A2F7"),
    "Rosa": ("#FF2D55", "#FF6B81"),
    "Marrón": ("#A2845E", "#C8AD7F"),
    "Blanco": ("#FFFFFF", "#F5F5F5"),
    "Negro": ("#000000", "#333333"),
    "Gris": ("#8E8E93", "#C7C7CC"),
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

G0 = 9.80665  # gravedad estándar para energía específica

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
    Horizonte artificial que representa roll y pitch, con:
    - Escala de pitch
    - Marcas de bank en el anillo
    - Indicador de slip
    - Flight Path Vector (FPV)
    - Indicador simple de energía (ganando/perdiendo)
    - Mini plano de coordenadas 3D (X/Y/Z) que acompaña a la actitud
    """

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.theme = theme
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0

        # FPV y slip
        self.fpv_pitch = 0.0
        self.fpv_yaw = 0.0
        self.has_fpv = False
        self.slip = 0.0          # [-1,1] izquierda-derecha
        self.energy_trend = 0    # -1: perdiendo, 0: estable, 1: ganando

        self.setMinimumSize(220, 220)

    def set_theme(self, theme: str):
        self.theme = theme
        self.update()

    def set_attitude(
        self,
        roll_deg: float,
        pitch_deg: float,
        yaw_deg: Optional[float] = None,
        fpv_pitch_deg: Optional[float] = None,
        fpv_yaw_deg: Optional[float] = None,
        slip: Optional[float] = None,
        energy_trend: Optional[int] = None,
    ):
        """Actualiza valores de actitud + FPV + slip + energía."""
        self.roll = roll_deg or 0.0
        self.pitch = pitch_deg or 0.0
        if yaw_deg is not None:
            self.yaw = yaw_deg or 0.0

        if fpv_pitch_deg is not None and fpv_yaw_deg is not None:
            self.fpv_pitch = fpv_pitch_deg
            self.fpv_yaw = fpv_yaw_deg
            self.has_fpv = True
        else:
            self.has_fpv = False

        if slip is not None:
            self.slip = max(-1.0, min(1.0, slip))
        if energy_trend is not None:
            self.energy_trend = int(max(-1, min(1, energy_trend)))

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

        # ------------------ FONDO CIELO/TIERRA + ESCALA PITCH ------------------
        p.save()
        p.translate(center)
        p.rotate(-self.roll)

        # Pitch -> desplazamiento vertical de horizonte
        pitch_clamp = max(-45.0, min(45.0, self.pitch))
        pitch_norm = pitch_clamp / 45.0
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

        # Escala de pitch (cada 10° entre -30 y +30)
        p.setPen(QPen(QColor(t["text_main"]), 1.5))
        pitch_scale = radius * 0.6 / 45.0  # px por grado
        for ang in range(-30, 31, 10):
            if ang == 0:
                continue
            y_mark = y_offset - ang * pitch_scale
            if abs(y_mark) > radius * 1.2:
                continue
            # línea centrada
            half_w = radius * (0.35 if abs(ang) % 20 == 0 else 0.25)
            p.drawLine(QPointF(-half_w, y_mark), QPointF(half_w, y_mark))
            # texto pitch
            txt = f"{ang:+d}"
            p.setFont(QFont("Segoe UI", 7))
            p.drawText(
                QRectF(-half_w - 24, y_mark - 6, 20, 12),
                Qt.AlignRight | Qt.AlignVCenter,
                txt,
            )
            p.drawText(
                QRectF(half_w + 4, y_mark - 6, 20, 12),
                Qt.AlignLeft | Qt.AlignVCenter,
                txt,
            )

        # Línea de horizonte
        p.setPen(QPen(QColor(t["text_main"]), 2))
        p.drawLine(QPointF(-radius * 2, y_offset), QPointF(radius * 2, y_offset))

        p.restore()

        # ------------------ ANILLO PRINCIPAL + MARCAS DE BANK ------------------
        p.translate(center)

        # Círculo principal
        p.setPen(QPen(QColor(t["border_color"]), 3, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(0, 0), radius * 0.9, radius * 0.9)

        # Marcas de bank
        bank_pen = QPen(QColor(t["text_secondary"]), 1.5, Qt.SolidLine, Qt.RoundCap)
        p.setPen(bank_pen)
        for ang in [-60, -45, -30, -20, -10, 10, 20, 30, 45, 60]:
            a = radians(ang)
            outer_r = radius * 0.9
            if abs(ang) in (30, 45):
                inner_r = outer_r - radius * 0.11
            elif abs(ang) == 60:
                inner_r = outer_r - radius * 0.07
            else:
                inner_r = outer_r - radius * 0.07
            x1 = inner_r * sin(a)
            y1 = -inner_r * cos(a)
            x2 = outer_r * sin(a)
            y2 = -outer_r * cos(a)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Triángulo índice superior (0° bank)
        top_y = -radius * 0.9
        tri_w = radius * 0.10
        tri_h = radius * 0.06
        bank_index = QPolygonF(
            [
                QPointF(0, top_y - tri_h),
                QPointF(-tri_w / 2, top_y),
                QPointF(tri_w / 2, top_y),
            ]
        )
        p.setBrush(QColor(t["text_main"]))
        p.setPen(Qt.NoPen)
        p.drawPolygon(bank_index)

        # ------------------ SÍMBOLO DEL AVIÓN ------------------
        aircraft_pen = QPen(QColor(t["accent_color"]), 3, Qt.SolidLine, Qt.RoundCap)
        p.setPen(aircraft_pen)
        p.setBrush(Qt.NoBrush)
        p.drawLine(-radius * 0.4, 0, -radius * 0.1, 0)
        p.drawLine(radius * 0.1, 0, radius * 0.4, 0)
        p.drawEllipse(QPointF(0, 0), 4, 4)

        # ------------------ FLIGHT PATH VECTOR (FPV) ------------------
        if self.has_fpv:
            # Diferencia yaw entre trayectoria y actitud
            yaw_diff = self.fpv_yaw - self.yaw
            # wrap a [-180,180]
            while yaw_diff > 180:
                yaw_diff -= 360
            while yaw_diff < -180:
                yaw_diff += 360

            max_pitch = 30.0
            max_yaw_diff = 30.0
            fpv_pitch_clamp = max(-max_pitch, min(max_pitch, self.fpv_pitch))
            yaw_diff_clamp = max(-max_yaw_diff, min(max_yaw_diff, yaw_diff))

            x_fpv = (yaw_diff_clamp / max_yaw_diff) * radius * 0.45
            y_fpv = -(fpv_pitch_clamp / max_pitch) * radius * 0.45

            fpv_color = QColor(t["accent_soft"])
            p.setPen(QPen(fpv_color, 2, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            # círculo FPV
            p.drawEllipse(QPointF(x_fpv, y_fpv), 6, 6)
            # alitas FPV
            p.drawLine(
                QPointF(x_fpv - 12, y_fpv),
                QPointF(x_fpv - 4, y_fpv),
            )
            p.drawLine(
                QPointF(x_fpv + 4, y_fpv),
                QPointF(x_fpv + 12, y_fpv),
            )

        # ------------------ INDICADOR DE SLIP ------------------
        bar_y = radius * 0.65
        bar_w = radius * 0.7
        bar_h = radius * 0.08

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(t["bg_card"]))
        slip_rect = QRectF(-bar_w / 2, bar_y - bar_h / 2, bar_w, bar_h)
        p.drawRoundedRect(slip_rect, bar_h / 2, bar_h / 2)

        p.setPen(QPen(QColor(t["border_color"]), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(slip_rect, bar_h / 2, bar_h / 2)

        ball_r = bar_h * 0.45
        slip_norm = max(-1.0, min(1.0, self.slip))
        ball_x = slip_rect.center().x() + slip_norm * (bar_w / 2 - ball_r - 2)
        if abs(slip_norm) > 0.7:
            ball_color = QColor(t["danger_color"])
        else:
            ball_color = QColor(t["accent_color"])
        p.setBrush(ball_color)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ball_x, slip_rect.center().y()), ball_r, ball_r)

        # ------------------ INDICADOR DE ENERGÍA ------------------
        # Barra vertical simple en el lado derecho del anillo.
        energy_x = radius * 0.9
        energy_h = radius * 0.4
        p.setPen(QPen(QColor(t["border_color"]), 1))
        p.drawLine(
            QPointF(energy_x, -energy_h / 2),
            QPointF(energy_x, energy_h / 2),
        )

        # Flecha según tendencia de energía
        if self.energy_trend != 0:
            arrow_color = (
                QColor(t["success_color"]) if self.energy_trend > 0 else QColor(t["danger_color"])
            )
            p.setBrush(arrow_color)
            p.setPen(Qt.NoPen)
            if self.energy_trend > 0:
                # flecha hacia arriba
                tri = QPolygonF(
                    [
                        QPointF(energy_x, -energy_h / 2),
                        QPointF(energy_x - 6, -energy_h / 2 + 10),
                        QPointF(energy_x + 6, -energy_h / 2 + 10),
                    ]
                )
            else:
                # flecha hacia abajo
                tri = QPolygonF(
                    [
                        QPointF(energy_x, energy_h / 2),
                        QPointF(energy_x - 6, energy_h / 2 - 10),
                        QPointF(energy_x + 6, energy_h / 2 - 10),
                    ]
                )
            p.drawPolygon(tri)

        # ------------------ TEXTO ROLL/PITCH ------------------
        p.setPen(QColor(t["text_secondary"]))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(
            QRectF(-radius, radius * 0.55, radius * 2, 20),
            Qt.AlignCenter,
            f"ROLL {self.roll:+.1f}°   PITCH {self.pitch:+.1f}°",
        )

        # ------------------ MINI PLANO DE COORDENADAS 3D ------------------
        p.save()
        p.resetTransform()
        p.setRenderHint(QPainter.Antialiasing)

        margin = 18
        axis_center = QPointF(margin + 24, self.height() - margin - 28)
        axis_len = 18.0

        yaw_rad = radians(self.yaw)
        pitch_rad = radians(self.pitch)

        # Ejes X/Y en el plano horizontal (rotan con yaw)
        x_dir = QPointF(axis_len * cos(yaw_rad), -axis_len * sin(yaw_rad))
        y_dir = QPointF(axis_len * sin(yaw_rad), axis_len * cos(yaw_rad))

        # Eje Z proyectado (afectado por pitch)
        z_dir = QPointF(0, -axis_len * cos(pitch_rad))

        # Fondo suave del widget de coordenadas
        bg_color = QColor(0, 0, 0, 90) if self.theme == "dark" else QColor(255, 255, 255, 160)
        p.setBrush(bg_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(axis_center.x() - 24, axis_center.y() - 24, 48, 48), 8, 8)

        # Ejes
        p.setPen(QPen(QColor(t["accent_color"]), 1.5))
        p.drawLine(axis_center, axis_center + x_dir)
        p.setPen(QPen(QColor("#0A84FF"), 1.3))
        p.drawLine(axis_center, axis_center + y_dir)
        p.setPen(QPen(QColor(t["success_color"]), 1.3))
        p.drawLine(axis_center, axis_center + z_dir)

        # Etiquetas X/Y/Z
        p.setFont(QFont("Segoe UI", 7))
        p.setPen(QColor(t["text_main"]))
        p.drawText(axis_center + x_dir + QPointF(3, 0), "X")
        p.drawText(axis_center + y_dir + QPointF(3, 0), "Y")
        p.drawText(axis_center + z_dir + QPointF(3, 0), "Z")

        p.restore()

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
      - Mapa / navegación.
      - Gráficas individuales.
      - Historial de telemetría.
      - Configuración de conexión/backend.
      - Configuración de rendimiento y alertas.
    """

    def __init__(self, logo_path: Optional[str] = None) -> None:
        super().__init__()

        # Tema inicial
        self.current_theme = "dark"

        # Configuración persistente
        self.settings = QSettings("UAV-IASA", "GCS")

        # Config de acentos (color principal)
        self.accent_options = ACCENT_COLOR_OPTIONS
        self.accent_choice_dark = self.settings.value("accent_dark", "Naranja")
        self.accent_choice_light = self.settings.value("accent_light", "Naranja")
        self._apply_accent_to_theme("dark", self.accent_choice_dark)
        self._apply_accent_to_theme("light", self.accent_choice_light)

        self.setStyleSheet(build_stylesheet(self.current_theme))
        pg.setConfigOption("background", THEMES[self.current_theme]["graph_bg"])
        pg.setConfigOption("foreground", THEMES[self.current_theme]["text_main"])

        self.setWindowTitle("UAV-IASA UNAM — Ground Control")
        self.setMinimumSize(1280, 800)

        if logo_path:
            self.logo_path = logo_path
        else:
            root_logo = Path(__file__).resolve().parent.parent / "uav_iasa_logo.png"
            self.logo_path = str(root_logo) if root_logo.exists() else ""
        self.save_dir = Path("datos_vuelo")
        self.save_dir.mkdir(exist_ok=True)

        # Parámetros de rendimiento / BD (ajustables desde Configuración)
        self.db_commit_per_sample = True       # escribir en disco por muestra
        self.db_timer_interval_ms = 1000       # flush periódico (ms)

        # Base de datos local de historial
        self.db = HistorialDB(self.save_dir / "telemetria_ui.db")
        self.db_timer = QTimer(self)
        self.db_timer.timeout.connect(self.db.flush)
        self.db_timer.start(self.db_timer_interval_ms)

        self.last_export_path: Optional[str] = None

        # Backend de telemetría
        self.backend = None
        self.backend_task = None
        self.source_name = "DEMO"

        # Reconexión automática
        self.auto_reconnect_enabled = False
        self.reconnect_interval_s = 5.0
        self.reconnect_max_attempts = 3
        self._last_endpoint: str = ""
        self._reconnect_attempts = 0

        # Buffers para gráficas
        self.time_buf = deque(maxlen=600)
        self.alt_buf = deque(maxlen=600)
        self.spd_buf = deque(maxlen=600)
        self.volt_buf = deque(maxlen=600)
        self.temp_buf = deque(maxlen=600)
        self.pres_buf = deque(maxlen=600)
        self.hum_buf = deque(maxlen=600)

        # Habilitación individual de gráficas
        self.graph_enabled = {
            "alt": True,
            "spd": True,
            "vbat": True,
            "tmp": True,
            "pres": True,
            "hum": True,
        }
        self.graph_toggle_buttons = {}

        # Parámetros de rendimiento para cámara / gráficas / mapa
        self.camera_update_ms = 120
        self.graph_update_period_ms = 0        # 0 = actualizar cada muestra
        self.map_update_period_ms = 0          # 0 = actualizar cada muestra
        self.graph_max_points = 600
        self.map_max_points = 1000

        # Perfiles (6 niveles) para Configuración
        self._cam_profile_intervals = [80, 100, 120, 150, 180, 220]
        self._graph_profile_periods = [0, 0, 50, 100, 150, 200]
        self._graph_profile_points = [0, 400, 600, 800, 1000, 1500]
        self._map_profile_periods = [0, 0, 50, 100, 150, 200]
        self._map_profile_points = [400, 600, 800, 1000, 1500, 2000]
        self._db_profile_commit_flags = [True, True, False, False, False, False]
        self._db_profile_intervals = [500, 1000, 1000, 1500, 2000, 3000]

        # Buffer para mapa (lat/lon)
        self.map_positions: deque[Tuple[float, float]] = deque(maxlen=self.map_max_points)
        self.map_home: Optional[Tuple[float, float]] = None

        self.graph_paused = False
        self.graph_smooth = False

        # Tiempo de vuelo acumulado
        self.flight_time_s = 0.0
        self.last_time_s = None

        # Energía específica (para tendencia)
        self.prev_energy = None
        self.energy_trend = 0

        self.last_sample: Optional[TelemetrySample] = None

        # Timestamps para controlar frecuencia de refresco de mapa y gráficas
        self._last_graph_update_ms = 0.0
        self._last_map_update_ms = 0.0

        # Alertas y seguridad (umbrales)
        self.alert_batt_warn_pct = 30.0
        self.alert_batt_crit_pct = 15.0
        self.alert_alt_max = 120.0
        self.alert_spd_max = 20.0
        self.alert_temp_max = 70.0
        self.alert_gps_min_sats = 5

        self.alert_enable_batt = True
        self.alert_enable_alt = True
        self.alert_enable_spd = True
        self.alert_enable_temp = True
        self.alert_enable_gps = True
        self.alert_enable_link = True

        # Modo de alerta: "ui" = solo colores, "popup" = colores + QMessageBox
        self.alert_style = "ui"

        # Estado interno de alertas
        self.last_batt_alert_level = 0   # 0=ok, 1=warn, 2=crit
        self.alt_alert_active = False
        self.spd_alert_active = False
        self.temp_alert_active = False
        self.gps_alert_active = False
        self.link_alert_active = False

        # Timeout de enlace (heartbeat)
        self.link_timeout_s = 5.0
        self.link_timeout_timer = QTimer(self)
        self.link_timeout_timer.setSingleShot(True)
        self.link_timeout_timer.timeout.connect(self._on_link_timeout)

        self.signals = TelemetrySignals()
        self.signals.sample.connect(self._handle_sample)

        # Animación de “Conectando...”
        self.connect_anim_timer = QTimer(self)
        self.connect_anim_timer.timeout.connect(self._update_connecting_label)
        self._connecting_phase = 0
        self._is_connecting = False
        self._connecting_fake_level = 0

        # Animación de pulse de barras al conectar OK
        self.signal_pulse_timer = QTimer(self)
        self.signal_pulse_timer.timeout.connect(self._signal_pulse_step)
        self._signal_pulse_target = 4
        self._signal_pulse_level = 0

        # Construcción de UI
        self._build_ui()
        self._setup_button_animations()

        # Cámara simulada (se actualiza según perfil de rendimiento)
        self.cam_timer = QTimer(self)
        self.cam_timer.timeout.connect(self._tick_camera)
        self.cam_timer.start(self.camera_update_ms)

        # Inicializar controles de rendimiento (perfiles) con valores intermedios
        self._init_performance_controls()

        self.statusBar().hide()

    # ------------------------------------------------------------------
    # APLICAR ACENTOS
    # ------------------------------------------------------------------

    def _apply_accent_to_theme(self, theme_name: str, color_name: str):
        palette = self.accent_options.get(color_name)
        if not palette:
            return
        THEMES[theme_name]["accent_color"] = palette[0]
        THEMES[theme_name]["accent_soft"] = palette[1]

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
        self.btn_map = self._nav_button("Mapa")
        self.btn_graph = self._nav_button("Gráficas")
        self.btn_hist = self._nav_button("Historial")
        self.btn_conn = self._nav_button("Conexión")

        self.btn_dash.setChecked(True)

        sbl.addWidget(self.btn_dash)
        sbl.addWidget(self.btn_map)
        sbl.addWidget(self.btn_graph)
        sbl.addWidget(self.btn_hist)
        sbl.addWidget(self.btn_conn)
        sbl.addStretch()

        # Botones inferiores: engrane pequeño + cambio de tema
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        # ÚNICO botón de engrane (emoji ⚙️) junto al cambio de tema
        self.btn_open_settings_small = QPushButton("⚙️")
        self.btn_open_settings_small.setProperty("action", "secondary")
        self.btn_open_settings_small.setFixedWidth(36)
        self.btn_open_settings_small.clicked.connect(lambda: self._set_page(5))

        self.btn_theme = QPushButton("Modo claro")
        self.btn_theme.setObjectName("ThemeToggleButton")
        self.btn_theme.clicked.connect(self._toggle_theme)

        bottom_row.addWidget(self.btn_open_settings_small)
        bottom_row.addWidget(self.btn_theme, 1)

        sbl.addLayout(bottom_row)

        layout.addWidget(sidebar)

        # --- STACK DE PÁGINAS -----------------------------------------
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.page_dashboard = self._build_page_dashboard()
        self.page_map = self._build_page_map()
        self.page_graphs = self._build_page_graphs()
        self.page_history = self._build_page_history()
        self.page_connection = self._build_page_connection()
        self.page_settings = self._build_page_settings()

        self.stack.addWidget(self.page_dashboard)   # 0
        self.stack.addWidget(self.page_map)         # 1
        self.stack.addWidget(self.page_graphs)      # 2
        self.stack.addWidget(self.page_history)     # 3
        self.stack.addWidget(self.page_connection)  # 4
        self.stack.addWidget(self.page_settings)    # 5

        # Conectar navegación
        self.btn_dash.clicked.connect(lambda: self._set_page(0))
        self.btn_map.clicked.connect(lambda: self._set_page(1))
        self.btn_graph.clicked.connect(lambda: self._set_page(2))
        self.btn_hist.clicked.connect(lambda: self._set_page(3))
        self.btn_conn.clicked.connect(lambda: self._set_page(4))

    def _nav_button(self, text: str) -> QPushButton:
        """Crea un botón de navegación lateral."""
        b = QPushButton(text)
        b.setCheckable(True)
        b.setProperty("nav", True)
        return b

    def _set_page(self, idx: int):
        """Cambia la página visible en el stack."""
        self.stack.setCurrentIndex(idx)
        btns = [
            self.btn_dash,
            self.btn_map,
            self.btn_graph,
            self.btn_hist,
            self.btn_conn,
        ]
        for i, b in enumerate(btns):
            b.setChecked(i == idx)

        if idx == 3:
            # Al entrar al historial, recargar tabla
            self._reload_history_table()
        elif idx == 2:
            # Al entrar a gráficas, refrescar una vez con todos los datos acumulados
            self._update_graphs()
        elif idx == 1 and self.last_sample is not None:
            # Al entrar al mapa, refrescar una vez con la última muestra
            lat = getattr(self.last_sample, "lat_deg", 0.0) or 0.0
            lon = getattr(self.last_sample, "lon_deg", 0.0) or 0.0
            alt = getattr(self.last_sample, "rel_alt_m", 0.0) or 0.0
            spd = getattr(self.last_sample, "groundspeed_ms", 0.0) or 0.0
            self._update_map(lat, lon, alt, spd)

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
        accent = THEMES[self.current_theme]["accent_color"]
        self.lbl_status_line1.setStyleSheet(
            f"font-size: 12px; color: {THEMES[self.current_theme]['text_main']};"
        )

        # CONTRATO DE DATOS EN FORMATO EXACTO: temp:23.7,hum:45.2,...
        self.lbl_status_line2 = QLabel(
            "temp:--,hum:--,pres:--,lat:--,lon:--,speed:--,acc:--"
        )
        self.lbl_status_line2.setTextFormat(Qt.PlainText)
        self.lbl_status_line2.setStyleSheet(
            f"font-size: 12px; color: {accent};"
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
    # PÁGINA: MAPA / NAVEGACIÓN
    # ------------------------------------------------------------------

    def _build_page_map(self) -> QWidget:
        """
        Página de mapa / navegación:
        - Traza la trayectoria en coordenadas lat/lon.
        - Muestra posición actual y punto "home".
        - Auto-zoom y crosshair interactivo.
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Mapa / Navegación")
        title.setProperty("role", "title")
        header.addWidget(title)
        header.addStretch()

        self.lbl_map_status = QLabel("Lat: --  Lon: --  Alt: -- m  Vel: -- m/s")
        self.lbl_map_status.setProperty("role", "unit")
        header.addWidget(self.lbl_map_status)

        layout.addLayout(header)

        card = QFrame()
        card.setProperty("card", True)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setSpacing(8)

        lbl_sub = QLabel("Trayectoria (vista top-down)")
        lbl_sub.setProperty("role", "subtitle")
        cl.addWidget(lbl_sub)

        self.map_plot = pg.PlotWidget()
        self.map_plot.showGrid(x=True, y=True, alpha=0.15)
        self.map_plot.setBackground(THEMES[self.current_theme]["graph_bg"])
        self.map_plot.setAspectLocked(True)
        self.map_plot.setLabel("left", "Latitud [deg]")
        self.map_plot.setLabel("bottom", "Longitud [deg]")
        self.map_plot.setMouseEnabled(x=True, y=True)
        self.map_plot.enableAutoRange(x=True, y=True)

        # Curva de trayectoria
        self.map_curve = self.map_plot.plot(
            pen=pg.mkPen(THEMES[self.current_theme]["accent_color"], width=2)
        )
        # Punto UAV actual
        self.map_uav_spot = pg.ScatterPlotItem(
            size=10,
            pen=pg.mkPen("w", width=1),
            brush=pg.mkBrush(THEMES[self.current_theme]["accent_color"]),
            symbol="o",
        )
        self.map_plot.addItem(self.map_uav_spot)

        # Punto home
        self.map_home_spot = pg.ScatterPlotItem(
            size=12,
            pen=pg.mkPen("#FFD60A", width=1.5),
            brush=pg.mkBrush(0, 0, 0, 0),
            symbol="+",
        )
        self.map_plot.addItem(self.map_home_spot)

        # Crosshair
        self.map_crosshair_v = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#444", width=1))
        self.map_crosshair_h = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("#444", width=1))
        self.map_plot.addItem(self.map_crosshair_v, ignoreBounds=True)
        self.map_plot.addItem(self.map_crosshair_h, ignoreBounds=True)

        self.map_plot.scene().sigMouseMoved.connect(self._on_map_mouse_moved)

        cl.addWidget(self.map_plot)
        layout.addWidget(card, 1)

        return page

    def _on_map_mouse_moved(self, pos):
        """Actualiza el crosshair cuando se mueve el mouse sobre el mapa."""
        if self.map_plot.sceneBoundingRect().contains(pos):
            mouse_point = self.map_plot.plotItem.vb.mapSceneToView(pos)
            x = mouse_point.x()
            y = mouse_point.y()
            self.map_crosshair_v.setPos(x)
            self.map_crosshair_h.setPos(y)

    # ------------------------------------------------------------------
    # PÁGINA: GRÁFICAS DE TELEMETRÍA
    # ------------------------------------------------------------------

    def _build_page_graphs(self) -> QWidget:
        """
        Construye la página de gráficas:
        - Cada métrica tiene su propia gráfica y color.
        - Botones para pausar y suavizar la señal.
        - Botón de habilitar/deshabilitar gráfica (punto verde/rojo).
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
            "alt": THEMES[self.current_theme]["accent_color"],   # se actualiza con el tema
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
              - botón de habilitar/deshabilitar gráfica (punto verde/rojo)
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

            # Botón para activar/desactivar esta gráfica
            toggle_btn = QPushButton("●")
            toggle_btn.setCheckable(True)
            toggle_btn.setFlat(True)
            toggle_btn.setFixedWidth(24)
            toggle_btn.setChecked(self.graph_enabled.get(key, True))

            def _update_toggle_style():
                checked = toggle_btn.isChecked()
                color = (
                    THEMES[self.current_theme]["success_color"]
                    if checked
                    else THEMES[self.current_theme]["danger_color"]
                )
                toggle_btn.setStyleSheet(
                    f"color:{color}; background:transparent; border:none; font-size:16px;"
                )

            def _on_toggle(checked: bool, k=key):
                self.graph_enabled[k] = checked
                _update_toggle_style()

            toggle_btn.toggled.connect(_on_toggle)
            self.graph_toggle_buttons[key] = toggle_btn
            _update_toggle_style()

            btn_expand = QPushButton("Detalle")
            btn_expand.setProperty("action", "secondary")

            value_lbl = QLabel("--")
            value_lbl.setProperty("role", "metricSmall")

            btn_expand.clicked.connect(
                lambda _, col=db_column, u=unit, ttl=title_text, k=key: self._open_metric_detail(
                    ttl, col, u, self.metric_colors[k]
                )
            )

            header_plot.addWidget(toggle_btn)
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
        - Config avanzada por backend.
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
        self.combo_source.currentTextChanged.connect(self._on_source_changed)

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

        # Configuración avanzada MAVSDK
        self.mavsdk_adv_frame = QFrame()
        mav_form = QFormLayout(self.mavsdk_adv_frame)
        self.spin_mav_system_id = QSpinBox()
        self.spin_mav_system_id.setRange(1, 255)
        self.spin_mav_system_id.setValue(1)
        self.spin_mav_comp_id = QSpinBox()
        self.spin_mav_comp_id.setRange(1, 255)
        self.spin_mav_comp_id.setValue(1)
        self.spin_mav_timeout = QDoubleSpinBox()
        self.spin_mav_timeout.setRange(0.5, 60.0)
        self.spin_mav_timeout.setDecimals(1)
        self.spin_mav_timeout.setValue(10.0)
        mav_form.addRow("MAVSDK system_id:", self.spin_mav_system_id)
        mav_form.addRow("MAVSDK component_id:", self.spin_mav_comp_id)
        mav_form.addRow("Timeout conexión SITL (s):", self.spin_mav_timeout)
        cl.addWidget(self.mavsdk_adv_frame)

        # Configuración avanzada LoRa
        self.lora_adv_frame = QFrame()
        lora_form = QFormLayout(self.lora_adv_frame)
        self.combo_lora_baud = QComboBox()
        self.combo_lora_baud.addItems(["57600", "115200", "38400", "19200"])
        self.combo_lora_baud.setCurrentText("57600")
        self.spin_lora_buffer = QSpinBox()
        self.spin_lora_buffer.setRange(32, 4096)
        self.spin_lora_buffer.setValue(256)
        self.spin_lora_retry_delay = QDoubleSpinBox()
        self.spin_lora_retry_delay.setRange(0.1, 10.0)
        self.spin_lora_retry_delay.setDecimals(1)
        self.spin_lora_retry_delay.setValue(1.0)
        lora_form.addRow("LoRa baudrate:", self.combo_lora_baud)
        lora_form.addRow("Tamaño buffer paquete:", self.spin_lora_buffer)
        lora_form.addRow("Retraso reintento (s):", self.spin_lora_retry_delay)
        cl.addWidget(self.lora_adv_frame)

        # Botón conectar
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

        # Ajustar visibilidad inicial
        self._on_source_changed(self.combo_source.currentText())

        return page

    def _on_source_changed(self, text: str):
        """Muestra/oculta configuración avanzada según backend."""
        if text == "MAVSDK":
            self.mavsdk_adv_frame.show()
            self.lora_adv_frame.hide()
        elif text == "LoRa":
            self.mavsdk_adv_frame.hide()
            self.lora_adv_frame.show()
        else:
            self.mavsdk_adv_frame.hide()
            self.lora_adv_frame.hide()

    # ------------------------------------------------------------------
    # PÁGINA: CONFIGURACIÓN (RENDIMIENTO, ALERTAS, COLOR PRINCIPAL)
    # ------------------------------------------------------------------

    def _build_page_settings(self) -> QWidget:
        """
        Página de configuración:
        - Color principal (accent) para modo oscuro y claro.
        - Cámara / HUD.
        - Gráficas.
        - Mapa.
        - BD / disco.
        - Alertas y seguridad.
        - Reconexión automática.
        - Timeout de enlace.
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Configuración")
        title.setProperty("role", "title")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        card = QFrame()
        card.setProperty("card", True)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(18)

        # --- Color principal (accent) --------------------------------
        lbl_accent = QLabel("Color principal (accent)")
        lbl_accent.setProperty("role", "subtitle")
        cl.addWidget(lbl_accent)

        row_accent_dark = QHBoxLayout()
        lbl_dark = QLabel("Modo oscuro:")
        lbl_dark.setProperty("role", "unit")
        row_accent_dark.addWidget(lbl_dark)
        row_accent_dark.addStretch()
        self.combo_accent_dark = QComboBox()
        self.combo_accent_dark.addItems(list(self.accent_options.keys()))
        idx_dark = self.combo_accent_dark.findText(self.accent_choice_dark)
        if idx_dark >= 0:
            self.combo_accent_dark.setCurrentIndex(idx_dark)
        self.combo_accent_dark.currentTextChanged.connect(self._on_accent_dark_changed)
        row_accent_dark.addWidget(self.combo_accent_dark)
        cl.addLayout(row_accent_dark)

        row_accent_light = QHBoxLayout()
        lbl_light = QLabel("Modo claro:")
        lbl_light.setProperty("role", "unit")
        row_accent_light.addWidget(lbl_light)
        row_accent_light.addStretch()
        self.combo_accent_light = QComboBox()
        self.combo_accent_light.addItems(list(self.accent_options.keys()))
        idx_light = self.combo_accent_light.findText(self.accent_choice_light)
        if idx_light >= 0:
            self.combo_accent_light.setCurrentIndex(idx_light)
        self.combo_accent_light.currentTextChanged.connect(self._on_accent_light_changed)
        row_accent_light.addWidget(self.combo_accent_light)
        cl.addLayout(row_accent_light)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        cl.addWidget(sep1)

        # Cámara / HUD
        row_cam = QHBoxLayout()
        lbl_cam = QLabel("Cámara y HUD (frecuencia de actualización):")
        lbl_cam.setProperty("role", "unit")
        row_cam.addWidget(lbl_cam)
        row_cam.addStretch()
        self.combo_cam_profile = QComboBox()
        self.combo_cam_profile.addItems([
            "Nivel 1 – Muy ligero",
            "Nivel 2 – Ligero",
            "Nivel 3 – Medio",
            "Nivel 4 – Alto",
            "Nivel 5 – Muy alto",
            "Nivel 6 – Extremo (más carga)",
        ])
        self.combo_cam_profile.currentIndexChanged.connect(self._on_cam_profile_changed)
        row_cam.addWidget(self.combo_cam_profile)
        cl.addLayout(row_cam)

        # Gráficas
        row_graph = QHBoxLayout()
        lbl_graph = QLabel("Gráficas (downsampling y refresco):")
        lbl_graph.setProperty("role", "unit")
        row_graph.addWidget(lbl_graph)
        row_graph.addStretch()
        self.combo_graph_profile = QComboBox()
        self.combo_graph_profile.addItems([
            "Nivel 1 – Máxima precisión (sin downsampling)",
            "Nivel 2 – Alta precisión",
            "Nivel 3 – Equilibrado",
            "Nivel 4 – Rendimiento medio",
            "Nivel 5 – Rendimiento alto",
            "Nivel 6 – Modo extremo (pocos puntos)",
        ])
        self.combo_graph_profile.currentIndexChanged.connect(self._on_graph_profile_changed)
        row_graph.addWidget(self.combo_graph_profile)
        cl.addLayout(row_graph)

        # Mapa
        row_map = QHBoxLayout()
        lbl_map = QLabel("Mapa (puntos en trayectoria y refresco):")
        lbl_map.setProperty("role", "unit")
        row_map.addWidget(lbl_map)
        row_map.addStretch()
        self.combo_map_profile = QComboBox()
        self.combo_map_profile.addItems([
            "Nivel 1 – Trayectoria corta",
            "Nivel 2 – 400–600 puntos",
            "Nivel 3 – 800 puntos",
            "Nivel 4 – 1000 puntos (recomendado)",
            "Nivel 5 – 1500 puntos",
            "Nivel 6 – 2000 puntos (máximo)",
        ])
        self.combo_map_profile.currentIndexChanged.connect(self._on_map_profile_changed)
        row_map.addWidget(self.combo_map_profile)
        cl.addLayout(row_map)

        # BD / disco
        row_db = QHBoxLayout()
        lbl_db = QLabel("Escritura a disco (frecuencia de commits):")
        lbl_db.setProperty("role", "unit")
        row_db.addWidget(lbl_db)
        row_db.addStretch()
        self.combo_db_profile = QComboBox()
        self.combo_db_profile.addItems([
            "Nivel 1 – Máxima precisión (por muestra + flush rápido)",
            "Nivel 2 – Alta precisión (por muestra + flush estándar)",
            "Nivel 3 – Equilibrado (solo flush rápido)",
            "Nivel 4 – Ahorro (solo flush estándar)",
            "Nivel 5 – Ahorro alto (flush más espaciado)",
            "Nivel 6 – Modo extremo (mínimo acceso a disco)",
        ])
        self.combo_db_profile.currentIndexChanged.connect(self._on_db_profile_changed)
        row_db.addWidget(self.combo_db_profile)
        cl.addLayout(row_db)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        cl.addWidget(sep2)

        # Alertas y seguridad
        lbl_alerts = QLabel("Alertas y seguridad")
        lbl_alerts.setProperty("role", "subtitle")
        cl.addWidget(lbl_alerts)

        alerts_form = QFormLayout()
        self.spin_batt_warn = QSpinBox()
        self.spin_batt_warn.setRange(0, 100)
        self.spin_batt_warn.setValue(int(self.alert_batt_warn_pct))
        self.spin_batt_warn.valueChanged.connect(
            lambda v: setattr(self, "alert_batt_warn_pct", float(v))
        )

        self.spin_batt_crit = QSpinBox()
        self.spin_batt_crit.setRange(0, 100)
        self.spin_batt_crit.setValue(int(self.alert_batt_crit_pct))
        self.spin_batt_crit.valueChanged.connect(
            lambda v: setattr(self, "alert_batt_crit_pct", float(v))
        )

        self.spin_alt_max = QDoubleSpinBox()
        self.spin_alt_max.setRange(0.0, 10000.0)
        self.spin_alt_max.setDecimals(1)
        self.spin_alt_max.setValue(self.alert_alt_max)
        self.spin_alt_max.valueChanged.connect(
            lambda v: setattr(self, "alert_alt_max", float(v))
        )

        self.spin_spd_max = QDoubleSpinBox()
        self.spin_spd_max.setRange(0.0, 200.0)
        self.spin_spd_max.setDecimals(1)
        self.spin_spd_max.setValue(self.alert_spd_max)
        self.spin_spd_max.valueChanged.connect(
            lambda v: setattr(self, "alert_spd_max", float(v))
        )

        self.spin_temp_max = QDoubleSpinBox()
        self.spin_temp_max.setRange(-40.0, 150.0)
        self.spin_temp_max.setDecimals(1)
        self.spin_temp_max.setValue(self.alert_temp_max)
        self.spin_temp_max.valueChanged.connect(
            lambda v: setattr(self, "alert_temp_max", float(v))
        )

        self.spin_gps_min_sats = QSpinBox()
        self.spin_gps_min_sats.setRange(0, 30)
        self.spin_gps_min_sats.setValue(self.alert_gps_min_sats)
        self.spin_gps_min_sats.valueChanged.connect(
            lambda v: setattr(self, "alert_gps_min_sats", int(v))
        )

        self.spin_link_timeout = QDoubleSpinBox()
        self.spin_link_timeout.setRange(0.0, 60.0)
        self.spin_link_timeout.setDecimals(1)
        self.spin_link_timeout.setValue(self.link_timeout_s)
        self.spin_link_timeout.valueChanged.connect(self._on_link_timeout_changed)

        alerts_form.addRow("Batería baja 1 (warning %) :", self.spin_batt_warn)
        alerts_form.addRow("Batería baja 2 (crítico %) :", self.spin_batt_crit)
        alerts_form.addRow("Altitud máx recomendada (m):", self.spin_alt_max)
        alerts_form.addRow("Velocidad máx recomendada (m/s):", self.spin_spd_max)
        alerts_form.addRow("Temperatura máx (°C):", self.spin_temp_max)
        alerts_form.addRow("GPS sats mínimos:", self.spin_gps_min_sats)
        alerts_form.addRow("Timeout enlace (s, 0=desact.):", self.spin_link_timeout)
        cl.addLayout(alerts_form)

        # Selección de eventos
        row_events = QHBoxLayout()
        row_events.addWidget(QLabel("Eventos activos:"))
        self.chk_alert_batt = QCheckBox("Batería baja")
        self.chk_alert_batt.setChecked(self.alert_enable_batt)
        self.chk_alert_batt.toggled.connect(
            lambda v: setattr(self, "alert_enable_batt", bool(v))
        )
        self.chk_alert_alt = QCheckBox("Altitud alta")
        self.chk_alert_alt.setChecked(self.alert_enable_alt)
        self.chk_alert_alt.toggled.connect(
            lambda v: setattr(self, "alert_enable_alt", bool(v))
        )
        self.chk_alert_spd = QCheckBox("Velocidad alta")
        self.chk_alert_spd.setChecked(self.alert_enable_spd)
        self.chk_alert_spd.toggled.connect(
            lambda v: setattr(self, "alert_enable_spd", bool(v))
        )
        self.chk_alert_temp = QCheckBox("Temperatura alta")
        self.chk_alert_temp.setChecked(self.alert_enable_temp)
        self.chk_alert_temp.toggled.connect(
            lambda v: setattr(self, "alert_enable_temp", bool(v))
        )
        self.chk_alert_gps = QCheckBox("GPS bajo")
        self.chk_alert_gps.setChecked(self.alert_enable_gps)
        self.chk_alert_gps.toggled.connect(
            lambda v: setattr(self, "alert_enable_gps", bool(v))
        )
        self.chk_alert_link = QCheckBox("Pérdida de enlace")
        self.chk_alert_link.setChecked(self.alert_enable_link)
        self.chk_alert_link.toggled.connect(
            lambda v: setattr(self, "alert_enable_link", bool(v))
        )
        row_events.addWidget(self.chk_alert_batt)
        row_events.addWidget(self.chk_alert_alt)
        row_events.addWidget(self.chk_alert_spd)
        row_events.addWidget(self.chk_alert_temp)
        row_events.addWidget(self.chk_alert_gps)
        row_events.addWidget(self.chk_alert_link)
        row_events.addStretch()
        cl.addLayout(row_events)

        # Estilo de alerta
        row_style = QHBoxLayout()
        lbl_style = QLabel("Estilo de alerta:")
        lbl_style.setProperty("role", "unit")
        row_style.addWidget(lbl_style)
        row_style.addStretch()
        self.combo_alert_style = QComboBox()
        self.combo_alert_style.addItems(
            ["Solo color en la interfaz", "Color + ventana emergente"]
        )
        self.combo_alert_style.setCurrentIndex(
            0 if self.alert_style == "ui" else 1
        )
        self.combo_alert_style.currentIndexChanged.connect(self._on_alert_style_changed)
        row_style.addWidget(self.combo_alert_style)
        cl.addLayout(row_style)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        cl.addWidget(sep3)

        # Reconexión automática
        lbl_reconn = QLabel("Reconexión automática (backend / redes)")
        lbl_reconn.setProperty("role", "subtitle")
        cl.addWidget(lbl_reconn)

        row_auto_reconn = QHBoxLayout()
        self.chk_auto_reconnect = QCheckBox("Habilitar reconexión automática")
        self.chk_auto_reconnect.setChecked(self.auto_reconnect_enabled)
        self.chk_auto_reconnect.toggled.connect(
            lambda v: setattr(self, "auto_reconnect_enabled", bool(v))
        )
        row_auto_reconn.addWidget(self.chk_auto_reconnect)
        row_auto_reconn.addStretch()
        cl.addLayout(row_auto_reconn)

        reconn_form = QFormLayout()
        self.spin_reconnect_interval = QDoubleSpinBox()
        self.spin_reconnect_interval.setRange(1.0, 120.0)
        self.spin_reconnect_interval.setDecimals(1)
        self.spin_reconnect_interval.setValue(self.reconnect_interval_s)
        self.spin_reconnect_interval.valueChanged.connect(
            lambda v: setattr(self, "reconnect_interval_s", float(v))
        )

        self.spin_reconnect_max = QSpinBox()
        self.spin_reconnect_max.setRange(0, 100)
        self.spin_reconnect_max.setValue(self.reconnect_max_attempts)
        self.spin_reconnect_max.valueChanged.connect(
            lambda v: setattr(self, "reconnect_max_attempts", int(v))
        )

        reconn_form.addRow("Reintentar cada (s):", self.spin_reconnect_interval)
        reconn_form.addRow("Máx reintentos (0 = infinito):", self.spin_reconnect_max)
        cl.addLayout(reconn_form)

        info_txt = QLabel(
            "Nota:\n"
            "- Mapa y gráficas solo se redibujan cuando su pestaña está visible.\n"
            "- La cámara solo se anima en el Dashboard.\n"
            "- Puedes combinar niveles para buscar el mejor compromiso entre lag y precisión."
        )
        info_txt.setProperty("role", "unit")
        cl.addWidget(info_txt)

        layout.addWidget(card)

        return page

    # ------------------------------------------------------------------
    # MANEJO DE PERFILES DE RENDIMIENTO
    # ------------------------------------------------------------------

    def _init_performance_controls(self):
        """
        Inicializa los combos de rendimiento con valores intermedios sin
        comprometer nada. Se llama después de crear timers.
        """
        # Cámara: nivel 3 (índice 2)
        if hasattr(self, "combo_cam_profile"):
            self.combo_cam_profile.blockSignals(True)
            self.combo_cam_profile.setCurrentIndex(2)
            self.combo_cam_profile.blockSignals(False)
            self._on_cam_profile_changed(2)

        # Gráficas: nivel 3 (equilibrado)
        if hasattr(self, "combo_graph_profile"):
            self.combo_graph_profile.blockSignals(True)
            self.combo_graph_profile.setCurrentIndex(2)
            self.combo_graph_profile.blockSignals(False)
            self._on_graph_profile_changed(2)

        # Mapa: nivel 4 (1000 puntos aprox)
        if hasattr(self, "combo_map_profile"):
            self.combo_map_profile.blockSignals(True)
            self.combo_map_profile.setCurrentIndex(3)
            self.combo_map_profile.blockSignals(False)
            self._on_map_profile_changed(3)

        # BD: nivel 2 (alta precisión)
        if hasattr(self, "combo_db_profile"):
            self.combo_db_profile.blockSignals(True)
            self.combo_db_profile.setCurrentIndex(1)
            self.combo_db_profile.blockSignals(False)
            self._on_db_profile_changed(1)

    def _on_cam_profile_changed(self, idx: int):
        """Cambia el periodo de actualización de la cámara según el nivel."""
        if not hasattr(self, "_cam_profile_intervals"):
            return
        idx = max(0, min(5, idx))
        self.camera_update_ms = self._cam_profile_intervals[idx]
        if hasattr(self, "cam_timer"):
            self.cam_timer.setInterval(self.camera_update_ms)

    def _on_graph_profile_changed(self, idx: int):
        """Ajusta frecuencia y downsampling de gráficas."""
        if not hasattr(self, "_graph_profile_periods"):
            return
        idx = max(0, min(5, idx))
        self.graph_update_period_ms = self._graph_profile_periods[idx]
        self.graph_max_points = self._graph_profile_points[idx]

    def _on_map_profile_changed(self, idx: int):
        """Ajusta frecuencia de refresco y nº máximo de puntos en el mapa."""
        if not hasattr(self, "_map_profile_periods"):
            return
        idx = max(0, min(5, idx))
        self.map_update_period_ms = self._map_profile_periods[idx]
        new_max = self._map_profile_points[idx]
        self._set_map_max_points(new_max)

    def _on_db_profile_changed(self, idx: int):
        """Cambia cómo y cada cuánto se hace flush de la BD."""
        if not hasattr(self, "_db_profile_commit_flags"):
            return
        idx = max(0, min(5, idx))
        self.db_commit_per_sample = self._db_profile_commit_flags[idx]
        self.db_timer_interval_ms = self._db_profile_intervals[idx]
        if hasattr(self, "db_timer"):
            self.db_timer.setInterval(self.db_timer_interval_ms)

    # ------------------------------------------------------------------
    # ANIMACIONES DE SEÑAL / CONEXIÓN
    # ------------------------------------------------------------------

    def _start_signal_pulse(self, target_level: int = 4):
        """Inicia una animación rápida de subida de barras de señal."""
        self._signal_pulse_target = max(0, min(4, target_level))
        self._signal_pulse_level = 0
        self.signal_pulse_timer.start(80)

    def _signal_pulse_step(self):
        """Paso de la animación de barras de señal."""
        self._signal_pulse_level += 1
        lvl = min(self._signal_pulse_level, self._signal_pulse_target)
        self.signal_widget.set_level(lvl)
        self.signal_widget_conn.set_level(lvl)
        if self._signal_pulse_level >= self._signal_pulse_target:
            self.signal_pulse_timer.stop()

    def _set_connection_status(self, connected: bool, extra: str = ""):
        """Actualiza el texto de estado de conexión en el header del dashboard."""
        t = THEMES[self.current_theme]
        if connected:
            self._stop_connecting_animation()
            self.lbl_conn_status.setText(f"Conectado ({extra})")
            self.lbl_conn_status.setStyleSheet(
                f"color:{t['success_color']}; font-weight:600;"
            )
            self._start_signal_pulse(4)
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
        self._connecting_fake_level = (self._connecting_fake_level + 1) % 5
        self.signal_widget.set_level(self._connecting_fake_level)
        self.signal_widget_conn.set_level(self._connecting_fake_level)

    def _on_connect_clicked(self):
        """Manejador del botón Conectar."""
        src = self.combo_source.currentText()
        self.source_name = src
        endpoint = self.edit_endpoint.text().strip()
        self._last_endpoint = endpoint
        self._reconnect_attempts = 0

        # Detener backend previo si existe
        if self.backend is not None and hasattr(self.backend, "stop"):
            try:
                asyncio.create_task(self.backend.stop())
            except RuntimeError:
                pass

        # Crear backend según la fuente seleccionada
        if src == "DEMO":
            self.backend = BackendTelemetria(force_demo=True)
        elif src == "MAVSDK":
            self.backend = BackendTelemetria(force_demo=False)
            if hasattr(self.backend, "system_id"):
                self.backend.system_id = self.spin_mav_system_id.value()
            if hasattr(self.backend, "component_id"):
                self.backend.component_id = self.spin_mav_comp_id.value()
            if hasattr(self.backend, "connection_timeout_s"):
                self.backend.connection_timeout_s = float(self.spin_mav_timeout.value())
        else:  # LoRa
            try:
                baud = int(self.combo_lora_baud.currentText())
            except ValueError:
                baud = 57600
            self.backend = LoRaBackend(port=endpoint or "COM3", baud=baud)
            if hasattr(self.backend, "buffer_size"):
                self.backend.buffer_size = int(self.spin_lora_buffer.value())
            if hasattr(self.backend, "retry_delay_s"):
                self.backend.retry_delay_s = float(self.spin_lora_retry_delay.value())

        self._start_connecting_animation()

        try:
            asyncio.create_task(self._run_backend(endpoint))
        except RuntimeError:
            # Si se ejecuta sin loop de asyncio, el usuario deberá lanzar el backend externamente.
            pass

    async def _run_backend(self, endpoint: str):
        """
        Corrutina que se encarga de conectar el backend y consumir las muestras.
        Implementa política de reconexión automática básica.
        """
        attempts = 0
        while True:
            try:
                await self.backend.connect(endpoint)
                self._set_connection_status(True, self.source_name)
                attempts = 0
                async for sample in self.backend.samples():
                    self.signals.sample.emit(sample)
                # Si el generador termina sin excepción, lo tratamos como desconexión
                raise RuntimeError("Enlace finalizado")
            except Exception as e:
                self._set_connection_status(False, "error")
                if not self.auto_reconnect_enabled:
                    QMessageBox.critical(self, "Error de backend", str(e))
                    break
                attempts += 1
                self._reconnect_attempts = attempts
                max_attempts = self.reconnect_max_attempts
                if max_attempts > 0 and attempts > max_attempts:
                    QMessageBox.critical(
                        self,
                        "Error de backend",
                        f"Fallo de conexión tras {attempts} intentos: {e}",
                    )
                    break
                await asyncio.sleep(self.reconnect_interval_s)

    # ------------------------------------------------------------------
    # MANEJO DE TELEMETRÍA ENTRANTE
    # ------------------------------------------------------------------

    def _handle_sample(self, s: TelemetrySample):
        """
        Lógica principal al recibir una muestra:
        - Actualiza buffers de gráficas.
        - Actualiza HUD y estado rápido.
        - Actualiza texto de “Contrato”.
        - Actualiza mapa de trayectoria.
        - Aplica alertas y seguridad.
        - Guarda la muestra en la base de datos.
        """
        self.last_sample = s

        # Reset del timeout de enlace (heartbeat)
        self._reset_link_timeout_timer()

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

        roll = getattr(s, "roll_deg", 0.0) or 0.0
        pitch = getattr(s, "pitch_deg", 0.0) or 0.0
        yaw = getattr(s, "yaw_deg", 0.0) or 0.0
        vx = getattr(s, "vx_ms", 0.0) or 0.0
        vy = getattr(s, "vy_ms", 0.0) or 0.0
        vz = getattr(s, "vz_ms", 0.0) or 0.0

        # Buffers para gráficas
        self.alt_buf.append(alt)
        self.spd_buf.append(spd)
        self.volt_buf.append(vbat)
        self.temp_buf.append(tmp)
        self.pres_buf.append(pres)
        self.hum_buf.append(hum)

        # --- Dashboard: batería / valores rápidos -------------------
        self.bat_widget.set_level(bat_pct)
        self.lbl_bat_val.setText(f"{vbat:.2f} V" if vbat > 0 else "-- V")

        self.lbl_alt_val.setText(f"{alt:.1f}")
        self.lbl_spd_val.setText(f"{spd:.1f}")
        self.lbl_tmp_val.setText(f"{tmp:.1f}")

        t_theme = THEMES[self.current_theme]

        # Batería: color + alertas
        batt_level = 0
        if bat_pct <= self.alert_batt_crit_pct:
            batt_color = t_theme["danger_color"]
            batt_level = 2
        elif bat_pct <= self.alert_batt_warn_pct:
            batt_color = t_theme["warning_color"]
            batt_level = 1
        else:
            batt_color = t_theme["text_main"]
            batt_level = 0

        self.lbl_bat_val.setStyleSheet(
            f"color:{batt_color}; font-weight:700; font-size:18px;"
        )

        if self.alert_enable_batt and batt_level > self.last_batt_alert_level:
            if batt_level == 1 and self.alert_style == "popup":
                QMessageBox.warning(
                    self,
                    "Batería baja",
                    f"La batería ha bajado a {bat_pct:.0f}%.",
                )
            elif batt_level == 2 and self.alert_style == "popup":
                QMessageBox.critical(
                    self,
                    "Batería crítica",
                    f"La batería ha bajado a {bat_pct:.0f}%. Aterriza lo antes posible.",
                )
        if batt_level == 0 and self.last_batt_alert_level != 0:
            self.last_batt_alert_level = 0
        else:
            self.last_batt_alert_level = max(self.last_batt_alert_level, batt_level)

        # Altitud con umbral máximo
        if alt < 5.0:
            color_alt = t_theme["danger_color"]
            alt_over = False
        elif alt > self.alert_alt_max:
            color_alt = t_theme["warning_color"]
            alt_over = True
        else:
            color_alt = t_theme["accent_color"]
            alt_over = False

        self.lbl_alt_val.setStyleSheet(
            f"color:{color_alt}; font-weight:800; font-size:24px;"
        )

        if self.alert_enable_alt:
            if alt_over and not self.alt_alert_active:
                self.alt_alert_active = True
                if self.alert_style == "popup":
                    QMessageBox.warning(
                        self,
                        "Altitud alta",
                        f"Se superó la altitud recomendada de {self.alert_alt_max:.0f} m.",
                    )
            elif not alt_over and self.alt_alert_active:
                self.alt_alert_active = False

        # Velocidad con umbral máximo
        if hasattr(self, "metric_colors"):
            base_spd_color = self.metric_colors["spd"]
        else:
            base_spd_color = "#00D1FF"

        spd_over = spd > self.alert_spd_max
        spd_color = t_theme["danger_color"] if spd_over else base_spd_color
        self.lbl_spd_val.setStyleSheet(
            f"color:{spd_color}; font-weight:700; font-size:22px;"
        )

        if self.alert_enable_spd:
            if spd_over and not self.spd_alert_active:
                self.spd_alert_active = True
                if self.alert_style == "popup":
                    QMessageBox.warning(
                        self,
                        "Velocidad alta",
                        f"La velocidad ha superado {self.alert_spd_max:.1f} m/s.",
                    )
            elif not spd_over and self.spd_alert_active:
                self.spd_alert_active = False

        # Temperatura con umbral máximo
        if hasattr(self, "metric_colors"):
            base_tmp_color = self.metric_colors["tmp"]
        else:
            base_tmp_color = "#FF375F"

        temp_over = tmp > self.alert_temp_max
        tmp_color = t_theme["danger_color"] if temp_over else base_tmp_color
        self.lbl_tmp_val.setStyleSheet(
            f"color:{tmp_color}; font-weight:700; font-size:22px;"
        )

        if self.alert_enable_temp:
            if temp_over and not self.temp_alert_active:
                self.temp_alert_active = True
                if self.alert_style == "popup":
                    QMessageBox.warning(
                        self,
                        "Temperatura alta",
                        f"La temperatura ha superado {self.alert_temp_max:.1f} °C.",
                    )
            elif not temp_over and self.temp_alert_active:
                self.temp_alert_active = False

        # Tiempo de vuelo en formato hh:mm:ss
        hrs = int(self.flight_time_s // 3600)
        mins = int((self.flight_time_s % 3600) // 60)
        secs = int(self.flight_time_s % 60)
        self.lbl_flight_time_val.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")

        # ------------------ ENERGÍA ESPECÍFICA + FPV ------------------
        v_mod = sqrt(vx * vx + vy * vy + vz * vz)
        energia = G0 * alt + 0.5 * v_mod * v_mod

        trend = 0
        if self.prev_energy is not None:
            if energia > self.prev_energy + 5.0:
                trend = 1
            elif energia < self.prev_energy - 5.0:
                trend = -1
        self.prev_energy = energia
        self.energy_trend = trend

        if v_mod > 0.1:
            fpv_pitch = atan2(-vz, sqrt(vx * vx + vy * vy)) * 180.0 / pi
            fpv_yaw = atan2(vy, vx) * 180.0 / pi
        else:
            fpv_pitch = pitch
            fpv_yaw = yaw

        slip_val = 0.0

        self.att_widget.set_attitude(
            roll,
            pitch,
            yaw_deg=yaw,
            fpv_pitch_deg=fpv_pitch,
            fpv_yaw_deg=fpv_yaw,
            slip=slip_val,
            energy_trend=self.energy_trend,
        )

        # Líneas de estado tipo “Contrato”
        modo = getattr(s, "flight_mode", "--") or "--"
        en_aire_txt = "Sí" if in_air else "No"
        self.lbl_status_line1.setText(
            f"GPS: {sats} sats | Modo: {modo} | En aire: {en_aire_txt} | Fuente: {self.source_name}"
        )

        self.lbl_status_line2.setText(
            f"temp:{tmp:.1f},hum:{hum:.1f},pres:{pres:.2f},"
            f"lat:{lat:.4f},lon:{lon:.4f},speed:{spd:.1f},acc:{acc:.1f}"
        )

        # Alertas basadas en GPS
        if self.alert_enable_gps:
            gps_bad = sats < self.alert_gps_min_sats
            if gps_bad and not self.gps_alert_active:
                self.gps_alert_active = True
                if self.alert_style == "popup":
                    QMessageBox.warning(
                        self,
                        "GPS limitado",
                        f"Se detectan solo {sats} satélites (< {self.alert_gps_min_sats}).",
                    )
            elif not gps_bad and self.gps_alert_active:
                self.gps_alert_active = False

            if gps_bad:
                self.lbl_status_line1.setStyleSheet(
                    f"font-size: 12px; color: {t_theme['warning_color']};"
                )
            else:
                self.lbl_status_line1.setStyleSheet(
                    f"font-size: 12px; color: {THEMES[self.current_theme]['text_main']};"
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

        # Tiempo actual para control de refresco
        now_ms = time.monotonic() * 1000.0

        # Gráficas
        if self._should_update_graphs(now_ms):
            self._update_graphs()

        # Etiquetas bajo las gráficas
        self.lbl_alt_graph_val.setText(f"{alt:.1f} m")
        self.lbl_spd_graph_val.setText(f"{spd:.1f} m/s")
        self.lbl_vbat_graph_val.setText(f"{vbat:.2f} V")
        self.lbl_tmp_graph_val.setText(f"{tmp:.1f} °C")
        self.lbl_pres_graph_val.setText(f"{pres:.1f} hPa")
        self.lbl_hum_graph_val.setText(f"{hum:.1f} %")

        # Mapa / trayectoria
        if self._should_update_map(now_ms):
            self._update_map(lat, lon, alt, spd)

        # Guardar en BD
        self.db.append(self.source_name, s)
        if self.db_commit_per_sample:
            self.db.flush()

    def _should_update_graphs(self, now_ms: float) -> bool:
        """
        Controla si se deben redibujar las gráficas:
        - Solo si la pestaña de gráficas está activa.
        - Respetando el periodo configurado (graph_update_period_ms).
        """
        if not hasattr(self, "stack"):
            return False
        if self.stack.currentIndex() != 2:
            return False
        if self.graph_update_period_ms <= 0:
            self._last_graph_update_ms = now_ms
            return True
        if now_ms - self._last_graph_update_ms >= self.graph_update_period_ms:
            self._last_graph_update_ms = now_ms
            return True
        return False

    def _should_update_map(self, now_ms: float) -> bool:
        """
        Controla si se debe redibujar el mapa:
        - Solo si la pestaña de mapa está activa.
        - Respetando el periodo configurado (map_update_period_ms).
        """
        if not hasattr(self, "stack"):
            return False
        if self.stack.currentIndex() != 1:
            return False
        if self.map_update_period_ms <= 0:
            self._last_map_update_ms = now_ms
            return True
        if now_ms - self._last_map_update_ms >= self.map_update_period_ms:
            self._last_map_update_ms = now_ms
            return True
        return False

    def _update_graphs(self):
        """Actualiza las curvas de las gráficas en la pestaña correspondiente."""
        if self.graph_paused:
            return
        if not self.time_buf:
            return

        x_full = list(self.time_buf)

        def apply_smooth(vals: List[float]) -> List[float]:
            if not self.graph_smooth or len(vals) < 5:
                return vals
            w = 5
            sm = []
            for i in range(len(vals)):
                i0 = max(0, i - w + 1)
                window = vals[i0:i + 1]
                sm.append(sum(window) / len(window))
            return sm

        alt_vals = apply_smooth(list(self.alt_buf))
        spd_vals = apply_smooth(list(self.spd_buf))
        vbat_vals = apply_smooth(list(self.volt_buf))
        tmp_vals = apply_smooth(list(self.temp_buf))
        pres_vals = apply_smooth(list(self.pres_buf))
        hum_vals = apply_smooth(list(self.hum_buf))

        step = 1
        if self.graph_max_points and len(x_full) > self.graph_max_points:
            step = max(1, len(x_full) // self.graph_max_points)

        x = x_full[::step]
        alt_y = alt_vals[::step]
        spd_y = spd_vals[::step]
        vbat_y = vbat_vals[::step]
        tmp_y = tmp_vals[::step]
        pres_y = pres_vals[::step]
        hum_y = hum_vals[::step]

        if self.graph_enabled.get("alt", True):
            self.curve_alt.setData(x, alt_y)
        else:
            self.curve_alt.clear()

        if self.graph_enabled.get("spd", True):
            self.curve_spd.setData(x, spd_y)
        else:
            self.curve_spd.clear()

        if self.graph_enabled.get("vbat", True):
            self.curve_vbat.setData(x, vbat_y)
        else:
            self.curve_vbat.clear()

        if self.graph_enabled.get("tmp", True):
            self.curve_tmp.setData(x, tmp_y)
        else:
            self.curve_tmp.clear()

        if self.graph_enabled.get("pres", True):
            self.curve_pres.setData(x, pres_y)
        else:
            self.curve_pres.clear()

        if self.graph_enabled.get("hum", True):
            self.curve_hum.setData(x, hum_y)
        else:
            self.curve_hum.clear()

    def _set_map_max_points(self, max_points: int):
        """Cambia el máximo de puntos de trayectoria en el mapa."""
        max_points = max(10, int(max_points))
        self.map_max_points = max_points
        self.map_positions = deque(self.map_positions, maxlen=self.map_max_points)

    def _update_map(self, lat: float, lon: float, alt: float, spd: float):
        """
        Actualiza la página de mapa con la trayectoria:
        - Guarda posiciones (lat/lon).
        - Actualiza curva y puntos de home / UAV.
        - Auto-zoom suave.
        """
        if lat == 0.0 and lon == 0.0:
            return

        if self.map_home is None:
            self.map_home = (lat, lon)

        self.map_positions.append((lat, lon))

        lats = [p[0] for p in self.map_positions]
        lons = [p[1] for p in self.map_positions]

        self.map_curve.setData(lons, lats)
        self.map_uav_spot.setData(x=[lon], y=[lat])

        if self.map_home is not None:
            home_lat, home_lon = self.map_home
            self.map_home_spot.setData(x=[home_lon], y=[home_lat])

        if len(self.map_positions) >= 2:
            self.map_plot.autoRange(padding=0.12)

        self.lbl_map_status.setText(
            f"Lat: {lat:.5f}  Lon: {lon:.5f}  Alt: {alt:.1f} m  Vel: {spd:.1f} m/s"
        )

    # ------------------------------------------------------------------
    # CAMBIO DE TEMA (OSC/CLARO) + ACENTO
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
        if hasattr(self, "metric_colors"):
            # Altitud toma el color de acento actual
            self.metric_colors["alt"] = THEMES[self.current_theme]["accent_color"]
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

        # Fondo del mapa
        self.map_plot.setBackground(THEMES[self.current_theme]["graph_bg"])

        self.btn_theme.setText(
            "Modo claro" if self.current_theme == "dark" else "Modo oscuro"
        )

        # Colores de líneas de estado
        accent = THEMES[self.current_theme]["accent_color"]
        self.lbl_status_line1.setStyleSheet(
            f"font-size: 12px; color: {THEMES[self.current_theme]['text_main']};"
        )
        self.lbl_status_line2.setStyleSheet(
            f"font-size: 12px; color: {accent};"
        )

        if self.last_sample is not None:
            s = self.last_sample
            tmp = getattr(s, "temp_c", 0.0) or 0.0
            hum = getattr(s, "hum_pct", 0.0) or 0.0
            pres = getattr(s, "pres_hpa", 0.0) or 0.0
            lat = getattr(s, "lat_deg", 0.0) or 0.0
            lon = getattr(s, "lon_deg", 0.0) or 0.0
            spd = getattr(s, "groundspeed_ms", 0.0) or 0.0
            acc = getattr(s, "acc_ms2", 0.0) or 0.0
            modo = getattr(s, "flight_mode", "--") or "--"
            in_air = bool(getattr(s, "in_air", False))
            sats = getattr(s, "num_sat", 0) or 0
            en_aire_txt = "Sí" if in_air else "No"
            self.lbl_status_line1.setText(
                f"GPS: {sats} sats | Modo: {modo} | En aire: {en_aire_txt} | Fuente: {self.source_name}"
            )
            self.lbl_status_line2.setText(
                f"temp:{tmp:.1f},hum:{hum:.1f},pres:{pres:.2f},"
                f"lat:{lat:.4f},lon:{lon:.4f},speed:{spd:.1f},acc:{acc:.1f}"
            )

        # Actualizar estilo de los toggles de gráficas
        if hasattr(self, "graph_toggle_buttons"):
            for key, btn in self.graph_toggle_buttons.items():
                checked = self.graph_enabled.get(key, True)
                color = (
                    THEMES[self.current_theme]["success_color"]
                    if checked
                    else THEMES[self.current_theme]["danger_color"]
                )
                btn.setStyleSheet(
                    f"color:{color}; background:transparent; border:none; font-size:16px;"
                )

    # ------------------------------------------------------------------
    # HANDLERS CONFIG (acentos, alertas, timeout enlace)
    # ------------------------------------------------------------------

    def _on_accent_dark_changed(self, name: str):
        self.accent_choice_dark = name
        self._apply_accent_to_theme("dark", name)
        self.settings.setValue("accent_dark", name)
        if self.current_theme == "dark":
            self._apply_theme()

    def _on_accent_light_changed(self, name: str):
        self.accent_choice_light = name
        self._apply_accent_to_theme("light", name)
        self.settings.setValue("accent_light", name)
        if self.current_theme == "light":
            self._apply_theme()

    def _on_alert_style_changed(self, idx: int):
        self.alert_style = "ui" if idx == 0 else "popup"

    def _on_link_timeout_changed(self, v: float):
        self.link_timeout_s = float(v)
        if self.link_timeout_s <= 0.0:
            self.link_timeout_timer.stop()
        else:
            self.link_timeout_timer.setInterval(int(self.link_timeout_s * 1000))

    def _reset_link_timeout_timer(self):
        """Reinicia el temporizador de timeout de enlace (heartbeat)."""
        if self.link_timeout_s <= 0.0:
            self.link_timeout_timer.stop()
            return
        self.link_timeout_timer.setInterval(int(self.link_timeout_s * 1000))
        self.link_timeout_timer.start()
        self.link_alert_active = False

    def _on_link_timeout(self):
        """Se dispara cuando no llega telemetría durante el tiempo configurado."""
        if not self.alert_enable_link:
            return
        if self.link_alert_active:
            return
        self.link_alert_active = True
        self._set_connection_status(False, "timeout")
        self.signal_widget.set_level(0)
        self.signal_widget_conn.set_level(0)
        if self.alert_style == "popup":
            QMessageBox.warning(
                self,
                "Enlace perdido",
                "No se ha recibido telemetría dentro del tiempo configurado.",
            )

    # ------------------------------------------------------------------
    # CÁMARA: ACTUALIZACIÓN Y CAPTURAS
    # ------------------------------------------------------------------

    def _tick_camera(self):
        """
        Se llama periódicamente para actualizar el cuadro de la cámara.
        La cámara solo se anima cuando el Dashboard está visible.
        """
        active_backend = self.backend is not None
        active = active_backend and hasattr(self, "stack") and self.stack.currentIndex() == 0
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
            self.btn_map,
            self.btn_graph,
            self.btn_hist,
            self.btn_conn,
            self.btn_theme,
            self.btn_open_settings_small,
            getattr(self, "btn_pause_graphs", None),
            getattr(self, "btn_smooth_graphs", None),
        ]
        buttons = [b for b in buttons if b is not None]

        def wrap(btn):
            btn.pressed.connect(lambda b=btn: self._animate_button(b))

        for b in buttons:
            wrap(b)

    def _animate_button(self, btn: QPushButton):
        """Anima ligeramente el botón reduciendo su opacidad un instante."""
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