"""托盘管理器 — 系统托盘图标 + 右键菜单"""

import os
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle
from PySide6.QtGui import QIcon, QAction


class TrayManager:
    """系统托盘管理器"""

    def __init__(self, app: QApplication, icon_path: str):
        self._app = app
        self._tray = QSystemTrayIcon()
        self._tray.setToolTip("Paste Helper - 粘贴助手")

        # 使用 resources/icon.ico
        if os.path.exists(icon_path):
            self._tray.setIcon(QIcon(icon_path))
        else:
            # 回退到内置图标
            self._tray.setIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))

        self._hotkey_enabled = True

        # 右键菜单
        self._build_menu()

        # 左键单击 / 双击打开面板
        self._tray.activated.connect(self._on_activated)

    def _build_menu(self):
        menu = QMenu()

        # 打开 / 隐藏面板
        self._show_action = QAction("打开面板", menu)
        self._show_action.triggered.connect(self._on_show)
        menu.addAction(self._show_action)

        menu.addSeparator()

        # 切换快捷键开关
        self._hotkey_action = QAction("快捷键: 已开启", menu)
        self._hotkey_action.setCheckable(True)
        self._hotkey_action.setChecked(True)
        self._hotkey_action.triggered.connect(self._toggle_hotkey)
        menu.addAction(self._hotkey_action)

        # 开机自启（占位）
        self._autostart_action = QAction("开机自启: 关闭", menu)
        self._autostart_action.triggered.connect(self._toggle_autostart)
        menu.addAction(self._autostart_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self._on_quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)

    def _on_show(self):
        pass  # 由外部 set_show_callback 设置

    def _on_quit(self):
        self._tray.hide()
        self._app.quit()

    def _on_activated(self, reason):
        # 左键单击或双击都打开面板
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,       # 单击
            QSystemTrayIcon.ActivationReason.DoubleClick,   # 双击
        ):
            self._on_show()

    def _toggle_hotkey(self, checked: bool):
        self._hotkey_enabled = checked
        self._hotkey_action.setText(f"快捷键: {'已开启' if checked else '已关闭'}")
        # TODO: 实际启用/禁用快捷键注册

    def _toggle_autostart(self):
        # TODO: 实现开机自启
        self.show_message("Paste Helper", "开机自启功能开发中...")

    def set_show_callback(self, callback):
        """设置打开面板的回调"""
        self._on_show = callback

    def show(self):
        self._tray.show()

    def hide(self):
        self._tray.hide()

    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information, duration=3000):
        self._tray.showMessage(title, message, icon, duration)
