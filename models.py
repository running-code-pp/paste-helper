"""数据模型定义"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ClipItem:
    """剪切板条目"""
    id: str = ""
    grp: str = ""           # 分组（预留）
    content: str = ""
    comment: str = ""
    created_at: int = 0     # Unix 时间戳


@dataclass
class AppSettings:
    """应用设置"""
    current_index: int = -1
    opacity: int = 85        # 10-100
    prev_keys: str = "Ctrl,Up"
    next_keys: str = "Ctrl,Down"
    theme: str = "dark"       # "dark" | "light"

    @classmethod
    def defaults(cls) -> "AppSettings":
        return cls()
