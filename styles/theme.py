"""主题样式定义 — 深色/浅色两套 QSS"""

DARK_QSS = """
/* ===== 全局 ===== */
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ===== 主窗口背景 ===== */
#mainWindow {
    background-color: #1e1e2e;
    border-radius: 4px;
}

/* ===== 横条 ===== */
#barWidget {
    background-color: #2a2a3c;
    border-radius: 4px;
    border: 1px solid #3a3a50;
}

#indexLabel {
    color: #8888a0;
    font-size: 12px;
    min-width: 36px;
    padding: 0 4px;
}

#contentLabel {
    color: #d0d0e0;
    font-size: 13px;
    padding: 0 4px;
}

#hintLabel {
    color: #666680;
    font-size: 12px;
    padding: 0 4px;
}

/* ===== 按钮 ===== */
QPushButton {
    border: none;
    border-radius: 3px;
    padding: 2px 8px;
    color: #8888a0;
    background: transparent;
    font-size: 14px;
    min-width: 28px;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #3a3a50;
    color: #d0d0e0;
}

QPushButton:pressed {
    background-color: #4a4a60;
}

#closeBtn:hover {
    background-color: #c0392b;
    color: #ffffff;
}

#expandBtn {
    font-size: 12px;
}

#addBtn {
    background-color: #4a7cf7;
    color: #ffffff;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}

#addBtn:hover {
    background-color: #5a8cf7;
}

#addBtn:disabled {
    background-color: #3a3a50;
    color: #666680;
}

/* ===== 抽屉面板 ===== */
#drawerWidget {
    background-color: #1e1e2e;
    border: 1px solid #3a3a50;
    border-top: none;
    border-radius: 0 0 4px 4px;
}

QTabWidget::pane {
    border: none;
    background-color: #1e1e2e;
}

QTabBar::tab {
    background-color: #2a2a3c;
    color: #8888a0;
    padding: 6px 16px;
    border: 1px solid #3a3a50;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #353550;
    color: #d0d0e0;
    border-color: #4a4a60;
}

QTabBar::tab:hover:!selected {
    background-color: #303045;
}

/* ===== 输入框 ===== */
QLineEdit, QTextEdit {
    background-color: #1a1a2e;
    color: #d0d0e0;
    border: 1px solid #3a3a50;
    border-radius: 4px;
    padding: 6px 10px;
    selection-background-color: #4a7cf7;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #4a7cf7;
}

QScrollArea {
    background-color: #1e1e2e;
    border: none;
}
QScrollArea > QWidget {
    background-color: #1e1e2e;
}
#listContainer {
    background-color: #1e1e2e;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #4a4a60;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5a5a70;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ===== 滑块 ===== */
QSlider::groove:horizontal {
    background-color: #1a1a2e;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #4a7cf7;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background-color: #5a8cf7;
}

/* ===== 提示条 / Tooltip ===== */
#tooltipWidget {
    background-color: #2a2a3c;
    color: #d0d0e0;
    border: 1px solid #4a7cf7;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
}

QToolTip {
    background-color: #2a2a3c;
    color: #d0d0e0;
    border: 1px solid #4a4a60;
    padding: 4px 8px;
}

/* ===== 空状态 ===== */
#emptyLabel {
    color: #666680;
    font-size: 13px;
    padding: 20px;
}

/* ===== Toast ===== */
#toastLabel {
    background-color: #4a7cf7;
    color: #ffffff;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 12px;
}

/* ===== 条目列表项 ===== */
#itemWidget {
    background-color: #1e1e2e;
    border-radius: 4px;
    padding: 6px 10px;
    margin: 2px 4px;
}

#itemWidget:hover {
    background-color: #2a2a3c;
}

#itemWidget[selected="true"] {
    background-color: #2a2a3c;
    border-left: 3px solid #4a7cf7;
}

#itemWidget QLabel {
    color: #8888a0;
    border: none;
    background: transparent;
}

/* ===== 快捷键捕获按钮 ===== */
#hotkeyBtn {
    background-color: #1a1a2e;
    color: #8888a0;
    border: 1px solid #3a3a50;
    border-radius: 4px;
    padding: 6px 12px;
    font-family: "Consolas", "Courier New", monospace;
}

#hotkeyBtn[capturing="true"] {
    border-color: #4a7cf7;
    color: #d0d0e0;
    background-color: #2a2a4c;
}
"""

LIGHT_QSS = """
/* ===== 全局 ===== */
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ===== 主窗口背景 ===== */
#mainWindow {
    background-color: #f0f0f5;
    border-radius: 4px;
}

/* ===== 横条 ===== */
#barWidget {
    background-color: #ffffff;
    border-radius: 4px;
    border: 1px solid #d0d0d8;
}

#indexLabel {
    color: #9999a0;
    font-size: 12px;
    min-width: 36px;
    padding: 0 4px;
}

#contentLabel {
    color: #333340;
    font-size: 13px;
    padding: 0 4px;
}

#hintLabel {
    color: #9999a0;
    font-size: 12px;
    padding: 0 4px;
}

/* ===== 按钮 ===== */
QPushButton {
    border: none;
    border-radius: 3px;
    padding: 2px 8px;
    color: #666680;
    background: transparent;
    font-size: 14px;
    min-width: 28px;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #e0e0e8;
    color: #333340;
}

QPushButton:pressed {
    background-color: #d0d0d8;
}

#closeBtn:hover {
    background-color: #c0392b;
    color: #ffffff;
}

#expandBtn {
    font-size: 12px;
}

#addBtn {
    background-color: #4a7cf7;
    color: #ffffff;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}

#addBtn:hover {
    background-color: #3a6ce7;
}

#addBtn:disabled {
    background-color: #d0d0d8;
    color: #9999a0;
}

/* ===== 抽屉面板 ===== */
#drawerWidget {
    background-color: #f0f0f5;
    border: 1px solid #d0d0d8;
    border-top: none;
    border-radius: 0 0 4px 4px;
}

QTabWidget::pane {
    border: none;
    background-color: #f0f0f5;
}

QTabBar::tab {
    background-color: #f0f0f5;
    color: #666680;
    padding: 6px 16px;
    border: 1px solid #d0d0d8;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #333340;
    border-color: #c0c0c8;
}

QTabBar::tab:hover:!selected {
    background-color: #e8e8f0;
}

/* ===== 输入框 ===== */
QLineEdit, QTextEdit {
    background-color: #ffffff;
    color: #333340;
    border: 1px solid #d0d0d8;
    border-radius: 4px;
    padding: 6px 10px;
    selection-background-color: #4a7cf7;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #4a7cf7;
}

QScrollArea {
    background-color: #f0f0f5;
    border: none;
}
QScrollArea > QWidget {
    background-color: #f0f0f5;
}
#listContainer {
    background-color: #f0f0f5;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background-color: #f0f0f5;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c8;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ===== 滑块 ===== */
QSlider::groove:horizontal {
    background-color: #e0e0e8;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #4a7cf7;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background-color: #3a6ce7;
}

/* ===== 提示条 / Tooltip ===== */
#tooltipWidget {
    background-color: #ffffff;
    color: #333340;
    border: 1px solid #4a7cf7;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
}

QToolTip {
    background-color: #ffffff;
    color: #333340;
    border: 1px solid #c0c0c8;
    padding: 4px 8px;
}

/* ===== 空状态 ===== */
#emptyLabel {
    color: #9999a0;
    font-size: 13px;
    padding: 20px;
}

/* ===== Toast ===== */
#toastLabel {
    background-color: #4a7cf7;
    color: #ffffff;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 12px;
}

/* ===== 条目列表项 ===== */
#itemWidget {
    background-color: #f0f0f5;
    border-radius: 4px;
    padding: 6px 10px;
    margin: 2px 4px;
}

#itemWidget:hover {
    background-color: #e8e8f0;
}

#itemWidget[selected="true"] {
    background-color: #e0e5ff;
    border-left: 3px solid #4a7cf7;
}

#itemWidget QLabel {
    color: #666680;
    border: none;
    background: transparent;
}

/* ===== 快捷键捕获按钮 ===== */
#hotkeyBtn {
    background-color: #f0f0f5;
    color: #666680;
    border: 1px solid #d0d0d8;
    border-radius: 4px;
    padding: 6px 12px;
    font-family: "Consolas", "Courier New", monospace;
}

#hotkeyBtn[capturing="true"] {
    border-color: #4a7cf7;
    color: #333340;
    background-color: #e0e5ff;
}
"""
