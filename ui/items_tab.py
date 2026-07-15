"""条目标签页 — 添加表单 + 条目列表"""

from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QScrollArea, QLabel, QFrame, QComboBox
)
from PySide6.QtCore import Qt, Signal
from models import ClipItem


class ItemWidget(QFrame):
    """单个条目展示"""

    clicked = Signal(int)        # real_idx（原始索引）
    delete_clicked = Signal(str)  # item_id

    def __init__(self, item: ClipItem, idx: int, real_idx: int, selected: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("itemWidget")
        self._item = item
        self._idx = idx              # 过滤后的位置（用于显示序号和选中高亮）
        self._real_idx = real_idx    # 原始索引（用于点击时通知 MainWindow）

        if selected:
            self.setProperty("selected", "true")
            self.style().unpolish(self)
            self.style().polish(self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 4, 4)
        layout.setSpacing(6)

        # 序号 + 内容
        display = f"{idx + 1}. {item.content[:50]}"
        if len(item.content) > 50:
            display += "…"
        lbl = QLabel(display)
        layout.addWidget(lbl, 1)

        if item.comment:
            comment_lbl = QLabel(f"📝{item.comment[:15]}")
            comment_lbl.setStyleSheet("font-size: 11px;")
            layout.addWidget(comment_lbl)

        # 分组标签
        grp_display = item.grp if item.grp else "其他"
        grp_lbl = QLabel(grp_display)
        grp_lbl.setStyleSheet(
            "font-size: 10px; color: #8888a0; background: transparent; "
            "border: 1px solid #4a4a60; border-radius: 2px; padding: 0px 5px; margin-left: 2px;"
        )
        layout.addWidget(grp_lbl)

        # 删除按钮（默认隐藏）
        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(22, 22)
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setVisible(False)
        self.del_btn.clicked.connect(lambda: self.delete_clicked.emit(item.id))
        layout.addWidget(self.del_btn)

    def enterEvent(self, event):
        self.del_btn.setVisible(True)

    def leaveEvent(self, event):
        self.del_btn.setVisible(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._real_idx)


class ItemsTab(QWidget):
    """条目标签页"""

    item_added = Signal(str, str, str)     # content, comment, grp
    item_deleted = Signal(str)        # item_id
    item_selected = Signal(int)       # idx

    def __init__(self, parent=None):
        super().__init__(parent)

        # 过滤状态
        self._all_items: List[ClipItem] = []
        self._filter_text: str = ""
        self._selected_idx: int = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 4)
        layout.setSpacing(6)

        # ===== 添加表单 =====
        form_layout = QHBoxLayout()
        form_layout.setSpacing(6)

        self.content_edit = QLineEdit()
        self.content_edit.setPlaceholderText("命令 / 文本内容...")
        self.content_edit.setMinimumHeight(30)
        self.content_edit.returnPressed.connect(self._add_item)
        self.content_edit.textChanged.connect(self._on_content_changed)
        form_layout.addWidget(self.content_edit, 2)

        self.comment_edit = QLineEdit()
        self.comment_edit.setPlaceholderText("注释（可选）")
        self.comment_edit.setMinimumHeight(30)
        self.comment_edit.returnPressed.connect(self._add_item)
        form_layout.addWidget(self.comment_edit, 1)

        self.group_combo = QComboBox()
        self.group_combo.setEditable(True)
        self.group_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.group_combo.setPlaceholderText("分组（可选）")
        self.group_combo.setToolTip("选择或输入分组名称")
        self.group_combo.setMinimumWidth(75)
        self.group_combo.setMaximumWidth(100)
        self.group_combo.setMinimumHeight(30)
        form_layout.addWidget(self.group_combo)

        self.add_btn = QPushButton("添加")
        self.add_btn.setObjectName("addBtn")
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self._add_item)
        form_layout.addWidget(self.add_btn)

        layout.addLayout(form_layout)

        # ===== 搜索框 =====
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchEdit")
        self.search_edit.setPlaceholderText("搜索命令 / 注释…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumHeight(30)
        self.search_edit.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self.search_edit)

        # ===== 条目列表 =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_container = QWidget()
        self.list_container.setObjectName("listContainer")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(3)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll, 1)

        # 空状态
        self.empty_lbl = QLabel("还没有保存的条目")
        self.empty_lbl.setObjectName("emptyLabel")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_lbl)

    def _on_content_changed(self, text: str):
        """内容非空才启用添加按钮"""
        self.add_btn.setEnabled(bool(text.strip()))

    def _add_item(self):
        """添加条目"""
        content = self.content_edit.text().strip()
        if not content:
            return
        comment = self.comment_edit.text().strip()
        grp = self.group_combo.currentText().strip()
        self.item_added.emit(content, comment, grp)
        # 清空输入
        self.content_edit.clear()
        self.comment_edit.clear()
        self.content_edit.setFocus()

    def refresh(self, items: List[ClipItem], selected_idx: int, groups: List[str] = None, current_grp: str = ""):
        """刷新条目列表（外部调用入口）"""
        self._all_items = items
        self._selected_idx = selected_idx

        # 更新表单中的分组下拉框
        if groups is not None:
            self.group_combo.blockSignals(True)
            cur = self.group_combo.currentText().strip()
            self.group_combo.clear()
            # 表单下拉框不需要"全部"选项
            form_groups = [g for g in groups if g != "全部"]
            self.group_combo.addItems(form_groups)
            self.group_combo.setCurrentText(cur or current_grp if current_grp != "全部" else "")
            self.group_combo.blockSignals(False)

        self._apply_filter()

    def _apply_filter(self):
        """根据当前搜索文本过滤并重新渲染"""
        # 清除旧列表
        for i in reversed(range(self.list_layout.count())):
            w = self.list_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not self._all_items:
            self.empty_lbl.setText("还没有保存的条目")
            self.empty_lbl.setVisible(True)
            return

        # 过滤
        if self._filter_text:
            tokens = self._filter_text.lower().split()
            filtered = []
            for real_idx, item in enumerate(self._all_items):
                text = f"{item.content} {item.comment}".lower()
                if all(token in text for token in tokens):
                    filtered.append((real_idx, item))
        else:
            filtered = [(i, item) for i, item in enumerate(self._all_items)]

        if not filtered:
            self.empty_lbl.setText("没有匹配的条目")
            self.empty_lbl.setVisible(True)
            return

        self.empty_lbl.setVisible(False)

        # 确定过滤后的选中索引
        filtered_selected = -1
        if 0 <= self._selected_idx < len(self._all_items):
            for fi, (ri, _) in enumerate(filtered):
                if ri == self._selected_idx:
                    filtered_selected = fi
                    break

        for filtered_i, (real_i, item) in enumerate(filtered):
            is_selected = (filtered_i == filtered_selected)
            item_widget = ItemWidget(item, filtered_i, real_i, is_selected)
            item_widget.clicked.connect(self._on_item_clicked)
            item_widget.delete_clicked.connect(self._on_item_delete)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item_widget)

    def _on_filter_changed(self, text: str):
        """搜索文本变更"""
        self._filter_text = text.strip()
        self._apply_filter()

    def set_selected_index(self, idx: int):
        """高亮选中条目（idx 为原始索引）"""
        self._selected_idx = idx
        for i in range(self.list_layout.count()):
            w = self.list_layout.itemAt(i).widget()
            if isinstance(w, ItemWidget):
                w.setProperty("selected", "true" if w._real_idx == idx else "false")
                w.style().unpolish(w)
                w.style().polish(w)

    def _on_item_clicked(self, idx: int):
        self.item_selected.emit(idx)

    def _on_item_delete(self, item_id: str):
        self.item_deleted.emit(item_id)
