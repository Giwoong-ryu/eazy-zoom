import json
import sys
from pathlib import Path
from typing import Any


def _default_config() -> dict[str, Any]:
    return {
        "zoom_level": 2.0,
        "zoom_min": 1.5,
        "zoom_max": 4.0,
        "zoom_step": 0.25,
        "lens_width_ratio": 0.3,
        "lens_height_ratio": 0.3,
        "border_color": "#4FC3F7",
        "border_width": 2,
        "cursor_highlight_color": "#4FC3F7",
        "cursor_highlight_radius": 24,
        "cursor_highlight_opacity": 100,
        "cursor_style": "crosshair",
        "capture_fps": 30,
        "animation_duration_ms": 200,
        "badge_fade_ms": 1500,
        "guide_display_ms": 1500,
        "window_x": -1,
        "window_y": -1,
        "overlay_w": -1,
        "overlay_h": -1,
        "hotkey_toggle": "<ctrl>+1",
        "hotkey_escape": "escape",
        "hotkey_guide": "f1",
    }


def _config_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "config.json"
    return Path(__file__).parent / "config.json"


class Config:
    def __init__(self) -> None:
        self._path = _config_path()
        self._data = _default_config()
        self.load()

    def load(self) -> None:
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def get(self, key: str) -> Any:
        return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    @property
    def data(self) -> dict[str, Any]:
        return self._data.copy()
