"""主窗口 — 无边框、置顶、隐藏任务栏、居中于屏幕顶部"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QGuiApplication

from ui.bar_widget import BarWidget
from ui.drawer_widget import DrawerWidget
from database import get_settings, set_setting, get_all_items
from clipboard import copy_to_clipboard
from styles.theme import DARK_QSS, LIGHT_QSS
from hotkey import HotkeyManager


BAR_HEIGHT = 40
DRAWER_HEIGHT = 400
COLLAPSED_SIZE = (420, BAR_HEIGHT)
EXPANDED_SIZE = (420, BAR_HEIGHT + DRAWER_HEIGHT)


class MainWindow(QWidget):
    """粘贴助手主窗口"""

    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")

        # 窗口属性
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # 从设置加载
        self._settings = get_settings()
        self._items = get_all_items()
        self._expanded = False

        # 创建 UI
        self._setup_ui()
        self._apply_theme()
        self._apply_opacity()

        # 位置
        self._center_on_screen()

        # 快捷键管理器
        self._hotkey_mgr = HotkeyManager(self)
        self._register_hotkeys()

        # 安装原生事件过滤器
        import ctypes
        if hasattr(ctypes, "windll"):
            from PySide6.QtCore import QAbstractNativeEventFilter
            QGuiApplication.instance().installNativeEventFilter(self._hotkey_mgr)

    def _setup_ui(self):
        """构建 UI 布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 横条
        self.bar = BarWidget()
        self.bar.setFixedHeight(BAR_HEIGHT)
        layout.addWidget(self.bar)

        # 抽屉
        self.drawer = DrawerWidget()
        self.drawer.setFixedHeight(DRAWER_HEIGHT)
        self.drawer.setVisible(False)
        layout.addWidget(self.drawer)

        # 初始尺寸
        self.setFixedSize(*COLLAPSED_SIZE)

        # ---------- 信号连接 ----------

        # 横条按钮 → 导航
        self.bar.prev_clicked.connect(self._prev_item)
        self.bar.next_clicked.connect(self._next_item)
        self.bar.expand_clicked.connect(self._toggle_expand)
        self.bar.close_clicked.connect(self._on_close)
        self.bar.double_clicked.connect(self._toggle_expand)

        # 横条 → 提示条
        self.bar.hover_enter.connect(lambda: self._show_tooltip())
        self.bar.hover_leave.connect(lambda: self._schedule_tooltip_hide())

        # 抽屉 → 条目变更
        self.drawer.items_tab.item_added.connect(self._on_item_added)
        self.drawer.items_tab.item_deleted.connect(self._on_item_deleted)
        self.drawer.items_tab.item_selected.connect(self._on_item_selected)

        # 抽屉 → 设置变更
        self.drawer.settings_tab.opacity_changed.connect(self._on_opacity_changed)
        self.drawer.settings_tab.prev_keys_changed.connect(self._on_prev_keys_changed)
        self.drawer.settings_tab.next_keys_changed.connect(self._on_next_keys_changed)
        self.drawer.settings_tab.theme_changed.connect(self._on_theme_changed)
        self.drawer.settings_tab.exit_clicked.connect(self._on_close)

        # 刷新显示
        self._refresh_bar()
        self._refresh_list()
        self._init_settings_tab()

    # ==================== 主题 ====================

    def _apply_theme(self):
        """切换主题样式"""
        if self._settings.theme == "light":
            self.setStyleSheet(LIGHT_QSS)
        else:
            self.setStyleSheet(DARK_QSS)

    def _apply_opacity(self):
        """应用透明度设置（10-100 → 0.1-1.0）"""
        win_opacity = max(0.1, self._settings.opacity / 100.0)
        self.setWindowOpacity(win_opacity)

    # ==================== 位置 ====================

    def _center_on_screen(self):
        """居中于屏幕顶部"""
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - COLLAPSED_SIZE[0]) // 2
            y = geo.y() + 4  # 距顶部 4px
            self.move(x, y)

    # ==================== 展开 / 收起 ====================

    def _toggle_expand(self):
        """切换抽屉展开/收起"""
        self._expanded = not self._expanded
        target_h = EXPANDED_SIZE[1] if self._expanded else COLLAPSED_SIZE[1]
        self.drawer.setVisible(self._expanded)

        # 动画
        anim = QPropertyAnimation(self, b"size")
        anim.setDuration(200)
        anim.setStartValue(self.size())
        anim.setEndValue(EXPANDED_SIZE if self._expanded else COLLAPSED_SIZE)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def _on_finished():
            self.setFixedSize(420, target_h)

        anim.finished.connect(_on_finished)
        anim.start()

        # 更新展开按钮箭头
        self.bar.update_expand_state(self._expanded)

    # ==================== 导航 ====================

    def _prev_item(self):
        """切换到上一条"""
        if not self._items:
            return
        idx = self._settings.current_index
        if idx <= 0:
            idx = len(self._items) - 1
        else:
            idx -= 1
        self._select_item(idx)

    def _next_item(self):
        """切换到下一条"""
        if not self._items:
            return
        idx = self._settings.current_index
        if idx >= len(self._items) - 1:
            idx = 0
        else:
            idx += 1
        self._select_item(idx)

    def _select_item(self, idx: int):
        """选中指定索引的条目"""
        if idx < 0 or idx >= len(self._items):
            return
        self._settings.current_index = idx
        set_setting("current_index", str(idx))
        self._refresh_bar()
        self.drawer.items_tab.set_selected_index(idx)
        # 自动复制
        item = self._items[idx]
        copy_to_clipboard(item.content)
        # 显示 Toast
        self.bar.show_toast("已复制")
        # 显示提示条
        self._show_tooltip()
        self._schedule_tooltip_hide()

    # ==================== 显示刷新 ====================

    def _refresh_bar(self):
        """刷新横条显示"""
        total = len(self._items)
        idx = self._settings.current_index
        if total == 0:
            self.bar.set_index(-1, 0)
            self.bar.set_content("暂无内容 — 双击添加", "")
            return
        self.bar.set_index(idx, total)
        item = self._items[idx] if 0 <= idx < total else self._items[0]
        self.bar.set_content(item.content, item.comment)

    def _refresh_list(self):
        """刷新条目列表"""
        self._items = get_all_items()
        self.drawer.items_tab.refresh(self._items, self._settings.current_index)

    def _init_settings_tab(self):
        """初始化设置标签页的值"""
        s = self._settings
        self.drawer.settings_tab.set_opacity(s.opacity)
        self.drawer.settings_tab.set_hotkeys(s.prev_keys, s.next_keys)
        self.drawer.settings_tab.set_theme(s.theme)

    # ==================== 提示条 ====================

    _tooltip_timer: QTimer | None = None

    def _show_tooltip(self):
        """显示提示条"""
        if self._tooltip_timer:
            self._tooltip_timer.stop()
        total = len(self._items)
        idx = self._settings.current_index
        if total == 0 or idx < 0:
            return
        item = self._items[idx]
        self.bar.show_tooltip(item.content, item.comment)

    def _schedule_tooltip_hide(self):
        """2.5s 后隐藏提示条"""
        if self._tooltip_timer:
            self._tooltip_timer.stop()
        self._tooltip_timer = QTimer(self)
        self._tooltip_timer.setSingleShot(True)
        self._tooltip_timer.timeout.connect(self.bar.hide_tooltip)
        self._tooltip_timer.start(2500)

    # ==================== 条目操作 ====================

    def _on_item_added(self, content: str, comment: str):
        from database import add_item
        add_item(content, comment)
        self._items = get_all_items()
        # 如果之前没有条目，自动选中新条目
        if self._settings.current_index < 0 and self._items:
            self._settings.current_index = 0
            set_setting("current_index", "0")
        self._refresh_bar()
        self._refresh_list()

    def _on_item_deleted(self, item_id: str):
        from database import delete_item
        delete_item(item_id)
        self._items = get_all_items()
        if self._settings.current_index >= len(self._items):
            self._settings.current_index = len(self._items) - 1
            set_setting("current_index", str(self._settings.current_index))
        self._refresh_bar()
        self._refresh_list()
        # 刷新选中状态
        self.drawer.items_tab.set_selected_index(self._settings.current_index)

    def _on_item_selected(self, idx: int):
        """点击列表中的条目"""
        if 0 <= idx < len(self._items):
            self._select_item(idx)
            self._refresh_list()

    # ==================== 设置操作 ====================

    def _on_opacity_changed(self, value: int):
        self._settings.opacity = value
        set_setting("opacity", str(value))
        self._apply_opacity()

    def _on_prev_keys_changed(self, keys: str):
        self._settings.prev_keys = keys
        set_setting("prev_keys", keys)
        self._register_hotkeys()

    def _on_next_keys_changed(self, keys: str):
        self._settings.next_keys = keys
        set_setting("next_keys", keys)
        self._register_hotkeys()

    def _on_theme_changed(self, theme: str):
        self._settings.theme = theme
        set_setting("theme", theme)
        self._apply_theme()

    # ==================== 快捷键 ====================

    def _register_hotkeys(self):
        """注册（重新注册）全局快捷键"""
        self._hotkey_mgr.unregister_all()
        self._hotkey_mgr.register(self._settings.prev_keys, self._prev_item)
        self._hotkey_mgr.register(self._settings.next_keys, self._next_item)

    # ==================== 退出 ====================

    def _on_close(self):
        """关闭窗口 → 隐藏到托盘"""
        self.hide()

    # ==================== 供托盘使用 ====================

    def toggle_visible(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self._center_on_screen()
