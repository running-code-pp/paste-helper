"""系统剪切板操作 — 使用 PySide6 QClipboard"""

from PySide6.QtWidgets import QApplication


def copy_to_clipboard(text: str):
    """复制文本到系统剪切板"""
    if not text:
        return
    app = QApplication.instance()
    if app:
        clipboard = app.clipboard()
        clipboard.setText(text)
