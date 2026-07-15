"""主窗口 — 无边框、置顶、隐藏任务栏、居中于屏幕顶部"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
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
        self._current_grp = self._settings.current_grp  # 当前分组筛选

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

        # 初始尺寸（不用 setFixedSize，用 resize 允许后续动画）
        self.resize(*COLLAPSED_SIZE)
        self.setMinimumSize(420, BAR_HEIGHT)

        # ---------- 信号连接 ----------

        # 横条按钮 → 导航
        self.bar.prev_clicked.connect(self._prev_item)
        self.bar.next_clicked.connect(self._next_item)
        self.bar.expand_clicked.connect(self._toggle_expand)
        self.bar.close_clicked.connect(self._on_close)
        self.bar.double_clicked.connect(self._toggle_expand)

        # 横条 → 分组切换
        self.bar.group_changed.connect(self._on_group_changed)

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
        self.drawer.setVisible(self._expanded)

        target_size = EXPANDED_SIZE if self._expanded else COLLAPSED_SIZE

        # 展开前先解除最大尺寸限制
        if self._expanded:
            self.setMaximumSize(420, EXPANDED_SIZE[1])

        # 动画（存为实例属性防止 GC 回收）
        self._expand_anim = QPropertyAnimation(self, b"size")
        self._expand_anim.setDuration(200)
        self._expand_anim.setStartValue(self.size())
        self._expand_anim.setEndValue(target_size)
        self._expand_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._expand_anim.finished.connect(self._on_expand_finished)
        self._expand_anim.start()

        # 更新展开按钮箭头
        self.bar.update_expand_state(self._expanded)

    def _on_expand_finished(self):
        """动画结束后锁定尺寸"""
        target_h = EXPANDED_SIZE[1] if self._expanded else COLLAPSED_SIZE[1]
        self.setMaximumSize(420, target_h)
        self.resize(420, target_h)

    # ==================== 导航 ====================

    def _get_filtered_indices(self):
        """返回当前分组下的全局索引列表"""
        if not self._current_grp or self._current_grp == "全部":
            return list(range(len(self._items)))
        result = []
        for i, item in enumerate(self._items):
            grp = item.grp if item.grp else "其他"
            if grp == self._current_grp:
                result.append(i)
        return result

    def _prev_item(self):
        """切换到上一条（分组内循环）"""
        if not self._items:
            return
        indices = self._get_filtered_indices()
        if not indices:
            return
        idx = self._settings.current_index
        try:
            pos = indices.index(idx)
        except ValueError:
            pos = 0
        if pos <= 0:
            pos = len(indices) - 1
        else:
            pos -= 1
        self._select_item(indices[pos])

    def _next_item(self):
        """切换到下一条（分组内循环）"""
        if not self._items:
            return
        indices = self._get_filtered_indices()
        if not indices:
            return
        idx = self._settings.current_index
        try:
            pos = indices.index(idx)
        except ValueError:
            pos = -1
        if pos >= len(indices) - 1:
            pos = 0
        else:
            pos += 1
        self._select_item(indices[pos])

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

    # ==================== 显示刷新 ====================

    def _refresh_bar(self):
        """刷新横条显示（分组过滤后的 index）"""
        indices = self._get_filtered_indices()
        total = len(indices)
        idx = self._settings.current_index

        if total == 0:
            self.bar.set_index(-1, 0)
            self.bar.set_content("暂无内容 — 双击添加", "")
            return

        # 确保 current_index 在过滤范围内
        if idx not in indices:
            idx = indices[0]
            self._settings.current_index = idx
            set_setting("current_index", str(idx))

        pos = indices.index(idx)
        self.bar.set_index(pos, total)
        item = self._items[idx]
        self.bar.set_content(item.content, item.comment)

        # 更新 bar 的分组下拉框
        group_list = self._compute_group_list()
        self.bar.set_groups(group_list, self._current_grp or "全部")

    def _refresh_list(self):
        """刷新条目列表"""
        self._items = get_all_items()
        group_list = self._compute_group_list()
        self.drawer.items_tab.refresh(
            self._items, self._settings.current_index,
            groups=group_list, current_grp=self._current_grp
        )

    def _init_settings_tab(self):
        """初始化设置标签页的值"""
        s = self._settings
        self.drawer.settings_tab.set_opacity(s.opacity)
        self.drawer.settings_tab.set_hotkeys(s.prev_keys, s.next_keys)
        self.drawer.settings_tab.set_theme(s.theme)

    # ==================== 分组 ====================

    def _compute_group_list(self):
        """从所有条目中提取分组列表"""
        groups = set()
        for item in self._items:
            groups.add(item.grp if item.grp else "其他")
        return ["全部"] + sorted(groups)

    def _on_group_changed(self, grp: str):
        """分组下拉框切换"""
        self._current_grp = grp
        self._settings.current_grp = grp
        set_setting("current_grp", grp)

        # 自动选中该分组的第一条
        indices = self._get_filtered_indices()
        if indices:
            if self._settings.current_index not in indices:
                self._settings.current_index = indices[0]
                set_setting("current_index", str(indices[0]))
        else:
            self._settings.current_index = -1
            set_setting("current_index", "-1")

        self._refresh_bar()

    # ==================== 条目操作 ====================

    def _on_item_added(self, content: str, comment: str, grp: str):
        from database import add_item
        add_item(content, comment, grp)
        self._items = get_all_items()
        # 如果之前没有条目，自动选中新条目
        if self._settings.current_index < 0 and self._items:
            self._settings.current_index = 0
            set_setting("current_index", "0")
        # 验证当前索引在分组内有效
        indices = self._get_filtered_indices()
        if indices and self._settings.current_index not in indices:
            self._settings.current_index = indices[0]
            set_setting("current_index", str(indices[0]))
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
