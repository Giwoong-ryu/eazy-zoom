import threading
from typing import Callable

from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal


class HotkeySignals(QObject):
    """Bridge between pynput callbacks and Qt signals."""

    toggle_zoom = pyqtSignal()
    escape = pyqtSignal()
    show_guide = pyqtSignal()
    capture_shrink = pyqtSignal()
    capture_expand = pyqtSignal()
    edit_region = pyqtSignal()


class HotkeyManager:
    """Global hotkey listener using pynput."""

    def __init__(self) -> None:
        self.signals = HotkeySignals()
        self._listener: keyboard.GlobalHotKeys | None = None
        self._esc_listener: keyboard.Listener | None = None

    def start(self) -> None:
        hotkeys = {
            "<alt>+z": self._on_toggle,
            "<ctrl>+]": self._on_capture_shrink,
            "<ctrl>+[": self._on_capture_expand,
            "<ctrl>+2": self._on_edit_region,
        }
        self._listener = keyboard.GlobalHotKeys(hotkeys)
        self._listener.daemon = True
        self._listener.start()

        self._esc_listener = keyboard.Listener(on_press=self._on_key_press)
        self._esc_listener.daemon = True
        self._esc_listener.start()

    def _on_toggle(self) -> None:
        self.signals.toggle_zoom.emit()

    def _on_capture_shrink(self) -> None:
        self.signals.capture_shrink.emit()

    def _on_capture_expand(self) -> None:
        self.signals.capture_expand.emit()

    def _on_edit_region(self) -> None:
        self.signals.edit_region.emit()

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        try:
            if key == keyboard.Key.esc:
                self.signals.escape.emit()
            elif key == keyboard.Key.f1:
                self.signals.show_guide.emit()
        except AttributeError:
            pass

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if self._esc_listener is not None:
            self._esc_listener.stop()
            self._esc_listener = None
