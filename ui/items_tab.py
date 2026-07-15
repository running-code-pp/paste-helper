"""条目标签页 — 添加表单 + 条目列表"""

from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QScrollArea, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from models import ClipItem


class ItemWidget(QFrame):
    """单个条目展示"""

    clicked = Signal(int)        # idx
    delete_clicked = Signal(str)  # item_id

    def __init__(self, item: ClipItem, idx: int, selected: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("itemWidget")
        self._item = item
        self._idx = idx

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
        lbl.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(lbl, 1)

        if item.comment:
            comment_lbl = QLabel(f"📝{item.comment[:15]}")
            comment_lbl.setStyleSheet(
                "color: #8888a0; font-size: 11px; border: none; background: transparent;"
            )
            layout.addWidget(comment_lbl)

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
            self.clicked.emit(self._idx)


class ItemsTab(QWidget):
    """条目标签页"""

    item_added = Signal(str, str)     # content, comment
    item_deleted = Signal(str)        # item_id
    item_selected = Signal(int)       # idx

    def __init__(self, parent=None):
        super().__init__(parent)

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

        self.add_btn = QPushButton("添加")
        self.add_btn.setObjectName("addBtn")
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self._add_item)
        form_layout.addWidget(self.add_btn)

        layout.addLayout(form_layout)

        # ===== 条目列表 =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_container = QWidget()
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
        self.item_added.emit(content, comment)
        # 清空输入
        self.content_edit.clear()
        self.comment_edit.clear()
        self.content_edit.setFocus()

    def refresh(self, items: List[ClipItem], selected_idx: int):
        """刷新条目列表"""
        # 清除旧列表
        for i in reversed(range(self.list_layout.count())):
            w = self.list_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not items:
            self.empty_lbl.setVisible(True)
            return

        self.empty_lbl.setVisible(False)

        for i, item in enumerate(items):
            is_selected = (i == selected_idx)
            item_widget = ItemWidget(item, i, is_selected)
            item_widget.clicked.connect(self._on_item_clicked)
            item_widget.delete_clicked.connect(self._on_item_delete)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item_widget)

    def set_selected_index(self, idx: int):
        """高亮选中条目"""
        for i in range(self.list_layout.count()):
            w = self.list_layout.itemAt(i).widget()
            if isinstance(w, ItemWidget):
                w.setProperty("selected", "true" if w._idx == idx else "false")
                w.style().unpolish(w)
                w.style().polish(w)

    def _on_item_clicked(self, idx: int):
        self.item_selected.emit(idx)

    def _on_item_delete(self, item_id: str):
        self.item_deleted.emit(item_id)
