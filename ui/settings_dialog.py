from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from config import Config
from core.zoom_renderer import CURSOR_STYLES

_STYLE = """
QDialog {
    background: #0f0f23;
    color: #e0e0e0;
}
QLabel {
    color: #ccc;
    font-size: 13px;
    background: transparent;
    border: none;
}
QLabel#header {
    color: #4FC3F7;
    font-size: 15px;
    font-weight: bold;
}
QDoubleSpinBox, QSpinBox {
    background: #1a1a35;
    color: #e0e0e0;
    border: 1px solid rgba(79,195,247,40);
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    min-width: 60px;
}
QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1px solid #4FC3F7;
}
QSlider::groove:horizontal {
    background: #1a1a35;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #4FC3F7;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #81D4FA;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0288D1, stop:1 #4FC3F7);
    border-radius: 3px;
}
QComboBox {
    background: #1a1a35;
    color: #e0e0e0;
    border: 1px solid rgba(79,195,247,40);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
QComboBox:hover {
    border: 1px solid #4FC3F7;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background: #1a1a35;
    color: #e0e0e0;
    selection-background-color: #0288D1;
    border: 1px solid rgba(79,195,247,40);
}
QPushButton#close_btn {
    background: rgba(255,255,255,10);
    color: #aaa;
    border: 1px solid rgba(255,255,255,15);
    border-radius: 8px;
    padding: 10px 28px;
    font-size: 13px;
}
QPushButton#close_btn:hover {
    background: rgba(255,255,255,20);
    color: #ddd;
}
"""


def _make_slider_row(
    label_text: str,
    min_val: float,
    max_val: float,
    step: float,
    current: float,
    decimals: int = 2,
    suffix: str = "",
) -> tuple[QHBoxLayout, QSlider, QDoubleSpinBox]:
    row = QHBoxLayout()
    row.setSpacing(8)

    lbl = QLabel(label_text)
    lbl.setFixedWidth(100)
    row.addWidget(lbl)

    slider = QSlider(Qt.Orientation.Horizontal)
    mult = int(1 / step) if step < 1 else 1
    slider.setMinimum(int(min_val * mult))
    slider.setMaximum(int(max_val * mult))
    slider.setValue(int(current * mult))
    slider.setSingleStep(1)
    slider.setProperty("_mult", mult)
    row.addWidget(slider, 1)

    spin = QDoubleSpinBox()
    spin.setRange(min_val, max_val)
    spin.setSingleStep(step)
    spin.setDecimals(decimals)
    spin.setValue(current)
    if suffix:
        spin.setSuffix(suffix)
    row.addWidget(spin)

    def slider_to_spin(v: int) -> None:
        spin.setValue(v / mult)

    def spin_to_slider(v: float) -> None:
        slider.setValue(int(v * mult))

    slider.valueChanged.connect(slider_to_spin)
    spin.valueChanged.connect(spin_to_slider)

    return row, slider, spin


def _make_int_slider_row(
    label_text: str,
    min_val: int,
    max_val: int,
    current: int,
    suffix: str = "",
) -> tuple[QHBoxLayout, QSlider, QSpinBox]:
    row = QHBoxLayout()
    row.setSpacing(8)

    lbl = QLabel(label_text)
    lbl.setFixedWidth(100)
    row.addWidget(lbl)

    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setMinimum(min_val)
    slider.setMaximum(max_val)
    slider.setValue(current)
    row.addWidget(slider, 1)

    spin = QSpinBox()
    spin.setRange(min_val, max_val)
    spin.setValue(current)
    if suffix:
        spin.setSuffix(suffix)
    row.addWidget(spin)

    slider.valueChanged.connect(spin.setValue)
    spin.valueChanged.connect(slider.setValue)

    return row, slider, spin


class SettingsDialog(QDialog):
    """Eazy Zoom 설정 - 슬라이더 + 실시간 적용."""

    settings_changed = pyqtSignal()

    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("Eazy Zoom 설정")
        self.setFixedSize(440, 480)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet(_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 18, 24, 18)

        header = QLabel("Eazy Zoom 설정")
        header.setObjectName("header")
        layout.addWidget(header)

        # zoom level
        row, _, self._zoom_spin = _make_slider_row(
            "기본 배율", 1.5, 4.0, 0.25, config.get("zoom_level"), decimals=1, suffix="x"
        )
        self._zoom_spin.valueChanged.connect(lambda v: self._live("zoom_level", v))
        layout.addLayout(row)

        # zoom min
        row, _, self._zoom_min_spin = _make_slider_row(
            "최소 배율", 1.0, 3.0, 0.25, config.get("zoom_min"), decimals=1, suffix="x"
        )
        self._zoom_min_spin.valueChanged.connect(lambda v: self._live("zoom_min", v))
        layout.addLayout(row)

        # zoom max
        row, _, self._zoom_max_spin = _make_slider_row(
            "최대 배율", 2.0, 6.0, 0.25, config.get("zoom_max"), decimals=1, suffix="x"
        )
        self._zoom_max_spin.valueChanged.connect(lambda v: self._live("zoom_max", v))
        layout.addLayout(row)

        # fps
        row, _, self._fps_spin = _make_int_slider_row(
            "캡처 FPS", 15, 60, config.get("capture_fps"), suffix=" fps"
        )
        self._fps_spin.valueChanged.connect(lambda v: self._live("capture_fps", v))
        layout.addLayout(row)

        # cursor radius
        row, _, self._radius_spin = _make_int_slider_row(
            "커서 크기", 8, 48, config.get("cursor_highlight_radius"), suffix=" px"
        )
        self._radius_spin.valueChanged.connect(
            lambda v: self._live("cursor_highlight_radius", v)
        )
        layout.addLayout(row)

        # cursor opacity
        row, _, self._opacity_spin = _make_int_slider_row(
            "커서 투명도", 20, 255, config.get("cursor_highlight_opacity")
        )
        self._opacity_spin.valueChanged.connect(
            lambda v: self._live("cursor_highlight_opacity", v)
        )
        layout.addLayout(row)

        # lens width ratio
        row, _, self._lens_w_spin = _make_slider_row(
            "렌즈 너비", 0.2, 0.8, 0.05, config.get("lens_width_ratio"), decimals=2
        )
        self._lens_w_spin.valueChanged.connect(
            lambda v: self._live("lens_width_ratio", v)
        )
        layout.addLayout(row)

        # lens height ratio
        row, _, self._lens_h_spin = _make_slider_row(
            "렌즈 높이", 0.2, 0.8, 0.05, config.get("lens_height_ratio"), decimals=2
        )
        self._lens_h_spin.valueChanged.connect(
            lambda v: self._live("lens_height_ratio", v)
        )
        layout.addLayout(row)

        # cursor style combo
        cursor_row = QHBoxLayout()
        cursor_row.setSpacing(8)
        cursor_lbl = QLabel("커서 모양")
        cursor_lbl.setFixedWidth(100)
        cursor_row.addWidget(cursor_lbl)

        self._cursor_combo = QComboBox()
        current_style = config.get("cursor_style") or "crosshair"
        for key, display in CURSOR_STYLES.items():
            self._cursor_combo.addItem(display, key)
        idx = list(CURSOR_STYLES.keys()).index(current_style) if current_style in CURSOR_STYLES else 0
        self._cursor_combo.setCurrentIndex(idx)
        self._cursor_combo.currentIndexChanged.connect(self._on_cursor_style)
        cursor_row.addWidget(self._cursor_combo, 1)
        layout.addLayout(cursor_row)

        layout.addStretch()

        # close button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("닫기")
        close_btn.setObjectName("close_btn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _live(self, key: str, value: object) -> None:
        self._config.set(key, value)
        self._config.save()
        self.settings_changed.emit()

    def _on_cursor_style(self, index: int) -> None:
        key = self._cursor_combo.itemData(index)
        self._config.set("cursor_style", key)
        self._config.save()
        self.settings_changed.emit()
