from PyQt6.QtCore import QPoint, QSize, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QImage, QMouseEvent, QWheelEvent
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

from core.capture import ScreenCapture
from core.region_highlight import RegionHighlight
from core.zoom_renderer import ZoomRenderer

_EDGE_MARGIN = 8
_MIN_SIZE = 200


class OverlayWindow(QWidget):
    """Frameless overlay that shows zoomed content."""

    zoom_changed = pyqtSignal(float)
    zoom_closed = pyqtSignal()

    def __init__(
        self,
        capture: ScreenCapture,
        zoom_level: float = 2.0,
        zoom_min: float = 1.5,
        zoom_max: float = 4.0,
        zoom_step: float = 0.25,
        lens_w_ratio: float = 0.5,
        lens_h_ratio: float = 0.5,
        border_color: str = "#4FC3F7",
        border_width: int = 2,
        cursor_color: str = "#4FC3F7",
        cursor_radius: int = 24,
        cursor_opacity: int = 100,
        capture_fps: int = 30,
        anim_ms: int = 200,
    ) -> None:
        super().__init__()
        self._capture = capture
        self._zoom = zoom_level
        self._zoom_min = zoom_min
        self._zoom_max = zoom_max
        self._zoom_step = zoom_step
        self._dragging = False
        self._resizing = False
        self._resize_edge = 0  # bitmask: 1=left,2=right,4=top,8=bottom
        self._drag_offset = QPoint()
        self._frozen = False
        self._frozen_cap_x = 0
        self._frozen_cap_y = 0
        self._frozen_cap_w = 0
        self._frozen_cap_h = 0

        screen_w, screen_h = capture.screen_size()
        self._lens_w = int(screen_w * lens_w_ratio)
        self._lens_h = int(screen_h * lens_h_ratio)

        # Base capture region size (independent of viewer window size)
        # This defines the "real screen area" that gets captured at zoom=1x
        self._base_cap_w = self._lens_w
        self._base_cap_h = self._lens_h

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(_MIN_SIZE, _MIN_SIZE)
        self.resize(self._lens_w, self._lens_h)

        self._renderer = ZoomRenderer(self)
        self._renderer.set_border_style(border_color, border_width)
        self._renderer.set_cursor_style(cursor_color, cursor_radius, cursor_opacity)
        self._renderer.set_zoom_level(zoom_level, animate=False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._renderer)

        self._highlight = RegionHighlight(border_color)

        self._position_default(screen_w)

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        interval = max(16, 1000 // capture_fps)
        self._timer.setInterval(interval)
        self._timer.timeout.connect(self._tick)

    def _position_default(self, screen_w: int) -> None:
        x = screen_w - self._lens_w - 20
        y = 20
        self.move(x, y)

    def move_to(self, x: int, y: int) -> None:
        self.move(x, y)

    def start(self) -> None:
        self.show()
        self._highlight.show()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()
        self._highlight.hide()

    def live_update(
        self,
        zoom_level: float,
        zoom_min: float,
        zoom_max: float,
        cursor_color: str,
        cursor_radius: int,
        cursor_opacity: int,
        cursor_style: str,
    ) -> None:
        """Update properties without recreating the overlay."""
        self._zoom = zoom_level
        self._zoom_min = zoom_min
        self._zoom_max = zoom_max
        self._renderer.set_cursor_style(cursor_color, cursor_radius, cursor_opacity)
        self._renderer.set_cursor_shape(cursor_style)
        self._renderer.set_zoom_level(zoom_level, animate=False)

    def adjust_capture_region(self, delta: int) -> None:
        """Adjust base capture region size. Negative = smaller region (more zoom)."""
        screen_w, screen_h = self._capture.screen_size()
        self._base_cap_w = max(200, min(screen_w, self._base_cap_w + delta))
        self._base_cap_h = max(150, min(screen_h, self._base_cap_h + delta))

    def set_zoom(self, level: float, animate: bool = True) -> None:
        level = max(self._zoom_min, min(self._zoom_max, level))
        self._zoom = level
        self._renderer.set_zoom_level(level, animate=animate)
        self.zoom_changed.emit(level)

    def current_zoom(self) -> float:
        return self._zoom

    def _edge_at(self, pos: QPoint) -> int:
        """Return bitmask for which edges the point is near."""
        edge = 0
        if pos.x() < _EDGE_MARGIN:
            edge |= 1
        if pos.x() > self.width() - _EDGE_MARGIN:
            edge |= 2
        if pos.y() < _EDGE_MARGIN:
            edge |= 4
        if pos.y() > self.height() - _EDGE_MARGIN:
            edge |= 8
        return edge

    def _tick(self) -> None:
        pos = QCursor.pos()
        mx, my = pos.x(), pos.y()

        modifiers = QApplication.instance().queryKeyboardModifiers()
        ctrl_held = bool(modifiers & Qt.KeyboardModifier.ControlModifier)

        w = self.width()
        h = self.height()
        # Capture region is based on fixed base size, NOT viewer window size
        cap_w = int(self._base_cap_w / self._zoom)
        cap_h = int(self._base_cap_h / self._zoom)

        if ctrl_held and not self._frozen:
            # freeze: lock capture region, allow cursor to move inside it
            self._frozen = True
            self._frozen_cap_w = cap_w
            self._frozen_cap_h = cap_h
            self._frozen_cap_x = mx - cap_w // 2
            self._frozen_cap_y = my - cap_h // 2
            screen_w, screen_h = self._capture.screen_size()
            self._frozen_cap_x = max(0, min(self._frozen_cap_x, screen_w - cap_w))
            self._frozen_cap_y = max(0, min(self._frozen_cap_y, screen_h - cap_h))
        elif not ctrl_held and self._frozen:
            self._frozen = False

        if self._frozen:
            cap_x = self._frozen_cap_x
            cap_y = self._frozen_cap_y
            cap_w = self._frozen_cap_w
            cap_h = self._frozen_cap_h
            # calculate cursor position relative to frozen region
            rel_x = (mx - cap_x) / cap_w  # 0.0 ~ 1.0
            rel_y = (my - cap_y) / cap_h
            # clamp to region bounds
            rel_x = max(0.0, min(1.0, rel_x))
            rel_y = max(0.0, min(1.0, rel_y))
            cursor_px = int(rel_x * w)
            cursor_py = int(rel_y * h)
            self._renderer.set_cursor_pixel(cursor_px, cursor_py)
        else:
            cap_x = mx - cap_w // 2
            cap_y = my - cap_h // 2
            screen_w, screen_h = self._capture.screen_size()
            cap_x = max(0, min(cap_x, screen_w - cap_w))
            cap_y = max(0, min(cap_y, screen_h - cap_h))
            self._renderer.set_cursor_pos(mx, my)

        self._highlight.update_region(cap_x, cap_y, cap_w, cap_h)

        # Skip if cursor is inside overlay (avoid self-capture)
        overlay_rect = self.geometry()
        if overlay_rect.contains(mx, my):
            return

        image = self._capture.capture_region(cap_x, cap_y, cap_w, cap_h)
        if image is not None:
            self._renderer.set_image(image)

    def wheelEvent(self, event: QWheelEvent) -> None:
        modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            # Shift+scroll: adjust capture region size
            # Windows converts Shift+scroll to horizontal, so check x() too
            delta = event.angleDelta().x() or event.angleDelta().y()
            step = 50
            if delta > 0:
                self._base_cap_w = max(200, self._base_cap_w - step)
                self._base_cap_h = max(150, self._base_cap_h - step)
            elif delta < 0:
                screen_w, screen_h = self._capture.screen_size()
                self._base_cap_w = min(screen_w, self._base_cap_w + step)
                self._base_cap_h = min(screen_h, self._base_cap_h + step)
        else:
            # Normal scroll: adjust zoom level
            delta = event.angleDelta().y()
            if delta > 0:
                self.set_zoom(self._zoom + self._zoom_step)
            elif delta < 0:
                self.set_zoom(self._zoom - self._zoom_step)
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._edge_at(event.pos())
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._drag_offset = event.globalPosition().toPoint()
                self._resize_origin = self.geometry()
            else:
                self._dragging = True
                self._drag_offset = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def _cursor_for_edge(self, edge: int) -> Qt.CursorShape:
        if edge in (1, 2):
            return Qt.CursorShape.SizeHorCursor
        if edge in (4, 8):
            return Qt.CursorShape.SizeVerCursor
        if edge in (5, 10):
            return Qt.CursorShape.SizeFDiagCursor
        if edge in (6, 9):
            return Qt.CursorShape.SizeBDiagCursor
        return Qt.CursorShape.ArrowCursor

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._resizing:
            self.setCursor(self._cursor_for_edge(self._resize_edge))
            delta = event.globalPosition().toPoint() - self._drag_offset
            geo = self._resize_origin
            x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
            if self._resize_edge & 2:  # right
                w = max(_MIN_SIZE, geo.width() + delta.x())
            if self._resize_edge & 1:  # left
                dx = min(delta.x(), geo.width() - _MIN_SIZE)
                x = geo.x() + dx
                w = geo.width() - dx
            if self._resize_edge & 8:  # bottom
                h = max(_MIN_SIZE, geo.height() + delta.y())
            if self._resize_edge & 4:  # top
                dy = min(delta.y(), geo.height() - _MIN_SIZE)
                y = geo.y() + dy
                h = geo.height() - dy
            self.setGeometry(x, y, w, h)
            event.accept()
        elif self._dragging:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
        else:
            edge = self._edge_at(event.pos())
            self.setCursor(self._cursor_for_edge(edge))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._resizing = False
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.zoom_closed.emit()
        event.accept()
