"""数据模型定义"""

import json
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ClipItem:
    """剪切板条目"""
    id: str = ""
    grp: str = ""           # 分组
    content: str = ""
    comment: str = ""
    created_at: int = 0     # Unix 时间戳


# 分组颜色预设（循环使用）
GROUP_COLOR_PRESETS = [
    "#4a7cf7", "#e74c3c", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#3498db",
]


@dataclass
class AppSettings:
    """应用设置"""
    current_index: int = -1
    current_grp: str = ""     # 当前选中的分组，"" = 全部
    opacity: int = 85        # 10-100
    prev_keys: str = "Ctrl,Up"
    next_keys: str = "Ctrl,Down"
    theme: str = "dark"       # "dark" | "light"
    window_width: int = 420   # 窗口宽度
    auto_collapse: bool = False  # 点击复制后自动收起面板
    group_colors: Dict[str, str] = field(default_factory=dict)  # 分组名 -> 颜色值

    def to_group_colors_json(self) -> str:
        return json.dumps(self.group_colors, ensure_ascii=False)

    @staticmethod
    def parse_group_colors(raw: str) -> Dict[str, str]:
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}

    @classmethod
    def defaults(cls) -> "AppSettings":
        return cls()
