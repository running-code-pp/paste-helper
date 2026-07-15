"""设置标签页 — 透明度、快捷键、退出"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QRadioButton
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeyEvent


class HotkeyCaptureButton(QPushButton):
    """快捷键捕获按钮 — 点击后进入捕获模式，按下组合键保存"""

    keys_changed = Signal(str)  # 格式: "Ctrl,Up"

    MOD_MAP = {
        Qt.KeyboardModifier.ControlModifier: "Ctrl",
        Qt.KeyboardModifier.AltModifier: "Alt",
        Qt.KeyboardModifier.ShiftModifier: "Shift",
        Qt.KeyboardModifier.MetaModifier: "Win",
    }

    KEY_MAP = {
        Qt.Key.Key_A: "A", Qt.Key.Key_B: "B", Qt.Key.Key_C: "C",
        Qt.Key.Key_D: "D", Qt.Key.Key_E: "E", Qt.Key.Key_F: "F",
        Qt.Key.Key_G: "G", Qt.Key.Key_H: "H", Qt.Key.Key_I: "I",
        Qt.Key.Key_J: "J", Qt.Key.Key_K: "K", Qt.Key.Key_L: "L",
        Qt.Key.Key_M: "M", Qt.Key.Key_N: "N", Qt.Key.Key_O: "O",
        Qt.Key.Key_P: "P", Qt.Key.Key_Q: "Q", Qt.Key.Key_R: "R",
        Qt.Key.Key_S: "S", Qt.Key.Key_T: "T", Qt.Key.Key_U: "U",
        Qt.Key.Key_V: "V", Qt.Key.Key_W: "W", Qt.Key.Key_X: "X",
        Qt.Key.Key_Y: "Y", Qt.Key.Key_Z: "Z",
        Qt.Key.Key_0: "0", Qt.Key.Key_1: "1", Qt.Key.Key_2: "2",
        Qt.Key.Key_3: "3", Qt.Key.Key_4: "4", Qt.Key.Key_5: "5",
        Qt.Key.Key_6: "6", Qt.Key.Key_7: "7", Qt.Key.Key_8: "8",
        Qt.Key.Key_9: "9",
        Qt.Key.Key_F1: "F1", Qt.Key.Key_F2: "F2", Qt.Key.Key_F3: "F3",
        Qt.Key.Key_F4: "F4", Qt.Key.Key_F5: "F5", Qt.Key.Key_F6: "F6",
        Qt.Key.Key_F7: "F7", Qt.Key.Key_F8: "F8", Qt.Key.Key_F9: "F9",
        Qt.Key.Key_F10: "F10", Qt.Key.Key_F11: "F11", Qt.Key.Key_F12: "F12",
        Qt.Key.Key_Up: "Up", Qt.Key.Key_Down: "Down",
        Qt.Key.Key_Left: "Left", Qt.Key.Key_Right: "Right",
        Qt.Key.Key_Space: "Space", Qt.Key.Key_Tab: "Tab",
        Qt.Key.Key_Return: "Enter", Qt.Key.Key_Escape: "Escape",
        Qt.Key.Key_Backspace: "Backspace", Qt.Key.Key_Delete: "Delete",
        Qt.Key.Key_Insert: "Insert", Qt.Key.Key_Home: "Home",
        Qt.Key.Key_End: "End", Qt.Key.Key_PageUp: "PageUp",
        Qt.Key.Key_PageDown: "PageDown",
    }

    def __init__(self, keys: str, parent=None):
        super().__init__(parent)
        self.setObjectName("hotkeyBtn")
        self._keys = keys
        self._capturing = False
        self._update_text()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(120)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _update_text(self):
        text = self._keys.replace(",", " + ")
        if self._capturing:
            self.setText("按下组合键…")
            self.setProperty("capturing", "true")
        else:
            self.setText(text)
            self.setProperty("capturing", "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if not self._capturing:
            self._capturing = True
            self._update_text()
            self.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        if not self._capturing:
            super().keyPressEvent(event)
            return

        key = event.key()
        mods = event.modifiers()

        # 忽略单独的修饰键
        if key in (
            Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Shift,
            Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R
        ):
            return

        if key == Qt.Key.Key_Escape:
            self._capturing = False
            self._update_text()
            return

        # 至少需要一个修饰键
        if mods == Qt.KeyboardModifier.NoModifier:
            return

        # 构建快捷键字符串
        parts = []
        if mods & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if mods & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        if mods & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
        if mods & Qt.KeyboardModifier.MetaModifier:
            parts.append("Win")

        key_name = self.KEY_MAP.get(key)
        if key_name is None:
            # 尝试用枚举名匹配
            for k, v in self.KEY_MAP.items():
                if k.name == key.name:
                    key_name = v
                    break
        if key_name is None:
            return

        parts.append(key_name)
        self._keys = ",".join(parts)
        self._capturing = False
        self._update_text()
        self.keys_changed.emit(self._keys)

    def focusOutEvent(self, event):
        if self._capturing:
            self._capturing = False
            self._update_text()

    def set_keys(self, keys: str):
        self._keys = keys
        self._capturing = False
        self._update_text()


class SettingsTab(QWidget):
    """设置标签页"""

    opacity_changed = Signal(int)       # 10-100
    prev_keys_changed = Signal(str)     # "Ctrl,Up"
    next_keys_changed = Signal(str)     # "Ctrl,Down"
    theme_changed = Signal(str)         # "dark" | "light"
    exit_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_opacity)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # ===== 透明度 =====
        opacity_label = QLabel("窗口透明度")
        opacity_label.setStyleSheet("color: #8888a0; font-size: 12px; border: none;")
        layout.addWidget(opacity_label)

        opacity_row = QHBoxLayout()
        opacity_row.setSpacing(10)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(85)
        self.opacity_slider.valueChanged.connect(self._on_slider_changed)
        opacity_row.addWidget(self.opacity_slider, 1)

        self.opacity_value = QLabel("85%")
        self.opacity_value.setMinimumWidth(40)
        self.opacity_value.setStyleSheet("color: #d0d0e0; border: none;")
        opacity_row.addWidget(self.opacity_value)

        layout.addLayout(opacity_row)

        # ===== 分隔 =====
        sep1 = QLabel()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background-color: #3a3a50; border: none;")
        layout.addWidget(sep1)

        # ===== 上一条快捷键 =====
        prev_label = QLabel("上一条快捷键")
        prev_label.setStyleSheet("color: #8888a0; font-size: 12px; border: none;")
        layout.addWidget(prev_label)

        self.prev_hotkey_btn = HotkeyCaptureButton("Ctrl,Up")
        self.prev_hotkey_btn.keys_changed.connect(self.prev_keys_changed.emit)
        layout.addWidget(self.prev_hotkey_btn)

        # ===== 下一条快捷键 =====
        next_label = QLabel("下一条快捷键")
        next_label.setStyleSheet("color: #8888a0; font-size: 12px; border: none;")
        layout.addWidget(next_label)

        self.next_hotkey_btn = HotkeyCaptureButton("Ctrl,Down")
        self.next_hotkey_btn.keys_changed.connect(self.next_keys_changed.emit)
        layout.addWidget(self.next_hotkey_btn)

        # ===== 分隔 =====
        sep2 = QLabel()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: #3a3a50; border: none;")
        layout.addWidget(sep2)

        # ===== 主题 =====
        theme_label = QLabel("主题")
        theme_label.setStyleSheet("color: #8888a0; font-size: 12px; border: none;")
        layout.addWidget(theme_label)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(16)

        self.dark_radio = QRadioButton("深色")
        self.dark_radio.setChecked(True)
        self.dark_radio.toggled.connect(
            lambda checked: checked and self.theme_changed.emit("dark")
        )
        theme_row.addWidget(self.dark_radio)

        self.light_radio = QRadioButton("浅色")
        self.light_radio.toggled.connect(
            lambda checked: checked and self.theme_changed.emit("light")
        )
        theme_row.addWidget(self.light_radio)

        theme_row.addStretch()
        layout.addLayout(theme_row)

        layout.addStretch()

        # ===== 退出按钮 =====
        exit_btn = QPushButton("退出应用")
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #c0392b; color: #fff; border: none;
                border-radius: 4px; padding: 8px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #e74c3c; }
        """)
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.clicked.connect(self.exit_clicked.emit)
        layout.addWidget(exit_btn)

    def set_opacity(self, value: int):
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(value)
        self.opacity_value.setText(f"{value}%")
        self.opacity_slider.blockSignals(False)

    def set_hotkeys(self, prev_keys: str, next_keys: str):
        self.prev_hotkey_btn.set_keys(prev_keys)
        self.next_hotkey_btn.set_keys(next_keys)

    def set_theme(self, theme: str):
        if theme == "light":
            self.light_radio.setChecked(True)
        else:
            self.dark_radio.setChecked(True)

    # ===== 透明度 150ms 防抖 =====
    _pending_opacity = 85

    def _on_slider_changed(self, value: int):
        self.opacity_value.setText(f"{value}%")
        self._pending_opacity = value
        self._debounce_timer.start(150)

    def _emit_opacity(self):
        self.opacity_changed.emit(self._pending_opacity)
