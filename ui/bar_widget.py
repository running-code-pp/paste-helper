"""横条组件 — 导航按钮、索引、内容显示、展开/收起、关闭"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont


class BarWidget(QWidget):
    """屏幕顶部横条"""

    prev_clicked = Signal()
    next_clicked = Signal()
    expand_clicked = Signal()
    close_clicked = Signal()
    double_clicked = Signal()

    # 悬浮信号
    hover_enter = Signal()
    hover_leave = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("barWidget")
        self.setMouseTracking(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(2)

        # 1. ◀ 按钮
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setToolTip("上一条 (Ctrl+Up)")
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self.prev_clicked.emit)
        layout.addWidget(self.prev_btn)

        # 2. 索引显示 "3/10"
        self.index_lbl = QLabel("-/-")
        self.index_lbl.setObjectName("indexLabel")
        self.index_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.index_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        font = self.index_lbl.font()
        font.setPointSize(10)
        self.index_lbl.setFont(font)
        layout.addWidget(self.index_lbl)

        # 3. 内容文本
        self.content_lbl = QLabel("暂无内容 — 双击添加")
        self.content_lbl.setObjectName("contentLabel")
        self.content_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        # 截断
        self.content_lbl.setMaximumWidth(240)
        layout.addWidget(self.content_lbl, 1)

        # 4. ▶ 按钮
        self.next_btn = QPushButton("▶")
        self.next_btn.setToolTip("下一条 (Ctrl+Down)")
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_clicked.emit)
        layout.addWidget(self.next_btn)

        # 5. ▼ 展开按钮
        self.expand_btn = QPushButton("▼")
        self.expand_btn.setObjectName("expandBtn")
        self.expand_btn.setToolTip("展开 / 收起面板")
        self.expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.expand_btn.clicked.connect(self.expand_clicked.emit)
        layout.addWidget(self.expand_btn)

        # 6. ✕ 关闭按钮
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setToolTip("退出应用")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.close_btn)

        # ===== 提示条 =====
        self._tooltip = QLabel(self)
        self._tooltip.setObjectName("tooltipWidget")
        self._tooltip.setWindowFlags(
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self._tooltip.setVisible(False)
        self._tooltip.setMaximumWidth(400)
        self._tooltip.setWordWrap(True)

        # ===== Toast =====
        self._toast = QLabel(self)
        self._toast.setObjectName("toastLabel")
        self._toast.setWindowFlags(
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self._toast.setVisible(False)
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._hide_toast)

        # 悬浮计时器
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self.hover_enter.emit)

    # ==================== 更新显示 ====================

    def set_index(self, index: int, total: int):
        if total == 0:
            self.index_lbl.setText("-/-")
            self.index_lbl.setToolTip("")
        else:
            display_idx = index + 1
            self.index_lbl.setText(f"{display_idx}/{total}")
            self.index_lbl.setToolTip(f"第 {display_idx} 条，共 {total} 条")

    def set_content(self, content: str, comment: str):
        display = content[:60] + "…" if len(content) > 60 else content
        if comment:
            display += f" · {comment[:20]}"
        self.content_lbl.setText(display)
        self.content_lbl.setToolTip("")

    def update_expand_state(self, expanded: bool):
        self.expand_btn.setText("▲" if expanded else "▼")
        self.expand_btn.setToolTip("收起面板" if expanded else "展开面板")

    # ==================== 提示条 ====================

    def show_tooltip(self, content: str, comment: str):
        text = content
        if comment:
            text += f"\n\n📝 {comment}"
        text += "\n\nCtrl+C 快捷复制"
        self._tooltip.setText(text)
        self._tooltip.adjustSize()

        # 定位于横条下方
        pos = self.mapToGlobal(self.rect().bottomLeft())
        pos.setX(pos.x() + 10)
        pos.setY(pos.y() + 4)
        self._tooltip.move(pos)
        self._tooltip.setVisible(True)

    def hide_tooltip(self):
        self._tooltip.setVisible(False)

    # ==================== Toast ====================

    def show_toast(self, text: str):
        self._toast.setText(text)
        self._toast.adjustSize()
        pos = self.mapToGlobal(self.rect().topRight())
        pos.setX(pos.x() - self._toast.width() - 50)
        pos.setY(pos.y() + 45)
        self._toast.move(pos)
        self._toast.setVisible(True)
        self._toast_timer.start(1500)

    def _hide_toast(self):
        self._toast.setVisible(False)

    # ==================== 事件 ====================

    def mouseDoubleClickEvent(self, event):
        """双击 → 展开/收起"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()

    def enterEvent(self, event):
        """鼠标进入 → 启动悬浮计时器"""
        self._hover_timer.start(300)  # 300ms 后触发

    def leaveEvent(self, event):
        """鼠标离开 → 取消悬浮计时器，通知外部"""
        self._hover_timer.stop()
        self.hover_leave.emit()

    def mousePressEvent(self, event):
        """点击横条空白处拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint()
            self.window().windowHandle().startSystemMove()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 截断内容
        w = self.width()
        available = w - 200  # 减去按钮等占用的宽度
        self.content_lbl.setMaximumWidth(max(60, available))
        # 文本截断
        self._truncate_content()

    def _truncate_content(self):
        """根据可用宽度截断文本"""
        text = self.content_lbl.text()
        fm = self.content_lbl.fontMetrics()
        max_w = self.content_lbl.maximumWidth()
        if fm.horizontalAdvance(text) > max_w:
            elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, max_w)
            self.content_lbl.setText(elided)
