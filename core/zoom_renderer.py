from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    QRectF,
    Qt,
    pyqtProperty,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QImage,
    QRadialGradient,
)
from PyQt6.QtWidgets import QWidget

_CORNER_RADIUS = 12

CURSOR_STYLES = {
    "crosshair": "줄 하이라이트",
    "ring": "원형 링",
    "dot": "점",
    "target": "사각",
    "none": "없음",
}


class ZoomRenderer(QWidget):
    """Renders zoomed screen content with neon border, cursor, and badge."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._image: QImage | None = None
        self._zoom_level: float = 2.0
        self._animated_zoom: float = 2.0
        self._border_color = QColor("#4FC3F7")
        self._border_width = 2
        self._cursor_color = QColor(79, 195, 247, 100)
        self._cursor_radius = 24
        self._cursor_style = "crosshair"
        self._show_cursor = True
        self._cursor_x = 0
        self._cursor_y = 0
        self._cursor_pixel_mode = False
        self._cursor_px = 0
        self._cursor_py = 0
        self._badge_opacity: float = 0.0

        self._zoom_anim = QPropertyAnimation(self, b"animatedZoom")
        self._zoom_anim.setDuration(200)
        self._zoom_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._badge_anim = QPropertyAnimation(self, b"badgeOpacity")
        self._badge_anim.setDuration(1500)
        self._badge_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def _get_animated_zoom(self) -> float:
        return self._animated_zoom

    def _set_animated_zoom(self, value: float) -> None:
        self._animated_zoom = value
        self.update()

    animatedZoom = pyqtProperty(float, _get_animated_zoom, _set_animated_zoom)

    def _get_badge_opacity(self) -> float:
        return self._badge_opacity

    def _set_badge_opacity(self, value: float) -> None:
        self._badge_opacity = value
        self.update()

    badgeOpacity = pyqtProperty(float, _get_badge_opacity, _set_badge_opacity)

    def set_zoom_level(self, level: float, animate: bool = True) -> None:
        self._zoom_level = level
        if animate:
            self._zoom_anim.stop()
            self._zoom_anim.setStartValue(self._animated_zoom)
            self._zoom_anim.setEndValue(level)
            self._zoom_anim.start()
        else:
            self._animated_zoom = level
            self.update()
        self._flash_badge()

    def _flash_badge(self) -> None:
        self._badge_anim.stop()
        self._badge_anim.setStartValue(1.0)
        self._badge_anim.setEndValue(0.0)
        self._badge_anim.start()

    def set_image(self, image: QImage) -> None:
        self._image = image
        self.update()

    def set_cursor_pos(self, x: int, y: int) -> None:
        self._cursor_x = x
        self._cursor_y = y
        self._cursor_pixel_mode = False

    def set_cursor_pixel(self, px: int, py: int) -> None:
        """Set cursor position directly in widget pixel coordinates (for frozen mode)."""
        self._cursor_px = px
        self._cursor_py = py
        self._cursor_pixel_mode = True

    def set_border_style(self, color: str, width: int) -> None:
        self._border_color = QColor(color)
        self._border_width = width

    def set_cursor_style(self, color: str, radius: int, opacity: int) -> None:
        self._cursor_color = QColor(color)
        self._cursor_color.setAlpha(opacity)
        self._cursor_radius = radius

    def set_cursor_shape(self, style: str) -> None:
        self._cursor_style = style
        self.update()

    def set_show_cursor(self, show: bool) -> None:
        self._show_cursor = show

    def paintEvent(self, event: object) -> None:
        if self._image is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(0, 0, w, h), _CORNER_RADIUS, _CORNER_RADIUS)
        painter.setClipPath(clip_path)

        scaled = self._image.scaled(
            w, h,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawImage(0, 0, scaled)

        if self._show_cursor and self._cursor_style != "none":
            self._draw_cursor(painter, w, h)

        painter.setClipping(False)

        # neon glow border
        glow_color = QColor(self._border_color)
        glow_color.setAlpha(50)
        for i in range(3):
            glow_pen = QPen(glow_color, self._border_width + (3 - i) * 2)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(
                QRectF(1, 1, w - 2, h - 2), _CORNER_RADIUS, _CORNER_RADIUS
            )
            glow_color.setAlpha(glow_color.alpha() + 20)

        painter.setPen(QPen(self._border_color, self._border_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(
            QRectF(1, 1, w - 2, h - 2), _CORNER_RADIUS, _CORNER_RADIUS
        )

        if self._badge_opacity > 0.01:
            self._draw_badge(painter, w, h)

        painter.end()

    def _draw_cursor(self, painter: QPainter, w: int, h: int) -> None:
        if self._cursor_pixel_mode:
            cx = self._cursor_px
            cy = self._cursor_py
        else:
            cx = w // 2
            cy = h // 2
        r = self._cursor_radius
        c = self._cursor_color
        style = self._cursor_style

        if style == "crosshair":
            # horizontal line highlight (full width, thin bar)
            line_h = 3
            # glow behind line
            glow_h = line_h + 6
            glow_color = QColor(c.red(), c.green(), c.blue(), 30)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow_color)
            painter.drawRect(QRectF(0, cy - glow_h // 2, w, glow_h))
            # main line
            line_color = QColor(c.red(), c.green(), c.blue(), 140)
            painter.setPen(QPen(line_color, line_h))
            painter.drawLine(0, cy, w, cy)
            # center dot
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(c.red(), c.green(), c.blue(), 200))
            painter.drawEllipse(cx - 3, cy - 3, 6, 6)

        elif style == "ring":
            # simple ring + glow
            r3 = r + 6
            glow = QRadialGradient(cx, cy, r3)
            glow.setColorAt(0.0, QColor(c.red(), c.green(), c.blue(), 0))
            glow.setColorAt(0.7, QColor(c.red(), c.green(), c.blue(), 0))
            glow.setColorAt(0.9, QColor(c.red(), c.green(), c.blue(), 50))
            glow.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(cx - r3, cy - r3, r3 * 2, r3 * 2)
            painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 180), 2.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        elif style == "dot":
            # filled circle
            painter.setPen(Qt.PenStyle.NoPen)
            fill = QColor(c.red(), c.green(), c.blue(), 80)
            painter.setBrush(fill)
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            # bright center
            painter.setBrush(QColor(c.red(), c.green(), c.blue(), 200))
            painter.drawEllipse(cx - 4, cy - 4, 8, 8)

        elif style == "target":
            # horizontal line highlight (approx 10 Korean chars wide ~150px, 1 line height ~22px)
            rect_w = 150
            rect_h = 44
            rx = cx - rect_w // 2
            ry = cy - rect_h // 2

            # filled highlight bar
            fill = QColor(c.red(), c.green(), c.blue(), 45)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            painter.drawRoundedRect(QRectF(rx, ry, rect_w, rect_h), 4, 4)

            # border
            border_c = QColor(c.red(), c.green(), c.blue(), 140)
            painter.setPen(QPen(border_c, 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(rx, ry, rect_w, rect_h), 4, 4)

            # left/right edge markers
            marker_c = QColor(c.red(), c.green(), c.blue(), 200)
            painter.setPen(QPen(marker_c, 2))
            painter.drawLine(rx, ry + 2, rx, ry + rect_h - 2)
            painter.drawLine(rx + rect_w, ry + 2, rx + rect_w, ry + rect_h - 2)

            # center dot
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(c.red(), c.green(), c.blue(), 180))
            painter.drawEllipse(cx - 2, cy - 2, 4, 4)

    def _draw_badge(self, painter: QPainter, w: int, h: int) -> None:
        text = f"{self._animated_zoom:.1f}x"
        font = QFont("Segoe UI", 13, QFont.Weight.Bold)
        painter.setFont(font)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text)
        th = fm.height()

        pad = 10
        bw = tw + pad * 2
        bh = th + pad
        bx = w - bw - 12
        by = h - bh - 12

        badge_rect = QRectF(bx, by, bw, bh)
        bg = QColor(15, 15, 35, int(220 * self._badge_opacity))
        painter.setBrush(bg)
        border_c = QColor(79, 195, 247, int(120 * self._badge_opacity))
        painter.setPen(QPen(border_c, 1))
        painter.drawRoundedRect(badge_rect, bh / 2, bh / 2)

        fg = QColor(79, 195, 247, int(255 * self._badge_opacity))
        painter.setPen(fg)
        painter.drawText(bx + pad, by + th - 1, text)
