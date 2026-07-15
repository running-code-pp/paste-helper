"""设置标签页 — 透明度、快捷键、分组颜色、导入导出、退出"""

from typing import Dict, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QRadioButton, QCheckBox,
    QScrollArea, QFrame, QColorDialog, QDialog,
    QDialogButtonBox, QApplication,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeyEvent, QColor


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


class GroupSelectDialog(QDialog):
    """导入/导出分组选择对话框"""

    # 对话框专用样式
    _DLG_QSS = {
        "dark": """
            GroupSelectDialog {
                background-color: #1e1e2e;
            }
            QLabel {
                color: #d0d0e0;
                background: transparent;
                border: none;
                font-size: 12px;
            }
            QCheckBox {
                color: #c0c0d0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #4a4a60;
                border-radius: 3px;
                background-color: #1a1a2e;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #4a7cf7;
                border-radius: 3px;
                background-color: #4a7cf7;
            }
            QPushButton {
                border: 1px solid #3a3a50;
                border-radius: 3px;
                padding: 4px 12px;
                color: #c0c0d0;
                background-color: #2a2a3c;
            }
            QPushButton:hover {
                background-color: #3a3a50;
                border-color: #4a7cf7;
            }
            QDialogButtonBox QPushButton {
                min-width: 70px;
            }
        """,
        "light": """
            GroupSelectDialog {
                background-color: #f0f0f5;
            }
            QLabel {
                color: #333340;
                background: transparent;
                border: none;
                font-size: 12px;
            }
            QCheckBox {
                color: #333340;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #c0c0c8;
                border-radius: 3px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #4a7cf7;
                border-radius: 3px;
                background-color: #4a7cf7;
            }
            QPushButton {
                border: 1px solid #d0d0d8;
                border-radius: 3px;
                padding: 4px 12px;
                color: #333340;
                background-color: #ffffff;
            }
            QPushButton:hover {
                background-color: #e8e8f0;
                border-color: #4a7cf7;
            }
            QDialogButtonBox QPushButton {
                min-width: 70px;
            }
        """,
    }

    def __init__(self, groups: List[str], title: str, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.setObjectName("GroupSelectDialog")
        self.setWindowTitle(title)
        self.setMinimumWidth(280)
        self.setModal(True)

        # 应用主题样式
        self.setStyleSheet(self._DLG_QSS.get(theme, self._DLG_QSS["dark"]))

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        hint = QLabel("选择要操作的分组（不选则操作全部）：")
        layout.addWidget(hint)

        self._checks: Dict[str, QCheckBox] = {}
        for g in groups:
            cb = QCheckBox(g)
            cb.setChecked(True)
            layout.addWidget(cb)
            self._checks[g] = cb

        # 快捷按钮行
        btn_row = QHBoxLayout()
        all_btn = QPushButton("全选")
        all_btn.clicked.connect(lambda: self._set_all(True))
        none_btn = QPushButton("全不选")
        none_btn.clicked.connect(lambda: self._set_all(False))
        btn_row.addWidget(all_btn)
        btn_row.addWidget(none_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _set_all(self, checked: bool):
        for cb in self._checks.values():
            cb.setChecked(checked)

    def selected_groups(self) -> List[str]:
        return [g for g, cb in self._checks.items() if cb.isChecked()]


class SettingsTab(QWidget):
    """设置标签页"""

    opacity_changed = Signal(int)       # 10-100
    prev_keys_changed = Signal(str)     # "Ctrl,Up"
    next_keys_changed = Signal(str)     # "Ctrl,Down"
    theme_changed = Signal(str)         # "dark" | "light"
    auto_collapse_changed = Signal(bool)  # 点击复制后自动收起
    group_colors_changed = Signal(dict)   # {group_name: "#rrggbb"}
    import_clicked = Signal()            # 触发导入
    export_clicked = Signal()            # 触发导出
    exit_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_opacity)

        self._group_colors: Dict[str, str] = {}

        # 外层滚动
        outer_scroll = QScrollArea()
        outer_scroll.setObjectName("settingsScrollArea")
        outer_scroll.setWidgetResizable(True)
        outer_scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        inner.setObjectName("settingsInner")
        layout = QVBoxLayout(inner)
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
        layout.addWidget(self._make_sep())

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
        layout.addWidget(self._make_sep())

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

        # ===== 分隔 =====
        layout.addWidget(self._make_sep())

        # ===== 点击后自动收起 =====
        self.auto_collapse_cb = QCheckBox("点击复制后自动收起面板")
        self.auto_collapse_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auto_collapse_cb.toggled.connect(self.auto_collapse_changed.emit)
        layout.addWidget(self.auto_collapse_cb)

        # ===== 分隔 =====
        layout.addWidget(self._make_sep())

        # ===== 分组颜色（可折叠） =====
        self._color_section_header = QPushButton("▼ 分组颜色")
        self._color_section_header.setObjectName("sectionHeader")
        self._color_section_header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color_section_header.clicked.connect(self._toggle_color_section)
        layout.addWidget(self._color_section_header)

        # 分组颜色容器（包裹滚动区域 + 统一背景色）
        self._color_section_wrap = QWidget()
        self._color_section_wrap.setObjectName("colorSectionWrap")
        wrap_layout = QVBoxLayout(self._color_section_wrap)
        wrap_layout.setContentsMargins(4, 4, 4, 8)
        wrap_layout.setSpacing(0)

        self._color_scroll = QScrollArea()
        self._color_scroll.setObjectName("colorScroll")
        self._color_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._color_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._color_scroll.setMaximumHeight(150)
        self._color_scroll.setWidgetResizable(True)

        self._color_container = QWidget()
        self._color_container.setObjectName("colorContainer")
        self._color_layout = QVBoxLayout(self._color_container)
        self._color_layout.setContentsMargins(0, 0, 0, 0)
        self._color_layout.setSpacing(4)
        self._color_layout.addStretch()
        self._color_scroll.setWidget(self._color_container)
        wrap_layout.addWidget(self._color_scroll)

        self._no_group_hint = QLabel("暂无分组，添加条目后自动创建")
        self._no_group_hint.setStyleSheet("color: #666680; font-size: 11px; border: none;")
        self._no_group_hint.setVisible(True)
        self._color_layout.insertWidget(0, self._no_group_hint)

        layout.addWidget(self._color_section_wrap)

        self._color_collapsed = False

        # ===== 分隔 =====
        layout.addWidget(self._make_sep())

        # ===== 导入导出 =====
        io_label = QLabel("数据管理")
        io_label.setStyleSheet("color: #8888a0; font-size: 12px; border: none;")
        layout.addWidget(io_label)

        io_row = QHBoxLayout()
        io_row.setSpacing(10)

        self.import_btn = QPushButton("📥 导入CSV")
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.setObjectName("ioBtn")
        self.import_btn.clicked.connect(self.import_clicked.emit)
        io_row.addWidget(self.import_btn)

        self.export_btn = QPushButton("📤 导出CSV")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setObjectName("ioBtn")
        self.export_btn.clicked.connect(self.export_clicked.emit)
        io_row.addWidget(self.export_btn)

        io_row.addStretch()
        layout.addLayout(io_row)

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

        outer_scroll.setWidget(inner)

        # 顶层布局
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(outer_scroll)

    def _make_sep(self) -> QLabel:
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #3a3a50; border: none;")
        return sep

    # ===== 分组颜色折叠 =====

    def _toggle_color_section(self):
        """折叠/展开分组颜色区域"""
        self._color_collapsed = not self._color_collapsed
        self._color_section_wrap.setVisible(not self._color_collapsed)
        arrow = "▶" if self._color_collapsed else "▼"
        self._color_section_header.setText(f"{arrow} 分组颜色")

    # ===== 公开设置方法 =====

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

    def set_auto_collapse(self, enabled: bool):
        self.auto_collapse_cb.blockSignals(True)
        self.auto_collapse_cb.setChecked(enabled)
        self.auto_collapse_cb.blockSignals(False)

    def set_groups(self, groups: List[str]):
        """更新分组列表（排除"全部"）"""
        # 清除旧的颜色行（保留 stretch 和 hint）
        for i in reversed(range(self._color_layout.count())):
            w = self._color_layout.itemAt(i).widget()
            if w and w is not self._no_group_hint:
                w.deleteLater()

        filtered = [g for g in groups if g != "全部"]
        if not filtered:
            self._no_group_hint.setVisible(True)
            return

        self._no_group_hint.setVisible(False)
        for grp_name in filtered:
            row = self._make_color_row(grp_name)
            self._color_layout.insertWidget(self._color_layout.count() - 1, row)

    def set_group_colors(self, colors: Dict[str, str]):
        """设置分组颜色"""
        self._group_colors = colors
        self._refresh_color_buttons()

    def _make_color_row(self, grp_name: str) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        name_lbl = QLabel(grp_name)
        name_lbl.setMinimumWidth(60)
        name_lbl.setStyleSheet("color: #c0c0d0; border: none;")
        layout.addWidget(name_lbl)

        color = self._group_colors.get(grp_name, "#8888a0")
        color_btn = QPushButton()
        color_btn.setObjectName("colorBtn")
        color_btn.setFixedSize(28, 28)
        color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        color_btn.setToolTip(f"{grp_name} 的颜色 — 点击修改")
        self._set_btn_color(color_btn, QColor(color))
        color_btn.clicked.connect(lambda checked=False, g=grp_name, b=color_btn: self._pick_color(g, b))
        layout.addWidget(color_btn)

        # 重置按钮
        reset_btn = QPushButton("默认")
        reset_btn.setFixedSize(40, 24)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setToolTip(f"恢复 {grp_name} 的默认颜色")
        reset_btn.clicked.connect(lambda checked=False, g=grp_name: self._reset_color(g))
        layout.addWidget(reset_btn)

        layout.addStretch()
        return row

    @staticmethod
    def _set_btn_color(btn: QPushButton, color: QColor):
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {color.name()}; "
            f"border: 1px solid {color.darker(120).name()}; border-radius: 4px; }}"
            f"QPushButton:hover {{ border: 2px solid #ffffff; }}"
        )

    def _pick_color(self, grp_name: str, btn: QPushButton):
        current = self._group_colors.get(grp_name, "#8888a0")
        color = QColorDialog.getColor(QColor(current), self, f"选择 {grp_name} 的颜色")
        if color.isValid():
            self._group_colors[grp_name] = color.name()
            self._set_btn_color(btn, color)
            self.group_colors_changed.emit(dict(self._group_colors))

    def _reset_color(self, grp_name: str):
        if grp_name in self._group_colors:
            del self._group_colors[grp_name]
        self.group_colors_changed.emit(dict(self._group_colors))
        self._refresh_color_buttons()

    def _refresh_color_buttons(self):
        """刷新所有颜色按钮"""
        for i in range(self._color_layout.count()):
            w = self._color_layout.itemAt(i).widget()
            if w and w is not self._no_group_hint:
                # 找到 color_btn（第二个子控件）
                row_layout = w.layout()
                if row_layout and row_layout.count() >= 2:
                    name_lbl = row_layout.itemAt(0).widget()
                    color_btn = row_layout.itemAt(1).widget()
                    if isinstance(name_lbl, QLabel) and isinstance(color_btn, QPushButton):
                        grp_name = name_lbl.text()
                        color = self._group_colors.get(grp_name, "#8888a0")
                        self._set_btn_color(color_btn, QColor(color))

    # ===== 透明度 150ms 防抖 =====
    _pending_opacity = 85

    def _on_slider_changed(self, value: int):
        self.opacity_value.setText(f"{value}%")
        self._pending_opacity = value
        self._debounce_timer.start(150)

    def _emit_opacity(self):
        self.opacity_changed.emit(self._pending_opacity)
