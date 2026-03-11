from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QPixmap, QColor, QPainter
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


def _create_icon() -> QIcon:
    px = QPixmap(32, 32)
    px.fill(QColor(0, 0, 0, 0))
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#4FC3F7"))
    painter.setPen(QColor("#0288D1"))
    painter.drawRoundedRect(2, 2, 28, 28, 6, 6)
    painter.setPen(QColor(255, 255, 255))
    from PyQt6.QtGui import QFont
    font = QFont("Segoe UI", 16, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(px.rect(), 0x0084, "Z")  # AlignCenter
    painter.end()
    return QIcon(px)


class TrayIcon(QSystemTrayIcon):
    """System tray icon with context menu."""

    toggle_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(_create_icon(), parent)
        self.setToolTip("Lecture Zoom")

        menu = QMenu()

        self._toggle_action = QAction("Toggle Zoom (Ctrl+1)")
        self._toggle_action.triggered.connect(self.toggle_requested.emit)
        menu.addAction(self._toggle_action)

        menu.addSeparator()

        settings_action = QAction("Settings...")
        settings_action.triggered.connect(self.settings_requested.emit)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("Quit")
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_requested.emit()

    def update_status(self, active: bool) -> None:
        status = "ON" if active else "OFF"
        self._toggle_action.setText(f"Toggle Zoom (Ctrl+1) [{status}]")
        self.setToolTip(f"Lecture Zoom [{status}]")
