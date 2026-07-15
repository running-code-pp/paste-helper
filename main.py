"""Paste Helper — Windows 桌面粘贴助手 (PySide6)

轻量级剪切板管理工具：预存常用文本片段，通过全局快捷键快速切换并粘贴。
"""

import sys
import os

# 确保项目目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from database import init_db, get_settings
from ui.main_window import MainWindow
from ui.tray_manager import TrayManager

# 图标路径
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icon.ico")


def main():
    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Paste Helper")
    app.setApplicationDisplayName("Paste Helper - 粘贴助手")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，托盘驻留

    # 设置全局图标
    app_icon = QIcon(ICON_PATH)
    app.setWindowIcon(app_icon)

    # 初始化数据库
    init_db()

    # 创建主窗口
    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()

    # 创建托盘
    tray = TrayManager(app, ICON_PATH)
    tray.set_show_callback(window.toggle_visible)
    tray.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
