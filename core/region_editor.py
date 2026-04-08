from PyQt6.QtCore import QPoint, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import QWidget

_EDGE = 12
_MIN_W = 100
_MIN_H = 80


class CaptureRegionEditor(QWidget):
    """Fullscreen overlay for interactively resizing the capture region."""

    region_confirmed = pyqtSignal(int, int)  # (width, height)

    def __init__(self, screen_w: int, screen_h: int) -> None:
        super().__init__()
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._dragging = False
        self._resizing = False
        self._resize_edge = 0
        self._drag_offset = QPoint()
        self._resize_origin = (0, 0, 0, 0)

        # The editable rectangle (screen coordinates within this widget)
        self._rx = 0
        self._ry = 0
        self._rw = 400
        self._rh = 300

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(0, 0, screen_w, screen_h)

    def set_region(self, w: int, h: int) -> None:
        """Set initial region size, centered on screen."""
        self._rw = w
        self._rh = h
        self._rx = (self._screen_w - w) // 2
        self._ry = (self._screen_h - h) // 2

    def _edge_at(self, x: int, y: int) -> int:
        edge = 0
        rx, ry, rw, rh = self._rx, self._ry, self._rw, self._rh
        if rx - _EDGE <= x <= rx + _EDGE:
            edge |= 1  # left
        if rx + rw - _EDGE <= x <= rx + rw + _EDGE:
            edge |= 2  # right
        if ry - _EDGE <= y <= ry + _EDGE:
            edge |= 4  # top
        if ry + rh - _EDGE <= y <= ry + rh + _EDGE:
            edge |= 8  # bottom
        return edge

    def _inside_rect(self, x: int, y: int) -> bool:
        return (self._rx < x < self._rx + self._rw and
                self._ry < y < self._ry + self._rh)

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # dim background
        painter.setBrush(QColor(0, 0, 0, 120))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, self._screen_w, self._screen_h)

        # clear the region rectangle (transparent hole)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.drawRect(self._rx, self._ry, self._rw, self._rh)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # region border
        pen = QPen(QColor("#4FC3F7"), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(self._rx, self._ry, self._rw, self._rh))

        # corner handles
        handle_size = 8
        handle_color = QColor("#4FC3F7")
        painter.setBrush(handle_color)
        painter.setPen(Qt.PenStyle.NoPen)
        corners = [
            (self._rx, self._ry),
            (self._rx + self._rw, self._ry),
            (self._rx, self._ry + self._rh),
            (self._rx + self._rw, self._ry + self._rh),
        ]
        for cx, cy in corners:
            painter.drawRect(cx - handle_size // 2, cy - handle_size // 2,
                             handle_size, handle_size)

        # edge midpoint handles
        mids = [
            (self._rx + self._rw // 2, self._ry),
            (self._rx + self._rw // 2, self._ry + self._rh),
            (self._rx, self._ry + self._rh // 2),
            (self._rx + self._rw, self._ry + self._rh // 2),
        ]
        for cx, cy in mids:
            painter.drawRect(cx - handle_size // 2, cy - handle_size // 2,
                             handle_size, handle_size)

        # size label
        label = f"{self._rw} x {self._rh}"
        painter.setPen(QColor(255, 255, 255, 220))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.drawText(self._rx, self._ry - 10, label)

        # hint
        hint = "드래그: 이동 / 가장자리 드래그: 크기 조절 / Esc: 확정"
        painter.setFont(QFont("Segoe UI", 11))
        painter.setPen(QColor(200, 200, 200, 180))
        fm = painter.fontMetrics()
        hint_w = fm.horizontalAdvance(hint)
        painter.drawText((self._screen_w - hint_w) // 2, self._screen_h - 40, hint)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        x, y = event.pos().x(), event.pos().y()
        edge = self._edge_at(x, y)
        if edge:
            self._resizing = True
            self._resize_edge = edge
            self._drag_offset = event.pos()
            self._resize_origin = (self._rx, self._ry, self._rw, self._rh)
        elif self._inside_rect(x, y):
            self._dragging = True
            self._drag_offset = QPoint(x - self._rx, y - self._ry)
        event.accept()

    def _update_cursor(self, edge: int, x: int, y: int) -> None:
        if edge in (1, 2):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edge in (4, 8):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif edge in (5, 10):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge in (6, 9):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif self._inside_rect(x, y):
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        x, y = event.pos().x(), event.pos().y()
        if self._resizing:
            self._update_cursor(self._resize_edge, x, y)
            ox, oy, ow, oh = self._resize_origin
            dx = x - self._drag_offset.x()
            dy = y - self._drag_offset.y()
            rx, ry, rw, rh = ox, oy, ow, oh
            if self._resize_edge & 2:  # right
                rw = max(_MIN_W, ow + dx)
            if self._resize_edge & 1:  # left
                d = min(dx, ow - _MIN_W)
                rx = ox + d
                rw = ow - d
            if self._resize_edge & 8:  # bottom
                rh = max(_MIN_H, oh + dy)
            if self._resize_edge & 4:  # top
                d = min(dy, oh - _MIN_H)
                ry = oy + d
                rh = oh - d
            self._rx, self._ry, self._rw, self._rh = rx, ry, rw, rh
            self.update()
        elif self._dragging:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            self._rx = max(0, min(self._screen_w - self._rw, x - self._drag_offset.x()))
            self._ry = max(0, min(self._screen_h - self._rh, y - self._drag_offset.y()))
            self.update()
        else:
            edge = self._edge_at(x, y)
            self._update_cursor(edge, x, y)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging = False
        self._resizing = False
        event.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape or event.key() == Qt.Key.Key_Return:
            self.region_confirmed.emit(self._rw, self._rh)
            self.close()
            event.accept()
        else:
            super().keyPressEvent(event)
