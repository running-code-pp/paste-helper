"""主窗口 — 无边框、置顶、隐藏任务栏、居中于屏幕顶部"""

import sys
import csv

if sys.platform == "win32":
    import ctypes
    from ctypes.wintypes import MSG

from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QGuiApplication

from ui.bar_widget import BarWidget
from ui.drawer_widget import DrawerWidget
from ui.settings_tab import GroupSelectDialog
from database import get_settings, set_setting, get_all_items, import_items
from clipboard import copy_to_clipboard
from styles.theme import DARK_QSS, LIGHT_QSS
from hotkey import HotkeyManager
from models import GROUP_COLOR_PRESETS


BAR_HEIGHT = 40
DRAWER_HEIGHT = 400
DEFAULT_WIDTH = 420
MIN_WIDTH = 300
_MAX_DIM = 16777215  # QWIDGETSIZE_MAX，不限制宽度
COLLAPSED_SIZE = (DEFAULT_WIDTH, BAR_HEIGHT)
EXPANDED_SIZE = (DEFAULT_WIDTH, BAR_HEIGHT + DRAWER_HEIGHT)


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
        self._animating = False  # 动画进行中标记
        self._current_grp = self._settings.current_grp  # 当前分组筛选

        # 为没有颜色的分组自动分配颜色
        self._ensure_group_colors()

        # 宽度持久化：拖曳结束 500ms 后保存
        self._save_width_timer = QTimer(self)
        self._save_width_timer.setSingleShot(True)
        self._save_width_timer.setInterval(500)
        self._save_width_timer.timeout.connect(self._save_window_width)

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

    # ==================== 分组颜色 ====================

    def _ensure_group_colors(self):
        """为没有颜色的分组自动分配预设颜色"""
        groups = set()
        for item in self._items:
            g = item.grp if item.grp else "其他"
            groups.add(g)

        changed = False
        for i, g in enumerate(sorted(groups)):
            if g not in self._settings.group_colors:
                self._settings.group_colors[g] = GROUP_COLOR_PRESETS[i % len(GROUP_COLOR_PRESETS)]
                changed = True

        if changed:
            self._save_group_colors()

    def _save_group_colors(self):
        """持久化分组颜色"""
        set_setting("group_colors", self._settings.to_group_colors_json())

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

        # 初始尺寸 — 优先使用上次保存的宽度
        saved_w = self._settings.window_width
        init_w = saved_w if saved_w and saved_w >= MIN_WIDTH else DEFAULT_WIDTH
        self.resize(init_w, BAR_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, BAR_HEIGHT)

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
        self.drawer.settings_tab.auto_collapse_changed.connect(self._on_auto_collapse_changed)
        self.drawer.settings_tab.group_colors_changed.connect(self._on_group_colors_changed)
        self.drawer.settings_tab.import_clicked.connect(self._on_import)
        self.drawer.settings_tab.export_clicked.connect(self._on_export)
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

    # ==================== 窗口大小事件 ====================

    def resizeEvent(self, event):
        """窗口大小变化时，非动画状态下延迟保存宽度"""
        super().resizeEvent(event)
        if not self._animating:
            self._save_width_timer.start()  # 防抖 500ms

    def _save_window_width(self):
        """持久化当前窗口宽度"""
        set_setting("window_width", str(self.width()))

    # ==================== 位置 ====================

    def _center_on_screen(self):
        """居中于屏幕顶部"""
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + 4  # 距顶部 4px
            self.move(x, y)

    # ==================== 窗口拖曳调整大小 ====================

    def nativeEvent(self, eventType, message):
        """处理 Windows WM_NCHITTEST，为无边框窗口提供边缘拖曳调整大小"""
        if sys.platform != "win32":
            return False, 0

        # WM_NCHITTEST 及边框常量
        WM_NCHITTEST = 0x0084
        HTLEFT = 10
        HTRIGHT = 11
        HTTOP = 12
        HTTOPLEFT = 13
        HTTOPRIGHT = 14
        HTBOTTOM = 15
        HTBOTTOMLEFT = 16
        HTBOTTOMRIGHT = 17

        msg = ctypes.cast(int(message), ctypes.POINTER(MSG)).contents

        if msg.message != WM_NCHITTEST:
            return False, 0

        # 鼠标屏幕坐标
        x = msg.pt.x
        y = msg.pt.y

        # 窗口屏幕坐标和尺寸
        pos = self.mapToGlobal(self.rect().topLeft())
        win_x = pos.x()
        win_y = pos.y()
        win_w = self.width()
        win_h = self.height()

        BORDER = 6  # 可拖曳边框宽度（像素）

        on_left = x < win_x + BORDER
        on_right = x > win_x + win_w - BORDER
        on_top = y < win_y + BORDER
        on_bottom = y > win_y + win_h - BORDER

        if on_left and on_top:
            return True, HTTOPLEFT
        if on_left and on_bottom:
            return True, HTBOTTOMLEFT
        if on_right and on_top:
            return True, HTTOPRIGHT
        if on_right and on_bottom:
            return True, HTBOTTOMRIGHT
        if on_left:
            return True, HTLEFT
        if on_right:
            return True, HTRIGHT
        if on_top:
            return True, HTTOP
        if on_bottom:
            return True, HTBOTTOM

        return False, 0

    # ==================== 展开 / 收起 ====================

    def _toggle_expand(self):
        """切换抽屉展开/收起"""
        self._expanded = not self._expanded
        self.drawer.setVisible(self._expanded)

        # 展开时刷新列表（应用当前分组过滤）
        if self._expanded:
            self._refresh_list()

        target_h = EXPANDED_SIZE[1] if self._expanded else COLLAPSED_SIZE[1]

        # 动画前解除高度限制
        self.setMaximumSize(_MAX_DIM, _MAX_DIM)

        # 使用 QVariantAnimation 只动画高度，宽度始终取 self.width()
        self._animating = True
        self._expand_anim = QVariantAnimation()
        self._expand_anim.setDuration(200)
        self._expand_anim.setStartValue(self.height())
        self._expand_anim.setEndValue(target_h)
        self._expand_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._expand_anim.valueChanged.connect(self._on_expand_step)
        self._expand_anim.finished.connect(self._on_expand_finished)
        self._expand_anim.start()

        # 更新展开按钮箭头
        self.bar.update_expand_state(self._expanded)

    def _on_expand_step(self, h: int):
        """动画每帧：只改高度，宽度保持不变"""
        self.resize(self.width(), h)

    def _on_expand_finished(self):
        """动画结束后锁定高度"""
        self._animating = False
        target_h = EXPANDED_SIZE[1] if self._expanded else COLLAPSED_SIZE[1]
        self.setMaximumSize(_MAX_DIM, target_h)
        self.resize(self.width(), target_h)

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

    def _get_filtered_items(self):
        """返回当前分组下的条目列表"""
        if not self._current_grp or self._current_grp == "全部":
            return list(self._items)
        return [item for item in self._items
                if (item.grp if item.grp else "其他") == self._current_grp]

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
        self.drawer.items_tab.set_selected_id(self._items[idx].id)
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
        """刷新条目列表（按分组过滤）"""
        self._items = get_all_items()
        group_list = self._compute_group_list()

        # 根据当前分组过滤条目（小窗口选分组 → 展开只显示该分组）
        filtered_items = self._get_filtered_items()

        # 当前选中条目的 ID
        selected_id = ""
        if 0 <= self._settings.current_index < len(self._items):
            selected_id = self._items[self._settings.current_index].id

        self.drawer.items_tab.refresh(
            filtered_items, selected_id,
            groups=group_list, current_grp=self._current_grp,
            group_colors=self._settings.group_colors,
        )

        # 同时更新设置页的分组列表
        self._refresh_settings_groups()

    def _init_settings_tab(self):
        """初始化设置标签页的值"""
        s = self._settings
        self.drawer.settings_tab.set_opacity(s.opacity)
        self.drawer.settings_tab.set_hotkeys(s.prev_keys, s.next_keys)
        self.drawer.settings_tab.set_theme(s.theme)
        self.drawer.settings_tab.set_auto_collapse(s.auto_collapse)
        self._refresh_settings_groups()
        self.drawer.settings_tab.set_group_colors(s.group_colors)

    def _refresh_settings_groups(self):
        """刷新设置页的分组颜色列表"""
        group_list = self._compute_group_list()
        self.drawer.settings_tab.set_groups(group_list)
        self.drawer.settings_tab.set_group_colors(self._settings.group_colors)

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
        # 如果抽屉已展开，立即刷新列表
        if self._expanded:
            self._refresh_list()

    # ==================== 条目操作 ====================

    def _on_item_added(self, content: str, comment: str, grp: str):
        from database import add_item
        add_item(content, comment, grp)
        self._items = get_all_items()

        # 新分组自动分配颜色
        grp_name = grp if grp else "其他"
        if grp_name not in self._settings.group_colors:
            idx = len(self._settings.group_colors)
            self._settings.group_colors[grp_name] = GROUP_COLOR_PRESETS[idx % len(GROUP_COLOR_PRESETS)]
            self._save_group_colors()

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
        selected_id = ""
        if 0 <= self._settings.current_index < len(self._items):
            selected_id = self._items[self._settings.current_index].id
        self.drawer.items_tab.set_selected_id(selected_id)

    def _on_item_selected(self, item_id: str):
        """点击列表中的条目（按 ID）"""
        # 在全局 _items 中查找
        for idx, item in enumerate(self._items):
            if item.id == item_id:
                self._select_item(idx)
                self._refresh_list()
                # 若开启"复制后自动收起"且当前处于展开状态，则自动收起
                if self._settings.auto_collapse and self._expanded:
                    self._toggle_expand()
                break

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

    def _on_auto_collapse_changed(self, enabled: bool):
        self._settings.auto_collapse = enabled
        set_setting("auto_collapse", "1" if enabled else "0")

    def _on_group_colors_changed(self, colors: dict):
        """分组颜色变更"""
        self._settings.group_colors = colors
        self._save_group_colors()
        # 刷新条目列表以应用新颜色
        if self._expanded:
            self._refresh_list()

    # ==================== 导入导出 ====================

    def _on_import(self):
        """导入 CSV 文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入CSV", "", "CSV 文件 (*.csv);;所有文件 (*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"无法读取文件：{e}")
            return

        if not rows:
            QMessageBox.information(self, "导入", "文件中没有数据。")
            return

        # 检测 CSV 列名（兼容中英文列名）
        sample = rows[0]
        grp_col = None
        content_col = None
        comment_col = None
        for col in sample.keys():
            cl = col.strip().lower()
            if cl in ("grp", "group", "分组", "组"):
                grp_col = col
            elif cl in ("content", "命令", "内容", "text"):
                content_col = col
            elif cl in ("comment", "注释", "备注", "note"):
                comment_col = col

        if content_col is None:
            QMessageBox.warning(self, "导入失败",
                                "CSV 文件中未找到内容列（需要 content/命令/内容 列）。\n"
                                f"现有列：{list(sample.keys())}")
            return

        # 提取所有分组
        groups_in_file = set()
        for row in rows:
            g = row.get(grp_col, "") if grp_col else ""
            groups_in_file.add(g.strip() if g.strip() else "其他")

        # 分组选择对话框
        groups_sorted = sorted(groups_in_file)
        dlg = GroupSelectDialog(groups_sorted, "选择要导入的分组", self, theme=self._settings.theme)
        if dlg.exec() != GroupSelectDialog.DialogCode.Accepted:
            return

        selected = set(dlg.selected_groups())
        if not selected:
            return

        # 过滤并导入
        to_import = []
        for row in rows:
            g = row.get(grp_col, "") if grp_col else ""
            g = g.strip() if g.strip() else "其他"
            if g not in selected:
                continue
            content = row.get(content_col, "").strip()
            if not content:
                continue
            comment = row.get(comment_col, "").strip() if comment_col else ""
            to_import.append((content, comment, g))

        if not to_import:
            QMessageBox.information(self, "导入", "没有可导入的数据。")
            return

        count = import_items(to_import)

        # 自动分配新分组颜色
        self._items = get_all_items()
        self._ensure_group_colors()

        # 刷新
        self._refresh_bar()
        self._refresh_list()
        self._refresh_settings_groups()

        QMessageBox.information(self, "导入完成", f"成功导入 {count} 条记录。")

    def _on_export(self):
        """导出 CSV 文件"""
        # 获取所有分组
        group_list = self._compute_group_list()
        export_groups = [g for g in group_list if g != "全部"]

        if not export_groups:
            QMessageBox.information(self, "导出", "没有可导出的数据。")
            return

        # 分组选择对话框
        dlg = GroupSelectDialog(export_groups, "选择要导出的分组", self, theme=self._settings.theme)
        if dlg.exec() != GroupSelectDialog.DialogCode.Accepted:
            return

        selected = set(dlg.selected_groups())
        if not selected:
            return

        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出CSV", "paste-helper-export.csv", "CSV 文件 (*.csv)"
        )
        if not file_path:
            return

        # 过滤条目
        items_to_export = [
            item for item in self._items
            if (item.grp if item.grp else "其他") in selected
        ]

        if not items_to_export:
            QMessageBox.information(self, "导出", "没有匹配的条目。")
            return

        try:
            with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["grp", "content", "comment"])
                for item in items_to_export:
                    writer.writerow([
                        item.grp if item.grp else "其他",
                        item.content,
                        item.comment,
                    ])
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"无法写入文件：{e}")
            return

        QMessageBox.information(
            self, "导出完成",
            f"成功导出 {len(items_to_export)} 条记录到：\n{file_path}"
        )

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
