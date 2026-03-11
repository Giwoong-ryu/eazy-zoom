import time

from PyQt6.QtCore import QRect, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

_CORNER_LEN = 24
_LINE_WIDTH = 2.5
_GLOW_WIDTH = 6


class RegionHighlight(QWidget):
    """Transparent overlay that draws a glowing rectangle on the actual screen
    to show the region being captured/zoomed."""

    def __init__(self, color: str = "#4FC3F7") -> None:
        super().__init__()
        self._color = QColor(color)
        self._start_time = time.monotonic()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setGeometry(0, 0, 100, 100)

    def update_region(self, x: int, y: int, w: int, h: int) -> None:
        pad = 6
        self.setGeometry(x - pad, y - pad, w + pad * 2, h + pad * 2)
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        m = 5  # margin for glow

        # breathing alpha animation
        t = time.monotonic() - self._start_time
        breath = 0.6 + 0.4 * abs((t % 2.0) - 1.0)

        # outer glow
        glow_color = QColor(self._color)
        glow_color.setAlpha(int(35 * breath))
        glow_pen = QPen(glow_color, _GLOW_WIDTH)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(m, m, w - m * 2, h - m * 2), 4, 4)

        # thin dotted border
        dot_color = QColor(self._color)
        dot_color.setAlpha(int(70 * breath))
        dot_pen = QPen(dot_color, 1)
        dot_pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(dot_pen)
        painter.drawRoundedRect(QRectF(m, m, w - m * 2, h - m * 2), 4, 4)

        # solid corner brackets
        corner_color = QColor(self._color)
        corner_color.setAlpha(int(200 * breath))
        solid_pen = QPen(corner_color, _LINE_WIDTH)
        solid_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(solid_pen)

        cl = min(_CORNER_LEN, (w - m * 2) // 3, (h - m * 2) // 3)
        x1, y1 = m, m
        x2, y2 = w - m, h - m

        # top-left
        painter.drawLine(x1, y1, x1 + cl, y1)
        painter.drawLine(x1, y1, x1, y1 + cl)
        # top-right
        painter.drawLine(x2, y1, x2 - cl, y1)
        painter.drawLine(x2, y1, x2, y1 + cl)
        # bottom-left
        painter.drawLine(x1, y2, x1 + cl, y2)
        painter.drawLine(x1, y2, x1, y2 - cl)
        # bottom-right
        painter.drawLine(x2, y2, x2 - cl, y2)
        painter.drawLine(x2, y2, x2, y2 - cl)

        painter.end()
