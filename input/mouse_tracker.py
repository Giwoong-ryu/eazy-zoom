from PyQt6.QtCore import QObject, QPoint, pyqtSignal
from PyQt6.QtGui import QCursor


class MouseTracker(QObject):
    """Tracks mouse cursor position via Qt polling."""

    position_changed = pyqtSignal(int, int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._last_pos = QPoint(-1, -1)

    def poll(self) -> tuple[int, int]:
        pos = QCursor.pos()
        if pos != self._last_pos:
            self._last_pos = pos
            self.position_changed.emit(pos.x(), pos.y())
        return pos.x(), pos.y()
