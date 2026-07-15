"""SQLite 数据管理器 — 条目 CRUD + 设置读写"""

import os
import sqlite3
import uuid
import time
from typing import List, Optional
from models import ClipItem, AppSettings


DB_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "paste-helper")
DB_PATH = os.path.join(DB_DIR, "data.db")


def _get_conn() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """初始化数据库表"""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            grp TEXT DEFAULT '',
            content TEXT NOT NULL,
            comment TEXT DEFAULT '',
            created_at INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    # 初始化默认设置
    defaults = {
        "current_index": "-1",
        "current_grp": "",
        "opacity": "85",
        "prev_keys": "Ctrl,Up",
        "next_keys": "Ctrl,Down",
        "theme": "dark",
        "window_width": "420",
        "auto_collapse": "0",
        "group_colors": "{}",
    }
    for k, v in defaults.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES(?, ?)", (k, v)
        )
    conn.commit()
    conn.close()


# ---------- 条目操作 ----------

def get_all_items() -> List[ClipItem]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM items ORDER BY created_at ASC").fetchall()
    conn.close()
    return [ClipItem(
        id=row["id"], grp=row["grp"], content=row["content"],
        comment=row["comment"], created_at=row["created_at"]
    ) for row in rows]


def add_item(content: str, comment: str = "", grp: str = "") -> ClipItem:
    conn = _get_conn()
    item_id = str(uuid.uuid4())
    now = int(time.time())
    conn.execute(
        "INSERT INTO items(id, grp, content, comment, created_at) VALUES(?, ?, ?, ?, ?)",
        (item_id, grp, content, comment, now)
    )
    conn.commit()
    conn.close()
    return ClipItem(id=item_id, grp=grp, content=content, comment=comment, created_at=now)


def delete_item(item_id: str):
    conn = _get_conn()
    conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def update_item(item_id: str, content: str, comment: str):
    conn = _get_conn()
    conn.execute(
        "UPDATE items SET content = ?, comment = ? WHERE id = ?",
        (content, comment, item_id)
    )
    conn.commit()
    conn.close()


def update_item_group(item_id: str, grp: str):
    """更新条目的分组"""
    conn = _get_conn()
    conn.execute("UPDATE items SET grp = ? WHERE id = ?", (grp, item_id))
    conn.commit()
    conn.close()


def import_items(items: list) -> int:
    """批量导入条目，返回导入数量。每条为 (content, comment, grp)"""
    conn = _get_conn()
    import uuid as _uuid
    import time as _time
    count = 0
    for content, comment, grp in items:
        item_id = str(_uuid.uuid4())
        now = int(_time.time())
        conn.execute(
            "INSERT INTO items(id, grp, content, comment, created_at) VALUES(?, ?, ?, ?, ?)",
            (item_id, grp, content, comment, now)
        )
        count += 1
    conn.commit()
    conn.close()
    return count


# ---------- 设置操作 ----------

def get_settings() -> AppSettings:
    conn = _get_conn()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    kv = {row["key"]: row["value"] for row in rows}
    return AppSettings(
        current_index=int(kv.get("current_index", "-1")),
        current_grp=kv.get("current_grp", ""),
        opacity=int(kv.get("opacity", "85")),
        prev_keys=kv.get("prev_keys", "Ctrl,Up"),
        next_keys=kv.get("next_keys", "Ctrl,Down"),
        theme=kv.get("theme", "dark"),
        window_width=int(kv.get("window_width", "420")),
        auto_collapse=kv.get("auto_collapse", "0") == "1",
        group_colors=AppSettings.parse_group_colors(kv.get("group_colors", "{}")),
    )


def set_setting(key: str, value: str):
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)", (key, value)
    )
    conn.commit()
    conn.close()
