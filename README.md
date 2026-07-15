# Paste Helper（粘贴助手）

> Windows 桌面剪切板管理工具 — PySide6 实现

轻量级 Windows 桌面剪切板管理工具，预存常用文本片段（命令、代码、模板、回复等），通过全局快捷键在任意应用中快速切换并粘贴。

## 截图（深色主题）

```
┌──────────────────────────────────────────────┐
│ ◀  1/3  echo hello world · 测试    ▶  ▼  ✕  │  ← 横条 420×40
├──────────────────────────────────────────────┤
│  [条目]  [设置]                              │
│                                              │
│  ┌────────────────────────┐ ┌────────┐ ┌──┐ │
│  │ 命令 / 文本内容...      │ │注释(可选)│ │添加│ │
│  └────────────────────────┘ └────────┘ └──┘ │
│                                              │
│  ┃ 1. echo hello world      📝测试       ✕  │
│  ┃ 2. git commit -m "..."              ✕  │  ← 抽屉 420×400
│  ┃ 3. npm run dev                      ✕  │
│                                              │
└──────────────────────────────────────────────┘
```

## 功能

| 功能 | 说明 |
|------|------|
| 横条显示 | 当前条目内容、索引、导航按钮 |
| 抽屉面板 | 条目管理（添加/删除/选中）+ 设置 |
| 全局快捷键 | Ctrl+Up / Ctrl+Down 切换条目（可自定义） |
| 自动复制 | 切换条目时自动复制到系统剪切板 |
| 主题切换 | 深色 / 浅色一键切换 |
| 透明度调节 | 10%-100% 滑块调节，150ms 防抖 |
| 系统托盘 | 图标驻留，左键打开面板，右键菜单 |
| 快捷键捕获 | 点击进入捕获模式，按下组合键保存 |

## 技术栈

- **Python 3.11+** + **PySide6** 原生 Qt 桌面框架
- **SQLite** 数据持久化（`%APPDATA%/paste-helper/data.db`）
- **Win32 API** (ctypes) 全局快捷键 RegisterHotKey
- **QSS** 样式表实现深色/浅色主题

## 项目结构

```
paster-helper/
├── main.py                  # 应用入口
├── models.py                # 数据模型
├── database.py              # SQLite CRUD + 设置
├── clipboard.py             # 系统剪切板操作
├── hotkey.py                # 全局快捷键 (Win32)
├── requirements.txt         # Python 依赖
│
├── ui/
│   ├── main_window.py       # 主窗口（无边框/置顶/动画）
│   ├── bar_widget.py        # 横条组件
│   ├── drawer_widget.py     # 抽屉面板
│   ├── items_tab.py         # 条目标签页
│   ├── settings_tab.py      # 设置标签页
│   └── tray_manager.py      # 系统托盘
│
├── styles/
│   └── theme.py             # 深色/浅色 QSS 主题
│
└── resources/
    └── icon.ico             # 应用图标
```

## 快速开始

```bash
# 1. 安装依赖
uv pip install PySide6

# 2. 运行
cd paster-helper
python main.py
```

## 使用说明

| 操作 | 方式 |
|------|------|
| 添加条目 | 展开抽屉 → 条目标签页 → 输入内容 + 注释 → 添加 |
| 切换条目 | 横条 ◀▶ 按钮 / Ctrl+Up / Ctrl+Down |
| 展开面板 | 横条 ▼ 按钮 / 双击横条 |
| 选中条目 | 列表中点击条目 → 自动复制到剪切板 |
| 删除条目 | 列表项悬浮 → 点击 ✕ |
| 调整透明度 | 设置标签页 → 拖动滑块 |
| 自定义快捷键 | 设置标签页 → 点击快捷键按钮 → 按下组合键 |
| 切换主题 | 设置标签页 → 选择深色/浅色 |
| 隐藏到托盘 | 点击横条 ✕ → 窗口隐藏，托盘驻留 |
| 退出应用 | 托盘右键 → 退出 |

## 数据存储

SQLite 数据库位于 `%APPDATA%/paste-helper/data.db`，包含两张表：

- **items** — 剪切板条目（id, content, comment, created_at）
- **settings** — 应用设置（键值对：current_index, opacity, prev_keys, next_keys, theme）
