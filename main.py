import sys
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["PYTHONIOENCODING"] = "utf-8"

from PyQt6.QtWidgets import QApplication

from config import Config
from core.capture import ScreenCapture
from core.overlay import OverlayWindow
from input.hotkey import HotkeyManager
from ui.guide_overlay import GuideOverlay
from ui.settings_dialog import SettingsDialog
from ui.control_panel import ControlPanel


class LectureZoomApp:
    """Main application controller."""

    def __init__(self) -> None:
        self._app = QApplication(sys.argv)

        self._config = Config()
        self._capture = ScreenCapture()
        self._active = False

        self._build_overlay()

        screen_w, screen_h = self._capture.screen_size()
        self._guide = GuideOverlay(
            display_ms=self._config.get("guide_display_ms"),
        )

        self._hotkey = HotkeyManager()
        self._hotkey.signals.toggle_zoom.connect(self._toggle)
        self._hotkey.signals.escape.connect(self._deactivate)
        self._hotkey.signals.show_guide.connect(self._show_guide)

        self._panel = ControlPanel()
        self._panel.toggle_requested.connect(self._toggle)
        self._panel.settings_requested.connect(self._open_settings)
        self._panel.quit_requested.connect(self._quit)
        self._panel.show()

    def _build_overlay(self) -> None:
        cfg = self._config
        self._overlay = OverlayWindow(
            capture=self._capture,
            zoom_level=cfg.get("zoom_level"),
            zoom_min=cfg.get("zoom_min"),
            zoom_max=cfg.get("zoom_max"),
            zoom_step=cfg.get("zoom_step"),
            lens_w_ratio=cfg.get("lens_width_ratio"),
            lens_h_ratio=cfg.get("lens_height_ratio"),
            border_color=cfg.get("border_color"),
            border_width=cfg.get("border_width"),
            cursor_color=cfg.get("cursor_highlight_color"),
            cursor_radius=cfg.get("cursor_highlight_radius"),
            cursor_opacity=cfg.get("cursor_highlight_opacity"),
            capture_fps=cfg.get("capture_fps"),
            anim_ms=cfg.get("animation_duration_ms"),
        )
        self._overlay.zoom_closed.connect(self._deactivate)
        self._overlay._renderer.set_cursor_shape(cfg.get("cursor_style") or "crosshair")

        # restore position
        wx = cfg.get("window_x")
        wy = cfg.get("window_y")
        if wx is not None and wy is not None and wx >= 0 and wy >= 0:
            self._overlay.move_to(wx, wy)

        # restore size
        ow = cfg.get("overlay_w")
        oh = cfg.get("overlay_h")
        if ow is not None and oh is not None and ow > 0 and oh > 0:
            self._overlay.resize(ow, oh)

    def _toggle(self) -> None:
        if self._active:
            self._deactivate()
        else:
            self._activate()

    def _activate(self) -> None:
        if self._active:
            return
        self._active = True
        self._overlay.start()
        self._panel.update_status(True)

    def _deactivate(self) -> None:
        if not self._active:
            return
        self._active = False
        self._overlay.stop()
        self._panel.update_status(False)
        self._save_state()

    def _save_state(self) -> None:
        pos = self._overlay.pos()
        self._config.set("window_x", pos.x())
        self._config.set("window_y", pos.y())
        self._config.set("overlay_w", self._overlay.width())
        self._config.set("overlay_h", self._overlay.height())
        self._config.save()

    def _show_guide(self) -> None:
        screen_w, screen_h = self._capture.screen_size()
        self._guide.show_guide(screen_w, screen_h)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._config)
        dialog.settings_changed.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self) -> None:
        cfg = self._config
        self._overlay.live_update(
            zoom_level=cfg.get("zoom_level"),
            zoom_min=cfg.get("zoom_min"),
            zoom_max=cfg.get("zoom_max"),
            cursor_color=cfg.get("cursor_highlight_color"),
            cursor_radius=cfg.get("cursor_highlight_radius"),
            cursor_opacity=cfg.get("cursor_highlight_opacity"),
            cursor_style=cfg.get("cursor_style") or "crosshair",
        )

    def _quit(self) -> None:
        if self._active:
            self._save_state()
        self._deactivate()
        self._hotkey.stop()
        self._capture.close()
        self._panel.hide()
        self._app.quit()

    def run(self) -> int:
        self._hotkey.start()
        return self._app.exec()


def main() -> None:
    app = LectureZoomApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
