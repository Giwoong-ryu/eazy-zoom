from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QFont, QPainter, QPaintEvent
from PyQt6.QtWidgets import QWidget


_GUIDE_TEXT = [
    ("Ctrl+1", "확대 켜기/끄기"),
    ("마우스 휠", "배율 조절"),
    ("ESC", "확대 종료"),
    ("F1", "이 안내 보기"),
    ("드래그", "확대 창 이동"),
    ("가장자리 드래그", "확대 창 크기 조절"),
    ("더블클릭", "확대 종료"),
]


class GuideOverlay(QWidget):
    """반투명 단축키 안내 (자동 숨김)."""

    def __init__(self, display_ms: int = 1500, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._display_ms = display_ms
        self._opacity: float = 0.0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(340, 270)

        self._fade_in = QPropertyAnimation(self, b"windowOpacity_custom")
        self._fade_in.setDuration(150)
        self._fade_in.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._fade_out = QPropertyAnimation(self, b"windowOpacity_custom")
        self._fade_out.setDuration(300)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade_out)

    def _get_opacity(self) -> float:
        return self._opacity

    def _set_opacity(self, value: float) -> None:
        self._opacity = value
        self.update()
        if value <= 0.01 and not self._fade_in.state():
            self.hide()

    windowOpacity_custom = pyqtProperty(float, _get_opacity, _set_opacity)

    def show_guide(self, screen_w: int, screen_h: int) -> None:
        x = (screen_w - self.width()) // 2
        y = (screen_h - self.height()) // 2
        self.move(x, y)
        self.show()
        self.raise_()

        self._fade_out.stop()
        self._fade_in.stop()
        self._fade_in.setStartValue(self._opacity)
        self._fade_in.setEndValue(1.0)
        self._fade_in.start()

        self._hide_timer.start(self._display_ms)

    def _start_fade_out(self) -> None:
        self._fade_in.stop()
        self._fade_out.setStartValue(self._opacity)
        self._fade_out.setEndValue(0.0)
        self._fade_out.start()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QColor(15, 15, 35, int(230 * self._opacity))
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

        if self._opacity < 0.01:
            painter.end()
            return

        # border
        from PyQt6.QtGui import QPen
        border_c = QColor(79, 195, 247, int(60 * self._opacity))
        painter.setPen(QPen(border_c, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 12, 12)

        title_font = QFont("Segoe UI", 13, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(79, 195, 247, int(255 * self._opacity)))
        painter.drawText(24, 34, "단축키 안내")

        row_font = QFont("Segoe UI", 11)
        painter.setFont(row_font)

        y = 64
        for key, desc in _GUIDE_TEXT:
            painter.setPen(QColor(255, 255, 255, int(230 * self._opacity)))
            painter.drawText(28, y, key)
            painter.setPen(QColor(180, 180, 180, int(200 * self._opacity)))
            painter.drawText(175, y, desc)
            y += 28

        painter.end()
