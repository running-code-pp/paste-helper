"""抽屉面板 — 包含条目标签页和设置标签页"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Qt
from ui.items_tab import ItemsTab
from ui.settings_tab import SettingsTab


class DrawerWidget(QWidget):
    """展开面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("drawerWidget")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标签页
        self.tabs = QTabWidget()
        self.items_tab = ItemsTab()
        self.settings_tab = SettingsTab()
        self.tabs.addTab(self.items_tab, "条目")
        self.tabs.addTab(self.settings_tab, "设置")

        layout.addWidget(self.tabs)
