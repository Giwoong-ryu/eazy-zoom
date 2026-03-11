import mss
import mss.tools
from PyQt6.QtGui import QImage


class ScreenCapture:
    """mss-based screen capture engine."""

    def __init__(self) -> None:
        self._sct = mss.mss()

    def capture_region(self, x: int, y: int, width: int, height: int) -> QImage | None:
        monitor = {"top": y, "left": x, "width": width, "height": height}
        try:
            shot = self._sct.grab(monitor)
        except Exception:
            return None

        img = QImage(
            shot.raw,
            shot.width,
            shot.height,
            shot.width * 4,
            QImage.Format.Format_RGBX8888,
        )
        return img.copy()

    def screen_size(self) -> tuple[int, int]:
        mon = self._sct.monitors[1]
        return mon["width"], mon["height"]

    def close(self) -> None:
        self._sct.close()
