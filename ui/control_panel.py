from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_BTN_MAIN = (
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
    "stop:0 #0288D1,stop:1 #4FC3F7);"
    "color:white;border:none;border-radius:10px;"
    "padding:14px;font-size:15px;font-weight:bold;"
)
_BTN_MAIN_HOVER = (
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
    "stop:0 #039BE5,stop:1 #81D4FA);"
    "color:white;border:none;border-radius:10px;"
    "padding:14px;font-size:15px;font-weight:bold;"
)
_BTN_STOP = (
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
    "stop:0 #C62828,stop:1 #EF5350);"
    "color:white;border:none;border-radius:10px;"
    "padding:14px;font-size:15px;font-weight:bold;"
)
_BTN_STOP_HOVER = (
    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
    "stop:0 #E53935,stop:1 #EF9A9A);"
    "color:white;border:none;border-radius:10px;"
    "padding:14px;font-size:15px;font-weight:bold;"
)
_BTN_SEC = (
    "background:rgba(255,255,255,15);color:#bbb;"
    "border:1px solid rgba(255,255,255,20);"
    "border-radius:8px;padding:10px;font-size:12px;"
)
_BTN_SEC_HOVER = (
    "background:rgba(255,255,255,30);color:#eee;"
    "border:1px solid rgba(79,195,247,60);"
    "border-radius:8px;padding:10px;font-size:12px;"
)
_BTN_WINCTRL = (
    "background:transparent;color:#777;border:none;"
    "font-size:16px;font-weight:bold;padding:4px 8px;"
)
_BTN_WINCTRL_HOVER_CLOSE = (
    "background:#C62828;color:white;border:none;"
    "font-size:16px;font-weight:bold;padding:4px 8px;border-radius:4px;"
)
_BTN_WINCTRL_HOVER_MIN = (
    "background:rgba(255,255,255,20);color:#ccc;border:none;"
    "font-size:16px;font-weight:bold;padding:4px 8px;border-radius:4px;"
)
_PANEL_STYLE = (
    "QWidget#panel {"
    "  background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
    "  stop:0 rgba(15,15,35,245),stop:1 rgba(10,10,25,250));"
    "  border:1px solid rgba(79,195,247,60);border-radius:16px;"
    "}"
    "QWidget#panel > QLabel {"
    "  background:transparent;border:none;"
    "}"
)


class PulseIndicator(QWidget):
    """Animated dot that pulses when zoom is active."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self._active = False
        self._pulse: float = 0.0
        self._color = QColor("#555")

        self._anim = QPropertyAnimation(self, b"pulse")
        self._anim.setDuration(1200)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)

    def _get_pulse(self) -> float:
        return self._pulse

    def _set_pulse(self, v: float) -> None:
        self._pulse = v
        self.update()

    pulse = pyqtProperty(float, _get_pulse, _set_pulse)

    def set_active(self, on: bool) -> None:
        self._active = on
        if on:
            self._color = QColor("#00E676")
            self._anim.start()
        else:
            self._anim.stop()
            self._color = QColor("#555")
            self._pulse = 0.0
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() // 2, self.height() // 2
        if self._active:
            ring_r = int(4 + self._pulse * 4)
            ring_c = QColor(self._color)
            ring_c.setAlpha(int(120 * (1 - self._pulse)))
            painter.setPen(QPen(ring_c, 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(cx - 4, cy - 4, 8, 8)
        painter.end()


def _hover_btn(btn: QPushButton, normal: str, hover: str) -> None:
    btn.setStyleSheet(normal)
    btn.enterEvent = lambda e, b=btn, n=normal, h=hover: b.setStyleSheet(h)
    btn.leaveEvent = lambda e, b=btn, n=normal, h=hover: b.setStyleSheet(n)


class ControlPanel(QWidget):
    """Premium control panel with dark theme and animations."""

    toggle_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Eazy Zoom")
        self.setFixedSize(340, 230)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._dragging = False
        self._drag_offset = QPoint()

        inner = QWidget(self)
        inner.setObjectName("panel")
        inner.setStyleSheet(_PANEL_STYLE)

        layout = QVBoxLayout(inner)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 12, 12, 18)

        # title bar
        title_row = QHBoxLayout()
        title_row.setSpacing(4)

        self._indicator = PulseIndicator()
        title_row.addWidget(self._indicator)
        title_row.addSpacing(6)

        title = QLabel("Eazy Zoom")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#4FC3F7;background:transparent;")
        title_row.addWidget(title)
        title_row.addStretch()

        min_btn = QPushButton("\u2015")
        min_btn.setFixedSize(30, 26)
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _hover_btn(min_btn, _BTN_WINCTRL, _BTN_WINCTRL_HOVER_MIN)
        min_btn.clicked.connect(self.showMinimized)
        title_row.addWidget(min_btn)

        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(30, 26)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _hover_btn(close_btn, _BTN_WINCTRL, _BTN_WINCTRL_HOVER_CLOSE)
        close_btn.clicked.connect(self.close)
        title_row.addWidget(close_btn)

        layout.addLayout(title_row)

        # status
        self._status = QLabel("\ub300\uae30 \uc911")
        self._status.setFont(QFont("Segoe UI", 11))
        self._status.setStyleSheet("color:#666;background:transparent;")
        layout.addWidget(self._status)

        layout.addSpacing(2)

        # main toggle
        self._toggle_btn = QPushButton("\ud655\ub300 \uc2dc\uc791   Ctrl+1")
        self._toggle_btn.setFixedHeight(44)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _hover_btn(self._toggle_btn, _BTN_MAIN, _BTN_MAIN_HOVER)
        self._toggle_btn.clicked.connect(self.toggle_requested.emit)
        layout.addWidget(self._toggle_btn)

        # bottom row
        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        bottom.setContentsMargins(0, 0, 8, 0)

        settings_btn = QPushButton("\uc124\uc815")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _hover_btn(settings_btn, _BTN_SEC, _BTN_SEC_HOVER)
        settings_btn.clicked.connect(self.settings_requested.emit)
        bottom.addWidget(settings_btn)

        quit_btn = QPushButton("\uc885\ub8cc")
        quit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _hover_btn(quit_btn, _BTN_SEC, _BTN_SEC_HOVER)
        quit_btn.clicked.connect(self.quit_requested.emit)
        bottom.addWidget(quit_btn)
        layout.addLayout(bottom)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(8, 8, 8, 8)
        outer_layout.addWidget(inner)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        inner.setGraphicsEffect(shadow)

    def update_status(self, active: bool) -> None:
        self._indicator.set_active(active)
        if active:
            self._status.setText("\ud655\ub300 \ud65c\uc131\ud654")
            self._status.setStyleSheet("color:#00E676;font-weight:bold;background:transparent;")
            self._toggle_btn.setText("\ud655\ub300 \uc911\uc9c0   Ctrl+1")
            _hover_btn(self._toggle_btn, _BTN_STOP, _BTN_STOP_HOVER)
        else:
            self._status.setText("\ub300\uae30 \uc911")
            self._status.setStyleSheet("color:#666;background:transparent;")
            self._toggle_btn.setText("\ud655\ub300 \uc2dc\uc791   Ctrl+1")
            _hover_btn(self._toggle_btn, _BTN_MAIN, _BTN_MAIN_HOVER)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            event.accept()

    def closeEvent(self, event):
        self.quit_requested.emit()
        event.accept()
